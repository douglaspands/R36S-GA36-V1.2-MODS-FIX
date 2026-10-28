import subprocess
import sys
import unittest

from context import ROOT, TempDirCase
from test_analisa_bateria import CABECALHO, csv_descarga, linhas_descarga

import ajusta_curva_bateria as aj

SCRIPT = ROOT / "tools" / "ajusta_curva_bateria.py"
BATERIA = ROOT / "features" / "48-bateria-percentual" / "system" / "usr" / "lib" / "r36" / "bateria-percentual"


def le_conf(caminho):
    chaves, pontos = {}, []
    for l in caminho.read_text().splitlines():
        if l.startswith("#") or not l.strip():
            continue
        k, v = l.split("=", 1)
        if k == "ponto":
            mv, pct = v.split(",")
            pontos.append((int(mv), int(pct)))
        else:
            chaves[k] = int(v)
    return chaves, pontos


class Ajuste(TempDirCase):
    def setUp(self):
        super().setUp()
        self.csv = self.tmp / "r36-thermal.csv"
        self.saida = self.tmp / "r36-bateria-curva.conf"

    def roda(self, *args, texto=None):
        self.csv.write_text(csv_descarga() if texto is None else texto)
        return subprocess.run([sys.executable, "-I", str(SCRIPT), "-o", str(self.saida), *args, str(self.csv)],
                              capture_output=True, text=True, timeout=120)

    def test_gera_curva_com_pontos_crescentes_e_o_que_o_aparelho_aceita(self):
        r = self.roda()
        self.assertEqual(r.returncode, 0, r.stderr)
        chaves, pontos = le_conf(self.saida)
        self.assertEqual((chaves["filtro"], chaves["v_zero"], chaves["v_um"]), (4, 3450, 3500))
        self.assertIn("r_mohm", chaves)
        self.assertGreaterEqual(len(pontos), 2)
        self.assertLessEqual(len(pontos), aj.PONTOS)
        mvs, pcts = [p[0] for p in pontos], [p[1] for p in pontos]
        self.assertEqual(mvs, sorted(set(mvs)))
        self.assertEqual(pcts, sorted(pcts))
        self.assertTrue(all(0 <= p <= 100 for p in pcts))
        # a validação do script do aparelho (a mesma que decide se o cartão troca a curva)
        v = subprocess.run(["sh", str(BATERIA), "valida", str(self.saida)], capture_output=True, text=True)
        self.assertEqual(v.returncode, 0, v.stdout)

    def test_curva_nova_tem_erro_pequeno_contra_a_carga_integrada(self):
        r = self.roda()
        self.assertIn("erro médio", r.stdout)
        medio = float(r.stdout.split("erro médio ")[1].split(" ")[0])
        self.assertLess(medio, 1.5)
        self.assertIn("Erro contra a carga integrada", self.saida.read_text())

    def test_a_curva_acompanha_a_descarga(self):
        self.roda()
        _, pontos = le_conf(self.saida)
        self.assertGreaterEqual(pontos[-1][1], 95)   # a tensão cheia dá perto de 100%
        self.assertLessEqual(pontos[0][1], 5)        # a do fim dá perto de 0%

    def test_ciclo_incompleto_exige_a_opcao(self):
        parcial = "\n".join([CABECALHO, *linhas_descarga("aaaaaaaa", 60, 4100, 3800)]) + "\n"
        r = self.roda(texto=parcial)
        self.assertEqual(r.returncode, 1)
        self.assertIn("relativa", r.stderr)
        self.assertIn("--aceita-relativo", r.stderr)
        self.assertFalse(self.saida.exists())
        r = self.roda("--aceita-relativo", texto=parcial)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ciclo incompleto", self.saida.read_text())

    def test_r_fixo(self):
        r = self.roda("--r-mohm", "150")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(le_conf(self.saida)[0]["r_mohm"], 150)

    def test_sem_corrente_nao_ha_o_que_ajustar(self):
        antigo = "\n".join(["date,uptime_s,boot,bat_status,bat_pct,bat_voltage",
                            *(f"x,{i * 5},aaaaaaaa,Discharging,50,{3900 - i}" for i in range(20))]) + "\n"
        r = self.roda(texto=antigo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("nenhum ciclo", r.stderr)
        self.assertFalse(self.saida.exists())

    def test_argumentos_invalidos(self):
        r = self.roda("--filtro", "0")
        self.assertEqual(r.returncode, 2)
        self.assertFalse(self.saida.exists())

    def test_o_ciclo_escolhido_e_o_ultimo(self):
        c1 = linhas_descarga("aaaaaaaa", 30, 4100, 3400)
        c2 = linhas_descarga("bbbbbbbb", 30, 4150, 3420, up0=1000)
        carga = linhas_descarga("aaaaaaaa", 3, 3500, 4100, status="Charging", up0=500)
        r = self.roda(texto="\n".join([CABECALHO, *c1, *carga, *c2]) + "\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("bbbbbbbb", self.saida.read_text())
        self.assertNotIn("aaaaaaaa", self.saida.read_text())
        r = self.roda("--desde", "aaaa", texto="\n".join([CABECALHO, *c1, *carga, *c2]) + "\n")
        self.assertIn("aaaaaaaa", self.saida.read_text())


class Funcoes(unittest.TestCase):
    def test_pav_funde_o_que_decresce(self):
        blocos = aj.pav([(1, 10), (2, 30), (3, 20), (4, 40)])
        ys = [b[1] for b in blocos]
        self.assertEqual(ys, sorted(ys))
        self.assertEqual(blocos[1][1], 25)  # 30 e 20 fundidos
        self.assertEqual(blocos[1][2], 2)

    def test_interpola_corta_nas_pontas(self):
        pts = [(3500, 0), (4000, 100)]
        self.assertEqual(aj.interpola(pts, 3000), 0)
        self.assertEqual(aj.interpola(pts, 4500), 100)
        self.assertEqual(aj.interpola(pts, 3750), 50)

    def test_inteira_descarta_mv_repetido(self):
        self.assertEqual(aj.inteira([(3500.2, 0.4), (3499.8, 5), (3600, 50.6), (3700, 99.9)]),
                         [(3500, 0), (3600, 51), (3700, 100)])


if __name__ == "__main__":
    unittest.main()
