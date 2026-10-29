"""Testes do botão FN como hotkey do RetroArch (feature 20-controle-posicional)."""

import os
import stat
import subprocess
import threading
import time
import tomllib
import unittest

from context import ROOT, TempDirCase
from test_audio import escreve
from test_otimizacoes import UnitCase, diretivas

F20 = ROOT / "features" / "20-controle-posicional"
UNITS = "usr/lib/systemd/system"
REMAPEIA = F20 / "system" / "usr" / "lib" / "r36" / "fn-remapeia"
FN_KEY = "sys/devices/platform/micro_gamepad/fn_key"


class FnFeature(UnitCase):
    def test_descritor(self):
        dados = tomllib.loads((F20 / "feature.toml").read_text(encoding="utf-8"))
        self.assertEqual(dados["order"], 20)
        self.assertTrue(dados["enabled"])
        self.assertIn("FN", dados["description"])

    def test_scripts(self):
        self.assert_script(REMAPEIA)
        self.assertEqual(stat.S_IMODE(REMAPEIA.stat().st_mode), 0o755, REMAPEIA)
        proc = subprocess.run(["sh", "-n", str(REMAPEIA)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_unit_do_remapeamento(self):
        unit = F20 / "system" / UNITS / "r36-fn.service"
        d = diretivas(unit)
        self.assertEqual(d["Type"], ["oneshot"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/fn-remapeia"])
        # 60 s do fn_key mais 20 s da p1, com folga
        self.assertEqual(d["TimeoutStartSec"], ["120"])
        self.assertEqual(d["WantedBy"], ["emuelec.target"])
        # esperar o autostart, que espera o ES, trava o boot no splash
        self.assertNotIn("After", d)
        self.assertNotIn("Before", d)
        self.assertNotIn("ConditionPathExists", d)

    def test_fn_reservado_no_emulationstation(self):
        # o FN (botão 10) fica sem função no ES: nenhuma feature o mapeia
        for cfg in (ROOT / "features").rglob("es_input.cfg"):
            texto = cfg.read_text(encoding="utf-8")
            self.assertNotRegex(texto, r'<input[^>]*\bid="10"', cfg)

    def test_links(self):
        self.assert_link(F20, "emuelec.target.wants", "r36-fn.service")


class FnCase(TempDirCase):
    def setUp(self):
        super().setUp()
        self.root = self.tmp / "root"
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        (self.root / "storage/roms").mkdir(parents=True)
        escreve(self.root / FN_KEY, "464\n")

    def roda(self, script, **extra):
        env = dict(
            os.environ,
            PATH=f"{self.bin}:{os.environ['PATH']}",
            R36_ROOT=str(self.root),
            TMPDIR=str(self.tmp),
            R36_FN_DURACAO="2",
            R36_FN_VARREDURA="1",
            R36_FN_ESPERA_FN="3",
        )
        env.update(extra)
        return subprocess.run(["sh", str(script)], env=env, capture_output=True, text=True, timeout=30)

    def fn(self):
        return (self.root / FN_KEY).read_text().strip()


CFG_P8 = "storage/joypads/micro_gamepad.cfg"
CFG_TEXTO = 'input_device = "micro_gamepad"\ninput_select_btn = "8"\ninput_enable_hotkey_btn = "8"\ninput_menu_toggle_btn = "2"\n'


class FnRemapeia(FnCase):
    def cfg(self):
        return (self.root / CFG_P8).read_text()

    def test_escreve_316_por_padrao(self):
        proc = self.roda(REMAPEIA)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.fn(), "316")
        estado = (self.root / "run/r36-fn.estado").read_text()
        self.assertIn("modo=remapeado", estado)
        self.assertIn("antes=464", estado)
        self.assertIn("depois=316", estado)

    def test_chave_deixa_464(self):
        escreve(self.root / "storage/roms/r36-fn-original", "")
        proc = self.roda(REMAPEIA)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.fn(), "464")
        self.assertIn("modo=original", (self.root / "run/r36-fn.estado").read_text())

    def test_sem_p1_escreve_depois_da_espera(self):
        (self.root / "storage/roms").rmdir()
        proc = self.roda(REMAPEIA, R36_FN_ESPERA="1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.fn(), "316")

    def test_sem_fn_key_sai_com_zero_depois_da_espera(self):
        (self.root / FN_KEY).unlink()
        inicio = time.monotonic()
        proc = self.roda(REMAPEIA, R36_FN_ESPERA_FN="2")
        self.assertGreaterEqual(time.monotonic() - inicio, 2)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, "")
        self.assertFalse((self.root / FN_KEY).exists())
        self.assertIn("modo=sem-fn_key", (self.root / "run/r36-fn.estado").read_text())

    def test_fn_key_que_aparece_depois_recebe_316(self):
        (self.root / FN_KEY).unlink()
        destino = self.root / FN_KEY
        threading.Timer(2, lambda: escreve(destino, "464\n")).start()
        proc = self.roda(REMAPEIA, R36_FN_ESPERA_FN="10")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.fn(), "316")
        estado = (self.root / "run/r36-fn.estado").read_text()
        self.assertIn("modo=remapeado", estado)
        self.assertIn("antes=464", estado)

    def test_cfg_da_p8_recebe_10_quando_remapeou(self):
        escreve(self.root / CFG_P8, CFG_TEXTO)
        proc = self.roda(REMAPEIA)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # só a linha do hotkey muda
        self.assertEqual(self.cfg(), CFG_TEXTO.replace('hotkey_btn = "8"', 'hotkey_btn = "10"'))

    def test_cfg_da_p8_fica_com_8_com_a_chave(self):
        escreve(self.root / CFG_P8, CFG_TEXTO.replace('hotkey_btn = "8"', 'hotkey_btn = "10"'))
        escreve(self.root / "storage/roms/r36-fn-original", "")
        self.roda(REMAPEIA)
        self.assertEqual(self.cfg(), CFG_TEXTO)

    def test_cfg_da_p8_fica_com_8_sem_fn_key(self):
        escreve(self.root / CFG_P8, CFG_TEXTO.replace('hotkey_btn = "8"', 'hotkey_btn = "10"'))
        (self.root / FN_KEY).unlink()
        proc = self.roda(REMAPEIA, R36_FN_ESPERA_FN="1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.cfg(), CFG_TEXTO)

    def test_cfg_da_p8_recebe_10_mesmo_com_leitura_diferente_de_316(self):
        # o driver aceita a escrita mas devolve outro número na leitura (como no aparelho)
        escreve(self.bin / "cat", '#!/bin/sh\necho -1088990680\n', 0o755)
        escreve(self.root / CFG_P8, CFG_TEXTO)
        proc = self.roda(REMAPEIA)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("depois=-1088990680", (self.root / "run/r36-fn.estado").read_text())
        self.assertEqual(self.cfg(), CFG_TEXTO.replace('hotkey_btn = "8"', 'hotkey_btn = "10"'))

    def test_cfg_da_p8_fica_com_8_se_a_escrita_falha(self):
        # fn_key que não aceita escrita (aqui, um diretório)
        (self.root / FN_KEY).unlink()
        (self.root / FN_KEY).mkdir()
        escreve(self.root / CFG_P8, CFG_TEXTO.replace('hotkey_btn = "8"', 'hotkey_btn = "10"'))
        proc = self.roda(REMAPEIA)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.cfg(), CFG_TEXTO)

    def test_cfg_ausente_nao_e_criado(self):
        proc = self.roda(REMAPEIA)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.root / CFG_P8).exists())

    def test_uptimes_no_estado(self):
        escreve(self.root / "proc/uptime", "42.50 100.00\n")
        proc = self.roda(REMAPEIA)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        estado = (self.root / "run/r36-fn.estado").read_text()
        for chave in ("uptime_inicio=42", "uptime_fn_key=42", "uptime_fim=42"):
            self.assertIn(chave, estado)


if __name__ == "__main__":
    unittest.main()
