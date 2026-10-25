"""Testes do port nativo ClassiCube para Allwinner A33 (feature 60-port-classicube)."""

import os
import re
import stat
import subprocess
import tempfile
import tomllib
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from context import ROOT, needs_base
from r36img import cores as C

FEATURE_DIR = ROOT / "features" / "60-port-classicube"
ROMS_DIR = FEATURE_DIR / "roms"
PORT_DIR = ROMS_DIR / "ports" / "classicube"
SCRIPTS_DIR = ROMS_DIR / "ports_scripts"
LAUNCHER = SCRIPTS_DIR / "ClassiCube.sh"
OPTIONS = PORT_DIR / "options.txt"
TEXPACK = PORT_DIR / "texpacks" / "default.zip"
AUDIO_ZIP = PORT_DIR / "audio" / "default.zip"
RECIPE = ROOT / "ports" / "classicube" / "receita.toml"
BUILD_SCRIPT = ROOT / "ports" / "classicube" / "compilar.sh"

SYSTEM_DIR = FEATURE_DIR / "system"
SYSTEM_SHARE_DIR = SYSTEM_DIR / "usr" / "share" / "classicube"
SYSTEM_PORTS_DIR = SYSTEM_SHARE_DIR / "ports_scripts"
BINARY = SYSTEM_SHARE_DIR / "ClassiCube"
SYNC_SCRIPT = SYSTEM_DIR / "usr" / "lib" / "r36" / "classicube-sync"
SERVICE_FILE = SYSTEM_DIR / "usr" / "lib" / "systemd" / "system" / "r36-classicube-sync.service"
SERVICE_WANTS_LINK = (
    SYSTEM_DIR / "usr" / "lib" / "systemd" / "system" / "emuelec.target.wants" / "r36-classicube-sync.service"
)


class TestPortClassiCube(unittest.TestCase):
    def test_feature_descriptor(self):
        desc = FEATURE_DIR / "feature.toml"
        self.assertTrue(desc.is_file(), "feature.toml ausente")
        dados = tomllib.loads(desc.read_text(encoding="utf-8"))
        self.assertEqual(dados["schema"], 1)
        self.assertEqual(dados["order"], 60)
        self.assertTrue(dados["enabled"])
        self.assertIn("ClassiCube", dados["name"])

    def test_recipe_and_build_script(self):
        self.assertTrue(RECIPE.is_file(), "receita.toml ausente")
        rec = tomllib.loads(RECIPE.read_text(encoding="utf-8"))
        self.assertEqual(rec["port"]["nome"], "classicube")
        self.assertEqual(rec["port"]["versao"], "1.3.9")
        self.assertEqual(rec["port"]["saida"], "ClassiCube")
        self.assertTrue(BUILD_SCRIPT.is_file(), "compilar.sh ausente")
        proc = subprocess.run(["bash", "-n", str(BUILD_SCRIPT)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Erro de sintaxe no compilar.sh: {proc.stderr}")

    def test_controls_patches_in_build_script(self):
        txt = BUILD_SCRIPT.read_text(encoding="utf-8")
        # Analógicos: y sem negar, zona morta radial de 20% com reescala
        # (sem o "-" do original; o trecho original aparece só como alvo da substituição)
        self.assertIn('eixo_subst = "Gamepad_SetAxis(port, axis, fx, fy, delta);"', txt)
        self.assertIn("#define PAD_DEADZONE   0.2f", txt)
        self.assertIn("(mag - PAD_DEADZONE) / (1.0f - PAD_DEADZONE)", txt)
        zona_subst = txt.split('zona_subst = """')[1].split('"""')[0]
        self.assertNotIn("1024", zona_subst)
        # Sensibilidade dos analógicos
        self.assertIn("Gamepad_AxisSensitivity[PAD_AXIS_LEFT]  = AXIS_SENSI_HIGHER;", txt)
        self.assertIn("Gamepad_AxisSensitivity[PAD_AXIS_RIGHT] = AXIS_SENSI_HIGHER;", txt)
        # Binds padrão do gamepad
        self.assertIn("{ CCPAD_LSTICK, CCPAD_RSTICK }, /* BIND_JUMP, BIND_RESPAWN */", txt)
        self.assertIn("{ 0, 0 },           { 0, 0 },           /* BIND_SET_SPAWN, BIND_CHAT */", txt)
        self.assertIn("{ CCPAD_4, 0 },{ CCPAD_R, 0 },/* BIND_DELETE_BLOCK, BIND_PICK_BLOCK", txt)
        # Cada substituição falha de forma ruidosa quando o trecho não existe
        for padrao in (
            "Padrão da zona morta não encontrado",
            "Padrão Gamepad_SetAxis não encontrado",
            "Padrão PAD_AXIS_SCALE não encontrado",
            "Padrão Gamepads_Init não encontrado",
            "Padrão de PadBind_Defaults não encontrado",
        ):
            self.assertIn(padrao, txt)

    def test_binary_exists_and_stripped(self):
        self.assertTrue(BINARY.is_file(), "Binário ClassiCube não encontrado na feature")
        self.assertGreater(BINARY.stat().st_size, 500 * 1024, "Binário excessivamente pequeno")
        texto = subprocess.run(["readelf", "-S", str(BINARY)], capture_output=True, text=True, check=True).stdout
        self.assertFalse(re.search(r"\[\s*\d+\]\s+\.debug_\S+", texto), "Binário contém seções de depuração")

    def test_binary_architecture_and_abi(self):
        texto = subprocess.run(
            ["readelf", "-h", "-A", "-d", "-V", "-W", "-s", str(BINARY)],
            capture_output=True, text=True, check=True,
            env={"LC_ALL": "C"}
        ).stdout

        self.assertRegex(texto, r"Class:\s+ELF32\b", "Não é ELF 32-bit")
        self.assertRegex(texto, r"Machine:\s+ARM\b", "Não é arquitetura ARM")
        self.assertRegex(texto, r"Tag_CPU_arch: v7\b", "Não é ARMv7-A")
        self.assertRegex(texto, r"Tag_FP_arch: VFPv4\b", "Não usa VFPv4")
        self.assertRegex(texto, r"Tag_ABI_VFP_args: VFP registers\b", "Não é hard-float")

        # Versões de GLIBC não podem exceder 2.36 (base da imagem)
        glibc_versoes = re.findall(r"\bGLIBC_(\d+\.\d+)\b", texto)
        self.assertTrue(glibc_versoes, "Nenhum símbolo GLIBC identificado")
        for v in glibc_versoes:
            partes = tuple(int(x) for x in v.split("."))
            self.assertLessEqual(partes, (2, 36), f"Símbolo {v} superior a GLIBC_2.36")

        # Bibliotecas dinâmicas necessárias
        needed = re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]", texto)
        self.assertIn("libSDL2-2.0.so.0", needed)
        self.assertIn("libc.so.6", needed)
        # Nenhuma biblioteca do desktop X11 / OpenGL comum
        self.assertNotIn("libX11.so.6", needed)
        self.assertNotIn("libGL.so.1", needed)

        # Patch SDL 2.0.9 GameControllerAddMappingsFromFile e gamecontrollerdb
        self.assertIn("SDL_GameControllerAddMappingsFromRW", texto)
        bin_conteudo = BINARY.read_bytes()
        self.assertIn(b"/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt", bin_conteudo)

        # O binário fica só no SYSTEM; a p1 não leva cópia
        self.assertFalse((PORT_DIR / "ClassiCube").exists(), "Binário duplicado em roms/ports/classicube/")

    @needs_base
    def test_binary_libraries_against_base(self):
        texto = subprocess.run(
            ["readelf", "-d", str(BINARY)],
            capture_output=True, text=True, check=True,
            env={"LC_ALL": "C"}
        ).stdout
        needed = re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]", texto)
        libs = C.libs_base()
        for lib in needed:
            self.assertIn(lib, libs, f"Biblioteca {lib} não encontrada no SYSTEM da imagem base")

    def test_launcher_script(self):
        self.assertTrue(LAUNCHER.is_file(), "ClassiCube.sh ausente")
        proc = subprocess.run(["bash", "-n", str(LAUNCHER)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Sintaxe inválida no ClassiCube.sh: {proc.stderr}")
        conteudo = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("SDL_VIDEO_GL_DRIVER", conteudo)
        self.assertIn("SDL_VIDEO_EGL_DRIVER", conteudo)
        self.assertIn("SDL_GAMECONTROLLERCONFIG", conteudo)
        self.assertIn("/storage/roms/ports/classicube", conteudo)
        self.assertIn("/usr/share/classicube", conteudo)
        self.assertIn('BIN="$SHARE_DIR/ClassiCube"', conteudo)
        self.assertNotIn("/tmp/classicube", conteudo)
        self.assertNotIn("SDL_GAMECONTROLLERCONFIG_FILE", conteudo)
        self.assertIn("--singleplayer", conteudo)
        self.assertNotIn('"$@"', conteudo)

    def roda_regra_sensibilidade(self, options_txt):
        """Roda o trecho da sensibilidade do ClassiCube.sh num options.txt temporário."""
        launcher = LAUNCHER.read_text(encoding="utf-8")
        m = re.search(r"# Sensibilidade da câmera.*?\nfi\n", launcher, re.S)
        self.assertIsNotNone(m, "Regra da sensibilidade ausente no ClassiCube.sh")
        with tempfile.TemporaryDirectory() as tmp:
            opts = Path(tmp) / "options.txt"
            opts.write_text(options_txt, encoding="utf-8")
            proc = subprocess.run(
                ["bash", "-euo", "pipefail", "-c", m.group(0)],
                capture_output=True, text=True, env={"PATH": os.environ["PATH"], "PORT_DIR": tmp},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return opts.read_text(encoding="utf-8")

    def test_launcher_sensibilidade_antiga_vira_nova(self):
        antes = "viewdist = 96\nmousesensitivity = 30\nauto-pause = false\n"
        depois = self.roda_regra_sensibilidade(antes)
        self.assertEqual(depois, "viewdist = 96\nmousesensitivity = 120\nauto-pause = false\n")

    def test_launcher_preserva_sensibilidade_do_jogador(self):
        for txt in ("mousesensitivity = 80\nviewdist = 96\n", "mousesensitivity = 300\n", "mousesensitivity = 120\n"):
            self.assertEqual(self.roda_regra_sensibilidade(txt), txt)

    def test_launcher_sensibilidade_ausente_recebe_padrao_novo(self):
        depois = self.roda_regra_sensibilidade("viewdist = 96\n")
        self.assertEqual(depois, "viewdist = 96\nmousesensitivity = 120\n")

    def test_options_preset(self):
        self.assertTrue(OPTIONS.is_file(), "options.txt ausente")
        txt = OPTIONS.read_text(encoding="utf-8")
        self.assertIn("mousesensitivity = 120", txt)
        self.assertIn("window-width = 640", txt)
        self.assertIn("window-height = 480", txt)
        self.assertIn("fpslimit = Limit60FPS", txt)
        self.assertIn("defaulttexpack = default.zip", txt)
        self.assertIn("auto-pause = false", txt)

    def test_offline_texpack(self):
        self.assertTrue(TEXPACK.is_file(), "texpacks/default.zip ausente")
        with zipfile.ZipFile(TEXPACK, "r") as z:
            nomes = z.namelist()
            self.assertIn("terrain.png", nomes)
            self.assertIn("gui.png", nomes)
            self.assertIn("char.png", nomes)
            self.assertIn("particles.png", nomes)

    def test_offline_audio(self):
        self.assertTrue(AUDIO_ZIP.is_file(), "audio/default.zip ausente")
        with zipfile.ZipFile(AUDIO_ZIP, "r") as z:
            nomes = z.namelist()
            self.assertTrue(any(n.startswith("dig_") and n.endswith(".wav") for n in nomes))
            self.assertTrue(any(n.startswith("step_") and n.endswith(".wav") for n in nomes))

        wavs = list((PORT_DIR / "audio").glob("*.wav"))
        self.assertGreaterEqual(len(wavs), 30, "Poucos arquivos .wav extraídos em audio/")

    def test_gamelist_and_images(self):
        gamelist = SCRIPTS_DIR / "gamelist.xml"
        self.assertTrue(gamelist.is_file(), "gamelist.xml ausente em ports_scripts/")
        txt = gamelist.read_text(encoding="utf-8")
        self.assertIn("<path>./ClassiCube.sh</path>", txt)
        self.assertIn("<name>Classic Craft (ClassiCube)</name>", txt)
        self.assertIn("<image>./img/ClassiCube.png</image>", txt)
        self.assertIn("<thumbnail>./img/ClassiCube.png</thumbnail>", txt)
        self.assertIn("<marquee>./img/ClassiCube.png</marquee>", txt)

        img = SCRIPTS_DIR / "img" / "ClassiCube.png"
        self.assertTrue(img.is_file(), "img/ClassiCube.png ausente")
        self.assertGreater(img.stat().st_size, 1024, "ClassiCube.png vazio ou muito pequeno")

        img_alt = SCRIPTS_DIR / "images" / "ClassiCube-image.png"
        self.assertTrue(img_alt.is_file(), "images/ClassiCube-image.png ausente")
        img_thumb = SCRIPTS_DIR / "images" / "ClassiCube-thumb.png"
        self.assertTrue(img_thumb.is_file(), "images/ClassiCube-thumb.png ausente")
        img_marquee = SCRIPTS_DIR / "images" / "ClassiCube-marquee.png"
        self.assertTrue(img_marquee.is_file(), "images/ClassiCube-marquee.png ausente")

    def test_system_ports_mirror_and_sync(self):
        for nome in (
            "ClassiCube.sh",
            "gamelist.xml",
            "img/ClassiCube.png",
            "images/ClassiCube-image.png",
            "images/ClassiCube-thumb.png",
            "images/ClassiCube-marquee.png",
        ):
            sys_file = SYSTEM_PORTS_DIR / nome
            rom_file = SCRIPTS_DIR / nome
            self.assertTrue(sys_file.is_file(), f"{nome} ausente em system/usr/share/classicube/ports_scripts/")
            self.assertEqual(sys_file.read_bytes(), rom_file.read_bytes(), f"{nome} difere entre system e roms")

        for nome in ("options.txt", "texpacks/default.zip", "audio/default.zip"):
            sys_file = SYSTEM_SHARE_DIR / nome
            rom_file = PORT_DIR / nome
            self.assertTrue(sys_file.is_file(), f"{nome} ausente em system/usr/share/classicube/")
            self.assertEqual(sys_file.read_bytes(), rom_file.read_bytes(), f"{nome} difere entre system e roms")

        self.assertTrue(SYNC_SCRIPT.is_file(), "classicube-sync ausente")
        mode = SYNC_SCRIPT.stat().st_mode
        self.assertTrue(bool(mode & stat.S_IXUSR), "classicube-sync sem permissão de execução")
        proc = subprocess.run(["sh", "-n", str(SYNC_SCRIPT)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Sintaxe inválida no classicube-sync: {proc.stderr}")
        conteudo_sync = SYNC_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("/usr/share/classicube", conteudo_sync)
        self.assertNotIn("/usr/bin/ports", conteudo_sync)
        self.assertNotIn("/storage/.config/emuelec/ports", conteudo_sync)
        self.assertNotIn("gamelists/ports", conteudo_sync)

        self.assertTrue(SERVICE_FILE.is_file(), "r36-classicube-sync.service ausente")
        conteudo_service = SERVICE_FILE.read_text(encoding="utf-8")
        self.assertIn("ExecStart=/usr/lib/r36/classicube-sync", conteudo_service)
        # O autostart só termina depois de "systemctl start emustation": ordenar
        # depois dele e antes do ES trava o boot no splash.
        self.assertNotRegex(conteudo_service, r"(?m)^After=.*emuelec-autostart")
        self.assertIn("Before=emustation.service", conteudo_service)
        self.assertIn("until mountpoint -q /storage/roms", conteudo_sync)
        self.assertIn("WantedBy=emuelec.target", conteudo_service)

        self.assertTrue(SERVICE_WANTS_LINK.is_symlink(), "Symlink r36-classicube-sync.service em emuelec.target.wants ausente")
        self.assertEqual(os.readlink(SERVICE_WANTS_LINK), "../r36-classicube-sync.service")

    def test_nenhuma_feature_cria_usr_bin_ports(self):
        # /usr/bin/ports ativa o overlay do mount_romfs.sh e esconde ports_scripts da p1
        criam = sorted(str(d.relative_to(ROOT)) for d in (ROOT / "features").glob("*/system/usr/bin/ports"))
        self.assertEqual(criam, [], "Feature cria /usr/bin/ports")


GAMELIST_OUTRO = """<?xml version="1.0"?>
<gameList>
	<game id="7" source="ScreenScraper">
		<path>./Outro.sh</path>
		<name>Outro port</name>
		<playcount>3</playcount>
	</game>
</gameList>
"""


class TestClassiCubeSync(unittest.TestCase):
    """Roda o classicube-sync com R36_ROOT num diretório temporário."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        share = self.root / "usr" / "share"
        share.mkdir(parents=True)
        os.symlink(SYSTEM_SHARE_DIR, share / "classicube")
        self.scripts = self.root / "storage" / "roms" / "ports_scripts"
        self.port = self.root / "storage" / "roms" / "ports" / "classicube"
        self.gamelist = self.scripts / "gamelist.xml"

    def tearDown(self):
        self._tmp.cleanup()

    def roda(self):
        proc = subprocess.run(
            ["sh", str(SYNC_SCRIPT)], capture_output=True, text=True,
            env={"PATH": os.environ["PATH"], "R36_ROOT": str(self.root)},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")

    def caminhos(self):
        return [g.findtext("path") for g in ET.parse(self.gamelist).getroot().iter("game")]

    def test_cartao_sem_classicube(self):
        self.roda()
        self.assertEqual(self.caminhos(), ["./ClassiCube.sh"])
        for nome in ("ClassiCube.sh", "img/ClassiCube.png", "images/ClassiCube-image.png"):
            self.assertEqual((self.scripts / nome).read_bytes(), (SYSTEM_PORTS_DIR / nome).read_bytes())
        for nome in ("options.txt", "texpacks/default.zip", "audio/default.zip"):
            self.assertTrue((self.port / nome).is_file(), nome)
        self.assertFalse((self.port / "ClassiCube").exists())

    def test_mescla_sem_apagar_outros_ports(self):
        self.scripts.mkdir(parents=True)
        self.gamelist.write_text(GAMELIST_OUTRO, encoding="utf-8")
        self.roda()
        self.assertEqual(self.caminhos(), ["./Outro.sh", "./ClassiCube.sh"])
        outro = ET.parse(self.gamelist).getroot().find("game")
        self.assertEqual(outro.get("id"), "7")
        self.assertEqual(outro.findtext("playcount"), "3")

        # Segunda execução não duplica nem altera o arquivo
        antes = self.gamelist.read_bytes()
        self.roda()
        self.assertEqual(self.gamelist.read_bytes(), antes)
        self.assertFalse((self.scripts / "gamelist.xml.r36tmp").exists())

    def test_preserva_opcoes_do_jogador(self):
        self.port.mkdir(parents=True)
        (self.port / "options.txt").write_text("viewdist = 32\n", encoding="utf-8")
        self.roda()
        self.assertEqual((self.port / "options.txt").read_text(encoding="utf-8"), "viewdist = 32\n")


if __name__ == "__main__":
    unittest.main()
