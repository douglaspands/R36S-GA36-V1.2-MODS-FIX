import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from context import ROOT
from r36img import features as F

class TestTemaEpicCodyML(unittest.TestCase):
    def setUp(self):
        self.feat_dir = ROOT / "features" / "50-temas-extras"
        self.theme_dir = self.feat_dir / "storage" / ".config" / "emulationstation" / "themes" / "Epic Cody ML"
        self.languages_dir = self.theme_dir / "_languages"

    def test_refatora_tool_exists(self):
        tool = ROOT / "tools" / "refatora_epic_cody_ml.py"
        self.assertTrue(tool.is_file(), "tools/refatora_epic_cody_ml.py deve existir")

    def test_all_xml_files_are_well_formed(self):
        """Valida que todos os XMLs gerados no tema são sintaticamente válidos e sem erros."""
        xml_files = list(self.theme_dir.glob("*.xml")) + list(self.theme_dir.glob("*/*.xml"))
        self.assertGreaterEqual(len(xml_files), 130, "Deve haver mais de 130 arquivos XML no tema refatorado")
        
        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                self.assertIsNotNone(tree.getroot(), f"Root inválido em {xml_file}")
            except Exception as e:
                self.fail(f"Erro de sintaxe XML em {xml_file.relative_to(ROOT)}: {e}")

    def test_catalogo_en_exists_and_valid(self):
        en_xml = self.languages_dir / "en.xml"
        self.assertTrue(en_xml.is_file(), "_languages/en.xml deve existir")
        tree = ET.parse(en_xml)
        root = tree.getroot()
        self.assertEqual(root.tag, "theme")
        vars_elem = root.find("variables")
        self.assertIsNotNone(vars_elem, "Deve conter tag <variables>")
        
        snes_short = vars_elem.find("snes.shortdescription")
        self.assertIsNotNone(snes_short, "Deve conter variável snes.shortdescription")
        self.assertIn("16-bit", snes_short.text)

    def test_console_theme_xml_uses_variables(self):
        snes_xml = self.theme_dir / "snes" / "theme.xml"
        self.assertTrue(snes_xml.is_file(), "snes/theme.xml deve existir no tema refatorado")
        content = snes_xml.read_text(encoding="utf-8")
        self.assertIn("${snes.shortdescription}", content)
        self.assertIn("${snes.longdescription}", content)
        self.assertNotIn("Super Nintendo Entertainment System", content)

    def test_catalogos_pt_br_and_es_latam_exist_and_consistent(self):
        en_xml = self.languages_dir / "en.xml"
        pt_xml = self.languages_dir / "pt-br.xml"
        es_xml = self.languages_dir / "es-latam.xml"

        self.assertTrue(pt_xml.is_file(), "_languages/pt-br.xml deve existir")
        self.assertTrue(es_xml.is_file(), "_languages/es-latam.xml deve existir")

        tree_en = ET.parse(en_xml)
        tree_pt = ET.parse(pt_xml)
        tree_es = ET.parse(es_xml)

        vars_en = {e.tag: e.text or "" for e in tree_en.getroot().find("variables")}
        vars_pt = {e.tag: e.text or "" for e in tree_pt.getroot().find("variables")}
        vars_es = {e.tag: e.text or "" for e in tree_es.getroot().find("variables")}

        # Todas as chaves devem ser rigorosamente simétricas
        diff_pt = set(vars_en.keys()) ^ set(vars_pt.keys())
        diff_es = set(vars_en.keys()) ^ set(vars_es.keys())
        self.assertEqual(diff_pt, set(), f"Divergência de variáveis entre en e pt-br: {diff_pt}")
        self.assertEqual(diff_es, set(), f"Divergência de variáveis entre en e es-latam: {diff_es}")

        # Nenhuma variável pode estar vazia
        empty_pt = [k for k, v in vars_pt.items() if not v.strip()]
        empty_es = [k for k, v in vars_es.items() if not v.strip()]
        self.assertEqual(empty_pt, [], f"Variáveis vazias em pt-br: {empty_pt}")
        self.assertEqual(empty_es, [], f"Variáveis vazias em es-latam: {empty_es}")

    def test_pt_br_terminologia_e_calibracao(self):
        pt_xml = self.languages_dir / "pt-br.xml"
        self.assertTrue(pt_xml.is_file())
        tree = ET.parse(pt_xml)
        vars_pt = {e.tag: e.text or "" for e in tree.getroot().find("variables")}

        # Preservação de termos técnicos consagrados
        self.assertIn("16-bit", vars_pt.get("snes.shortdescription", ""))
        self.assertIn("Arcade", vars_pt.get("arcade.nameLabel", "") + vars_pt.get("arcade.sys_line2", "") + vars_pt.get("arcade.shortdescription", ""))
        self.assertIn("RPGs", vars_pt.get("rpgs.nameLabel", "") + vars_pt.get("rpgs.sys_line2", ""))
        self.assertIn("Shmups", vars_pt.get("shmups.nameLabel", "") + vars_pt.get("shmups.sys_line2", ""))
        self.assertIn("Ports", vars_pt.get("ports.nameLabel", "") + vars_pt.get("ports.sys_line2", ""))

        # Calibração de tamanho para tela compacta 640x480
        for k, v in vars_pt.items():
            if k.endswith(".shortdescription"):
                self.assertLessEqual(len(v), 35, f"shortdescription muito longa em {k}: {v!r} ({len(v)} chars)")
            elif k.endswith(".longdescription"):
                self.assertLessEqual(len(v), 190, f"longdescription muito longa em {k}: {v!r} ({len(v)} chars)")

    def test_gba_recomp_pasta_e_arte(self):
        pasta = self.theme_dir / "gba-recomp"
        for nome in ("theme.xml", "logo.png", "poster.png", "system.png"):
            self.assertTrue((pasta / nome).is_file(), f"gba-recomp/{nome} ausente")
        # O tema acha pôster e controle por ${system.theme} (= gba-recomp)
        self.assertTrue((self.theme_dir / "_art" / "posters" / "gba-recomp.png").is_file())
        self.assertTrue((self.theme_dir / "_art" / "controllers" / "gba-recomp.png").is_file())
        for nome in ("logo.png", "poster.png", "system.png"):
            self.assertEqual((pasta / nome).read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        # Mesma estrutura do theme.xml do gba, com as variáveis do próprio sistema
        novo = (pasta / "theme.xml").read_text(encoding="utf-8")
        base = (self.theme_dir / "gba" / "theme.xml").read_text(encoding="utf-8")
        self.assertEqual(novo, base.replace("${gba.", "${gba-recomp."))
        for chave in ("nameLabel", "sys_line1", "sys_line2", "shortdescription", "longdescription"):
            self.assertIn("${gba-recomp.%s}" % chave, novo)

    def test_gba_recomp_variaveis_nos_tres_idiomas_sem_reticencias(self):
        chaves = ("nameLabel", "sys_line1", "sys_line2", "shortdescription", "longdescription")
        textos = {}
        for idioma in ("pt-br", "es-latam", "en"):
            raiz = ET.parse(self.languages_dir / f"{idioma}.xml").getroot().find("variables")
            vars_ = {e.tag: (e.text or "").strip() for e in raiz}
            for chave in chaves:
                self.assertTrue(vars_.get(f"gba-recomp.{chave}"), f"{idioma}: gba-recomp.{chave} ausente")
            textos[idioma] = vars_
            # Limites do tema (maiores valores já usados pelos outros sistemas): sem reticências
            self.assertLessEqual(len(vars_["gba-recomp.sys_line1"]), 32, idioma)
            self.assertLessEqual(len(vars_["gba-recomp.sys_line2"]), 23, idioma)
            self.assertLessEqual(len(vars_["gba-recomp.shortdescription"]), 35, idioma)
            self.assertLessEqual(len(vars_["gba-recomp.longdescription"]), 190, idioma)
            for chave in chaves:
                self.assertNotIn("...", vars_[f"gba-recomp.{chave}"])
                self.assertNotIn("…", vars_[f"gba-recomp.{chave}"])
        # Nada em inglês nos idiomas pt-br e es-latam, exceto o termo "Recomp"
        self.assertNotEqual(textos["pt-br"]["gba-recomp.longdescription"], textos["en"]["gba-recomp.longdescription"])
        self.assertNotEqual(textos["es-latam"]["gba-recomp.longdescription"], textos["en"]["gba-recomp.longdescription"])
        self.assertNotEqual(textos["pt-br"]["gba-recomp.shortdescription"], textos["en"]["gba-recomp.shortdescription"])
        self.assertNotEqual(textos["es-latam"]["gba-recomp.shortdescription"], textos["en"]["gba-recomp.shortdescription"])

    def test_root_theme_has_language_subset_default_pt_br(self):
        root_theme_file = self.theme_dir / "theme.xml"
        self.assertTrue(root_theme_file.is_file(), "theme.xml raiz deve existir")
        content = root_theme_file.read_text(encoding="utf-8")
        self.assertIn('<subset name="language"', content)

        tree = ET.parse(root_theme_file)
        subset_lang = None
        for s in tree.getroot().findall(".//subset"):
            if s.get("name") == "language":
                subset_lang = s
                break
        self.assertIsNotNone(subset_lang, "Subset language deve estar presente no theme.xml")
        includes = subset_lang.findall("include")
        self.assertGreaterEqual(len(includes), 3, "Subset language deve ter pt-br, es-latam e en")
        self.assertEqual(includes[0].get("name"), "pt-br", "O primeiro idioma (padrão) deve ser pt-br")
        self.assertEqual(includes[1].get("name"), "es-latam", "O segundo idioma deve ser es-latam")
        self.assertEqual(includes[2].get("name"), "en", "O terceiro idioma deve ser en")

    def test_feature_descriptor_and_es_settings(self):
        feat = F.load_feature(self.feat_dir)
        self.assertTrue(feat.enabled)

        # External aponta para Epic Cody ML
        ext_dest_list = [x.dest for x in feat.externals]
        self.assertIn(".config/emulationstation/themes/Epic Cody ML", ext_dest_list)
        self.assertNotIn(".config/emulationstation/themes/Epic Cody", ext_dest_list)

        # es_settings define Epic Cody ML como tema padrão
        es_settings = ROOT / "features" / "10-ptbr-sao-paulo" / "storage" / ".config" / "emulationstation" / "es_settings.cfg"
        self.assertTrue(es_settings.is_file())
        settings_xml = es_settings.read_text(encoding="utf-8")
        self.assertIn('<string name="ThemeSet" value="Epic Cody ML" />', settings_xml)
        self.assertNotIn('<string name="ThemeSet" value="Epic Cody" />', settings_xml)

    def test_no_symlinks_in_refactored_theme(self):
        """Garante que a árvore local do tema refatorado não contém symlinks."""
        for p in self.theme_dir.rglob("*"):
            self.assertFalse(p.is_symlink(), f"Symlink proibido encontrado: {p}")

    def test_imageviewer_suporte_e_artes(self):
        """Garante suporte completo ao imageviewer com theme.xml, variáveis e artes dedicadas."""
        iv_xml = self.theme_dir / "imageviewer" / "theme.xml"
        self.assertTrue(iv_xml.is_file(), "imageviewer/theme.xml deve existir")
        tree = ET.parse(iv_xml)
        self.assertIsNotNone(tree.getroot())

        # Artes temáticas
        poster_jpg = self.theme_dir / "_art" / "posters" / "imageviewer.jpg"
        controller_png = self.theme_dir / "_art" / "controllers" / "imageviewer.png"
        self.assertTrue(poster_jpg.is_file(), "Poster do imageviewer deve existir")
        self.assertTrue(controller_png.is_file(), "Ícone/controller do imageviewer deve existir")

        # Variáveis em pt-br
        pt_xml = self.languages_dir / "pt-br.xml"
        pt_tree = ET.parse(pt_xml)
        vars_pt = {e.tag: e.text or "" for e in pt_tree.getroot().find("variables")}
        self.assertEqual(vars_pt.get("imageviewer.nameLabel"), "Visualizador de Imagens")
        self.assertIn("capturas de tela", vars_pt.get("imageviewer.shortdescription", "").lower())

if __name__ == "__main__":
    unittest.main()
