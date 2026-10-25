"""Testes do port nativo ClassiCube para Allwinner A33 (feature 60-port-classicube)."""

import re
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
            ["readelf", "-h", "-A", "-d", "-V", "-W", str(BINARY)],
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
        self.assertIn("/storage/roms/ports/classicube", conteudo)
        self.assertIn("/tmp/classicube", conteudo)

    def test_options_preset(self):
        self.assertTrue(OPTIONS.is_file(), "options.txt ausente")
        txt = OPTIONS.read_text(encoding="utf-8")
        self.assertIn("window-width = 640", txt)
        self.assertIn("window-height = 480", txt)
        self.assertIn("fpslimit = Limit60FPS", txt)
        self.assertIn("defaulttexpack = default.zip", txt)

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
        self.assertIn("<name>ClassiCube</name>", txt)
        self.assertIn("<image>./img/ClassiCube.png</image>", txt)

        img = SCRIPTS_DIR / "img" / "ClassiCube.png"
        self.assertTrue(img.is_file(), "img/ClassiCube.png ausente")
        self.assertGreater(img.stat().st_size, 1024, "ClassiCube.png vazio ou muito pequeno")

        img_alt = SCRIPTS_DIR / "images" / "ClassiCube-image.png"
        self.assertTrue(img_alt.is_file(), "images/ClassiCube-image.png ausente")


if __name__ == "__main__":
    unittest.main()
