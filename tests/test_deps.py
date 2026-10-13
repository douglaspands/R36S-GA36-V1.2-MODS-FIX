import os
import shutil
import unittest

from context import TempDirCase
from r36img import deps
from r36img.errors import R36Error


class DepsTest(TempDirCase):
    def _fake_path(self, skip):
        """PATH com links para todas as ferramentas reais, exceto `skip`."""
        bindir = self.tmp / "bin"
        bindir.mkdir()
        for cmd in deps.BUILD_TOOLS:
            if cmd == skip:
                continue
            real = shutil.which(cmd)
            if real:
                os.symlink(real, bindir / cmd)
        return str(bindir)

    def test_host_ok(self):
        deps.check_build()

    def test_missing_tool_lists_and_suggests_dnf(self):
        path = self._fake_path(skip="debugfs")
        with self.assertRaises(R36Error) as cm:
            deps.check_build(path=path)
        msg = str(cm.exception)
        self.assertIn("debugfs (pacote e2fsprogs) não encontrado", msg)
        self.assertIn("sudo dnf install e2fsprogs", msg)
        self.assertNotIn("mtools", msg)

    def test_missing_squashfs(self):
        path = self._fake_path(skip="mksquashfs")
        with self.assertRaises(R36Error) as cm:
            deps.check_build(path=path)
        self.assertIn("squashfs-tools", str(cm.exception))

    def test_old_squashfs_version(self):
        path = self._fake_path(skip="mksquashfs")
        fake = self.tmp / "bin" / "mksquashfs"
        fake.write_text("#!/bin/sh\necho 'mksquashfs version 4.4 (2019/08/29)'\n")
        fake.chmod(0o755)
        with self.assertRaises(R36Error) as cm:
            deps.check_build(path=path)
        self.assertIn("4.4", str(cm.exception))
        self.assertIn("≥ 4.6", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
