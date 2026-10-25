"""Testes da feature do servidor SSH Dropbear para Allwinner A33 (feature 45-ssh-dropbear)."""

import os
import re
import stat
import subprocess
import tomllib
import unittest

from context import ROOT, needs_base
from r36img import cores as C

FEATURE_DIR = ROOT / "features" / "45-ssh-dropbear"
SYSTEM_DIR = FEATURE_DIR / "system"
SBIN_DIR = SYSTEM_DIR / "usr" / "sbin"
BIN_DIR = SYSTEM_DIR / "usr" / "bin"
LIB_DIR = SYSTEM_DIR / "usr" / "lib"
R36_DIR = LIB_DIR / "r36"
SYSTEMD_DIR = LIB_DIR / "systemd" / "system"
WANTS_DIR = SYSTEMD_DIR / "multi-user.target.wants"

DROPBEAR_BIN = SBIN_DIR / "dropbear"
DROPBEARKEY_BIN = SBIN_DIR / "dropbearkey"
DROPBEARKEY_LINK = BIN_DIR / "dropbearkey"
SETUP_SCRIPT = R36_DIR / "dropbear-setup"
SERVICE_FILE = SYSTEMD_DIR / "dropbear.service"
SERVICE_LINK = WANTS_DIR / "dropbear.service"

RECIPE = ROOT / "services" / "dropbear" / "receita.toml"
BUILD_SCRIPT = ROOT / "services" / "dropbear" / "compilar.sh"


class TestSshDropbear(unittest.TestCase):
    def test_feature_descriptor(self):
        desc = FEATURE_DIR / "feature.toml"
        self.assertTrue(desc.is_file(), "feature.toml ausente")
        dados = tomllib.loads(desc.read_text(encoding="utf-8"))
        self.assertEqual(dados["schema"], 1)
        self.assertEqual(dados["order"], 45)
        self.assertTrue(dados["enabled"])
        self.assertIn("Dropbear", dados["name"])

    def test_recipe_and_build_script(self):
        self.assertTrue(RECIPE.is_file(), "receita.toml ausente")
        rec = tomllib.loads(RECIPE.read_text(encoding="utf-8"))
        self.assertEqual(rec["servico"]["nome"], "dropbear")
        self.assertEqual(rec["servico"]["versao"], "2024.86")
        self.assertEqual(rec["servico"]["saida"], ["dropbear", "dropbearkey"])
        self.assertTrue(BUILD_SCRIPT.is_file(), "compilar.sh ausente")
        proc = subprocess.run(["bash", "-n", str(BUILD_SCRIPT)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Erro de sintaxe no compilar.sh: {proc.stderr}")

    def test_binaries_exist_and_permissions(self):
        for path in (DROPBEAR_BIN, DROPBEARKEY_BIN):
            self.assertTrue(path.is_file(), f"Binário ausente: {path}")
            mode = path.stat().st_mode
            self.assertTrue(bool(mode & stat.S_IXUSR), f"Sem permissão de execução: {path}")
            self.assertGreater(path.stat().st_size, 50 * 1024, f"Binário excessivamente pequeno: {path}")

            texto = subprocess.run(["readelf", "-S", str(path)], capture_output=True, text=True, check=True).stdout
            self.assertFalse(re.search(r"\[\s*\d+\]\s+\.debug_\S+", texto), f"Binário contém seções de depuração: {path}")

        self.assertTrue(DROPBEARKEY_LINK.is_symlink(), "dropbearkey em /usr/bin não é symlink")
        self.assertEqual(os.readlink(DROPBEARKEY_LINK), "../sbin/dropbearkey")

    def test_binaries_architecture_and_abi(self):
        for path in (DROPBEAR_BIN, DROPBEARKEY_BIN):
            texto = subprocess.run(
                ["readelf", "-h", "-A", "-d", "-V", "-W", str(path)],
                capture_output=True, text=True, check=True,
                env={"LC_ALL": "C"}
            ).stdout

            self.assertRegex(texto, r"Class:\s+ELF32\b", f"Não é ELF 32-bit: {path}")
            self.assertRegex(texto, r"Machine:\s+ARM\b", f"Não é arquitetura ARM: {path}")
            self.assertRegex(texto, r"Tag_CPU_arch: v7\b", f"Não é ARMv7-A: {path}")
            self.assertRegex(texto, r"Tag_FP_arch: VFPv4\b", f"Não usa VFPv4: {path}")
            self.assertRegex(texto, r"Tag_ABI_VFP_args: VFP registers\b", f"Não é hard-float: {path}")

            glibc_versoes = re.findall(r"\bGLIBC_(\d+\.\d+)\b", texto)
            self.assertTrue(glibc_versoes, f"Nenhum símbolo GLIBC em {path}")
            for v in glibc_versoes:
                partes = tuple(int(x) for x in v.split("."))
                self.assertLessEqual(partes, (2, 36), f"Símbolo {v} superior a GLIBC_2.36 em {path}")

    @needs_base
    def test_binary_libraries_against_base(self):
        libs = C.libs_base()
        for path in (DROPBEAR_BIN, DROPBEARKEY_BIN):
            texto = subprocess.run(
                ["readelf", "-d", str(path)],
                capture_output=True, text=True, check=True,
                env={"LC_ALL": "C"}
            ).stdout
            needed = re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]", texto)
            for lib in needed:
                self.assertIn(lib, libs, f"Biblioteca {lib} não encontrada no SYSTEM da base")

    def test_systemd_service_and_setup(self):
        self.assertTrue(SETUP_SCRIPT.is_file(), "dropbear-setup ausente")
        mode = SETUP_SCRIPT.stat().st_mode
        self.assertTrue(bool(mode & stat.S_IXUSR), "dropbear-setup sem permissão de execução")
        proc = subprocess.run(["sh", "-n", str(SETUP_SCRIPT)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Sintaxe inválida no dropbear-setup: {proc.stderr}")

        conteudo_setup = SETUP_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("/storage/.cache/ssh", conteudo_setup)
        self.assertIn("dropbear_ed25519_host_key", conteudo_setup)
        self.assertIn("dropbear_rsa_host_key", conteudo_setup)

        self.assertTrue(SERVICE_FILE.is_file(), "dropbear.service ausente")
        conteudo_service = SERVICE_FILE.read_text(encoding="utf-8")
        self.assertIn("ExecStartPre=/usr/lib/r36/dropbear-setup", conteudo_service)
        self.assertIn("ExecStart=/usr/sbin/dropbear", conteudo_service)
        self.assertIn("-p 22", conteudo_service)
        self.assertIn("multi-user.target", conteudo_service)

        self.assertTrue(SERVICE_LINK.is_symlink(), "Symlink dropbear.service em multi-user.target.wants ausente")
        self.assertEqual(os.readlink(SERVICE_LINK), "../dropbear.service")


if __name__ == "__main__":
    unittest.main()
