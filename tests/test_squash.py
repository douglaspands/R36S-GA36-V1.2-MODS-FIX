import os
import subprocess
import unittest
from dataclasses import replace

from context import CFG, TempDirCase, needs_base, slow
from r36img import squash
from r36img.errors import R36Error


def make_source(root):
    """Árvore pequena: setuid 0/81, symlink, nome com espaço, diretório 0555, mtime fixa."""
    (root / "usr/bin").mkdir(parents=True)
    (root / "usr/lib/dbus").mkdir(parents=True)
    (root / "dir com espaço").mkdir()
    (root / "ro").mkdir()
    (root / "usr/bin/busybox").write_bytes(b"\x7fELF busybox")
    (root / "usr/lib/dbus/dbus-daemon-launch-helper").write_bytes(b"helper")
    (root / "dir com espaço/arquivo 1.txt").write_text("olá")
    os.symlink("busybox", root / "usr/bin/ls")
    os.symlink("/usr/bin", root / "bin")
    for p in root.rglob("*"):
        os.utime(p, (1_700_000_000, 1_700_000_000), follow_symlinks=False)
    os.chmod(root / "ro", 0o555)
    pf = root.parent / "src.pf"
    pf.write_text(
        '"usr/bin/busybox" m 4755 0 0\n'
        '"usr/lib/dbus/dbus-daemon-launch-helper" m 4750 0 81\n'
        '"dir com espaço" m 755 0 0\n"dir com espaço/arquivo 1.txt" m 644 0 0\n'
        '"usr" m 755 0 0\n"usr/bin" m 755 0 0\n"usr/lib" m 755 0 0\n"usr/lib/dbus" m 755 0 0\n'
        '"usr/bin/ls" m 777 0 0\n"bin" m 777 0 0\n"ro" m 555 0 0\n'
    )
    return pf


class SquashTest(TempDirCase):
    def setUp(self):
        super().setUp()
        src = self.tmp / "src"
        src.mkdir()
        pf = make_source(src)
        self.sq = self.tmp / "orig.sq"
        subprocess.run(["mksquashfs", str(src), str(self.sq), "-pf", str(pf), *squash.MKSQUASHFS_ARGS,
                        "-root-mode", "775", "-root-uid", "0", "-root-gid", "0"], check=True, capture_output=True)

    def test_parse_lln(self):
        e = squash.listing(self.sq)
        self.assertEqual(e["usr/bin/busybox"].lsmode(), "-rwsr-xr-x")
        h = e["usr/lib/dbus/dbus-daemon-launch-helper"]
        self.assertEqual((h.lsmode(), h.uid, h.gid, h.size), ("-rwsr-x---", 0, 81, "6"))
        self.assertEqual(e["usr/bin/ls"].type, "l")
        self.assertEqual(e["usr/bin/ls"].target, "busybox")
        self.assertEqual(e["bin"].target, "/usr/bin")
        self.assertEqual(e["dir com espaço/arquivo 1.txt"].size, str(len("olá".encode())))
        self.assertEqual(e["ro"].mode, 0o555)
        self.assertEqual(e[""].type, "d")

    def test_symbolic_mode_roundtrip(self):
        for s in ("-rwsr-xr-x", "-rwsr-x---", "drwxrwxrwt", "-rwSr--r--", "-rwxr-sr-x", "lrwxrwxrwx"):
            self.assertEqual(squash.symbolic_mode(s[0], squash.parse_perms(s)), s)

    def roundtrip(self):
        base = squash.listing(self.sq)
        tree = self.tmp / "tree"
        times = squash.extract(self.sq, tree)
        squash.restore_dir_times(tree, times)
        pf = self.tmp / "out.pf"
        squash.write_pseudo_file(base, pf)
        out = self.tmp / "out.sq"
        squash.mksquashfs(tree, out, pf, base[""], squash.mkfs_time(self.sq))
        return base, tree, out

    def test_roundtrip_preserves_metadata_as_user(self):
        self.assertNotEqual(os.getuid(), 0)
        base, tree, out = self.roundtrip()
        got = squash.listing(out)
        self.assertEqual(got, base)  # inclui mtimes
        squash.verify(out, base, untouched=list(base), content_tree=tree, work_dir=self.tmp)
        self.assertEqual(squash.mkfs_time(out), squash.mkfs_time(self.sq))

    def test_verify_reports_mode_divergence(self):
        base, tree, out = self.roundtrip()
        expected = dict(base)
        expected["usr/bin/busybox"] = replace(base["usr/bin/busybox"], mode=0o755)
        with self.assertRaises(R36Error) as cm:
            squash.verify(out, expected, untouched=list(base))
        msg = str(cm.exception)
        self.assertIn("usr/bin/busybox: esperado -rwxr-xr-x 0/0", msg)
        self.assertIn("obtido -rwsr-xr-x 0/0", msg)

    def test_verify_reports_content_divergence(self):
        base, tree, out = self.roundtrip()
        (tree / "usr/bin/busybox").write_bytes(b"outro conteudo")
        with self.assertRaises(R36Error) as cm:
            squash.verify(out, base, content_tree=tree, work_dir=self.tmp)
        self.assertIn("usr/bin/busybox", str(cm.exception))


@needs_base
@slow
class RealSystemRoundtripTest(TempDirCase):
    """3.4: ida e volta do SYSTEM real sem features (lento: ~minutos)."""

    def test_real_system(self):
        from r36img import mtools
        from r36img.util import run
        sq = self.tmp / "SYSTEM.base"
        run(["mcopy", "-n", "-i", mtools.spec(CFG.base_path, CFG.part("system").offset), "::/SYSTEM", sq],
            env=mtools.ENV)
        base = squash.listing(sq)
        tree = self.tmp / "tree"
        times = squash.extract(sq, tree)
        squash.restore_dir_times(tree, times)
        pf = self.tmp / "system.pf"
        squash.write_pseudo_file(base, pf)
        out = self.tmp / "SYSTEM"
        squash.mksquashfs(tree, out, pf, base[""], squash.mkfs_time(sq))
        lln_base = run(["unsquashfs", "-lln", sq]).stdout
        lln_out = run(["unsquashfs", "-lln", out]).stdout
        self.assertEqual(lln_out, lln_base)
        got = squash.listing(out)
        self.assertEqual(got["usr/bin/busybox"].describe()[:14], "-rwsr-xr-x 0/0")
        self.assertEqual(got["usr/lib/dbus/dbus-daemon-launch-helper"].describe()[:15], "-rwsr-x--- 0/81")
        info = squash.superblock_info(out)
        self.assertIn("Compression lzo", info)
        self.assertIn("Block size 524288", info)
        squash.verify(out, base, untouched=list(base), content_tree=tree, work_dir=self.tmp)


if __name__ == "__main__":
    unittest.main()
