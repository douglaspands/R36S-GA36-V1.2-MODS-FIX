import os
import subprocess
import tomllib
import unittest

from context import ROOT, TempDirCase
from test_otimizacoes import UnitCase, diretivas

F48 = ROOT / "features" / "48-bateria-percentual"
UNITS = "usr/lib/systemd/system"
LIB = F48 / "system" / "usr" / "lib" / "r36"
SCRIPT = LIB / "bateria-percentual"
CURVA = LIB / "bateria-curva.conf"


def escreve(path, texto):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(texto)


class BateriaCase(TempDirCase):
    def setUp(self):
        super().setUp()
        self.sys = self.tmp / "sys"
        self.proc = self.tmp / "proc"
        self.run_dir = self.tmp / "run"
        self.roms = self.tmp / "roms"
        self.bin = self.tmp / "bin"
        self.chamadas = self.tmp / "chamadas"
        # /sys/class/power_supply/battery é um link para o dispositivo, como no aparelho
        self.real = self.sys / "devices/platform/axp/power_supply/battery"
        escreve(self.real / "type", "Battery\n")
        escreve(self.real / "capacity", "5\n")
        (self.sys / "class/power_supply").mkdir(parents=True)
        (self.sys / "class/power_supply/battery").symlink_to("../../devices/platform/axp/power_supply/battery")
        escreve(self.proc / "uptime", "42.00 100.00\n")
        escreve(self.proc / "mounts", "")
        self.roms.mkdir()
        self.mounted = True
        self.bin.mkdir()
        self.stub("logger", "")
        self.stub("sleep", "")
        self.stub("mountpoint", '[ -z "$R36_TEST_NOMOUNT" ]\n')
        # o mount falso registra a chamada, entra no /proc/mounts e copia o valor para o
        # destino (o efeito visível do bind); R36_TEST_BIND=falha recusa, =inutil não copia
        self.stub("mount", 'echo "mount $*" >> "$R36_TEST_CHAMADAS"\n'
                           '[ "$R36_TEST_BIND" = falha ] && { echo "mount: permissao negada" >&2; exit 1; }\n'
                           'echo "tmpfs $4 none rw 0 0" >> "$R36_PROC/mounts"\n'
                           '[ "$R36_TEST_BIND" = inutil ] || cp "$3" "$4"\n')
        self.stub("umount", 'echo "umount $*" >> "$R36_TEST_CHAMADAS"\n'
                            'grep -vF " $1 " "$R36_PROC/mounts" > "$R36_PROC/mounts.novo"\n'
                            'mv "$R36_PROC/mounts.novo" "$R36_PROC/mounts"\n')
        self.bateria(3800, 550)

    def stub(self, nome, corpo):
        p = self.bin / nome
        p.write_text("#!/bin/sh\n" + corpo)
        p.chmod(0o755)

    def bateria(self, mv, ma=None, status="Discharging", kernel=5):
        linhas = [f"POWER_SUPPLY_NAME=battery", f"POWER_SUPPLY_STATUS={status}",
                  f"POWER_SUPPLY_VOLTAGE_NOW={mv * 1000}", f"POWER_SUPPLY_CAPACITY={kernel}"]
        if ma is not None:
            linhas.append(f"POWER_SUPPLY_CURRENT_NOW={ma * 1000}")
        escreve(self.real / "uevent", "\n".join(linhas) + "\n")

    def env(self, **extra):
        env = dict(
            os.environ,
            PATH=f"{self.bin}:{os.environ['PATH']}",
            R36_SYS=str(self.sys), R36_PROC=str(self.proc), R36_RUN=str(self.run_dir),
            R36_ROMS=str(self.roms), R36_CURVA=str(CURVA), R36_CICLOS="1",
            R36_TEST_CHAMADAS=str(self.chamadas),
        )
        if not self.mounted:
            env["R36_TEST_NOMOUNT"] = "1"
        env.update(extra)
        return env

    def roda(self, *args, **extra):
        return subprocess.run(["sh", str(SCRIPT), *args], env=self.env(**extra), capture_output=True,
                              text=True, timeout=30)

    def once(self, apaga_estado=True):
        if apaga_estado:
            (self.run_dir / "estado").unlink(missing_ok=True)
        r = self.roda("--once")
        self.assertEqual(r.returncode, 0, r.stderr)
        return int(r.stdout)

    def calcula(self, mv, ma=None, **kw):
        self.bateria(mv, ma, **kw)
        return self.once()

    def publicado(self):
        return (self.run_dir / "capacity").read_text().strip()

    def log(self):
        return (self.run_dir / "log").read_text()

    def chamado(self):
        return self.chamadas.read_text().splitlines() if self.chamadas.exists() else []


class Calculo(BateriaCase):
    def test_curva_nunca_diminui_e_fica_entre_0_e_100(self):
        valores = [self.calcula(mv, 0) for mv in range(3500, 4101, 10)]
        self.assertEqual(valores, sorted(valores))
        self.assertTrue(all(0 <= v <= 100 for v in valores))
        self.assertGreater(valores[-1], valores[0])

    def test_mais_corrente_com_a_mesma_tensao_nunca_da_menos(self):
        for mv in (3600, 3800, 4000):
            sem, com, muito = (self.calcula(mv, ma) for ma in (0, 400, 900))
            self.assertLessEqual(sem, com, mv)
            self.assertLessEqual(com, muito, mv)
        self.assertLess(self.calcula(3800, 0), self.calcula(3800, 900))

    def test_fim_da_carga_chega_a_zero(self):
        self.assertEqual(self.calcula(3440, 850), 0)
        self.assertEqual(self.calcula(3450, 850), 0)

    def test_ainda_ha_carga_acima_de_3500(self):
        self.assertGreater(self.calcula(3500, 800), 0)
        self.assertGreater(self.calcula(3500, 0), 0)  # o piso vale também sem corrente

    def test_meio_da_descarga(self):
        self.assertTrue(30 <= self.calcula(3800, 550) <= 60)

    def test_sem_corrente_so_a_tensao(self):
        self.bateria(3800, None)
        sem_arquivo = self.once()
        self.assertEqual(sem_arquivo, self.calcula(3800, 0))
        self.assertLess(sem_arquivo, self.calcula(3800, 800))

    def test_o_valor_vai_para_o_arquivo(self):
        self.bateria(3900, 300)
        v = self.once()
        self.assertEqual(self.publicado(), str(v))

    def test_alivio_de_carga_nao_sobe(self):
        self.bateria(3700, 800)
        antes = self.once(apaga_estado=False)
        self.bateria(3760, 500)  # saiu do jogo: a tensão sobe 60 mV
        depois = self.once(apaga_estado=False)
        self.assertLessEqual(depois, antes)
        self.assertEqual(self.publicado(), str(depois))
        # sem o estado, o mesmo ponto daria um valor maior: é a descida monotônica que segura
        self.assertGreater(self.calcula(3760, 500), antes)

    def test_continua_descendo_com_a_tensao(self):
        valores = []
        for mv in (4000, 3950, 3900, 3850, 3800):
            self.bateria(mv, 300)
            valores.append(self.once(apaga_estado=False))
        self.assertEqual(valores, sorted(valores, reverse=True))
        self.assertLess(valores[-1], valores[0])

    def test_filtro_suaviza_um_afundamento(self):
        self.bateria(4000, 300)
        topo = self.once()
        self.bateria(3800, 300)  # pico de carga de uma amostra
        com_filtro = self.once(apaga_estado=False)
        sem_filtro = self.calcula(3800, 300)
        self.assertGreater(com_filtro, sem_filtro)
        self.assertLessEqual(com_filtro, topo)

    def test_carregando_publica_o_do_kernel_e_a_descarga_recomeca_da_curva(self):
        self.bateria(3600, 300)
        baixo = self.once()
        self.bateria(3900, 900, status="Charging", kernel=63)
        self.assertEqual(self.once(apaga_estado=False), 63)
        self.assertEqual(self.publicado(), "63")
        self.bateria(4150, 300)  # carregador retirado
        volta = self.once(apaga_estado=False)
        self.assertGreater(volta, 90)
        self.assertGreater(volta, baixo)
        self.assertEqual(volta, self.calcula(4150, 300))

    def test_cheio_tambem_segue_o_kernel(self):
        self.bateria(4180, 50, status="Full", kernel=100)
        self.assertEqual(self.once(), 100)

    def test_sem_tensao_publica_o_do_kernel(self):
        escreve(self.real / "uevent", "POWER_SUPPLY_STATUS=Discharging\nPOWER_SUPPLY_CAPACITY=17\n")
        self.assertEqual(self.once(), 17)

    def test_uevent_ausente_le_os_atributos(self):
        (self.real / "uevent").unlink()
        escreve(self.real / "status", "Discharging\n")
        escreve(self.real / "voltage_now", "3800000\n")
        escreve(self.real / "current_now", "550000\n")
        self.assertTrue(30 <= self.once() <= 60)


class CurvaTrocavel(BateriaCase):
    def test_curva_do_system_trocada_por_outro_arquivo(self):
        outra = self.tmp / "outra.conf"
        outra.write_text("r_mohm=0\nponto=3000,10\nponto=5000,90\n")
        self.bateria(4000, 0)
        self.run_dir.mkdir(exist_ok=True)
        r = self.roda("--once", R36_CURVA=str(outra))
        self.assertEqual(r.stdout.strip(), "50")

    def test_curva_do_cartao_valida_troca_a_curva(self):
        (self.roms / "r36-diagnostico").write_text("")
        (self.roms / "r36-bateria-curva.conf").write_text("r_mohm=0\nponto=3000,10\nponto=5000,90\n")
        self.bateria(4000, 800)
        r = self.roda("laco")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.publicado(), "50")
        self.assertIn("curva do cartao", self.log())
        self.assertIn("curva do cartao", (self.roms / "r36-bateria.log").read_text())

    def test_curva_do_cartao_invalida_e_ignorada(self):
        invalidas = {
            "fora de ordem": "ponto=3500,10\nponto=3400,20\n",
            "percentual cai": "ponto=3500,50\nponto=3600,20\n",
            "um ponto": "ponto=3500,10\n",
            "lixo": "ponto=abc\n",
            "acima de 100": "ponto=3500,10\nponto=3600,120\n",
            "chave desconhecida": "ponto=3500,10\nponto=3600,20\nfoo=1\n",
        }
        esperado = self.calcula(3800, 550)
        for nome, texto in invalidas.items():
            with self.subTest(nome):
                (self.run_dir / "log").unlink(missing_ok=True)
                (self.roms / "r36-bateria-curva.conf").write_text(texto)
                r = self.roda("laco")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(self.publicado(), str(esperado))
                self.assertIn("ignorado", self.log())
                self.assertNotIn("curva do cartao", self.log())

    def test_valida_aceita_a_curva_do_system(self):
        r = self.roda("valida", str(CURVA))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(r.stdout.startswith("ok "))

    def test_valida_recusa_curva_ruim(self):
        ruim = self.tmp / "ruim.conf"
        ruim.write_text("ponto=3600,10\nponto=3500,20\n")
        r = self.roda("valida", str(ruim))
        self.assertEqual(r.returncode, 1)
        self.assertIn("fora de ordem", r.stdout)

    def test_pontos_do_system_fixam_o_piso_da_spec(self):
        txt = CURVA.read_text()
        for linha in ("r_mohm=150", "filtro=4", "v_zero=3450", "v_um=3500"):
            self.assertIn(linha, txt.splitlines())
        pontos = [l for l in txt.splitlines() if l.startswith("ponto=")]
        self.assertGreaterEqual(len(pontos), 10)
        self.assertLessEqual(len(pontos), 14)


class Publicacao(BateriaCase):
    def alvo(self):
        return str((self.real / "capacity").resolve())

    def test_bind_com_o_caminho_resolvido(self):
        self.bateria(3900, 300)
        r = self.roda("publica")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.chamado(), [f"mount -o bind {self.run_dir}/capacity {self.alvo()}"])
        self.assertNotIn("class/power_supply", self.chamado()[0])  # não o link
        self.assertIn("bind ok", self.log())
        self.assertEqual((self.real / "capacity").read_text().strip(), self.publicado())
        self.assertNotEqual(self.publicado(), "5")

    def test_readlink_sem_f_resolve_pelo_diretorio(self):
        self.stub("readlink", "exit 1\n")  # busybox sem FEATURE_READLINK_FOLLOW
        self.bateria(3900, 300)
        r = self.roda("publica")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.chamado(), [f"mount -o bind {self.run_dir}/capacity {self.alvo()}"])

    def test_conferencia_que_diverge_desfaz_o_bind(self):
        self.bateria(3900, 300)
        r = self.roda("publica", R36_TEST_BIND="inutil")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([c.split()[0] for c in self.chamado()], ["mount", "umount"])
        self.assertEqual(self.chamado()[1], f"umount {self.alvo()}")
        self.assertIn("bind sem efeito", self.log())
        self.assertIn("lido '5'", self.log())
        self.assertEqual((self.real / "capacity").read_text().strip(), "5")

    def test_mount_recusado_deixa_o_motivo_e_o_boot_segue(self):
        self.bateria(3900, 300)
        r = self.roda("publica", R36_TEST_BIND="falha")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("mount --bind recusado", self.log())
        self.assertIn("permissao negada", self.log())
        self.assertEqual((self.real / "capacity").read_text().strip(), "5")

    def test_segundo_publica_nao_empilha(self):
        self.bateria(3900, 300)
        self.roda("publica")
        self.roda("publica")
        self.assertEqual([c.split()[0] for c in self.chamado()], ["mount", "umount", "mount"])
        self.assertEqual((self.proc / "mounts").read_text().count(self.alvo()), 1)

    def test_desmonta_chama_umount(self):
        self.bateria(3900, 300)
        self.roda("publica")
        r = self.roda("desmonta")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.chamado()[-1], f"umount {self.alvo()}")
        self.assertEqual((self.proc / "mounts").read_text().count(self.alvo()), 0)
        n = len(self.chamado())
        self.roda("desmonta")  # nada montado: não chama umount
        self.assertEqual(len(self.chamado()), n)

    def test_chave_na_p1_desmonta_e_encerra(self):
        (self.roms / "r36-diagnostico").write_text("")
        self.bateria(3900, 300)
        self.roda("publica")
        (self.roms / "r36-bateria-original").write_text("")
        r = self.roda("laco", R36_CICLOS="")  # sem limite de ciclos: só a chave pode encerrar
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.chamado()[-1], f"umount {self.alvo()}")
        self.assertIn("r36-bateria-original", self.log())
        self.assertIn("r36-bateria-original", (self.roms / "r36-bateria.log").read_text())

    def test_chave_ausente_publica(self):
        self.bateria(3900, 300)
        self.roda("publica")
        r = self.roda("laco")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([c.split()[0] for c in self.chamado()], ["mount"])
        self.assertIn("sem r36-bateria-curva.conf", self.log())

    def test_p1_ainda_nao_montada_nao_le_a_chave_nem_grava_o_log(self):
        self.mounted = False
        (self.roms / "r36-bateria-original").write_text("")
        self.bateria(3900, 300)
        self.roda("publica")
        r = self.roda("laco")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([c.split()[0] for c in self.chamado()], ["mount"])
        self.assertFalse((self.roms / "r36-bateria.log").exists())
        self.assertIn("bind ok", self.log())

    def test_log_da_p1_traz_o_bind_e_a_curva_do_boot(self):
        (self.roms / "r36-diagnostico").write_text("")
        self.bateria(3900, 300)
        self.roda("publica")
        self.roda("laco")
        txt = (self.roms / "r36-bateria.log").read_text()
        self.assertIn("curva do system", txt)
        self.assertIn("bind ok", txt)
        self.assertIn("laco iniciado", txt)

    def test_sem_a_chave_de_diagnostico_nao_grava_o_log_na_p1(self):
        self.bateria(3900, 300)
        self.roda("publica")
        r = self.roda("laco")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.roms / "r36-bateria.log").exists())
        self.assertEqual(self.publicado(), str(self.calcula(3900, 300)))
        self.assertIn("bind ok", self.log())

    def test_sem_a_chave_de_diagnostico_o_log_antigo_da_p1_fica(self):
        (self.roms / "r36-bateria.log").write_text("boot antigo\n")
        self.bateria(3900, 300)
        self.roda("publica")
        self.roda("laco")
        self.assertEqual((self.roms / "r36-bateria.log").read_text(), "boot antigo\n")

    def test_sem_a_chave_de_diagnostico_a_chave_original_ainda_vale(self):
        (self.roms / "r36-bateria-original").write_text("")
        self.bateria(3900, 300)
        self.roda("publica")
        r = self.roda("laco", R36_CICLOS="")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.chamado()[-1], f"umount {self.alvo()}")
        self.assertFalse((self.roms / "r36-bateria.log").exists())

    def test_sem_bateria_nao_publica_e_nao_falha(self):
        (self.real / "type").write_text("Mains\n")
        r = self.roda("publica")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.chamado(), [])
        self.assertIn("sem power_supply do tipo Battery", self.log())

    def test_curva_do_system_quebrada_nao_publica(self):
        ruim = self.tmp / "ruim.conf"
        ruim.write_text("ponto=1,1\n")
        r = self.roda("publica", R36_CURVA=str(ruim))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.chamado(), [])
        self.assertIn("curva do system recusada", self.log())

    def test_comando_desconhecido(self):
        r = self.roda("xyz")
        self.assertEqual(r.returncode, 2)


class Feature(UnitCase):
    def test_feature_toml(self):
        t = tomllib.loads((F48 / "feature.toml").read_text())
        self.assertEqual((t["order"], t["enabled"]), (48, True))

    def test_unit(self):
        d = diretivas(F48 / "system" / UNITS / "r36-bateria.service")
        self.assertEqual(d["Type"], ["simple"])
        self.assertEqual(d["ExecStartPre"], ["/usr/lib/r36/bateria-percentual publica"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/bateria-percentual laco"])
        self.assertEqual(d["ExecStopPost"], ["/usr/lib/r36/bateria-percentual desmonta"])
        self.assertEqual(d["Restart"], ["on-failure"])
        self.assertEqual(d["Nice"], ["19"])
        self.assertEqual(d["Before"], ["emustation.service"])
        # esperar o autostart travaria o boot no splash (ele só termina depois do ES)
        self.assertNotIn("After", d)
        self.assertEqual(d["WantedBy"], ["emuelec.target"])

    def test_link(self):
        self.assert_link(F48, "emuelec.target.wants", "r36-bateria.service")

    def test_script(self):
        self.assert_script(SCRIPT)
        subprocess.run(["sh", "-n", str(SCRIPT)], check=True)


if __name__ == "__main__":
    unittest.main()
