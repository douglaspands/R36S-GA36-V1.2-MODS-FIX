import subprocess
import sys
import unittest

from context import ROOT, TempDirCase

import analisa_bateria

SCRIPT = ROOT / "tools" / "analisa_bateria.py"

CABECALHO = "date,uptime_s,boot,bat_status,bat_pct,bat_voltage,bat_current,bat_pct_pub"


def linhas_descarga(boot, n, mv0, mv1, ma=500, kernel=None, pub=None, status="Discharging", up0=10, passo=5):
    """n amostras de um boot em descarga: tensão linear de mv0 a mv1, corrente constante.
    `kernel` e `pub` são funções (i, n) -> percentual, ou None para campo vazio."""
    saida = []
    for i in range(n):
        mv = round(mv0 + (mv1 - mv0) * i / (n - 1))
        k = "" if kernel is None else kernel(i, n)
        p = "" if pub is None else pub(i, n)
        saida.append(f"2026-10-26 10:00:00,{up0 + i * passo},{boot},{status},{k},{mv},{ma},{p}")
    return saida


def csv_descarga(extra=()):
    """Uma descarga de 4100 a 3400 mV em dois boots (200 amostras de 5 s cada, 500 mA). O
    kernel fica em 100 até a amostra 240 de 400 e depois em 5; o publicado acompanha a carga real."""
    a = linhas_descarga("aaaaaaaa", 200, 4100, 3750, kernel=lambda i, n: 100, pub=lambda i, n: round(100 * (1 - i / 399)))
    b = linhas_descarga("bbbbbbbb", 200, 3745, 3400, kernel=lambda i, n: 100 if i < 40 else 5,
                        pub=lambda i, n: round(100 * (1 - (200 + i) / 399)))
    return "\n".join([CABECALHO, *a, *b, *extra]) + "\n"


class Analise(TempDirCase):
    def setUp(self):
        super().setUp()
        self.csv = self.tmp / "r36-thermal.csv"

    def resume(self, texto, desde=None, nome=None):
        caminho = self.tmp / (nome or "r36-thermal.csv")
        caminho.write_text(texto)
        return analisa_bateria.resumo([str(caminho)], desde)

    def test_junta_os_boots_num_ciclo_e_soma_os_mah(self):
        saida, avisos = self.resume(csv_descarga())
        self.assertEqual(avisos, [])
        self.assertEqual(sum(1 for l in saida if l.startswith("ciclo ")), 1)
        self.assertIn("boots aaaaaaaa, bbbbbbbb", saida[0])
        # 2 boots x 199 intervalos de 5 s a 500 mA = 276,4 mAh em 33 min
        self.assertIn("276 mAh", saida[0])
        self.assertIn("33 min", saida[0])
        self.assertIn("4100 mV -> 3400 mV", saida[0])

    def test_integra_em_mah_por_intervalo_de_uptime(self):
        ciclo = [("a", {"uptime_s": str(t), "bat_current": "-1800", "bat_status": "Discharging",
                        "bat_voltage": "3800"}) for t in range(0, 3601, 30)]
        pontos, mah, minutos = analisa_bateria.integra(ciclo)
        self.assertAlmostEqual(mah, 1800.0, places=3)  # 1,8 A durante 1 h (o sinal não importa)
        self.assertAlmostEqual(minutos, 60.0)

    def test_lacuna_e_troca_de_boot_nao_entram_na_integral(self):
        ciclo = [("a", {"uptime_s": "0", "bat_current": "600"}), ("a", {"uptime_s": "10", "bat_current": "600"}),
                 ("a", {"uptime_s": "400", "bat_current": "600"}),   # 390 s sem amostra: lacuna
                 ("b", {"uptime_s": "5", "bat_current": "600"}),     # outro boot: sem intervalo
                 ("b", {"uptime_s": "15", "bat_current": "600"})]
        _, mah, minutos = analisa_bateria.integra(ciclo)
        self.assertAlmostEqual(mah, 600 * 20 / 3600)
        self.assertAlmostEqual(minutos, 20 / 60)

    def test_erro_do_kernel_parado_grande_e_o_do_publicado_pequeno(self):
        saida, _ = self.resume(csv_descarga())
        txt = "\n".join(saida)
        kernel = next(l for l in saida if "kernel (bat_pct)" in l)
        pub = next(l for l in saida if "publicado" in l)
        medio = lambda l: float(l.split("erro médio ")[1].split(" ")[0])
        self.assertGreater(medio(kernel), 15)
        self.assertLess(medio(pub), 1.5)
        self.assertIn("patamar do kernel em 100%", txt)
        self.assertIn("patamar do kernel em 5%", txt)

    def test_patamares_com_minutos_mah_e_tensoes(self):
        saida, _ = self.resume(csv_descarga())
        p100 = next(l for l in saida if "em 100%" in l)
        p5 = next(l for l in saida if "em 5%" in l)
        # 100% nas 200 amostras do primeiro boot e nas 40 primeiras do segundo: 20 min, 165 mAh
        self.assertIn("de 0 a 20 min", p100)
        self.assertIn("de 0 a 165 mAh", p100)
        self.assertIn("entra a 4100 mV", p100)
        self.assertIn("sai a 3677 mV", p100)
        self.assertIn("entra a 3676 mV", p5)
        self.assertIn("sai a 3400 mV", p5)

    def test_ciclo_incompleto_avisa_referencia_relativa(self):
        a = linhas_descarga("aaaaaaaa", 50, 4100, 3900)
        saida, avisos = self.resume("\n".join([CABECALHO, *a]) + "\n")
        self.assertEqual(len(avisos), 1)
        self.assertIn("relativa", avisos[0])
        self.assertTrue(saida[0].startswith("ciclo 1"))

    def test_separa_ciclos_pelo_status_charging(self):
        c1 = linhas_descarga("aaaaaaaa", 30, 4100, 3600)
        carga = linhas_descarga("aaaaaaaa", 5, 3700, 4150, status="Charging", up0=500)
        c2 = linhas_descarga("aaaaaaaa", 30, 4150, 3800, up0=1000)
        saida, _ = self.resume("\n".join([CABECALHO, *c1, *carga, *c2]) + "\n")
        self.assertEqual([l[:8] for l in saida if l.startswith("ciclo ")], ["ciclo 1:", "ciclo 2:"])
        self.assertIn("4150 mV -> 3800 mV", [l for l in saida if l.startswith("ciclo 2")][0])

    def test_separa_ciclos_por_boot_que_comeca_acima_do_fim_do_anterior(self):
        c1 = linhas_descarga("aaaaaaaa", 30, 4100, 3500)
        c2 = linhas_descarga("bbbbbbbb", 30, 4120, 3800)
        saida, _ = self.resume("\n".join([CABECALHO, *c1, *c2]) + "\n")
        self.assertEqual(sum(1 for l in saida if l.startswith("ciclo ")), 2)

    def test_boot_que_continua_a_descarga_fica_no_mesmo_ciclo(self):
        c1 = linhas_descarga("aaaaaaaa", 30, 4100, 3700)
        c2 = linhas_descarga("bbbbbbbb", 30, 3780, 3500)  # sobe 80 mV: ainda é o mesmo ciclo
        saida, _ = self.resume("\n".join([CABECALHO, *c1, *c2]) + "\n")
        self.assertEqual(sum(1 for l in saida if l.startswith("ciclo ")), 1)

    def test_desde_escolhe_o_ciclo_pelo_boot(self):
        c1 = linhas_descarga("aaaaaaaa", 30, 4100, 3500)
        c2 = linhas_descarga("bbbbbbbb", 30, 4120, 3800)
        saida, _ = self.resume("\n".join([CABECALHO, *c1, *c2]) + "\n", desde="bbbb")
        self.assertEqual(sum(1 for l in saida if l.startswith("ciclo ")), 1)
        self.assertIn("boots bbbbbbbb", saida[0])
        saida, _ = self.resume("\n".join([CABECALHO, *c1, *c2]) + "\n", desde="zzzz")
        self.assertIn("nenhum ciclo", saida[0])

    def test_ciclos_pequenos_demais_sao_ignorados(self):
        a = linhas_descarga("aaaaaaaa", 4, 4100, 4090)
        saida, _ = self.resume("\n".join([CABECALHO, *a]) + "\n")
        self.assertIn("nenhum ciclo", saida[0])

    def test_csv_sem_as_colunas_novas_avisa_e_termina(self):
        antigo = "\n".join([
            "date,uptime_s,boot,bat_status,bat_pct,bat_voltage",
            *(f"2026-10-24 09:{m:02d}:00,{m * 60},bbbbbbbb,Discharging,70,{3800 - m}" for m in range(12)),
        ]) + "\n"
        saida, avisos = self.resume(antigo)
        self.assertEqual(len([a for a in avisos if "colunas ausentes" in a]), 1)
        self.assertIn("bat_current", avisos[0])
        self.assertIn("bat_pct_pub", avisos[0])
        self.assertTrue(any("sem corrente" in a for a in avisos))
        self.assertTrue(saida[0].startswith("ciclo 1"))

    def test_dois_arquivos_na_ordem_dos_argumentos(self):
        texto = csv_descarga().splitlines()
        (self.tmp / "r36-thermal.1.csv").write_text("\n".join(texto[:201]) + "\n")
        self.csv.write_text("\n".join([texto[0], *texto[201:]]) + "\n")
        saida, avisos = analisa_bateria.resumo([str(self.tmp / "r36-thermal.1.csv"), str(self.csv)])
        self.assertEqual(sum(1 for l in saida if l.startswith("ciclo ")), 1)
        self.assertIn("boots aaaaaaaa, bbbbbbbb", saida[0])


class Linha(TempDirCase):
    def roda(self, *args):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True, timeout=30)

    def test_sem_argumentos_mostra_o_uso(self):
        r = self.roda()
        self.assertEqual(r.returncode, 2)
        self.assertIn("analisa_bateria.py", r.stderr)

    def test_arquivo_inexistente_e_erro(self):
        r = self.roda(str(self.tmp / "nao-existe.csv"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("erro:", r.stderr)

    def test_imprime_o_ciclo(self):
        (self.tmp / "t.csv").write_text(csv_descarga())
        r = self.roda("--desde", "aaaa", str(self.tmp / "t.csv"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ciclo 1:", r.stdout)
        self.assertIn("publicado (bat_pct_pub): erro médio", r.stdout)


if __name__ == "__main__":
    unittest.main()
