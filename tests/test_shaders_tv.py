"""Testes da feature de shaders de TV (57-shaders-tv)."""

import ast
import os
import re
import stat
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

from context import ROOT

FEATURE_DIR = ROOT / "features" / "57-shaders-tv"
SHADERS_DIR = FEATURE_DIR / "system" / "usr" / "share" / "common-shaders" / "tv"
SHADER_GLSL = SHADERS_DIR / "tv-modern-remaster.glsl"
SHADER_GLSLP = SHADERS_DIR / "tv-modern-remaster.glslp"
PREPARA = FEATURE_DIR / "system" / "usr" / "lib" / "r36" / "shader-tv-prepara"
SERVICE_DIR = FEATURE_DIR / "system" / "usr" / "lib" / "systemd" / "system"
REPLICA_ACTIVE = ROOT / "openspec" / "changes" / "shader-tv-modern-remaster" / "verificacao" / "replica_tv.py"
REPLICA_ARCHIVES = list((ROOT / "openspec" / "changes" / "archive").glob("*shader-tv-modern-remaster/verificacao/replica_tv.py")) if (ROOT / "openspec" / "changes" / "archive").exists() else []
REPLICA = REPLICA_ACTIVE if REPLICA_ACTIVE.exists() else (REPLICA_ARCHIVES[0] if REPLICA_ARCHIVES else REPLICA_ACTIVE)

REF = '#reference "/usr/share/common-shaders/tv/tv-modern-remaster.glslp"\n'
SET_VALUE = "tv/tv-modern-remaster.glslp"

TV_PARAMS = {
    "DITHER_BLEND": ("DITHER BLEND (0=Off)", 1.00, 0.0, 1.0, 0.05),
    "TV_SCANLINES": ("TV SCANLINES (0=Off)", 0.10, 0.0, 0.50, 0.02),
    "PIXEL_SOFTNESS": ("PIXEL SOFTNESS", 0.10, 0.0, 1.0, 0.05),
    "VIBRANCE": ("VIBRANCE", 0.40, 0.0, 1.0, 0.05),
    "SATURATION": ("SATURATION", 1.08, 0.5, 1.3, 0.01),
    "CONTRAST": ("S-CURVE Contrast", 0.25, 0.0, 1.0, 0.05),
    "ROLLOFF": ("HIGHLIGHT ROLLOFF", 0.35, 0.0, 1.0, 0.05),
    "BRIGHTNESS": ("BRIGHTNESS", 0.0, -0.30, 0.30, 0.01),
}

SISTEMAS = (
    "megadrive", "genesis", "snes", "nes", "mastersystem",
    "pce", "pcengine", "psx", "mame", "fbneo", "cps1", "cps2", "cps3", "neogeo"
)

CORES = (
    "Genesis Plus GX", "PicoDrive", "Snes9x", "Snes9x 2010",
    "Snes9x 2005 Plus", "Snes9x 2002", "FCEUmm", "Nestopia",
    "Gearsystem", "Beetle PCE Fast", "Mednafen PCE Fast",
    "Beetle SuperGrafx", "PCSX-ReARMed", "FinalBurn Neo",
    "FB Neo", "MAME 2003-Plus"
)


def pragmas(texto):
    return {
        m[0]: (m[1], float(m[2]), float(m[3]), float(m[4]), float(m[5]))
        for m in re.findall(
            r'^#pragma parameter (\w+) "([^"]*)" ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)\s*$',
            texto, re.MULTILINE
        )
    }


def padroes_da_replica():
    arvore = ast.parse(REPLICA.read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(getattr(t, "id", None) == "DEF_TV" for t in no.targets):
            return {k.value: v.value for k, v in zip(no.value.keys, no.value.values)}
    raise AssertionError("DEF_TV ausente em replica_tv.py")


class TestShadersTv(unittest.TestCase):
    def test_feature_descriptor(self):
        desc = FEATURE_DIR / "feature.toml"
        self.assertTrue(desc.is_file(), "feature.toml ausente")
        dados = tomllib.loads(desc.read_text(encoding="utf-8"))
        self.assertEqual(dados["schema"], 1)
        self.assertEqual(dados["order"], 57)
        self.assertTrue(dados["enabled"])
        self.assertIn("TV", dados["name"])

    def test_arquivos_e_permissoes(self):
        self.assertTrue(SHADER_GLSL.is_file(), "tv-modern-remaster.glsl ausente")
        self.assertTrue(SHADER_GLSLP.is_file(), "tv-modern-remaster.glslp ausente")
        self.assertEqual(oct(stat.S_IMODE(SHADER_GLSL.stat().st_mode)), oct(0o644))
        self.assertEqual(oct(stat.S_IMODE(SHADER_GLSLP.stat().st_mode)), oct(0o644))

    def test_preset_sintaxe(self):
        conteudo = SHADER_GLSLP.read_text(encoding="utf-8")
        linhas = [l.strip() for l in conteudo.splitlines() if l.strip()]
        d = {}
        for l in linhas:
            if "=" in l:
                k, v = l.split("=", 1)
                d[k.strip()] = v.strip().strip('"')
        self.assertEqual(d.get("shaders"), "1")
        self.assertEqual(d.get("shader0"), "tv-modern-remaster.glsl")
        self.assertEqual(d.get("filter_linear0"), "true")

    def test_shader_glsl_parametros_e_definicoes(self):
        conteudo = SHADER_GLSL.read_text(encoding="utf-8")
        self.assertIn("TV Modern Remaster Shader", conteudo)
        pars = pragmas(conteudo)
        self.assertEqual(sorted(pars.keys()), sorted(TV_PARAMS.keys()))
        for k, esperado in TV_PARAMS.items():
            self.assertEqual(pars[k], esperado, f"Parametro {k} difere do esperado")

        # Verifica defines de fallback
        defines = {
            m[0]: float(m[1])
            for m in re.findall(r"^#define (\w+) ([-\d.]+)\s*$", conteudo, re.MULTILINE)
            if m[0] in TV_PARAMS
        }
        for k, esperado in TV_PARAMS.items():
            self.assertAlmostEqual(defines[k], esperado[1], msg=f"Define de {k} difere do pragma")

    def test_parametros_alinham_com_replica(self):
        replica_defs = padroes_da_replica()
        for k, v in TV_PARAMS.items():
            self.assertIn(k, replica_defs)
            self.assertAlmostEqual(replica_defs[k], v[1], msg=f"Padrão de {k} difere entre GLSL e replica")

    def test_compatibilidade_mali400(self):
        conteudo = SHADER_GLSL.read_text(encoding="utf-8")
        self.assertNotIn("pow(", conteudo)
        bloco = re.sub(r"#ifdef GL_FRAGMENT_PRECISION_HIGH.*?#else", "", conteudo, flags=re.DOTALL)
        self.assertNotIn("highp", bloco)
        self.assertIn("mediump", conteudo)
        # Exatamente 3 leituras de textura na mesma scanline
        leituras = len(re.findall(r"COMPAT_TEXTURE\s*\(\s*Texture", conteudo))
        self.assertEqual(leituras, 3, "Shader de TV com fusão de dither deve ter exatamente 3 leituras")


class TestPreparoDoShaderTv(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.tv_p8 = self.root / "storage" / "shaders" / "tv"
        self.tv_p8.mkdir(parents=True, exist_ok=True)
        self.config = self.root / "storage" / ".config" / "retroarch" / "config"
        self.config.mkdir(parents=True, exist_ok=True)
        self.emuconf = self.root / "storage" / ".config" / "emuelec" / "configs" / "emuelec.conf"
        self.emuconf.parent.mkdir(parents=True, exist_ok=True)
        self.roms = self.root / "storage" / "roms"
        self.roms.mkdir(parents=True, exist_ok=True)

        # Instala arquivos de sistema simulados
        self.share = self.root / "usr" / "share" / "common-shaders" / "tv"
        self.share.mkdir(parents=True, exist_ok=True)
        (self.share / "tv-modern-remaster.glsl").write_text("#pragma parameter DITHER_BLEND novo\n")
        (self.share / "tv-modern-remaster.glslp").write_text('shader0 = "tv-modern-remaster.glsl"\n')

    def roda(self):
        proc = subprocess.run(
            ["sh", str(PREPARA)],
            capture_output=True, text=True,
            env={"PATH": os.environ["PATH"], "R36_ROOT": str(self.root)}
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_service_e_script_sintaxe(self):
        self.assertTrue(os.access(PREPARA, os.X_OK), "shader-tv-prepara sem permissão de execução")
        proc = subprocess.run(["sh", "-n", str(PREPARA)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        servico = (SERVICE_DIR / "r36-shader-tv-prepara.service").read_text(encoding="utf-8")
        self.assertIn("Before=emustation.service", servico)
        self.assertIn("After=r36-shader-gb-gbc-prepara.service", servico)
        self.assertIn("After=tmp-shaders.mount", servico)

        link = SERVICE_DIR / "emuelec.target.wants" / "r36-shader-tv-prepara.service"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(link), "../r36-shader-tv-prepara.service")

    def test_atualiza_copia_velha_na_p8(self):
        (self.tv_p8 / "tv-modern-remaster.glsl").write_text("#pragma parameter DITHER_BLEND antigo\n")
        (self.tv_p8 / "tv-modern-remaster.glslp").write_text('shader0 = "antigo.glsl"\n')
        self.roda()
        self.assertEqual((self.tv_p8 / "tv-modern-remaster.glsl").read_text(), "#pragma parameter DITHER_BLEND novo\n")
        self.assertEqual((self.tv_p8 / "tv-modern-remaster.glslp").read_text(), 'shader0 = "tv-modern-remaster.glsl"\n')

    def test_default_desligado_sem_chave(self):
        self.emuconf.write_text("system.language=pt_BR\n")
        self.roda()

        conf_texto = self.emuconf.read_text()
        for sis in SISTEMAS:
            self.assertNotIn(f"{sis}.shaderset={SET_VALUE}", conf_texto)

        for core in CORES:
            preset_core = self.config / core / f"{core}.glslp"
            self.assertFalse(preset_core.exists(), f"Preset não deve existir por padrão para {core}")

    def test_chave_ativa_shaderset_e_presets(self):
        (self.roms / "r36-tv-com-shader").touch()
        self.emuconf.write_text("system.language=pt_BR\n")
        self.roda()

        conf_texto = self.emuconf.read_text()
        for sis in SISTEMAS:
            self.assertIn(f"{sis}.shaderset={SET_VALUE}", conf_texto)

        for core in CORES:
            preset_core = self.config / core / f"{core}.glslp"
            self.assertTrue(preset_core.is_file(), f"Preset ausente para {core}")
            self.assertEqual(preset_core.read_text(), REF)

    def test_preserva_escolha_do_usuario(self):
        (self.roms / "r36-tv-com-shader").touch()
        self.emuconf.write_text("megadrive.shaderset=none\nsnes.shaderset=crt/crt-easymode.glslp\n")
        preset_snes = self.config / "Snes9x" / "Snes9x.glslp"
        preset_snes.parent.mkdir(parents=True, exist_ok=True)
        preset_snes.write_text('#reference "/tmp/shaders/crt/crt-easymode.glslp"\n')

        self.roda()

        conf_texto = self.emuconf.read_text()
        self.assertIn("megadrive.shaderset=none", conf_texto)
        self.assertIn("snes.shaderset=crt/crt-easymode.glslp", conf_texto)
        self.assertNotIn(f"snes.shaderset={SET_VALUE}", conf_texto)
        self.assertEqual(preset_snes.read_text(), '#reference "/tmp/shaders/crt/crt-easymode.glslp"\n')

    def test_remocao_da_chave_limpa_shaderset_e_presets(self):
        # Primeiro ativa com a chave
        (self.roms / "r36-tv-com-shader").touch()
        self.emuconf.write_text("system.language=pt_BR\n")
        self.roda()
        self.assertIn(f"megadrive.shaderset={SET_VALUE}", self.emuconf.read_text())
        self.assertTrue((self.config / "Genesis Plus GX" / "Genesis Plus GX.glslp").is_file())

        # Remove a chave: deve voltar para default desligado e limpar
        (self.roms / "r36-tv-com-shader").unlink()
        self.roda()

        conf_texto = self.emuconf.read_text()
        for sis in SISTEMAS:
            self.assertNotIn(f"{sis}.shaderset={SET_VALUE}", conf_texto)

        for core in CORES:
            self.assertFalse((self.config / core / f"{core}.glslp").exists(), f"Preset não removido para {core}")

    def test_log_condicionado_a_diagnostico(self):
        log = self.roms / "r36-shader-tv.log"
        self.roda()
        self.assertFalse(log.exists(), "Log não deve existir sem r36-diagnostico")

        (self.roms / "r36-diagnostico").touch()
        self.roda()
        self.assertTrue(log.is_file(), "Log deve existir com r36-diagnostico")
        conteudo_log = log.read_text()
        self.assertIn("r36-shader-tv-prepara", conteudo_log)


if __name__ == "__main__":
    unittest.main()
