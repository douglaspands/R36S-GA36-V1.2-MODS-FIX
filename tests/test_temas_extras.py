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
        self.assertEqual(self.feat.budget_mib, 250)
        self.assertTrue(self.feat.enabled)

        # O tema único e curado deve ser exclusivamente o Epic Cody ML no storage
        self.assertEqual(len(self.feat.externals), 1)
        ext = self.feat.externals[0]
        self.assertEqual(ext.layer, "storage")
        self.assertEqual(ext.dest, ".config/emulationstation/themes/Epic Cody ML")
        self.assertEqual(self.feat.removes, [])
        self.assertIn(
            "_art/ingame-global-bg.*",
            ext.exclude,
            "feature.toml deve excluir _art/ingame-global-bg.* para proteger arte curada",
        )

        # Ausência de temas secundários em roms/themes/
        self.assertFalse((self.feat_dir / "roms").exists(), "Camada roms não deve existir na feature 50 unificada")

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

    def test_epic_cody_ml_gamelist_calibracao(self):
        theme_dir = self.feat_dir / "storage" / ".config" / "emulationstation" / "themes" / "Epic Cody ML"
        root_theme_file = theme_dir / "theme.xml"
        root_content = root_theme_file.read_text(encoding="utf-8")

        # View unificada canônica
        self.assertIn('<view name="basic, detailed, video, grid">', root_content)
        self.assertNotIn('<view name="basic, detailed, video">', root_content)
        self.assertNotIn('<view name="basic, detailed">', root_content)
        self.assertNotIn('<feature supported="video">', root_content)

        # Calibração do gamelist (pos: 0 0.12, size: 0.319 0.805, termina em y=444px antes do rodapé)
        self.assertIn("<pos>0 0.12</pos>", root_content)
        self.assertIn("<size>0.319 0.805</size>", root_content)
        self.assertIn("<horizontalMargin>0.025</horizontalMargin>", root_content)

        # md_image e md_video adaptáveis com margem segura
        self.assertIn("<pos>0.66 0.485</pos>", root_content)
        self.assertIn("<maxSize>0.62 0.70</maxSize>", root_content)

        # md_name universal em todas as views (branco e rebaixado para y=0.865 com singleLineScroll ativo)
        self.assertIn('name="md_name"', root_content)
        self.assertIn("<pos>0.339 0.865</pos>", root_content)
        self.assertIn("<size>0.64 0.06</size>", root_content)
        self.assertIn("<color>FFFFFF</color>", root_content)
        self.assertIn("<singleLineScroll>true</singleLineScroll>", root_content)

        # Helpsystem alinhado à esquerda na visualização gamelist (0.965 para casar com system view)
        gamelist_match = re.search(
            r'<view name="basic,\s*detailed,\s*video,\s*grid">(.*?)</view>', root_content, re.DOTALL
        )
        self.assertIsNotNone(gamelist_match, "Bloco gamelist unificado não encontrado")
        gamelist_xml = gamelist_match.group(1)
        helpsystem_match = re.search(r'<helpsystem name="help">(.*?)</helpsystem>', gamelist_xml, re.DOTALL)
        self.assertIsNotNone(helpsystem_match, "helpsystem não encontrado no gamelist")
        help_xml = helpsystem_match.group(1)
        self.assertIn("<pos>0.025 0.965</pos>", help_xml)
        self.assertIn("<origin>0 1</origin>", help_xml)
        self.assertNotIn("<pos>1 1</pos>", help_xml)
        self.assertNotIn("<origin>1 1</origin>", help_xml)

        # Menu view calibrada
        self.assertIn('name="menutitle"', root_content)
        self.assertIn('name="menufooter"', root_content)
        self.assertIn('name="menutextsmall"', root_content)

    def test_epic_cody_ml_imagens_cabecalho_limpo(self):
        from PIL import Image

        art_dir = self.feat_dir / "storage" / ".config" / "emulationstation" / "themes" / "Epic Cody ML" / "_art"
        png_file = art_dir / "ingame-global-bg.png"
        jpg_file = art_dir / "ingame-global-bg.jpg"
        self.assertTrue(png_file.is_file(), "ingame-global-bg.png ausente")
        self.assertTrue(jpg_file.is_file(), "ingame-global-bg.jpg ausente")

        im_png = Image.open(png_file)
        self.assertEqual(im_png.size, (640, 480))
        crop_png = im_png.crop((0, 0, 207, 53))
        colors_png = set(crop_png.get_flattened_data())
        self.assertEqual(colors_png, {(0, 0, 0, 255)}, "Cabeçalho do PNG deve ser preto puro")

        # Linha vertical amarela deve terminar em y=444px e não invadir o rodapé (y=445..479)
        for y in range(445, 480):
            p = im_png.getpixel((207, y))
            self.assertEqual(p, (14, 14, 14, 255), f"Linha divisória no PNG em y={y} deve estar limpa")

        im_jpg = Image.open(jpg_file)
        self.assertEqual(im_jpg.size, (640, 480))
        crop_jpg = im_jpg.crop((0, 0, 200, 50))
        for r, g, b in crop_jpg.get_flattened_data():
            self.assertLessEqual(r, 2)
            self.assertLessEqual(g, 2)
            self.assertLessEqual(b, 2)

        for y in range(445, 480):
            p = im_jpg.getpixel((207, y))
            self.assertLess(p[0] + p[1] + p[2], 100, f"Linha divisória no JPG em y={y} deve estar escura")

    def test_refatora_epic_cody_ml_script(self):
        import sys

        sys.path.insert(0, str(ROOT))
        from tools.refatora_epic_cody_ml import refatora_raiz_theme_xml

        mock_upstream = """<theme>
<view name="system">
<text name="sys_line1"><text>Old</text></text>
</view>
<view name="basic, detailed, video">
<textlist name="gamelist"><pos>0 0.12</pos><size>0.319 0.91</size></textlist>
<helpsystem name="help"><pos>1 1</pos><origin>1 1</origin><textColor>ffffff</textColor><iconColor>ffffff</iconColor></helpsystem>
</view>
<view name="basic, detailed">
<image name="md_image"></image>
</view>
<feature supported="video">
<view name="video">
<text name="md_name"></text>
</view>
</feature>
<view name="screen">
</view>
<view name="menu">
</view>
</theme>"""
        out = refatora_raiz_theme_xml(mock_upstream)
        self.assertIn('<view name="basic, detailed, video, grid">', out)
        self.assertNotIn('<view name="basic, detailed, video">', out)
        self.assertNotIn('<feature supported="video">', out)
        self.assertIn("<pos>0.025 0.965</pos>", out)
        self.assertIn("<size>0.319 0.805</size>", out)
        self.assertIn("<horizontalMargin>0.025</horizontalMargin>", out)
        self.assertIn("<pos>0.339 0.865</pos>", out)
        self.assertIn("<color>FFFFFF</color>", out)
        self.assertIn("<singleLineScroll>true</singleLineScroll>", out)
        self.assertIn('name="menutitle"', out)


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
