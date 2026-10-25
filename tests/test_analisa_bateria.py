import contextlib
import io
import subprocess
import sys
import unittest

from context import ROOT, TempDirCase

import analisa_bateria

SCRIPT = ROOT / "tools" / "analisa_bateria.py"

CAB_NOVO = "date,uptime_s,boot,bat_status,bat_pct,bat_voltage,bat_current,bat_charge_now,bat_charge_full,bat_pct_est"
# Descarga de 1 h: kernel 90 -> 80 (10 pontos/h), estimado 80 -> 76 (4 pontos/h); a linha em
# Charging no fim (100%, sem estimativa) não conta para a queda.
CSV_NOVO = "\n".join([
    CAB_NOVO,
    *(f"2026-10-25 10:{m:02d}:00,{m * 60},aaaaaaaa,Discharging,90,3900,-450,1200,2000,80" for m in (0, 10, 20, 30, 40)),
    "2026-10-25 10:50:00,3000,aaaaaaaa,Discharging,85,3850,-450,1100,2000,78",
    "2026-10-25 11:00:00,3600,aaaaaaaa,Discharging,80,3800,-450,1000,2000,76",
    "2026-10-25 11:10:00,4200,aaaaaaaa,Charging,100,4150,900,2000,2000,",
]) + "\n"

CSV_ANTIGO = "\n".join([
    "date,uptime_s,boot,bat_status,bat_pct,bat_voltage",
    "2026-10-24 09:00:00,0,bbbbbbbb,Discharging,70,3800",
    "2026-10-24 09:30:00,1800,bbbbbbbb,Discharging,69,3790",
    "2026-10-24 10:00:00,3600,bbbbbbbb,Discharging,68,3780",
]) + "\n"


class Analise(TempDirCase):
    def setUp(self):
        super().setUp()
        self.novo = self.tmp / "novo.csv"
        self.antigo = self.tmp / "antigo.csv"
        self.novo.write_text(CSV_NOVO)
        self.antigo.write_text(CSV_ANTIGO)

    def test_diferenca_inicial_e_taxas_por_hora(self):
        saida, avisos = analisa_bateria.resumo([str(self.novo)])
        self.assertEqual(avisos, [])
        txt = "\n".join(saida)
        self.assertIn("boot aaaaaaaa: 8 amostras, 7 em descarga", txt)
        self.assertIn("tensão 3900.0 mV, kernel 90.0%, estimado 80.0%, diferença kernel - estimado 10.0 pontos", txt)
        self.assertIn("descarga: kernel 10.0 pontos/h, estimado 4.0 pontos/h", txt)

    def test_csv_antigo_avisa_as_colunas_e_segue(self):
        saida, avisos = analisa_bateria.resumo([str(self.antigo)])
        self.assertEqual(len(avisos), 1)
        for col in ("bat_current", "bat_charge_now", "bat_charge_full", "bat_pct_est"):
            self.assertIn(col, avisos[0])
        txt = "\n".join(saida)
        self.assertIn("kernel 69.0%, estimado n/d, diferença kernel - estimado n/d", txt)
        self.assertIn("descarga: kernel 2.0 pontos/h, estimado n/d", txt)

    def test_dois_boots_em_arquivos_diferentes(self):
        saida, avisos = analisa_bateria.resumo([str(self.antigo), str(self.novo)])
        self.assertEqual(len(avisos), 1)
        self.assertEqual([l for l in saida if l.startswith("boot ")],
                         ["boot bbbbbbbb: 3 amostras, 3 em descarga", "boot aaaaaaaa: 8 amostras, 7 em descarga"])

    def test_script_termina_com_sucesso_e_avisa_no_stderr(self):
        r = subprocess.run([sys.executable, "-I", str(SCRIPT), str(self.antigo), str(self.novo)],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("boot aaaaaaaa", r.stdout)
        self.assertIn("aviso:", r.stderr)
        self.assertIn("bat_pct_est", r.stderr)

    def test_sem_argumentos_mostra_o_uso(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(analisa_bateria.main([]), 2)
        self.assertIn("uv run python -I tools/analisa_bateria.py", err.getvalue())


if __name__ == "__main__":
    unittest.main()
