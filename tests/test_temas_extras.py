import re
import tarfile
import unittest
from pathlib import Path

from context import ROOT, TempDirCase
from r36img import features as F
from r36img.errors import R36Error


class TemasExtrasTest(unittest.TestCase):
    def setUp(self):
        self.feat_dir = ROOT / "features" / "50-temas-extras"
        self.assertTrue(self.feat_dir.is_dir(), "features/50-temas-extras não encontrada")
        self.feat = F.load_feature(self.feat_dir)

    def test_descriptor_layers_and_paths(self):
        self.assertEqual(self.feat.id, "50-temas-extras")
        self.assertEqual(self.feat.budget_mib, 700)
        self.assertTrue(self.feat.enabled)

        roms_themes = {}
        storage_themes = {}

        for ext in self.feat.externals:
            if ext.layer == "roms":
                self.assertTrue(
                    ext.dest.startswith("themes/"),
                    f"Tema na camada 'roms' deve iniciar com 'themes/': {ext.dest}",
                )
                theme_name = ext.dest.split("/", 1)[1]
                roms_themes[theme_name] = ext
            elif ext.layer == "storage":
                self.assertTrue(
                    ext.dest.startswith(".config/emulationstation/themes/"),
                    f"Tema na camada 'storage' deve iniciar com '.config/emulationstation/themes/': {ext.dest}",
                )
                theme_name = ext.dest.split("themes/", 1)[1]
                storage_themes[theme_name] = ext
            else:
                self.fail(f"Camada inesperada para tema: {ext.layer}")

        self.assertEqual(set(storage_themes.keys()), {"Minimal EmuELEC", "Graphite OGA", "Epic Cody ML"})
        self.assertEqual(set(roms_themes.keys()), {"Switch", "Crystal"})
        self.assertIn(("storage", ".config/emulationstation/themes/NES-BOX"), self.feat.removes)

        nesbox = self.feat_dir / "roms" / "themes" / "NES-BOX"
        self.assertTrue(nesbox.is_dir(), "NES-BOX ausente em roms/themes/")
        self.assertTrue((nesbox / "theme.xml").is_file(), "theme.xml do NES-BOX ausente")

    def test_roms_themes_cache_have_no_symlinks(self):
        cache = ROOT / "work" / "cache" / "external"
        for ext in self.feat.externals:
            if ext.layer == "roms":
                archive = cache / f"{ext.sha256}.tar.gz"
                if not archive.is_file():
                    continue
                with tarfile.open(archive, "r:gz") as tar:
                    for m in tar:
                        self.assertFalse(
                            m.issym(),
                            f"Tarball {archive.name} ({ext.dest}) contém link simbólico: {m.name} -> {m.linkname}",
                        )
                        self.assertFalse(
                            m.islnk(),
                            f"Tarball {archive.name} ({ext.dest}) contém hard link: {m.name} -> {m.linkname}",
                        )

    def test_epic_cody_ml_curadoria(self):
        theme_dir = self.feat_dir / "storage" / ".config" / "emulationstation" / "themes" / "Epic Cody ML"
        self.assertTrue(theme_dir.is_dir(), "Diretório do Epic Cody ML não encontrado")

        root_theme_file = theme_dir / "theme.xml"
        self.assertTrue(root_theme_file.is_file(), "theme.xml raiz ausente")
        root_content = root_theme_file.read_text(encoding="utf-8")

        # Verifica margens seguras (x = 0.025)
        for elem in ["shortdescription", "sys_line1", "sys_line2", "buttonA", "systemInfo", "longdescription"]:
            self.assertIn(f'name="{elem}"', root_content, f"Elemento {elem} ausente no theme.xml")
        self.assertIn("<pos>0.025 0.080</pos>", root_content)
        self.assertIn("<pos>0.025 0.115</pos>", root_content)
        self.assertIn("<pos>0.025 0.160</pos>", root_content)
        self.assertIn("<pos>0.025 0.460</pos>", root_content)
        self.assertIn("<pos>0.025 0.570</pos>", root_content)
        self.assertIn("<pos>0.025 0.660</pos>", root_content)

        # Calibração tipográfica e controller (limite até a largura total da tela para evitar abreviações)
        self.assertIn("<size>0.975 0.045</size>", root_content)
        self.assertIn("<fontSize>0.045</fontSize>", root_content)
        self.assertIn("<size>0.975 0.200</size>", root_content)
        self.assertIn("<fontSize>0.130</fontSize>", root_content)
        self.assertIn("<pos>0.35 0.62</pos>", root_content)
        self.assertIn("<maxSize>0.28 0.28</maxSize>", root_content)

        # Helpsystem explícito em view system
        self.assertIn("<pos>0.025 0.965</pos>", root_content)
        self.assertIn("<iconColor>FFAE00</iconColor>", root_content)
        self.assertIn("<textColor>A0A0A0</textColor>", root_content)

        # Binds de buttonImage
        self.assertIn("<path>${buttonImage}</path>", root_content)
        self.assertIn("<path>./_art/var/button.svg</path>", root_content)

        # SVGs de botões localizados
        var_art = theme_dir / "_art" / "var"
        btn_pt = var_art / "button-pt.svg"
        btn_es = var_art / "button-es.svg"
        self.assertTrue(btn_pt.is_file(), "button-pt.svg ausente")
        self.assertTrue(btn_es.is_file(), "button-es.svg ausente")
        self.assertIn("<svg", btn_pt.read_text(encoding="utf-8"))
        self.assertIn("<svg", btn_es.read_text(encoding="utf-8"))
        # Garante que a letra A de ENTRAR possua winding horário (CW) para recortar o vazado perfeitamente
        self.assertIn("M111.1,13.1h5.3l3.7,23.1", btn_pt.read_text(encoding="utf-8"))
        self.assertIn("M111.1,13.1h5.3l3.7,23.1", btn_es.read_text(encoding="utf-8"))
        self.assertIn("M111.1,13.1h5.3l3.7,23.1", (var_art / "button.svg").read_text(encoding="utf-8"))

        # Presença de sys_line1 em todos os 129 sistemas
        sys_dirs = [p for p in theme_dir.iterdir() if p.is_dir() and (p / "theme.xml").is_file()]
        self.assertGreaterEqual(len(sys_dirs), 120, "Número insuficiente de pastas de sistemas no tema")
        for s in sys_dirs:
            st_content = (s / "theme.xml").read_text(encoding="utf-8")
            self.assertIn('name="sys_line1"', st_content, f"Sistema {s.name} não possui sys_line1 declarado")

        # Catálogos de idioma e integridade das variáveis
        lang_dir = theme_dir / "_languages"
        for lang_name in ["en.xml", "pt-br.xml", "es-latam.xml"]:
            lang_file = lang_dir / lang_name
            self.assertTrue(lang_file.is_file(), f"Catálogo {lang_name} ausente")
            content = lang_file.read_text(encoding="utf-8")
            self.assertIn("<buttonImage>", content)
            self.assertIn("<auto-allgames.sys_line1>", content)
            self.assertIn("<auto-allgames.sys_line2>", content)
            self.assertIn("<gbc.sys_line1>", content)
            self.assertIn("<gbc.sys_line2>", content)
            self.assertIn("<n64.sys_line1>", content)
            self.assertIn("<n64.sys_line2>", content)
            self.assertIn("<psx.sys_line1>", content)
            self.assertIn("<psx.sys_line2>", content)

            # Garante que nenhum sys_line2 exceda limite seguro (evita truncamento em 640x480)
            matches = re.findall(r'<([a-zA-Z0-9_\-\.]+)\.sys_line2>([^<]+)</\1\.sys_line2>', content)
            for key, val in matches:
                clean_val = val.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                self.assertLessEqual(
                    len(clean_val),
                    28,
                    f"Título {key}.sys_line2='{clean_val}' no catálogo {lang_name} muito longo (risco de truncamento em 640x480)"
                )

        pt_content = (lang_dir / "pt-br.xml").read_text(encoding="utf-8")
        self.assertIn("<nes.sys_line2>Nintendo</nes.sys_line2>", pt_content)


class FatSymlinkRejectionTest(TempDirCase):
    def test_symlink_rejected_in_roms_layer(self):
        roms_dir = self.tmp / "roms"
        roms_dir.mkdir()
        target = roms_dir / "target.txt"
        target.write_text("ok")
        link = roms_dir / "link.txt"
        link.symlink_to(target)

        feat_mock = type("MockFeature", (), {"id": "test-feat"})()
        with self.assertRaises(R36Error) as cm:
            F._walk_tree(feat_mock, "roms", roms_dir, "")
        self.assertIn("FAT não suporta links simbólicos", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
