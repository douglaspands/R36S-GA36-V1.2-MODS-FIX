import os
import subprocess
import unittest
from pathlib import Path

from context import CFG, TempDirCase, mcopy, mkfat, needs_base
from r36img import ext4, fat, features as F, mtools, parts
from r36img.errors import R36Error
from r36img.util import MIB, extract_region
from test_features import desc, write_feature


def run(*cmd, **kw):
    return subprocess.run([str(c) for c in cmd], check=True, capture_output=True, text=True, **kw)


class StorageTest(TempDirCase):
    """5.1: ext4 pequeno criado com mke2fs -d."""

    def setUp(self):
        super().setUp()
        src = self.tmp / "src"
        (src / ".config/emuelec/configs").mkdir(parents=True)
        (src / ".config/emuelec/configs/emuelec.conf").write_text("original\n")
        (src / "roms").mkdir()
        self.img = self.tmp / "storage.img"
        run("mke2fs", "-q", "-t", "ext4", "-d", src, "-E", "root_owner=0:0", self.img, "16M")
        # o mke2fs -d copia o dono do usuário: força 0:0 e um modo especial como na base
        script = 'sif "/.config" uid 0\nsif "/.config" gid 0\n'
        for p in ("/.config/emuelec", "/.config/emuelec/configs", "/roms"):
            script += f'sif "{p}" uid 0\nsif "{p}" gid 0\n'
        script += 'sif "/.config/emuelec/configs/emuelec.conf" uid 0\nsif "/.config/emuelec/configs/emuelec.conf" gid 0\n'
        script += 'sif "/.config/emuelec/configs/emuelec.conf" mode 0100600\n'
        run("debugfs", "-w", "-f", "-", self.img, input=script)
        self.feats = self.tmp / "feats"

    def test_listing(self):
        e = ext4.listing(self.img)
        self.assertEqual(e[".config/emuelec/configs/emuelec.conf"].describe(), "-rw------- 0/0 9")
        self.assertEqual(e["roms"].type, "d")

    def test_apply_add_replace_meta(self):
        write_feature(self.feats, "10-a", desc(extra=(
            '[[meta]]\nlayer = "storage"\npath = "bin/ferramenta"\nmode = "4750"\nuid = 0\ngid = 81\n')), {
            "storage/.config/emuelec/configs/emuelec.conf": "da feature\n",
            "storage/bin/ferramenta": "#!/bin/sh\n",
            "storage/nova pasta/arquivo com espaço.txt": "x",
        })
        plan = F.plan_layer("storage", F.discover(self.feats), ext4.listing(self.img))
        parts.finish_storage(self.img, plan, "R36-STORAGE")
        st = run("debugfs", "-R", "stat /bin/ferramenta", self.img).stdout
        self.assertIn("Mode:  04750", st)
        self.assertRegex(st, r"User:\s+0\s+Group:\s+81")
        st = run("debugfs", "-R", "stat /.config/emuelec/configs/emuelec.conf", self.img).stdout
        self.assertIn("Mode:  0600", st)  # substituição herda o modo
        self.assertRegex(st, r"User:\s+0\s+Group:\s+0\s")
        cat = run("debugfs", "-R", "cat /.config/emuelec/configs/emuelec.conf", self.img).stdout
        self.assertEqual(cat, "da feature\n")
        e = ext4.listing(self.img)
        self.assertEqual(e["nova pasta"].describe(), "drwxr-xr-x 0/0 ")
        self.assertEqual(e["nova pasta/arquivo com espaço.txt"].describe(), "-rw-r--r-- 0/0 1")
        self.assertEqual(ext4.get_label(self.img), "R36-STORAGE")
        run("e2fsck", "-fn", self.img)

    def test_mtime_preservado(self):
        write_feature(self.feats, "10-a", desc(), {"storage/a.txt": "x"})
        mt = 1791918978  # 2026-10-13; sem "@" o debugfs gravava 2472
        os.utime(self.feats / "10-a" / "storage" / "a.txt", (mt, mt))
        plan = F.plan_layer("storage", F.discover(self.feats), ext4.listing(self.img))
        parts.finish_storage(self.img, plan, "R36-STORAGE")
        st = run("debugfs", "-R", "stat /a.txt", self.img).stdout
        self.assertIn(f"mtime: 0x{mt:08x}:00000000", st)
        p = subprocess.run(["e2fsck", "-fn", str(self.img)], capture_output=True, text=True)
        self.assertNotIn("1970", p.stdout + p.stderr)

    def test_remove(self):
        write_feature(self.feats, "10-a", desc(extra='[[remove]]\nlayer = "storage"\npath = ".config/emuelec"\n'))
        plan = F.plan_layer("storage", F.discover(self.feats), ext4.listing(self.img))
        parts.finish_storage(self.img, plan, "R36-STORAGE")
        self.assertNotIn(".config/emuelec", ext4.listing(self.img))


class BootTest(TempDirCase):
    """5.2: limite de 16 MiB da p2."""

    @needs_base
    def test_real_p2_without_features(self):
        plan = F.plan_layer("boot", [], mtools.listing(CFG.base_path, CFG.part("boot").offset))
        img = parts.build_boot(CFG, CFG.base_path, self.tmp, plan)
        self.assertEqual(os.path.getsize(img), 16 * MIB)
        self.assertEqual(mtools.label(img), "R36-BOOT")
        ext = parts.check_boot_limit(img, 16 * MIB)
        self.assertLessEqual(ext.used_end, 16 * MIB)
        names = set(mtools.listing(img))
        self.assertTrue({"bootlogo.bmp", "magic.bin", "bat", "font24.sft", "font32.sft"} <= names)

    @needs_base
    def test_real_p2_label_changes_only_label(self):
        p = CFG.part("boot")
        orig = self.tmp / "orig.img"
        extract_region(CFG.base_path, orig, p.offset, p.write_size)
        img = parts.build_boot(CFG, CFG.base_path, self.tmp, F.plan_layer("boot", [], mtools.listing(orig)))
        a, b = orig.read_bytes(), img.read_bytes()
        diff = {i // 32 for i in range(len(a)) if a[i] != b[i]}  # entradas de 32 bytes
        ext = fat.extent(img)
        root = range(ext.info.fats_end // 32, ext.info.root_dir_end // 32)
        self.assertTrue(diff and all(d in root for d in diff), diff)  # só a entrada de label na raiz
        self.assertEqual(a[:512], b[:512])  # setor de boot intacto

    def test_synthetic_fat16_overflow_fails(self):
        img = self.tmp / "p2.img"
        mkfat(img, 64, fat=16, extra=["-s", "4"])  # FS de 64 MiB, mas só 16 MiB valem
        big = self.tmp / "grande.bin"
        big.write_bytes(os.urandom(20 * MIB))
        mcopy(img, big)
        with self.assertRaises(R36Error) as cm:
            parts.check_boot_limit(img, 16 * MIB)
        self.assertIn("além do permitido", str(cm.exception))


class SystemPartTest(TempDirCase):
    """5.3: SYSTEM + R36-BUILD.txt na p7."""

    def setUp(self):
        super().setUp()
        self.img = self.tmp / "p7.img"
        mkfat(self.img, 64, fat=16, label="EMUELEC")
        old = self.tmp / "SYSTEM"
        old.write_bytes(os.urandom(10 * MIB))
        mcopy(self.img, old)

    def test_replace_and_build_info(self):
        new = self.tmp / "novo" / "SYSTEM"
        new.parent.mkdir()
        new.write_bytes(os.urandom(12 * MIB))
        parts.update_system_part(self.img, new, "timestamp: 20261013-153045\n", "R36-SYSTEM", self.tmp)
        out = run("mdir", "-i", self.img, "::/", env=dict(os.environ, MTOOLS_SKIP_CHECK="1")).stdout
        self.assertIn("SYSTEM", out)
        self.assertIn("R36-BUILD", out)
        lst = mtools.listing(self.img)
        self.assertEqual(lst["SYSTEM"].size, str(12 * MIB))
        self.assertEqual(mtools.label(self.img), "R36-SYSTEM")
        txt = run("mtype", "-i", self.img, "::/R36-BUILD.txt", env=dict(os.environ, MTOOLS_SKIP_CHECK="1")).stdout
        self.assertEqual(txt, "timestamp: 20261013-153045\n")

    def test_too_big_fails_with_sizes(self):
        new = self.tmp / "grande"
        with open(new, "wb") as f:
            f.truncate(80 * MIB)
        with self.assertRaises(R36Error) as cm:
            parts.update_system_part(self.img, new, "x\n", "R36-SYSTEM", self.tmp)
        msg = str(cm.exception)
        self.assertIn("SYSTEM grande demais", msg)
        self.assertIn(str(80 * MIB), msg)
        self.assertIn("disponível", msg)


@needs_base
class RomsTest(TempDirCase):
    """5.4: p1 FAT32 recriada do tamanho do cartão."""

    def test_roms_partition(self):
        card_sectors = 7000 * 2048
        plan = F.plan_layer("roms", [], mtools.listing(CFG.base_path, CFG.part("roms").offset))
        img, wl, ext = parts.build_roms(CFG, CFG.base_path, self.tmp, plan, card_sectors, 0x20261013)
        size = (card_sectors - CFG.part("roms").start) * 512
        self.assertEqual(os.path.getsize(img), size)
        run("fsck.fat", "-n", img)
        info = fat.read_info(img)
        self.assertEqual((info.fat_type, info.hidden_sectors, info.bytes_per_sector), (32, 4956160, 512))
        self.assertEqual(mtools.label(img), "R36-ROMS")
        # listagem igual à da base
        base_list = mtools.listing(CFG.base_path, CFG.part("roms").offset)
        new_list = mtools.listing(img)
        self.assertEqual(new_list, base_list)
        # conteúdo igual
        a, b = self.tmp / "a", self.tmp / "b"
        a.mkdir()
        b.mkdir()
        mtools.copy_tree_out(CFG.base_path, a, CFG.part("roms").offset)
        mtools.copy_tree_out(img, b)
        self.assertEqual(run("diff", "-r", a, b).returncode, 0)
        # write_length cobre o último cluster e é múltiplo de 4 MiB
        self.assertGreaterEqual(wl, ext.last_cluster_end)
        self.assertEqual(wl % (4 * MIB), 0)
        with open(img, "rb") as f:
            f.seek(wl)
            tail = f.read(64 * MIB)
        self.assertEqual(tail.count(0), len(tail))  # nada além do write_length

    def test_roms_layer_added(self):
        feats = self.tmp / "feats"
        write_feature(feats, "10-a", desc(), {"roms/nes/jogo.nes": "rom"})
        base_list = mtools.listing(CFG.base_path, CFG.part("roms").offset)
        plan = F.plan_layer("roms", F.discover(feats), base_list)
        img, wl, ext = parts.build_roms(CFG, CFG.base_path, self.tmp, plan, 7000 * 2048, 1)
        self.assertEqual(mtools.listing(img)["nes/jogo.nes"].size, "3")


if __name__ == "__main__":
    unittest.main()
