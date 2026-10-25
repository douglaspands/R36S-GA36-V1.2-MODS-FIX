"""Testes do port nativo ClassiCube para Allwinner A33 (feature 60-port-classicube)."""

import os
import re
import stat
import subprocess
import tomllib
import unittest
import zipfile

from context import ROOT, needs_base
from r36img import cores as C

FEATURE_DIR = ROOT / "features" / "60-port-classicube"
ROMS_DIR = FEATURE_DIR / "roms"
PORT_DIR = ROMS_DIR / "ports" / "classicube"
SCRIPTS_DIR = ROMS_DIR / "ports_scripts"
BINARY = PORT_DIR / "ClassiCube"
LAUNCHER = SCRIPTS_DIR / "ClassiCube.sh"
OPTIONS = PORT_DIR / "options.txt"
TEXPACK = PORT_DIR / "texpacks" / "default.zip"
AUDIO_ZIP = PORT_DIR / "audio" / "default.zip"
RECIPE = ROOT / "ports" / "classicube" / "receita.toml"
BUILD_SCRIPT = ROOT / "ports" / "classicube" / "compilar.sh"

SYSTEM_DIR = FEATURE_DIR / "system"
SYSTEM_PORTS_DIR = SYSTEM_DIR / "usr" / "bin" / "ports"
SYSTEM_SHARE_DIR = SYSTEM_DIR / "usr" / "share" / "classicube"
SYSTEM_BINARY = SYSTEM_SHARE_DIR / "ClassiCube"
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

        # Cópia em system/usr/share/classicube/ClassiCube deve ser idêntica
        self.assertTrue(SYSTEM_BINARY.is_file(), "ClassiCube ausente em system/usr/share/classicube/")
        self.assertEqual(BINARY.read_bytes(), SYSTEM_BINARY.read_bytes(), "Binários ROMS e SYSTEM diferem")

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
        self.assertIn("/tmp/classicube", conteudo)
        self.assertIn("--singleplayer", conteudo)
        self.assertNotIn('"$@"', conteudo)

    def test_options_preset(self):
        self.assertTrue(OPTIONS.is_file(), "options.txt ausente")
        txt = OPTIONS.read_text(encoding="utf-8")
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
            self.assertTrue(sys_file.is_file(), f"{nome} ausente em system/usr/bin/ports/")
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
        self.assertIn("/usr/bin/ports", conteudo_sync)
        self.assertIn("/usr/share/classicube", conteudo_sync)
        self.assertIn("/storage/.config/emuelec/ports", conteudo_sync)

        self.assertTrue(SERVICE_FILE.is_file(), "r36-classicube-sync.service ausente")
        conteudo_service = SERVICE_FILE.read_text(encoding="utf-8")
        self.assertIn("ExecStart=/usr/lib/r36/classicube-sync", conteudo_service)
        self.assertIn("After=emuelec-autostart.service", conteudo_service)
        self.assertIn("Before=emustation.service", conteudo_service)
        self.assertIn("WantedBy=emuelec.target", conteudo_service)

        self.assertTrue(SERVICE_WANTS_LINK.is_symlink(), "Symlink r36-classicube-sync.service em emuelec.target.wants ausente")
        self.assertEqual(os.readlink(SERVICE_WANTS_LINK), "../r36-classicube-sync.service")


if __name__ == "__main__":
    unittest.main()
