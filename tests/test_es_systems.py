"""Testes da declaração de sistemas no EmulationStation (es_systems.cfg)."""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from context import ROOT

F64 = ROOT / "features" / "64-love2d"
ES_SYSTEM = F64 / "system" / "usr" / "config" / "emulationstation" / "es_systems.cfg"
ES_STORAGE = F64 / "storage" / ".config" / "emulationstation" / "es_systems.cfg"


class TestEsSystems(unittest.TestCase):
    def test_arquivos_existem_e_sao_identicos(self):
        self.assertTrue(ES_SYSTEM.is_file(), "es_systems.cfg do system ausente")
        self.assertTrue(ES_STORAGE.is_file(), "es_systems.cfg do storage ausente")
        self.assertEqual(
            ES_SYSTEM.read_bytes(),
            ES_STORAGE.read_bytes(),
            "es_systems.cfg do system e do storage diferem",
        )

    def test_sistema_love_declarado(self):
        tree = ET.fromstring(ES_STORAGE.read_text(encoding="utf-8"))
        love_sys = None
        for sys_elem in tree.findall("system"):
            name_elem = sys_elem.find("name")
            if name_elem is not None and name_elem.text == "love":
                love_sys = sys_elem
                break

        self.assertIsNotNone(love_sys, "Sistema 'love' não encontrado em es_systems.cfg")

        path_elem = love_sys.find("path")
        self.assertIsNotNone(path_elem)
        self.assertEqual(path_elem.text, "/storage/roms/love")

        ext_elem = love_sys.find("extension")
        self.assertIsNotNone(ext_elem)
        extensions = ext_elem.text.split()
        for ext in [".love", ".zip", ".LOVE", ".ZIP"]:
            self.assertIn(ext, extensions, f"Extensão {ext} ausente do sistema love")

        cmd_elem = love_sys.find("command")
        self.assertIsNotNone(cmd_elem)
        self.assertEqual(cmd_elem.text, '/usr/bin/love.sh "%ROM%"')

        theme_elem = love_sys.find("theme")
        self.assertIsNotNone(theme_elem)
        self.assertEqual(theme_elem.text, "love2d")


if __name__ == "__main__":
    unittest.main()
