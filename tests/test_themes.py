"""Testes de integração visual do LÖVE no tema unificado do EmulationStation (Epic Cody ML)."""

import tomllib
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

from context import ROOT

FEATURE_50 = ROOT / "features" / "50-temas-extras"
THEMES_DIR = (
    FEATURE_50
    / "storage"
    / ".config"
    / "emulationstation"
    / "themes"
)
EPIC_CODY = THEMES_DIR / "Epic Cody ML"
EPIC_LOVE2D = EPIC_CODY / "love2d"
EPIC_LANGS = EPIC_CODY / "_languages"
POSTER_LOVE2D = EPIC_CODY / "_art" / "posters" / "love2d.png"
POSTER_LOVE2D_ALT = EPIC_LOVE2D / "poster.png"


class TestThemes(unittest.TestCase):
    def test_epic_cody_love2d_structure(self):
        theme_xml = EPIC_LOVE2D / "theme.xml"
        self.assertTrue(theme_xml.is_file(), "Epic Cody ML love2d/theme.xml ausente")
        tree = ET.fromstring(theme_xml.read_text(encoding="utf-8"))
        self.assertEqual(tree.tag, "theme")

        # Verifica se pelo menos uma arte gráfica do logotipo está presente
        logos = list(EPIC_LOVE2D.glob("*.png")) + list(EPIC_LOVE2D.glob("*.svg"))
        self.assertTrue(len(logos) > 0, "Logotipo do LÖVE ausente em Epic Cody ML love2d/")

    def test_epic_cody_namelabel_alignment(self):
        theme_xml = EPIC_CODY / "theme.xml"
        self.assertTrue(theme_xml.is_file(), "Epic Cody ML theme.xml ausente")
        tree = ET.fromstring(theme_xml.read_text(encoding="utf-8"))
        name_labels = tree.findall(".//text[@name='nameLabel']")
        self.assertTrue(len(name_labels) > 0, "nameLabel não encontrado no theme.xml")
        for nl in name_labels:
            align = nl.find("alignment")
            self.assertIsNotNone(align, "alignment ausente em nameLabel")
            self.assertEqual(
                align.text.strip(),
                "left",
                f"Alinhamento de nameLabel deve ser 'left' para evitar colisão com bateria/relógio, mas é '{align.text}'",
            )

    def test_epic_cody_md_name_present(self):
        theme_xml = EPIC_CODY / "theme.xml"
        tree = ET.fromstring(theme_xml.read_text(encoding="utf-8"))
        md_names = tree.findall(".//text[@name='md_name']")
        self.assertTrue(len(md_names) > 0, "Elemento md_name ausente no theme.xml")
        for md_name in md_names:
            font = md_name.find("fontPath")
            self.assertIsNotNone(font, "fontPath ausente em md_name")
            align = md_name.find("alignment")
            self.assertIsNotNone(align, "alignment ausente em md_name")

    def test_epic_cody_love2d_poster(self):
        self.assertTrue(POSTER_LOVE2D.is_file(), f"Poster {POSTER_LOVE2D} ausente")
        self.assertTrue(POSTER_LOVE2D_ALT.is_file(), f"Poster {POSTER_LOVE2D_ALT} ausente")

        with Image.open(POSTER_LOVE2D) as im:
            self.assertEqual(im.size, (640, 480), f"Resolução do poster deve ser 640x480, obtida: {im.size}")

        with Image.open(POSTER_LOVE2D_ALT) as im2:
            self.assertEqual(im2.size, (640, 480), f"Resolução do poster alternativo deve ser 640x480, obtida: {im2.size}")

    def test_single_curated_theme_integrity(self):
        # 1. Verifica exclusividade na pasta de temas do storage
        installed_themes = [p.name for p in THEMES_DIR.iterdir() if p.is_dir()]
        self.assertEqual(installed_themes, ["Epic Cody ML"], f"Apenas Epic Cody ML deve estar instalado: {installed_themes}")

        # 2. Verifica ausência de temas secundários em roms/themes
        roms_themes = FEATURE_50 / "roms" / "themes"
        self.assertFalse(roms_themes.exists(), f"Pasta {roms_themes} de temas extras não deve existir")

        # 3. Verifica declaração em feature.toml
        feat_toml = FEATURE_50 / "feature.toml"
        self.assertTrue(feat_toml.is_file())
        dados = tomllib.loads(feat_toml.read_text(encoding="utf-8"))
        externals = dados.get("external", [])
        self.assertEqual(len(externals), 1, "feature.toml deve ter apenas 1 tema externo (Epic Cody ML)")
        self.assertIn("Epic Cody ML", externals[0]["dest"])
        self.assertNotIn("NES-BOX", feat_toml.read_text(encoding="utf-8"))
        self.assertNotIn("Minimal EmuELEC", feat_toml.read_text(encoding="utf-8"))
        self.assertNotIn("Graphite OGA", feat_toml.read_text(encoding="utf-8"))
        self.assertNotIn("Switch", feat_toml.read_text(encoding="utf-8"))
        self.assertNotIn("Crystal", feat_toml.read_text(encoding="utf-8"))

    def test_epic_cody_language_catalogs(self):
        languages = ["pt-br.xml", "en.xml", "es-latam.xml"]
        required_keys = [
            "love2d.sys_line1",
            "love2d.sys_line2",
            "love2d.shortdescription",
            "love2d.longdescription",
            "love2d.nameLabel",
        ]

        for lang in languages:
            lang_file = EPIC_LANGS / lang
            self.assertTrue(lang_file.is_file(), f"Catálogo {lang} ausente")
            tree = ET.fromstring(lang_file.read_text(encoding="utf-8"))
            variables = tree.find("variables")
            self.assertIsNotNone(variables, f"<variables> ausente em {lang}")
            var_map = {c.tag: c for c in variables}

            for key in required_keys:
                elem = var_map.get(key)
                self.assertIsNotNone(
                    elem, f"Chave '{key}' ausente no catálogo de idioma {lang}"
                )
                self.assertTrue(
                    len(elem.text.strip()) > 0,
                    f"Chave '{key}' vazia no catálogo de idioma {lang}",
                )

                # Validação de espaçamento seguro para display 640x480
                if key.endswith("sys_line1") or key.endswith("sys_line2"):
                    self.assertLessEqual(
                        len(elem.text),
                        25,
                        f"Texto de título '{elem.text}' muito longo para 640x480 em {lang}",
                    )
                if key.endswith("shortdescription"):
                    self.assertLessEqual(
                        len(elem.text),
                        40,
                        f"Subtítulo '{elem.text}' muito longo para 640x480 em {lang}",
                    )


if __name__ == "__main__":
    unittest.main()
