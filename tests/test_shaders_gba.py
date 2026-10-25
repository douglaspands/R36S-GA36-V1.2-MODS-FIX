"""Testes da feature de shaders do GBA (54-shaders-gba)."""

import stat
import tomllib
import unittest

from context import ROOT

FEATURE_DIR = ROOT / "features" / "54-shaders-gba"
SHADERS_GBA_DIR = FEATURE_DIR / "system" / "usr" / "share" / "common-shaders" / "gba"
SHADER_GLSL = SHADERS_GBA_DIR / "gba-modern-remaster.glsl"
SHADER_GLSLP = SHADERS_GBA_DIR / "gba-modern-remaster.glslp"


class TestShadersGba(unittest.TestCase):
    def test_feature_descriptor(self):
        desc = FEATURE_DIR / "feature.toml"
        self.assertTrue(desc.is_file(), "feature.toml ausente")
        dados = tomllib.loads(desc.read_text(encoding="utf-8"))
        self.assertEqual(dados["schema"], 1)
        self.assertEqual(dados["order"], 54)
        self.assertTrue(dados["enabled"])
        self.assertIn("GBA", dados["name"])

    def test_shader_files_exist_and_permissions(self):
        self.assertTrue(SHADER_GLSL.is_file(), "gba-modern-remaster.glsl ausente")
        self.assertTrue(SHADER_GLSLP.is_file(), "gba-modern-remaster.glslp ausente")

        mode_glsl = stat.S_IMODE(SHADER_GLSL.stat().st_mode)
        mode_glslp = stat.S_IMODE(SHADER_GLSLP.stat().st_mode)
        self.assertEqual(oct(mode_glsl), oct(0o644), f"Permissão inesperada para {SHADER_GLSL}: {oct(mode_glsl)}")
        self.assertEqual(oct(mode_glslp), oct(0o644), f"Permissão inesperada para {SHADER_GLSLP}: {oct(mode_glslp)}")

    def test_shader_preset_syntax(self):
        conteudo = SHADER_GLSLP.read_text(encoding="utf-8")
        linhas = [linha.strip() for linha in conteudo.splitlines() if linha.strip()]
        d = {}
        for linha in linhas:
            if "=" in linha:
                k, v = linha.split("=", 1)
                d[k.strip()] = v.strip().strip('"')

        self.assertEqual(d.get("shaders"), "1")
        self.assertEqual(d.get("shader0"), "gba-modern-remaster.glsl")
        self.assertEqual(d.get("filter_linear0"), "true")

    def test_shader_glsl_content(self):
        conteudo = SHADER_GLSL.read_text(encoding="utf-8")
        self.assertIn("GBA Modern Remaster Shader", conteudo)
        self.assertIn("GBA_Matrix", conteudo)
        self.assertIn("CORRECTION_STRENGTH", conteudo)
        self.assertIn("PIXEL_SOFTNESS", conteudo)
        self.assertIn("smoothstep", conteudo)

    def test_desligado_por_padrao(self):
        # Preset automático do RetroArch (.glslp em config/<core>/) ligaria o
        # shader sempre e passaria por cima do SHADER SET escolhido no ES
        presets = sorted(str(p.relative_to(FEATURE_DIR)) for p in FEATURE_DIR.rglob("*.glslp") if p != SHADER_GLSLP)
        self.assertEqual(presets, [], "Feature traz preset automático de shader")
        self.assertFalse((FEATURE_DIR / "storage").exists(), "Feature não deve mexer na p8")


if __name__ == "__main__":
    unittest.main()
