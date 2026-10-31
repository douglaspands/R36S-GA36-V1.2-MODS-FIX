"""Testes do runtime LÖVE 11.5 standalone para Allwinner A33 (feature 64-love2d)."""

import os
import re
import stat
import subprocess
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path

from context import ROOT

FEATURE_DIR = ROOT / "features" / "64-love2d"
SYSTEM_BIN = FEATURE_DIR / "system" / "usr" / "bin"
LAUNCHER = SYSTEM_BIN / "love.sh"
BINARY = SYSTEM_BIN / "love"
GPTK_SYSTEM = FEATURE_DIR / "system" / "usr" / "config" / "gptokeyb" / "love.gptk"
GPTK_BIN = SYSTEM_BIN / "love.gptk"
ALSOFT_CONFIG_SYSTEM = FEATURE_DIR / "system" / "usr" / "config" / "openal" / "alsoft.conf"
ALSOFT_CONFIG_ETC = FEATURE_DIR / "system" / "etc" / "openal" / "alsoft.conf"
RECIPE = ROOT / "ports" / "love2d" / "receita.toml"
BUILD_SCRIPT = ROOT / "ports" / "love2d" / "compilar.sh"
PATCHES_DIR = ROOT / "ports" / "love2d" / "patches"
MRRESCUE_ROM = FEATURE_DIR / "roms" / "love" / "mrrescue.love"


class TestLove2D(unittest.TestCase):
    def test_recipe_and_build_script(self):
        self.assertTrue(RECIPE.is_file(), "receita.toml ausente")
        dados = tomllib.loads(RECIPE.read_text(encoding="utf-8"))
        self.assertEqual(dados["port"]["nome"], "love")
        self.assertEqual(dados["port"]["versao"], "11.5")
        self.assertIn("-mcpu=cortex-a7", dados["flags"]["cflags"])
        self.assertIn("-DLOVE_GRAPHICS_USE_OPENGLES=1", dados["flags"]["cflags"])
        self.assertTrue(BUILD_SCRIPT.is_file(), "compilar.sh ausente")
        self.assertTrue(os.access(BUILD_SCRIPT, os.X_OK), "compilar.sh não executável")

    def test_cxx_patches(self):
        self.assertTrue(PATCHES_DIR.is_dir(), "pasta de patches ausente")
        patch_viewport = PATCHES_DIR / "01-viewport-aspect-640x480.patch"
        self.assertTrue(patch_viewport.is_file(), "patch de viewport ausente")
        conteudo = patch_viewport.read_text(encoding="utf-8")
        self.assertIn("gl.setViewport", conteudo)
        self.assertIn("Graphics.cpp", conteudo)
        self.assertIn("640", conteudo)
        self.assertIn("480", conteudo)

    def test_launcher_permissions_and_syntax(self):
        self.assertTrue(LAUNCHER.is_file(), "love.sh ausente")
        self.assertTrue(os.access(LAUNCHER, os.X_OK), "love.sh não executável")
        res = subprocess.run(["bash", "-n", str(LAUNCHER)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Erro de sintaxe em love.sh: {res.stderr}")

    def test_launcher_environment_and_logic(self):
        txt = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("LOVE_GRAPHICS_USE_OPENGLES=1", txt)
        self.assertIn("SDL_GAMECONTROLLERCONFIG", txt)
        self.assertIn("guide:b10", txt)
        self.assertIn("SDL_AUDIODRIVER=alsa", txt)
        self.assertIn("loading-game.png", txt)
        self.assertIn("blank_buffer", txt)
        self.assertIn("gptokeyb", txt)
        self.assertIn("audio-ganho", txt)
        self.assertIn("aplica", txt)
        self.assertIn("ALSOFT_CONF", txt)
        self.assertIn("alsoft.conf", txt)
        self.assertIn("CONSOLE_LANG", txt)
        self.assertIn("CONSOLE_LANG_SHORT", txt)
        self.assertIn("console_lang", txt)
        self.assertIn("ENABLE_LOG", txt)
        self.assertIn("love.log", txt)

    def test_launcher_language_propagation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            mock_bin_dir = tmp_root / "usr" / "bin"
            mock_bin_dir.mkdir(parents=True, exist_ok=True)
            mock_tmp_dir = tmp_root / "tmp"
            mock_tmp_dir.mkdir(parents=True, exist_ok=True)
            mock_love = mock_bin_dir / "love"
            mock_love.write_text(
                "#!/bin/sh\n"
                "echo \"OUT_LANG=$CONSOLE_LANG\"\n"
                "echo \"OUT_SHORT=$CONSOLE_LANG_SHORT\"\n"
                "echo \"OUT_LANG_ENV=$LANG\"\n"
                "echo \"OUT_LANGUAGE=$LANGUAGE\"\n",
                encoding="utf-8",
            )
            mock_love.chmod(0o755)

            dummy_rom = tmp_root / "game.love"
            dummy_rom.write_text("dummy", encoding="utf-8")

            # 1. Teste de fallback quando nenhum arquivo de configuração existe
            env = os.environ.copy()
            env["R36_ROOT"] = str(tmp_root)
            res = subprocess.run(
                ["bash", str(LAUNCHER), str(dummy_rom)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res.returncode, 0, f"Falha no lançador: {res.stderr}")
            self.assertIn("OUT_LANG=en_US", res.stdout)
            self.assertIn("OUT_SHORT=en", res.stdout)
            self.assertIn("OUT_LANG_ENV=en_US.UTF-8", res.stdout)
            self.assertIn("OUT_LANGUAGE=en_US", res.stdout)
            lang_file = mock_tmp_dir / "console_lang"
            self.assertTrue(lang_file.is_file())
            self.assertEqual(lang_file.read_text(encoding="utf-8").strip(), "en_US")

            # 2. Teste com emuelec.conf definido como pt_BR
            conf_dir = tmp_root / "storage" / ".config" / "emuelec" / "configs"
            conf_dir.mkdir(parents=True, exist_ok=True)
            (conf_dir / "emuelec.conf").write_text("system.language=pt_BR\n", encoding="utf-8")

            res_pt = subprocess.run(
                ["bash", str(LAUNCHER), str(dummy_rom)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res_pt.returncode, 0, f"Falha no lançador: {res_pt.stderr}")
            self.assertIn("OUT_LANG=pt_BR", res_pt.stdout)
            self.assertIn("OUT_SHORT=pt", res_pt.stdout)
            self.assertIn("OUT_LANG_ENV=pt_BR.UTF-8", res_pt.stdout)
            self.assertIn("OUT_LANGUAGE=pt_BR", res_pt.stdout)
            self.assertEqual(lang_file.read_text(encoding="utf-8").strip(), "pt_BR")

            # 3. Teste com es_settings.cfg quando emuelec.conf está ausente
            (conf_dir / "emuelec.conf").unlink()
            es_dir = tmp_root / "storage" / ".config" / "emulationstation"
            es_dir.mkdir(parents=True, exist_ok=True)
            (es_dir / "es_settings.cfg").write_text(
                '<?xml version="1.0"?>\n<config>\n<string name="Language" value="es_ES" />\n</config>\n',
                encoding="utf-8",
            )

            res_es = subprocess.run(
                ["bash", str(LAUNCHER), str(dummy_rom)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res_es.returncode, 0, f"Falha no lançador: {res_es.stderr}")
            self.assertIn("OUT_LANG=es_ES", res_es.stdout)
            self.assertIn("OUT_SHORT=es", res_es.stdout)
            self.assertIn("OUT_LANG_ENV=es_ES.UTF-8", res_es.stdout)
            self.assertIn("OUT_LANGUAGE=es_ES", res_es.stdout)
            self.assertEqual(lang_file.read_text(encoding="utf-8").strip(), "es_ES")

    def test_launcher_diagnostics_audio(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            mock_bin_dir = tmp_root / "usr" / "bin"
            mock_bin_dir.mkdir(parents=True, exist_ok=True)
            mock_love = mock_bin_dir / "love"
            mock_love.write_text(
                "#!/bin/sh\n"
                "echo \"ALSOFT_LOGLEVEL=${ALSOFT_LOGLEVEL:-NONE}\"\n"
                "echo \"ALSOFT_LOGFILE=${ALSOFT_LOGFILE:-NONE}\"\n"
                "echo \"SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-NONE}\"\n"
                "echo \"SDL_GAMECONTROLLERCONFIG=${SDL_GAMECONTROLLERCONFIG:-NONE}\"\n",
                encoding="utf-8",
            )
            mock_love.chmod(0o755)

            dummy_rom = tmp_root / "game.love"
            dummy_rom.write_text("dummy", encoding="utf-8")

            # 1. Sem a chave r36-diagnostico
            env = os.environ.copy()
            env["R36_ROOT"] = str(tmp_root)
            res = subprocess.run(
                ["bash", str(LAUNCHER), str(dummy_rom)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("ALSOFT_LOGLEVEL=NONE", res.stdout)
            self.assertIn("SDL_AUDIODRIVER=alsa", res.stdout)
            self.assertIn("guide:b10", res.stdout)

            # 2. Com a chave r36-diagnostico na partição de ROMs
            roms_dir = tmp_root / "storage" / "roms"
            roms_dir.mkdir(parents=True, exist_ok=True)
            (roms_dir / "r36-diagnostico").touch()

            res_diag = subprocess.run(
                ["bash", str(LAUNCHER), str(dummy_rom)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res_diag.returncode, 0)
            self.assertIn("ALSOFT_LOGLEVEL=3", res_diag.stdout)
            self.assertIn("r36-love-alsoft.log", res_diag.stdout)

    def test_launcher_logging_and_rotation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            mock_bin_dir = tmp_root / "usr" / "bin"
            mock_bin_dir.mkdir(parents=True, exist_ok=True)
            mock_love = mock_bin_dir / "love"
            mock_love.write_text(
                "#!/bin/sh\n"
                "echo \"LOVE_RUNNING_OK\"\n",
                encoding="utf-8",
            )
            mock_love.chmod(0o755)

            dummy_rom = tmp_root / "game.love"
            dummy_rom.write_text("dummy", encoding="utf-8")

            log_dir = tmp_root / "storage" / "roms" / "love"
            log_file = log_dir / "love.log"
            rot_file = log_dir / "love.log.1"

            # 1. Ativação de log padrão (ENABLE_LOG=1)
            env = os.environ.copy()
            env["R36_ROOT"] = str(tmp_root)
            res = subprocess.run(
                ["bash", str(LAUNCHER), str(dummy_rom)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res.returncode, 0, f"Falha no lançador: {res.stderr}")
            self.assertTrue(log_file.is_file(), "love.log não foi gerado")
            log_content = log_file.read_text(encoding="utf-8")
            self.assertIn("=== LÖVE Inicialização:", log_content)
            self.assertIn("CONSOLE_LANG=", log_content)
            self.assertIn("LOVE_GRAPHICS_USE_OPENGLES=1", log_content)
            self.assertIn("--- Verificação ldd", log_content)
            self.assertIn("LOVE_RUNNING_OK", log_content)

            # 2. Rotação quando log atinge teto >= 100 KB
            old_data = "OLD_LOG_ENTRY_" + ("X" * 105000)
            log_file.write_text(old_data, encoding="utf-8")
            self.assertGreaterEqual(log_file.stat().st_size, 102400)

            res_rot = subprocess.run(
                ["bash", str(LAUNCHER), str(dummy_rom)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res_rot.returncode, 0)
            self.assertTrue(rot_file.is_file(), "love.log.1 ausente após rotação")
            self.assertIn("OLD_LOG_ENTRY_", rot_file.read_text(encoding="utf-8"))
            new_log_content = log_file.read_text(encoding="utf-8")
            self.assertNotIn("OLD_LOG_ENTRY_", new_log_content)
            self.assertIn("=== LÖVE Inicialização:", new_log_content)
            self.assertLess(log_file.stat().st_size, 102400)

            # 3. Desativação transparente com ENABLE_LOG=0
            log_file.unlink()
            rot_file.unlink()
            env["ENABLE_LOG"] = "0"
            res_nolog = subprocess.run(
                ["bash", str(LAUNCHER), str(dummy_rom)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(res_nolog.returncode, 0)
            self.assertIn("LOVE_RUNNING_OK", res_nolog.stdout)
            self.assertFalse(log_file.exists(), "love.log criado mesmo com ENABLE_LOG=0")

    def test_gptk_configuration(self):
        for gptk_path in (GPTK_SYSTEM, GPTK_BIN):
            self.assertTrue(gptk_path.is_file(), f"{gptk_path} ausente")
            content = gptk_path.read_text(encoding="utf-8")
            self.assertIn("back = esc", content)
            self.assertIn("start = enter", content)
            self.assertIn("guide = esc", content)
            self.assertIn("hotkey = guide", content)
            self.assertIn("deadzone_", content)
            # Sem mapeamentos conflitantes de teclado sobre botões ou direcionais
            for conflict in ("a = space", "b = c", "x = x", "y = v", "up = up", "down = down", "left = left", "right = right"):
                self.assertNotIn(conflict, content)

    def test_alsoft_configuration(self):
        for config_path in (ALSOFT_CONFIG_SYSTEM, ALSOFT_CONFIG_ETC):
            self.assertTrue(config_path.is_file(), f"{config_path} ausente")
            content = config_path.read_text(encoding="utf-8")
            self.assertIn("sample-type = int16", content)
            self.assertIn("frequency = 48000", content)
            self.assertIn("dither = false", content)
            self.assertIn("resampler = bsinc12", content)
            self.assertIn("allow-resampler = false", content)
            self.assertIn("output-limiter = false", content)
            self.assertIn("stereo-mode = speakers", content)
            self.assertIn("stereo-encoding = pan", content)
            self.assertIn("hrtf = false", content)

    def test_mrrescue_rom_configuration(self):
        self.assertTrue(MRRESCUE_ROM.is_file(), "mrrescue.love ausente")
        with zipfile.ZipFile(MRRESCUE_ROM, "r") as z:
            # conf.lua deve ter 640x480
            conf_txt = z.read("conf.lua").decode("utf-8")
            self.assertIn("t.window.width = 640", conf_txt)
            self.assertIn("t.window.height = 480", conf_txt)
            # main.lua deve ter suporte ao D-pad e inicialização correta sem duplicação
            main_txt = z.read("main.lua").decode("utf-8")
            self.assertIn("state = 0", main_txt)
            self.assertIn("dpleft", main_txt)
            self.assertIn("dpright", main_txt)
            self.assertIn("dpup", main_txt)
            self.assertIn("dpdown", main_txt)
            self.assertIn("isDown(14)", main_txt)
            self.assertIn("love.gamepadpressed", main_txt)
            self.assertIn("love.joystickpressed", main_txt)
            self.assertIn("joy.isGamepad", main_txt)
            # joystick.lua e config.lua com binds de console e volume seguro
            cfg_txt = z.read("config.lua").decode("utf-8")
            self.assertIn("jump = 2", cfg_txt)
            self.assertIn("action = 1", cfg_txt)
            self.assertIn("sfx_volume = 0.65", cfg_txt)

    def test_binary_elf_and_abi(self):
        self.assertTrue(BINARY.is_file(), "executável love ausente")
        self.assertTrue(os.access(BINARY, os.X_OK), "executável love não executável")

        # Verifica tipo ELF com readelf ou file
        res = subprocess.run(["readelf", "-h", str(BINARY)], capture_output=True, text=True)
        if res.returncode == 0:
            self.assertIn("ARM", res.stdout)

        # Inspeciona versões da glibc exigidas
        res_ver = subprocess.run(["readelf", "-V", str(BINARY)], capture_output=True, text=True)
        if res_ver.returncode == 0:
            glibc_versions = re.findall(r"GLIBC_([0-9]+\.[0-9]+)", res_ver.stdout)
            for v_str in glibc_versions:
                parts = [int(p) for p in v_str.split(".")]
                self.assertLessEqual(parts, [2, 36], f"Símbolo GLIBC_{v_str} excede 2.36")
            # Garante ausência de dependência dinâmica do libstdc++.so moderno
            self.assertNotIn("GLIBCXX_", res_ver.stdout)

        # Verifica presença e conformidade das bibliotecas compartilhadas auxiliares
        lib_dir = FEATURE_DIR / "system" / "usr" / "lib"
        for lib_name in ["libmodplug.so.1", "libogg.so.0", "libluajit-5.1.so.2"]:
            lib_path = lib_dir / lib_name
            self.assertTrue(lib_path.is_file(), f"Biblioteca compartilhada {lib_name} ausente em {lib_dir}")
            res_lib = subprocess.run(["readelf", "-h", str(lib_path)], capture_output=True, text=True)
            if res_lib.returncode == 0:
                self.assertIn("ARM", res_lib.stdout)
            res_ver = subprocess.run(["readelf", "-V", str(lib_path)], capture_output=True, text=True)
            if res_ver.returncode == 0:
                glibc_versions = re.findall(r"GLIBC_([0-9]+\.[0-9]+)", res_ver.stdout)
                for v_str in glibc_versions:
                    parts = [int(p) for p in v_str.split(".")]
                    self.assertLessEqual(parts, [2, 36], f"Biblioteca {lib_name} requer GLIBC_{v_str} > 2.36")


if __name__ == "__main__":
    unittest.main()
