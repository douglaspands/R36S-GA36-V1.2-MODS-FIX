import os
import subprocess
import tomllib

from context import ROOT, TempDirCase
from test_otimizacoes import UnitCase, diretivas

F43 = ROOT / "features" / "43-registro-termico"
UNITS = "usr/lib/systemd/system"
SCRIPT = F43 / "system" / "usr" / "lib" / "r36" / "thermal-log"

STAT_ANTES = (
    "cpu  0 0 0 0 0 0 0 0 0 0\n"
    "cpu0 100 0 100 700 100 0 0 0 0 0\n"
    "cpu1 0 0 0 1000 0 0 0 0 0 0\n"
    "cpu2 50 0 50 800 100 0 0 0 0 0\n"
)
# Intervalo: cpu0 +400 total (300 ocupados), cpu1 +100 (0 ocupados), cpu2 ausente em cur
STAT_DEPOIS = (
    "cpu  0 0 0 0 0 0 0 0 0 0\n"
    "cpu0 300 0 200 800 100 0 0 0 0 0\n"
    "cpu1 0 0 0 1100 0 0 0 0 0 0\n"
)
CMDLINE_JOGO = [
    "/bin/bash", "/usr/bin/emuelecRunEmu.sh", "/storage/roms/gba/Mario, \"Kart\".gba",
    "-Pgba", "--core=mgba", "--emulator=retroarch",
]


def escreve(path, texto):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(texto)


class ThermalLogCase(TempDirCase):
    def setUp(self):
        super().setUp()
        self.proc = self.tmp / "proc"
        self.sys = self.tmp / "sys"
        self.roms = self.tmp / "roms"
        self.bin = self.tmp / "bin"
        self.roms.mkdir()
        self.log = self.roms / "r36-thermal.csv"
        self.log1 = self.roms / "r36-thermal.1.csv"
        self.free_kb = 500000
        self.mounted = True

        escreve(self.proc / "stat", STAT_ANTES)
        escreve(self.proc / "uptime", "1234.56 4000.00\n")
        escreve(self.proc / "sys/kernel/random/boot_id", "abcdef01-2345-6789-abcd-ef0123456789\n")
        z = self.sys / "class/thermal/thermal_zone0"
        escreve(z / "type", "soc thermal\n")
        escreve(z / "temp", "56000\n")
        cpu = self.sys / "devices/system/cpu"
        escreve(cpu / "cpu0/cpufreq/scaling_cur_freq", "1200000\n")
        escreve(cpu / "cpu0/cpufreq/scaling_governor", "performance\n")
        escreve(cpu / "online", "0-3\n")
        escreve(self.sys / "devices/platform/sunxi-ddrfreq/dsm/scene", "0\n")
        bat = self.sys / "class/power_supply"
        escreve(bat / "ac/type", "Mains\n")
        escreve(bat / "battery/type", "Battery\n")
        escreve(bat / "battery/status", "Discharging\n")
        escreve(bat / "battery/capacity", "87\n")

        self.bin.mkdir()
        self.stub("df", 'echo "Filesystem 1K-blocks Used Available Use% Mounted on"\n'
                        'echo "/dev/x 1000000 1 $R36_TEST_FREE_KB 1% /roms"\n')
        self.stub("mountpoint", '[ -z "$R36_TEST_NOMOUNT" ]\n')
        # o sleep falso troca o /proc/stat, para haver variação entre as leituras
        self.stub("sleep", f'[ -f "{self.proc}/stat.next" ] && cp "{self.proc}/stat.next" "{self.proc}/stat"\n')
        escreve(self.proc / "stat.next", STAT_DEPOIS)

    def stub(self, nome, corpo):
        p = self.bin / nome
        p.write_text("#!/bin/sh\n" + corpo)
        p.chmod(0o755)

    def jogo(self, args=CMDLINE_JOGO, pid="777"):
        escreve(self.proc / pid / "cmdline", "\0".join(args) + "\0")

    def run_once(self, **extra):
        env = dict(
            os.environ,
            PATH=f"{self.bin}:{os.environ['PATH']}",
            R36_PROC=str(self.proc), R36_SYS=str(self.sys), R36_ROMS=str(self.roms),
            R36_TEST_FREE_KB=str(self.free_kb),
        )
        if not self.mounted:
            env["R36_TEST_NOMOUNT"] = "1"
        env.update(extra)
        subprocess.run(["sh", str(SCRIPT), "--once"], env=env, check=True, capture_output=True, timeout=30)

    def linhas(self, path=None):
        return (path or self.log).read_text().splitlines()

    def colunas(self):
        cab, linha = self.linhas()[:2]
        return dict(zip(cab.split(","), linha.split(",")))


class Registro(ThermalLogCase):
    def test_cabecalho_e_linha_tem_as_mesmas_colunas(self):
        self.run_once()
        cab, linha = self.linhas()
        self.assertEqual(len(cab.split(",")), len(linha.split(",")))
        self.assertEqual(
            cab,
            "date,uptime_s,boot,temp_soc_thermal,cpu_mhz,governor,cpus_online,"
            "cpu0,cpu1,cpu2,cpu3,dram_scene,bat_status,bat_pct,system,emulator,core,rom",
        )

    def test_campos_basicos(self):
        self.run_once()
        c = self.colunas()
        self.assertEqual(c["uptime_s"], "1234")
        self.assertEqual(c["boot"], "abcdef01")
        self.assertEqual(c["temp_soc_thermal"], "56")  # milésimos viram °C
        self.assertEqual(c["cpu_mhz"], "1200")
        self.assertEqual(c["governor"], "performance")
        self.assertEqual(c["cpus_online"], "0-3")
        self.assertEqual(c["dram_scene"], "0")
        self.assertEqual(c["bat_status"], "Discharging")
        self.assertEqual(c["bat_pct"], "87")

    def test_temperatura_em_graus(self):
        escreve(self.sys / "class/thermal/thermal_zone0/temp", "48\n")
        self.run_once()
        self.assertEqual(self.colunas()["temp_soc_thermal"], "48")

    def test_ocupacao_por_nucleo(self):
        self.run_once()
        c = self.colunas()
        self.assertEqual(c["cpu0"], "75")   # 300 de 400
        self.assertEqual(c["cpu1"], "0")
        self.assertEqual(c["cpu2"], "")     # ausente na segunda leitura
        self.assertEqual(c["cpu3"], "")     # nunca existiu

    def test_jogo_com_virgula_no_nome_da_rom(self):
        self.jogo()
        self.run_once()
        c = self.colunas()
        self.assertEqual((c["system"], c["emulator"], c["core"]), ("gba", "retroarch", "mgba"))
        self.assertEqual(c["rom"], "Mario; ;Kart;.gba")
        cab, linha = self.linhas()
        self.assertEqual(len(cab.split(",")), len(linha.split(",")))

    def test_sem_jogo_campos_vazios(self):
        escreve(self.proc / "42/cmdline", "/usr/bin/emulationstation\0--no-splash\0")
        self.run_once()
        c = self.colunas()
        self.assertEqual([c[k] for k in ("system", "emulator", "core", "rom")], [""] * 4)

    def test_processo_que_so_cita_o_script_nao_conta(self):
        self.jogo(["grep", "emuelecRunEmu.sh", "-Pgba"])
        self.run_once()
        self.assertEqual(self.colunas()["system"], "")

    def test_leituras_que_falham_ficam_vazias(self):
        (self.sys / "class/power_supply/battery/capacity").unlink()
        (self.sys / "devices/platform/sunxi-ddrfreq/dsm/scene").unlink()
        self.run_once()
        cab, linha = self.linhas()
        self.assertEqual(len(cab.split(",")), len(linha.split(",")))
        c = self.colunas()
        self.assertEqual((c["bat_pct"], c["dram_scene"]), ("", ""))

    def test_anexa_sem_repetir_cabecalho(self):
        self.run_once()
        self.run_once()
        linhas = self.linhas()
        self.assertEqual(len(linhas), 3)
        self.assertEqual(sum(1 for x in linhas if x.startswith("date,")), 1)


class Limites(ThermalLogCase):
    def test_rotacao_acima_de_1mb_substitui_o_anterior(self):
        self.run_once()
        cab = self.linhas()[0]
        self.log.write_text(cab + "\n" + "x" * 1048600 + "\n")
        self.log1.write_text("antigo\n")
        self.run_once()
        self.assertIn("x" * 100, self.log1.read_text())
        self.assertNotIn("antigo", self.log1.read_text())
        novo = self.linhas()
        self.assertEqual(novo[0], cab)
        self.assertEqual(len(novo), 2)  # cabeçalho novo e a linha do ciclo
        self.run_once()
        self.assertEqual(len(self.linhas()), 3)

    def test_sem_espaco_livre_nao_grava(self):
        self.free_kb = 65535
        self.run_once()
        self.assertFalse(self.log.exists())

    def test_espaco_liberado_volta_a_gravar(self):
        self.free_kb = 100
        self.run_once()
        self.assertFalse(self.log.exists())
        self.free_kb = 65536
        self.run_once()
        self.assertEqual(len(self.linhas()), 2)

    def test_roms_nao_montada_nao_grava(self):
        self.mounted = False
        self.run_once()
        self.assertFalse(self.log.exists())

    def test_cabecalho_diferente_forca_rotacao(self):
        self.log.write_text("date,coluna_antiga\n1,2\n")
        self.run_once()
        self.assertEqual(self.linhas(self.log1), ["date,coluna_antiga", "1,2"])
        novo = self.linhas()
        self.assertTrue(novo[0].startswith("date,uptime_s,boot"))
        self.assertEqual(len(novo), 2)


class Feature(UnitCase):
    def test_feature_toml(self):
        t = tomllib.loads((F43 / "feature.toml").read_text())
        self.assertEqual((t["order"], t["enabled"]), (43, True))

    def test_unit(self):
        d = diretivas(F43 / "system" / UNITS / "r36-thermal-log.service")
        self.assertEqual(d["Type"], ["simple"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/thermal-log"])
        self.assertEqual(d["Restart"], ["always"])
        self.assertEqual(d["RestartSec"], ["30"])
        self.assertEqual(d["Nice"], ["19"])
        self.assertEqual(d["After"], ["emuelec-autostart.service"])
        self.assertEqual(d["WantedBy"], ["emuelec.target"])

    def test_link(self):
        self.assert_link(F43, "emuelec.target.wants", "r36-thermal-log.service")

    def test_script(self):
        self.assert_script(SCRIPT)
        subprocess.run(["sh", "-n", str(SCRIPT)], check=True)
