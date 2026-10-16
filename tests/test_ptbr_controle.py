import re
import unittest

from context import ROOT

F10 = ROOT / "features" / "10-ptbr-sao-paulo" / "storage" / ".config"
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


if __name__ == "__main__":
    unittest.main()
