import dataclasses
import os
import unittest

from context import CFG, TempDirCase, needs_base
from r36img import base, build
from r36img.errors import R36Error


class CardSizeTest(unittest.TestCase):
    def test_default(self):
        self.assertEqual(base.card_size_mib(CFG), 15000)

    def test_below_minimum(self):
        with self.assertRaises(R36Error) as cm:
            base.card_size_mib(CFG, 6000)
        self.assertIn("7000", str(cm.exception))

    def test_alignment(self):
        self.assertEqual(base.card_size_mib(CFG, 7462), 7460)
        self.assertEqual(base.card_size_mib(CFG, 30000), 30000)
        self.assertEqual(base.card_size_mib(CFG, 7000), 7000)

    def test_not_int(self):
        with self.assertRaises(R36Error):
            base.card_size_mib(CFG, "15000")


class BaseVerifyTest(TempDirCase):
    def _cfg(self, path, sha=None, size=None):
        return dataclasses.replace(CFG, base_path=path, base_sha256=sha or CFG.base_sha256,
                                   base_size=size or CFG.base_size)

    def test_missing(self):
        with self.assertRaises(R36Error) as cm:
            base.verify_base(self._cfg(self.tmp / "nao-existe.img"))
        self.assertIn("nao-existe.img", str(cm.exception))

    def test_wrong_hash_fails_without_output(self):
        fake = self.tmp / "base.img"
        fake.write_bytes(b"x" * 4096)
        cfg = dataclasses.replace(self._cfg(fake, size=4096), root=self.tmp)
        out, work = self.tmp / "out", self.tmp / "work"
        with self.assertRaises(R36Error) as cm:
            build.build(cfg, none=True, out_root=out, work_root=work)
        msg = str(cm.exception)
        self.assertIn(CFG.base_sha256, msg)
        self.assertIn("sha256 obtido", msg)
        self.assertFalse(out.exists())
        self.assertFalse(work.exists())

    def test_size_error_before_output(self):
        out = self.tmp / "out"
        with self.assertRaises(R36Error):
            build.build(CFG, size_mib=6000, none=True, out_root=out, work_root=self.tmp / "w")
        self.assertFalse(out.exists())

    @needs_base
    def test_real_base_ok_and_readonly(self):
        before = os.stat(CFG.base_path).st_mtime_ns
        base.verify_base(CFG)
        self.assertEqual(os.stat(CFG.base_path).st_mtime_ns, before)


if __name__ == "__main__":
    unittest.main()
