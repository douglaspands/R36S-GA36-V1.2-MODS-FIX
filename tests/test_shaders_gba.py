"""Testes da feature de shaders do GBA (54-shaders-gba)."""

import os
import re
import stat
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

from context import ROOT

FEATURE_DIR = ROOT / "features" / "54-shaders-gba"
SHADERS_GBA_DIR = FEATURE_DIR / "system" / "usr" / "share" / "common-shaders" / "gba"
SHADER_GLSL = SHADERS_GBA_DIR / "gba-modern-remaster.glsl"
SHADER_GLSLP = SHADERS_GBA_DIR / "gba-modern-remaster.glslp"

LIMPA = FEATURE_DIR / "system" / "usr" / "lib" / "r36" / "shader-gba-prepara"
SERVICE_DIR = FEATURE_DIR / "system" / "usr" / "lib" / "systemd" / "system"
REF = '#reference "/storage/shaders/gba/gba-modern-remaster.glslp"\n'  # preset da versão de teste antiga
PADRAO = '#reference "/usr/share/common-shaders/gba/gba-modern-remaster.glslp"\n'
PADRAO_TMP = '#reference "/tmp/shaders/gba/gba-modern-remaster.glslp"\n'  # build 20261026-002054
SETLINE = "gba.shaderset=gba/gba-modern-remaster.glslp\n"
CORES = ("gpSP", "mGBA", "VBA-M", "VBA Next")


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
        parametros = re.findall(r"^#pragma parameter (\w+)", conteudo, re.MULTILINE)
        self.assertEqual(
            sorted(parametros), ["BRIGHTNESS", "CONTRAST", "HIGHLIGHT", "LCD_GRID", "ROLLOFF", "SATURATION", "SOFTNESS", "VIBRANCE"]
        )
        padroes = {
            m[0]: float(m[1])
            for m in re.findall(r'^#pragma parameter (\w+) "[^"]*" ([-\d.]+)', conteudo, re.MULTILINE)
        }
        self.assertEqual(
            padroes,
            {"VIBRANCE": 0.45, "SATURATION": 1.10, "ROLLOFF": 0.35, "CONTRAST": 0.28, "HIGHLIGHT": 0.05, "SOFTNESS": 0.15, "LCD_GRID": 0.10, "BRIGHTNESS": 0.0},
        )
        nomes = re.findall(r'^#pragma parameter \w+ "([^"]*)"', conteudo, re.MULTILINE)
        self.assertEqual(
            nomes,
            ["VIBRANCE", "SATURATION", "HIGHLIGHT ROLLOFF", "S-CURVE Contrast", "HIGHLIGHT SHOULDER", "PIXEL SOFTNESS", "LCD GRID (0=Off)", "BRIGHTNESS"],
        )
        # os #define de reserva repetem os padrões dos #pragma
        reserva = {m[0]: float(m[1]) for m in re.findall(r"^#define (\w+) ([-\d.]+)\s*$", conteudo, re.MULTILINE) if m[0] in padroes}
        self.assertEqual(reserva, padroes)
        for antigo in ("CORRECTION_STRENGTH", "GAMMA_BOOST", "PIXEL_SOFTNESS", "GBA_Matrix"):
            self.assertNotIn(antigo, conteudo)

    def test_shader_leve_para_mali400(self):
        conteudo = SHADER_GLSL.read_text(encoding="utf-8")
        self.assertNotIn("pow(", conteudo)
        # highp só dentro do bloco GL_FRAGMENT_PRECISION_HIGH
        bloco = re.sub(r"#ifdef GL_FRAGMENT_PRECISION_HIGH.*?#else", "", conteudo, flags=re.DOTALL)
        self.assertNotIn("highp", bloco)
        self.assertIn("mediump", conteudo)
        self.assertEqual(len(re.findall(r"COMPAT_TEXTURE\s*\(\s*Texture", conteudo)), 1)

    def test_preset_padrao_nasce_no_boot_nao_na_imagem(self):
        # O preset automático do RetroArch (.glslp em config/<core>/) é criado pelo
        # r36-shader-gba-prepara no boot, para valer também com --keep-storage:
        # a feature não traz .glslp de core nem mexe na p8.
        presets = sorted(str(p.relative_to(FEATURE_DIR)) for p in FEATURE_DIR.rglob("*.glslp") if p != SHADER_GLSLP)
        self.assertEqual(presets, [], "Feature traz preset automático de shader na imagem")
        self.assertFalse((FEATURE_DIR / "storage").exists(), "Feature não deve mexer na p8 pela imagem")


class TestPreparoDoShaderPadrao(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.gba = self.root / "storage" / "shaders" / "gba"
        self.config = self.root / "storage" / ".config" / "retroarch" / "config"

    def roda(self):
        proc = subprocess.run(
            ["sh", str(LIMPA)], capture_output=True, text=True,
            env={"PATH": os.environ["PATH"], "R36_ROOT": str(self.root)},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def instala(self, destino, glsl, glslp='shader0 = "gba-modern-remaster.glsl"\n'):
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "gba-modern-remaster.glsl").write_text(glsl)
        (destino / "gba-modern-remaster.glslp").write_text(glslp)

    def copia_antiga(self, glsl="#pragma parameter CORRECTION_STRENGTH x\n"):
        self.instala(self.root / "usr" / "share" / "common-shaders" / "gba", "#pragma parameter VIBRANCE novo\n")
        self.instala(self.gba, glsl)

    def preset(self, nome, texto):
        arq = self.config / nome
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(texto)
        return arq

    def test_service_e_script(self):
        self.assertTrue(os.access(LIMPA, os.X_OK), "shader-gba-prepara sem permissão de execução")
        proc = subprocess.run(["sh", "-n", str(LIMPA)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        servico = (SERVICE_DIR / "r36-shader-gba-prepara.service").read_text(encoding="utf-8")
        diretivas = [l for l in servico.splitlines() if l.strip() and not l.lstrip().startswith("#")]
        self.assertIn("Before=emustation.service", diretivas)
        self.assertFalse([l for l in diretivas if l.startswith("After=") and "emuelec-autostart" in l])
        # limpa a camada de cima do overlay /tmp/shaders e o remonta, então roda depois dele
        self.assertIn("After=tmp-shaders.mount", diretivas)
        link = SERVICE_DIR / "emuelec.target.wants" / "r36-shader-gba-prepara.service"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(link), "../r36-shader-gba-prepara.service")

    def system(self, nome):
        return (self.root / "usr" / "share" / "common-shaders" / "gba" / nome).read_text()

    def test_atualiza_copia_antiga_e_remove_presets_que_a_referenciam(self):
        # O emuelec_autostart.sh copia o SYSTEM para a p8 com rsync --ignore-existing e
        # nunca atualiza: a cópia de um build anterior esconde a nova no overlay. O serviço
        # regrava o conteúdo no mesmo arquivo (apagar com o overlay montado quebra a vista).
        self.copia_antiga()
        glsl = self.gba / "gba-modern-remaster.glsl"
        inode = glsl.stat().st_ino
        (self.gba / "gba-modern-remaster.glslp").write_text("antigo\n")
        a = self.preset("gpSP/gba.glslp", REF)
        b = self.preset("mGBA/gba.glslp", REF)
        outro = self.preset("mGBA/outro.glslp", '#reference "/tmp/shaders/crt/crt-pi.glslp"\n')
        self.roda()
        self.assertEqual(glsl.read_text(), self.system("gba-modern-remaster.glsl"))
        self.assertEqual(glsl.stat().st_ino, inode, "a cópia deve ser regravada no lugar, não recriada")
        self.assertEqual((self.gba / "gba-modern-remaster.glslp").read_text(), self.system("gba-modern-remaster.glslp"))
        self.assertFalse(a.exists())
        self.assertFalse(b.exists())
        self.assertTrue(outro.exists(), "preset de outro shader não pode ser apagado")

    def test_atualiza_copia_de_versao_anterior_do_shader_novo(self):
        self.copia_antiga("#pragma parameter VIBRANCE antigo\n")
        self.roda()
        self.assertEqual((self.gba / "gba-modern-remaster.glsl").read_text(), "#pragma parameter VIBRANCE novo\n")

    def test_nao_cria_copia_que_nao_existe(self):
        # Só atualiza o que o rsync do EmuELEC já pôs na p8; não cria a pasta
        self.system_com_shader()
        self.roda()
        self.assertFalse(self.gba.exists())

    def test_preserva_copia_identica_a_do_system(self):
        self.copia_antiga("#pragma parameter VIBRANCE novo\n")
        preset = self.preset("gpSP/gba.glslp", REF)
        self.roda()
        self.assertTrue((self.gba / "gba-modern-remaster.glsl").exists())
        self.assertTrue(preset.exists())

    def test_sem_nada_na_p8(self):
        self.roda()

    def test_cria_preset_padrao_para_os_cores_de_gba(self):
        self.copia_antiga("#pragma parameter VIBRANCE novo\n")
        self.roda()
        for core in CORES:
            self.assertEqual((self.config / core / f"{core}.glslp").read_text(), PADRAO, core)

    def test_preset_tambem_na_pasta_do_retroarch_cfg(self):
        # O RetroArch 1.17 procura o preset de core em rgui_config_directory (no cartão é
        # "/config", que não existe), na pasta do retroarch.cfg e em video_shader_dir/presets.
        self.system_com_shader()
        self.roda()
        radir = self.root / "storage" / ".config" / "retroarch"
        for core in CORES:
            self.assertEqual((radir / core / f"{core}.glslp").read_text(), PADRAO, core)
        roms = self.root / "storage" / "roms"
        roms.mkdir(parents=True)
        (roms / "r36-gba-sem-shader").write_text("")
        self.roda()
        for core in CORES:
            self.assertFalse((radir / core / f"{core}.glslp").exists(), core)

    def test_nao_sobrescreve_preset_salvo_pelo_usuario(self):
        self.instala(self.root / "usr" / "share" / "common-shaders" / "gba", "#pragma parameter VIBRANCE novo\n")
        salvo = self.preset("gpSP/gpSP.glslp", PADRAO + 'SATURATION = "0.80"\n')
        self.roda()
        self.assertIn("SATURATION", salvo.read_text())

    def test_idempotente(self):
        self.instala(self.root / "usr" / "share" / "common-shaders" / "gba", "#pragma parameter VIBRANCE novo\n")
        self.roda()
        antes = {c: (self.config / c / f"{c}.glslp").stat().st_mtime_ns for c in CORES}
        self.roda()
        self.assertEqual(antes, {c: (self.config / c / f"{c}.glslp").stat().st_mtime_ns for c in CORES})

    def test_chave_na_p1_desliga_e_remove_os_presets_criados(self):
        self.instala(self.root / "usr" / "share" / "common-shaders" / "gba", "#pragma parameter VIBRANCE novo\n")
        self.roda()
        outro = self.preset("mGBA/gba.glslp", '#reference "/tmp/shaders/crt/crt-pi.glslp"\n')
        salvo = self.preset("VBA-M/VBA-M.glslp", PADRAO + 'SATURATION = "0.80"\n')
        roms = self.root / "storage" / "roms"
        roms.mkdir(parents=True)
        (roms / "r36-gba-sem-shader").write_text("")
        self.roda()
        for core in ("gpSP", "mGBA", "VBA Next"):
            self.assertFalse((self.config / core / f"{core}.glslp").exists(), core)
        self.assertTrue(outro.exists(), "outro preset não pode ser apagado")
        self.assertTrue(salvo.exists(), "preset editado pelo usuário não pode ser apagado")
        self.roda()  # com a chave, nada volta
        self.assertFalse((self.config / "gpSP" / "gpSP.glslp").exists())

    def system_com_shader(self):
        self.instala(self.root / "usr" / "share" / "common-shaders" / "gba", "#pragma parameter VIBRANCE novo\n")

    def emuconf(self, texto):
        arq = self.root / "storage" / ".config" / "emuelec" / "configs" / "emuelec.conf"
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(texto)
        return arq

    def test_liga_gba_shaderset_no_emuelec_conf(self):
        self.system_com_shader()
        for fim in ("\n", ""):  # com e sem quebra de linha no fim do arquivo
            conf = self.emuconf("gba.core=gpsp" + fim)
            self.roda()
            self.assertEqual(conf.read_text(), "gba.core=gpsp\n" + SETLINE)
            self.roda()  # idempotente
            self.assertEqual(conf.read_text().count("gba.shaderset="), 1)

    def test_respeita_gba_shaderset_do_usuario(self):
        self.system_com_shader()
        for escolha in ("gba.shaderset=none\n", "gba.shaderset=crt/crt-pi.glslp\n"):
            conf = self.emuconf("gba.core=gpsp\n" + escolha)
            self.roda()
            self.assertEqual(conf.read_text(), "gba.core=gpsp\n" + escolha)

    def test_chave_remove_so_a_linha_nossa_do_emuelec_conf(self):
        self.system_com_shader()
        conf = self.emuconf("gba.core=gpsp\n" + SETLINE + "snes.shaderset=x\n")
        roms = self.root / "storage" / "roms"
        roms.mkdir(parents=True)
        (roms / "r36-gba-sem-shader").write_text("")
        self.roda()
        self.assertEqual(conf.read_text(), "gba.core=gpsp\nsnes.shaderset=x\n")
        escolha = self.emuconf("gba.shaderset=crt/crt-pi.glslp\n")
        self.roda()
        self.assertEqual(escolha.read_text(), "gba.shaderset=crt/crt-pi.glslp\n")

    def test_preset_do_build_anterior_e_reconhecido_pela_chave(self):
        self.system_com_shader()
        antigo = self.preset("gpSP/gpSP.glslp", PADRAO_TMP)
        roms = self.root / "storage" / "roms"
        roms.mkdir(parents=True)
        (roms / "r36-gba-sem-shader").write_text("")
        self.roda()
        self.assertFalse(antigo.exists())

    def test_sem_emuelec_conf_so_os_presets(self):
        self.system_com_shader()
        self.roda()
        self.assertTrue((self.config / "gpSP" / "gpSP.glslp").exists())

    def test_log_na_p1_quando_montada(self):
        self.system_com_shader()
        roms = self.root / "storage" / "roms"
        roms.mkdir(parents=True)
        (roms / "r36-diagnostico").write_text("")
        self.emuconf("gba.core=gpsp\n")
        self.roda()
        log = (roms / "r36-shader-gba.log").read_text()
        self.assertIn("gba.shaderset", log)
        self.assertIn("preset gpSP criado", log)

    def test_sem_a_chave_de_diagnostico_nao_cria_o_log_e_o_resto_vale(self):
        self.system_com_shader()
        roms = self.root / "storage" / "roms"
        roms.mkdir(parents=True)
        conf = self.emuconf("gba.core=gpsp\n")
        fb = self.root / "sys" / "class" / "graphics" / "fb0"
        fb.mkdir(parents=True)
        (fb / "modes").write_text("U:640x480p-60\n")
        self.roda()
        self.assertFalse((roms / "r36-shader-gba.log").exists())
        self.assertIn("gba.shaderset=", conf.read_text())
        self.assertTrue((self.config / "gpSP" / "gpSP.glslp").exists())
        # a chave de desligar continua valendo sem a de diagnostico
        (roms / "r36-gba-sem-shader").write_text("")
        self.roda()
        self.assertNotIn("gba.shaderset=", conf.read_text())
        self.assertFalse((self.config / "gpSP" / "gpSP.glslp").exists())
        self.assertFalse((roms / "r36-shader-gba.log").exists())

    def test_sem_a_chave_de_diagnostico_o_log_antigo_fica(self):
        self.system_com_shader()
        roms = self.root / "storage" / "roms"
        roms.mkdir(parents=True)
        (roms / "r36-shader-gba.log").write_text("boot antigo\n")
        self.roda()
        self.assertEqual((roms / "r36-shader-gba.log").read_text(), "boot antigo\n")

    def test_tmp_shaders_por_bind_sem_overlayfs(self):
        # O kernel 3.4 não tem overlayfs: o tmp-shaders.mount falha e /tmp/shaders (lista do
        # "SHADER SET" do ES) fica vazio. No aparelho, o serviço monta /storage/shaders ali.
        texto = LIMPA.read_text(encoding="utf-8")
        self.assertIn("mount -o bind /storage/shaders /tmp/shaders", texto)
        self.assertRegex(texto, r'\[ -z "\$ROOT" \] && ! grep -q \' /tmp/shaders \' /proc/mounts')

    def test_log_do_framebuffer(self):
        # Diagnóstico do tearing: o log da p1 traz os atributos do fb0 (buffer duplo?)
        self.system_com_shader()
        roms = self.root / "storage" / "roms"
        roms.mkdir(parents=True)
        (roms / "r36-diagnostico").write_text("")
        fb = self.root / "sys" / "class" / "graphics" / "fb0"
        fb.mkdir(parents=True)
        (fb / "virtual_size").write_text("640,960\n")
        (fb / "modes").write_text("U:640x480p-60\n")
        self.roda()
        log = (roms / "r36-shader-gba.log").read_text()
        self.assertIn("fb0 virtual_size: 640,960", log)
        self.assertIn("fb0 modes: U:640x480p-60", log)

    def test_sem_shader_no_system_nada_e_criado(self):
        self.roda()
        self.assertFalse(self.config.exists())


if __name__ == "__main__":
    unittest.main()
