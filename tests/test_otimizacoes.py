import os
import re
import subprocess
import unittest

from context import CFG, ROOT, TempDirCase, needs_base
from r36img import mtools

FEATS = ROOT / "features"
F40 = FEATS / "40-zram-swap"
F42 = FEATS / "42-roms-noatime"
UNITS = "usr/lib/systemd/system"


def diretivas(path):
    """{chave: [valores]} de uma unit systemd (ignora seções e comentários)."""
    out = {}
    for line in path.read_text().splitlines():
        m = re.match(r"^\s*([A-Za-z]+)\s*=\s*(.*?)\s*$", line)
        if m and not line.lstrip().startswith(("#", ";")):
            out.setdefault(m.group(1), []).append(m.group(2))
    return out


class UnitCase(unittest.TestCase):
    def assert_link(self, feature, wants, unit):
        link = feature / "system" / UNITS / wants / unit
        self.assertTrue(link.is_symlink(), link)
        self.assertEqual(os.readlink(link), f"../{unit}")
        self.assertTrue((feature / "system" / UNITS / unit).is_file(), unit)

    def assert_script(self, path):
        self.assertTrue(os.access(path, os.X_OK), f"{path} sem bit de execução")
        subprocess.run(["bash", "-n", str(path)], check=True)


class ZramSwap(UnitCase):
    def test_unit(self):
        d = diretivas(F40 / "system" / UNITS / "r36-zram-swap.service")
        self.assertEqual(d["DefaultDependencies"], ["no"])
        self.assertIn("swap.target", d["Before"][0].split())
        self.assertEqual(d["Type"], ["oneshot"])
        self.assertEqual(d["RemainAfterExit"], ["yes"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/zram-swap"])
        self.assertEqual(d["WantedBy"], ["basic.target"])

    def test_link(self):
        self.assert_link(F40, "basic.target.wants", "r36-zram-swap.service")

    def test_script(self):
        script = F40 / "system" / "usr" / "lib" / "r36" / "zram-swap"
        self.assert_script(script)
        txt = script.read_text()
        self.assertIn("/sys/block/zram0", txt)
        self.assertIn("swapon -p 32767", txt)
        # nenhum caminho de saída com código diferente de 0
        self.assertEqual(re.findall(r"exit\s+(\d+)", txt), ["0", "0"])

    def test_swap_conf(self):
        txt = (F40 / "storage" / ".config" / "swap.conf").read_text()
        self.assertRegex(txt, r'(?m)^SWAP_ENABLED="no"$')


class RomsNoatime(UnitCase):
    def test_unit(self):
        d = diretivas(F42 / "system" / UNITS / "r36-roms-noatime.service")
        self.assertEqual(d["After"], ["emuelec-autostart.service"])
        self.assertEqual(d["Type"], ["oneshot"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/roms-noatime"])
        self.assertEqual(d["WantedBy"], ["emuelec.target"])

    def test_link(self):
        self.assert_link(F42, "emuelec.target.wants", "r36-roms-noatime.service")

    def test_script(self):
        script = F42 / "system" / "usr" / "lib" / "r36" / "roms-noatime"
        self.assert_script(script)
        txt = script.read_text()
        self.assertIn('mountpoint -q "$ROMS"', txt)
        self.assertIn("mount -o remount,noatime", txt)
        self.assertEqual(re.findall(r"exit\s+(\d+)", txt), ["0", "0"])


@needs_base
class ZramSwapBase(TempDirCase):
    def test_mount_swap_le_swap_conf_do_storage(self):
        sq = self.tmp / "SYSTEM"
        subprocess.run(["mcopy", "-n", "-i", mtools.spec(CFG.base_path, CFG.part("system").offset),
                        "::/SYSTEM", str(sq)], check=True, env=mtools.ENV, capture_output=True)
        txt = subprocess.run(["unsquashfs", "-cat", str(sq), "usr/lib/libreelec/mount-swap"],
                             check=True, capture_output=True, text=True).stdout
        self.assertIn(". /storage/.config/swap.conf", txt)
        self.assertIn('[ ! "${SWAP_ENABLED}" = "yes" ]', txt)


if __name__ == "__main__":
    unittest.main()
