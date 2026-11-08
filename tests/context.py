"""Coloca tools/ no sys.path (os testes rodam com python3 -I) e oferece utilitários."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from r36img import config  # noqa: E402

CFG = config.load(ROOT)
HAVE_BASE = CFG.base_path.is_file()
SLOW = os.environ.get("R36_SLOW") == "1" or "--slow" in sys.argv

needs_base = unittest.skipUnless(HAVE_BASE, "imagem base ausente em base/")
slow = unittest.skipUnless(SLOW, "teste lento (rode com R36_SLOW=1)")

# Temporários dos testes em work/tests (disco), não em /tmp (tmpfs com cota pequena).
TEST_TMP = ROOT / "work" / "tests"


def mkdtemp(prefix):
    TEST_TMP.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=TEST_TMP))


def have(*tools):
    return all(shutil.which(t) for t in tools)


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = mkdtemp("r36test-")

    def tearDown(self):
        subprocess.run(["chmod", "-R", "u+rwX", str(self.tmp)], check=False)
        shutil.rmtree(self.tmp, ignore_errors=True)


def mkfat(path, size_mib, fat=16, label=None, extra=()):
    with open(path, "wb") as f:
        f.truncate(size_mib * 1024 * 1024)
    cmd = ["mkfs.fat", "-F", str(fat), *extra]
    if label:
        cmd += ["-n", label]
    subprocess.run([*cmd, str(path)], check=True, capture_output=True)


def mcopy(img, src, dst="::/"):
    env = dict(os.environ, MTOOLS_SKIP_CHECK="1")
    subprocess.run(["mcopy", "-s", "-o", "-i", str(img), str(src), dst], check=True, env=env, capture_output=True)
