import importlib
import subprocess
import unittest

from context import ROOT, CFG


class SmokeTest(unittest.TestCase):
    def test_modules_import(self):
        for mod in ("base", "build", "cli", "config", "deps", "errors", "ext4", "fat", "features",
                    "flash", "image", "layout", "mtools", "parts", "squash", "util"):
            importlib.import_module(f"r36img.{mod}")

    def test_config(self):
        self.assertEqual(CFG.image_prefix, "r36s_ga36-mb_v1.2-20260416")
        self.assertEqual(CFG.default_size_mib, 15000)
        self.assertEqual(CFG.min_size_mib, 7000)
        self.assertEqual(CFG.part("roms").start, 4956160)
        self.assertEqual(CFG.part("boot").write_size, 16 * 1024 * 1024)

    def test_wrappers_help_pt_br(self):
        for script in ("build.sh", "flash.sh"):
            p = subprocess.run([str(ROOT / script), "--help"], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("uso:", p.stdout)
            self.assertIn("mostra esta ajuda e sai", p.stdout)


if __name__ == "__main__":
    unittest.main()
