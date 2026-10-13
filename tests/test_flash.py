import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from context import CFG, HAVE_BASE, ROOT, SLOW, TempDirCase, mkdtemp, needs_base, slow
from r36img import build, flash, layout, mtools
from r36img.errors import R36Error
from r36img.util import MIB, sha256_file

FIXTURE = json.loads((ROOT / "tests/fixtures/lsblk_este_pc.json").read_text())
TS = "20261013-153045"
SHARED = {}


def setUpModule():
    if HAVE_BASE and SLOW:
        SHARED["tmp"] = mkdtemp("r36flash-")
        SHARED["out"] = SHARED["tmp"] / "out"
        with contextlib.redirect_stdout(io.StringIO()):
            build.build(CFG, none=True, timestamp=TS, out_root=SHARED["out"],
                        work_root=SHARED["tmp"] / "work", compress=False)


def tearDownModule():
    if "tmp" in SHARED:
        shutil.rmtree(SHARED["tmp"], ignore_errors=True)


def args(*argv):
    return flash.parse_args(list(argv))


def quiet(fn, *a, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        r = fn(*a, **kw)
    return r, buf.getvalue()


class TargetDetectionTest(unittest.TestCase):
    """7.1: travas sobre a saída real do lsblk deste PC."""

    def test_internal_disks_refused(self):
        for dev in ("/dev/sda", "/dev/sdb", "/dev/nvme0n1", "/dev/zram0"):
            with self.subTest(dev=dev), self.assertRaises(R36Error) as cm:
                flash.inspect_device(dev, FIXTURE)
            self.assertIn("não é removível", str(cm.exception))

    def test_sdc_accepted(self):
        info = flash.inspect_device("/dev/sdc", FIXTURE)
        self.assertEqual((info.name, info.size, info.removable), ("sdc", 15728640000, True))
        self.assertEqual(sorted(p for p, _ in info.mounted), ["sdc1", "sdc2", "sdc7"])

    def test_partition_refused(self):
        with self.assertRaises(R36Error) as cm:
            flash.inspect_device("/dev/sdc1", FIXTURE)
        self.assertIn("disco inteiro", str(cm.exception))
        self.assertIn("/dev/sdc", str(cm.exception))

    def test_unknown_device(self):
        with self.assertRaises(R36Error):
            flash.inspect_device("/dev/sdz", FIXTURE)

    def test_removable_with_system_mount_refused(self):
        data = {"blockdevices": [{"name": "sdd", "type": "disk", "rm": True, "size": 16 << 30,
                                  "children": [{"name": "sdd1", "type": "part", "mountpoints": ["/"]}]}]}
        with self.assertRaises(R36Error) as cm:
            flash.inspect_device("/dev/sdd", data)
        self.assertIn("sistema do PC", str(cm.exception))

    def test_swap_refused(self):
        data = {"blockdevices": [{"name": "sdd", "type": "disk", "rm": "1", "size": 16 << 30,
                                  "children": [{"name": "sdd1", "type": "part", "mountpoints": ["[SWAP]"]}]}]}
        with self.assertRaises(R36Error):
            flash.inspect_device("/dev/sdd", data)

    def test_mmcblk_accepted_even_rm0(self):
        data = {"blockdevices": [{"name": "mmcblk0", "type": "disk", "rm": False, "size": 16 << 30}]}
        self.assertEqual(flash.inspect_device("/dev/mmcblk0", data).name, "mmcblk0")


class ArgsTest(unittest.TestCase):
    """7.6: combinações inválidas."""

    def assertRefused(self, *argv, contains):
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf), self.assertRaises(SystemExit) as cm:
            flash.parse_args(list(argv))
        self.assertEqual(cm.exception.code, 2)
        self.assertIn(contains, buf.getvalue())

    def test_invalid_combinations(self):
        self.assertRefused("--device", "/dev/sdc", "--all", "--keep-roms", "--wipe-roms", "--wipe-storage",
                           contains="--keep-roms e --wipe-roms")
        self.assertRefused("--device", "/dev/sdc", "--all", "--keep-storage", "--wipe-storage",
                           contains="--keep-storage e --wipe-storage")
        self.assertRefused("--device", "/dev/sdc", "--all", contains="--keep-storage (manter) ou --wipe-storage")
        self.assertRefused("--device", "/dev/sdc", "--part", "roms", contains="--wipe-roms")
        self.assertRefused("--device", "/dev/sdc", "--part", "storage", contains="--wipe-storage")
        self.assertRefused("--device", "/dev/sdc", "--all", "--part", "system", "--wipe-storage", contains="--all")
        self.assertRefused("--device", "/dev/sdc", contains="--all")
        self.assertRefused("--all", "--wipe-storage", contains="--device ou --target-file")
        self.assertRefused("--device", "x", "--target-file", "y", "--part", "boot", contains="exatamente um alvo")
        self.assertRefused("--device", "/dev/sdc", "--part", "kernel", contains="não aceita")
        self.assertRefused("--device", "/dev/sdc", "--part", "boot", "--keep-roms", contains="só valem com --all")
        self.assertRefused("--device", "/dev/sdc", "--part", "boot", "--build", "ontem", contains="AAAAMMDD-HHMMSS")

    def test_help_lists_all_options(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit):
            flash.parse_args(["--help"])
        for opt in ("--device", "--target-file", "--all", "--part", "--keep-roms", "--wipe-roms",
                    "--keep-storage", "--wipe-storage", "--dry-run", "--build"):
            self.assertIn(opt, buf.getvalue())

    def test_parts_deduplicated_in_order(self):
        a = args("--device", "/dev/sdc", "--part", "system", "--part", "boot", "--part", "system")
        self.assertEqual(a.part, ["boot", "system"])


class BuildSelectionTest(TempDirCase):
    def _mk(self, *names):
        for n in names:
            (self.tmp / n).mkdir()
            (self.tmp / n / "manifest.json").write_text("{}")

    def test_latest_by_default(self):
        self._mk("20261013-153045", "20261014-090000")
        (self.tmp / "lixo").mkdir()
        self.assertEqual(flash.resolve_build(self.tmp).name, "20261014-090000")

    def test_missing_build_lists_available(self):
        self._mk("20261013-153045", "20261014-090000")
        with self.assertRaises(R36Error) as cm:
            flash.resolve_build(self.tmp, "20990101-000000")
        msg = str(cm.exception)
        self.assertIn("20990101-000000 não existe", msg)
        self.assertIn("20261013-153045", msg)
        self.assertIn("20261014-090000", msg)

    def test_no_builds(self):
        with self.assertRaises(R36Error):
            flash.resolve_build(self.tmp / "out")


FEATS = [{"id": "10-ptbr-sao-paulo", "name": "PT-BR", "order": 10},
         {"id": "20-controle-posicional", "name": "Controle", "order": 20}]
OLD, NEW = "20261013-101231", "20261013-124416"


def mk_build(root, ts, features=(), raw=None):
    d = root / ts
    d.mkdir()
    manifest = {"timestamp": ts, "card_size_mib": 15000, "features": list(features)}
    (d / "manifest.json").write_text(raw if raw is not None else json.dumps(manifest))
    return d


class BuildInfoTest(TempDirCase):
    """Linha de cada build e --list-builds sobre um out/ temporário."""

    def mk(self, ts, features=(), raw=None):
        return mk_build(self.tmp, ts, features, raw)

    def test_line_with_features(self):
        line = flash.build_line(self.mk(NEW, FEATS))
        self.assertEqual(line, f"{NEW}  15000 MiB  10-ptbr-sao-paulo, 20-controle-posicional")

    def test_line_without_features(self):
        self.assertEqual(flash.build_line(self.mk(OLD)), f"{OLD}  15000 MiB  sem features")

    def test_line_corrupted_manifest(self):
        d = self.mk(OLD, raw="{nada")
        self.assertEqual(flash.build_line(d), f"{OLD}  manifest ilegível")
        self.assertFalse(flash.build_readable(d))
        self.assertEqual(flash.build_line(self.mk(NEW, raw="{}")), f"{NEW}  manifest ilegível")

    def test_list_builds_args_need_no_target(self):
        a = args("--list-builds")
        self.assertTrue(a.list_builds)
        self.assertIsNone(a.device)

    def test_list_builds_newest_first(self):
        self.mk(OLD)
        self.mk(NEW, FEATS)
        rc, out = quiet(flash.flash, args("--list-builds"), out_root=self.tmp,
                        input_fn=lambda _p: self.fail("não deveria perguntar"))
        self.assertEqual(rc, 0)
        self.assertIn(f"1) {NEW}  15000 MiB  10-ptbr-sao-paulo", out)
        self.assertIn(f"2) {OLD}  15000 MiB  sem features", out)
        self.assertLess(out.index(NEW), out.index(OLD))

    def test_list_builds_empty(self):
        rc, out = quiet(flash.flash, args("--list-builds"), out_root=self.tmp / "out")
        self.assertEqual(rc, 0)
        self.assertIn("Nenhum build", out)
        self.assertIn("./build.sh", out)


class BuildMenuTest(TempDirCase):
    """Menu de escolha do build, com a digitação simulada por input_fn."""

    def setUp(self):
        super().setUp()
        mk_build(self.tmp, OLD)
        mk_build(self.tmp, NEW, FEATS)
        self.prompts = []

    def answers(self, *seq):
        it = iter(seq)

        def fn(prompt):
            self.prompts.append(prompt)
            ans = next(it)
            if ans is EOFError:
                raise EOFError
            return ans
        return fn

    def select(self, *seq, ts=None, interactive=True):
        return quiet(flash.select_build, self.tmp, ts, interactive=interactive, input_fn=self.answers(*seq))

    def test_choose_second(self):
        d, out = self.select("2")
        self.assertEqual(d.name, OLD)
        self.assertIn(f"1) {NEW}  15000 MiB  10-ptbr-sao-paulo, 20-controle-posicional  (mais recente)", out)
        self.assertIn(f"2) {OLD}  15000 MiB  sem features", out)

    def test_enter_picks_newest(self):
        d, _ = self.select("")
        self.assertEqual(d.name, NEW)

    def test_invalid_asks_again(self):
        d, out = self.select("9", "1")
        self.assertEqual(d.name, NEW)
        self.assertEqual(len(self.prompts), 2)
        self.assertIn("'9' não existe", out)

    def test_unreadable_cannot_be_chosen(self):
        (self.tmp / OLD / "manifest.json").write_text("{nada")
        d, out = self.select("2", "1")
        self.assertEqual(d.name, NEW)
        self.assertIn("manifest ilegível", out)

    def test_eof_cancels(self):
        d, _ = self.select(EOFError)
        self.assertIsNone(d)

    def test_single_build_no_menu(self):
        shutil.rmtree(self.tmp / OLD)
        d, out = self.select()
        self.assertEqual(d.name, NEW)
        self.assertEqual(self.prompts, [])
        self.assertEqual(out, "")

    def test_explicit_build_no_menu(self):
        d, _ = self.select(ts=OLD)
        self.assertEqual(d.name, OLD)
        self.assertEqual(self.prompts, [])

    def test_not_interactive_uses_newest(self):
        d, _ = self.select(interactive=False)
        self.assertEqual(d.name, NEW)
        self.assertEqual(self.prompts, [])

    def test_flash_eof_writes_nothing_before_touching_target(self):
        card = self.tmp / "cartao.img"
        card.write_bytes(b"")
        card.chmod(0o444)
        a = args("--target-file", str(card), "--all", "--wipe-roms", "--wipe-storage")
        rc, out = quiet(flash.flash, a, out_root=self.tmp, input_fn=self.answers(EOFError), interactive=True)
        self.assertEqual(rc, 1)
        self.assertIn("nada foi escrito", out)
        self.assertEqual(len(self.prompts), 1)
        self.assertNotIn("Alvo:", out)


@needs_base
@slow
class FlashWithBuildTest(TempDirCase):
    """7.2–7.5 com --target-file sobre um build real de 15000 MiB."""

    def setUp(self):
        super().setUp()
        self.out = SHARED["out"]
        self.build_dir = self.out / TS
        self.manifest = flash.load_manifest(self.build_dir)

    def card(self, mib=15000):
        p = self.tmp / "cartao.img"
        with open(p, "wb") as f:
            f.truncate(mib * MIB)
        return p

    def run_flash(self, *argv, answer=None, out_root=None):
        a = args(*argv)
        answers = iter([answer if answer is not None else Path(a.target_file).name])
        return quiet(flash.flash, a, out_root=out_root or self.out, input_fn=lambda _p: next(answers))

    def full_write(self, card):
        rc, log = self.run_flash("--target-file", str(card), "--all", "--wipe-roms", "--wipe-storage")
        self.assertEqual(rc, 0, log)
        return log

    # ---------------------------------------------------------------- 7.2
    def test_card_state_blank_incompatible(self):
        st = flash.read_card(flash.FileTarget(self.card()), self.build_dir, self.manifest)
        self.assertFalse(st.compatible)
        self.assertFalse(st.has_roms)

    def test_card_state_compatible_and_roms(self):
        card = self.card()
        self.full_write(card)
        t = flash.FileTarget(card)
        st = flash.read_card(t, self.build_dir, self.manifest)
        self.assertTrue(st.compatible, st.reasons)
        self.assertTrue(st.p1_compatible)
        self.assertTrue(st.roms_known)
        self.assertFalse(st.has_roms)
        rom = self.tmp / "Super Jogo.sfc"
        rom.write_bytes(os.urandom(3 * MIB))
        off = self.manifest["regions"]["roms"]["offset"]
        subprocess.run(["mcopy", "-i", f"{card}@@{off}", str(rom), "::/snes/"], check=True,
                       env=dict(os.environ, **mtools.ENV))
        st = flash.read_card(t, self.build_dir, self.manifest)
        self.assertTrue(st.has_roms)
        self.assertEqual(st.roms_extra, ["snes/Super Jogo.sfc"])
        self.assertGreaterEqual(st.roms_extra_bytes, 3 * MIB)

    def test_card_with_other_layout_incompatible(self):
        card = self.card()
        self.full_write(card)
        with open(card, "r+b") as f:  # move a p8 (EBR 4)
            f.seek(4 * 512 + 0x1BE + 8)
            f.write((1000).to_bytes(4, "little"))
        st = flash.read_card(flash.FileTarget(card), self.build_dir, self.manifest)
        self.assertFalse(st.compatible)
        self.assertIn("lógicas", " ".join(st.reasons))

    # ---------------------------------------------------------------- 7.3
    def plan(self, card, *argv):
        a = args("--target-file", str(card), *argv)
        t = flash.FileTarget(card)
        st = flash.read_card(t, self.build_dir, self.manifest)
        return flash.make_plan(a, self.build_dir, self.manifest, st, t.size)

    def test_plan_full(self):
        p = self.plan(self.card(), "--all", "--wipe-storage")
        self.assertEqual([i.name for i in p.items], list(flash.FULL_ORDER))
        boot = next(i for i in p.items if i.name == "boot")
        self.assertEqual((boot.offset, boot.length), (73728 * 512, 16 * MIB))
        roms = next(i for i in p.items if i.name == "roms")
        self.assertEqual(roms.length, self.manifest["regions"]["roms"]["write_length"])

    def test_plan_card_too_small(self):
        with self.assertRaises(R36Error) as cm:
            self.plan(self.card(7600), "--all", "--wipe-storage")
        msg = str(cm.exception)
        self.assertIn("cartão menor que a imagem", msg)
        self.assertIn(str(7600 * MIB), msg)
        self.assertIn(str(15000 * MIB), msg)
        self.assertIn("--size-mib 7600", msg)

    def test_plan_big_card_warns(self):
        p = self.plan(self.card(122000), "--all", "--wipe-storage")
        self.assertTrue(any("sem uso" in w for w in p.warnings))

    def test_partial_requires_compatible(self):
        with self.assertRaises(R36Error) as cm:
            self.plan(self.card(), "--part", "system")
        self.assertIn("gravação completa primeiro", str(cm.exception))

    def test_roms_present_requires_choice(self):
        card = self.card()
        self.full_write(card)
        off = self.manifest["regions"]["roms"]["offset"]
        rom = self.tmp / "jogo.nes"
        rom.write_bytes(os.urandom(MIB))
        subprocess.run(["mcopy", "-i", f"{card}@@{off}", str(rom), "::/nes/"], check=True,
                       env=dict(os.environ, **mtools.ENV))
        with self.assertRaises(R36Error) as cm:
            self.plan(card, "--all", "--wipe-storage")
        msg = str(cm.exception)
        self.assertIn("--keep-roms", msg)
        self.assertIn("--wipe-roms", msg)
        self.assertIn("MiB", msg)
        p = self.plan(card, "--all", "--keep-roms", "--keep-storage")
        self.assertEqual([i.name for i in p.items], ["bootarea", "boot", "env", "kernel", "system"])
        self.assertIsNotNone(p.items[0].override)
        p = self.plan(card, "--all", "--wipe-roms", "--wipe-storage")
        self.assertIn("roms", [i.name for i in p.items])

    def test_keep_roms_incompatible_refused(self):
        with self.assertRaises(R36Error) as cm:
            self.plan(self.card(), "--all", "--keep-roms", "--wipe-storage")
        self.assertIn("--keep-roms recusado", str(cm.exception))

    def test_partial_boot_is_16mib(self):
        card = self.card()
        self.full_write(card)
        p = self.plan(card, "--part", "boot")
        self.assertEqual([(i.name, i.offset, i.length) for i in p.items], [("boot", 73728 * 512, 16777216)])

    # ---------------------------------------------------------------- 7.4
    def test_wrong_confirmation_writes_nothing(self):
        card = self.card()
        before = os.stat(card).st_mtime_ns
        rc, log = self.run_flash("--target-file", str(card), "--all", "--wipe-roms", "--wipe-storage",
                                 answer="sdc")
        self.assertEqual(rc, 1)
        self.assertIn("nada foi escrito", log)
        self.assertEqual(os.stat(card).st_mtime_ns, before)
        self.assertEqual(os.stat(card).st_blocks, 0)

    def test_dry_run_does_not_open_for_write(self):
        card = self.card()
        card.chmod(0o444)
        rc, log = self.run_flash("--target-file", str(card), "--all", "--wipe-roms", "--wipe-storage", "--dry-run",
                                 answer="NUNCA")
        self.assertEqual(rc, 0, log)
        self.assertIn("nada foi escrito", log)
        self.assertIn("Regiões a escrever", log)
        self.assertIn("Dados que serão apagados", log)
        self.assertEqual(os.stat(card).st_blocks, 0)

    def test_dry_run_plan_shows_build_line(self):
        rc, log = self.run_flash("--target-file", str(self.card()), "--all", "--wipe-roms", "--wipe-storage",
                                 "--dry-run", answer="NUNCA")
        self.assertEqual(rc, 0, log)
        size = self.manifest["card_size_mib"]
        self.assertIn(f"Build: {TS}  {size} MiB  sem features", log)
        self.assertLess(log.index("Build:"), log.index("Regiões a escrever"))

    def test_unmount_device_uses_udisksctl_then_umount(self):
        calls = []

        class P:
            def __init__(self, rc):
                self.returncode, self.stderr = rc, "falhou"

        def fake_run(cmd, **kw):
            calls.append(cmd[:2])
            return P(1 if cmd[0] == "udisksctl" else 0)

        info = flash.DiskInfo("sdc", "/dev/sdc", 1, mounted=[("sdc1", "/run/media/u/EEROMS")])
        orig = flash.subprocess.run
        flash.subprocess.run = fake_run
        try:
            quiet(flash.DeviceTarget(info).unmount)
        finally:
            flash.subprocess.run = orig
        self.assertEqual(calls, [["udisksctl", "unmount"], ["sudo", "umount"]])

    # ---------------------------------------------------------------- 7.5
    def test_end_to_end(self):
        card = self.card(15000)
        log = self.full_write(card)
        self.assertIn("verificado", log)
        self.assertNotIn("DIVERGENTE", log)
        regions = self.manifest["regions"]
        for name in flash.FULL_ORDER:
            r = regions[name]
            self.assertEqual(sha256_file(card, r["write_length"], r["offset"]), r["sha256"], name)
        out = subprocess.run(["sfdisk", "-d", str(card)], capture_output=True, text=True, check=True).stdout
        self.assertIn("start=     4956160, size=    25763840, type=c", out)

        # --part system: só a p7 muda
        def snapshot():
            return {n: sha256_file(card, regions[n]["write_length"], regions[n]["offset"])
                    for n in ("bootarea", "boot", "env", "kernel", "storage", "roms")}
        with open(card, "r+b") as f:  # estraga a p7 para ver a regravação
            f.seek(regions["system"]["offset"] + 1024 * 1024)
            f.write(b"\xff" * 4096)
        before = snapshot()
        rc, log = self.run_flash("--target-file", str(card), "--part", "system")
        self.assertEqual(rc, 0, log)
        self.assertEqual(snapshot(), before)
        r = regions["system"]
        self.assertEqual(sha256_file(card, r["size"], r["offset"]), r["sha256"])

        # --keep-roms: p1 byte a byte igual (com uma ROM extra)
        off = regions["roms"]["offset"]
        rom = self.tmp / "jogo.gba"
        rom.write_bytes(os.urandom(2 * MIB))
        subprocess.run(["mcopy", "-i", f"{card}@@{off}", str(rom), "::/gba/"], check=True,
                       env=dict(os.environ, **mtools.ENV))
        p1_before = sha256_file(card, os.path.getsize(card) - off, off)
        entry_before = layout.p1_entry_bytes(flash.FileTarget(card).read(0, 512))
        rc, log = self.run_flash("--target-file", str(card), "--all", "--keep-roms", "--wipe-storage")
        self.assertEqual(rc, 0, log)
        self.assertEqual(sha256_file(card, os.path.getsize(card) - off, off), p1_before)
        self.assertEqual(layout.p1_entry_bytes(flash.FileTarget(card).read(0, 512)), entry_before)
        self.assertIn("gba/jogo.gba", mtools.listing(card, off))

    def test_corrupted_artifact_raises(self):
        bad_root = self.tmp / "out"
        (bad_root / TS / "parts").mkdir(parents=True)
        shutil.copy(self.build_dir / "manifest.json", bad_root / TS)
        for p in (self.build_dir / "parts").iterdir():
            os.symlink(p, bad_root / TS / "parts" / p.name)
        kernel = bad_root / TS / "parts/kernel.img"
        kernel.unlink()
        shutil.copy(self.build_dir / "parts/kernel.img", kernel)
        with open(kernel, "r+b") as f:
            f.write(b"corrompido")
        card = self.card()
        with self.assertRaises(R36Error) as cm:
            self.run_flash("--target-file", str(card), "--all", "--wipe-roms", "--wipe-storage", out_root=bad_root)
        self.assertIn("artefato corrompido", str(cm.exception))
        self.assertEqual(os.stat(card).st_blocks, 0)


if __name__ == "__main__":
    unittest.main()
