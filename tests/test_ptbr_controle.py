import difflib
import os
import re
import subprocess
import unittest

from context import CFG, ROOT, TempDirCase, needs_base
from r36img import mtools

F10 = ROOT / "features" / "10-ptbr-sao-paulo" / "storage" / ".config"
RUNEMU = ROOT / "features" / "10-ptbr-sao-paulo" / "system" / "usr" / "bin" / "emuelecRunEmu.sh"
F20 = ROOT / "features" / "20-controle-posicional" / "storage" / "joypads" / "micro_gamepad.cfg"


def parse_cfg(path):
    out = {}
    for line in path.read_text().splitlines():
        m = re.match(r'^\s*([\w.]+)\s*=\s*"?([^"]*)"?\s*$', line)
        if m and not line.lstrip().startswith("#"):
            out[m.group(1)] = m.group(2)
    return out


class PtBrSaoPaulo(unittest.TestCase):
    def test_emuelec_conf(self):
        c = parse_cfg(F10 / "emuelec" / "configs" / "emuelec.conf")
        self.assertEqual(c["system.language"], "pt_BR")
        self.assertEqual(c["system.timezone"], "America/Sao_Paulo")
        self.assertEqual(c["global.retroarch.menu_driver"], "rgui")
        self.assertEqual(c["global.ratio"], "core")
        self.assertEqual(c["gba.emulator"], "libretro")
        self.assertEqual(c["gba.core"], "gpsp")
        self.assertEqual(c["global.maxperf"], "0")
        self.assertEqual([k for k in c if k.endswith(".maxperf")], ["global.maxperf"])

    def test_es_settings(self):
        txt = (F10 / "emulationstation" / "es_settings.cfg").read_text()
        self.assertIn('<string name="Language" value="pt_BR" />', txt)

    def test_retroarch_cfg(self):
        c = parse_cfg(F10 / "retroarch" / "retroarch.cfg")
        self.assertEqual(c["user_language"], "7")
        self.assertEqual(c["menu_driver"], "rgui")
        self.assertEqual(c["menu_swap_ok_cancel_buttons"], "false")


class ControlePosicional(unittest.TestCase):
    def setUp(self):
        self.c = parse_cfg(F20)

    def test_driver_e_ids(self):
        self.assertEqual(self.c["input_driver"], "sdl2")
        self.assertEqual(self.c["input_vendor_id"], "26989")
        self.assertEqual(self.c["input_product_id"], "24431")

    def test_botoes_de_face(self):
        c = self.c
        self.assertEqual(
            (c["input_a_btn"], c["input_b_btn"], c["input_x_btn"], c["input_y_btn"]),
            ("0", "1", "2", "3"),
        )

    def test_hotkey_no_select(self):
        self.assertEqual(self.c["input_enable_hotkey_btn"], "8")

    def test_direcional_livre_de_atalhos(self):
        dpad = {f"input_{d}_btn" for d in ("up", "down", "left", "right")}
        for k, v in self.c.items():
            if k.endswith("_btn") and k not in dpad:
                self.assertNotIn(v, {"13", "14", "15", "16"}, k)


def bloco_maxperf(txt):
    i = txt.index("# R36: máximo desempenho")
    return txt[i:txt.index("\nfi\n", i) + 4]


class RunEmuMaxperf(TempDirCase):
    def roda(self, valor):
        """Executa só o bloco de escolha, com funções falsas; devolve a função chamada."""
        prog = (
            'get_ee_setting() { echo "$R36_VAL"; }\n'
            "maxperf() { echo maxperf; }\nnormperf() { echo normperf; }\n"
            'PLATFORM=gba; BASEROMNAME="a.zip"\n' + bloco_maxperf(RUNEMU.read_text())
        )
        return subprocess.run(
            ["bash", "-c", prog], check=True, capture_output=True, text=True,
            env=dict(os.environ, R36_VAL=valor),
        ).stdout.strip()

    def test_script_executavel_e_valido(self):
        self.assertTrue(os.access(RUNEMU, os.X_OK))
        subprocess.run(["bash", "-n", str(RUNEMU)], check=True)

    def test_sem_maxperf_incondicional(self):
        linhas = [l.strip() for l in RUNEMU.read_text().splitlines()]
        antes = linhas[: linhas.index("# R36: máximo desempenho só quando a chave maxperf (jogo, sistema ou global) vale 1")]
        self.assertNotIn("maxperf", antes)

    def test_chave_um_liga(self):
        self.assertEqual(self.roda("1"), "maxperf")

    def test_chave_zero_vazia_ou_outra_desliga(self):
        for v in ("0", "", "2", "off"):
            self.assertEqual(self.roda(v), "normperf", v)

    @needs_base
    def test_so_difere_da_base_nos_pontos_esperados(self):
        sq = self.tmp / "SYSTEM"
        subprocess.run(
            ["mcopy", "-n", "-i", mtools.spec(CFG.base_path, CFG.part("system").offset), "::/SYSTEM", str(sq)],
            check=True, env=mtools.ENV, capture_output=True)
        base = subprocess.run(
            ["unsquashfs", "-cat", str(sq), "usr/bin/emuelecRunEmu.sh"],
            check=True, capture_output=True, text=True).stdout.splitlines()
        nova = RUNEMU.read_text().splitlines()
        mudou = [l for l in difflib.unified_diff(base, nova, lineterm="", n=0)
                 if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        self.assertEqual(
            [l for l in mudou if l.startswith("-")], ["-maxperf"])
        self.assertEqual(sum(1 for l in mudou if l.startswith("+")), 8)
        self.assertEqual(bloco_maxperf("\n".join(nova)).count("get_ee_setting maxperf"), 1)


if __name__ == "__main__":
    unittest.main()
