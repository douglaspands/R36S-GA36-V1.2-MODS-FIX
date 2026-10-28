import os
import re
import shutil
import subprocess
import tomllib
import unittest

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
        escreve(cpu / "cpu0/cpufreq/scaling_max_freq", "1104000\n")
        escreve(cpu / "cpu0/cpufreq/scaling_available_governors", "ondemand performance\n")
        escreve(cpu / "cpufreq/ondemand/up_threshold", "30\n")
        escreve(cpu / "online", "0-3\n")
        escreve(self.sys / "devices/platform/sunxi-ddrfreq/dsm/scene", "0\n")
        bat = self.sys / "class/power_supply"
        escreve(bat / "ac/type", "Mains\n")
        escreve(bat / "battery/type", "Battery\n")
        escreve(bat / "battery/status", "Discharging\n")
        escreve(bat / "battery/capacity", "87\n")
        escreve(bat / "battery/voltage_now", "3950000\n")
        escreve(bat / "battery/current_now", "-450000\n")
        escreve(bat / "battery/uevent", "POWER_SUPPLY_NAME=battery\nPOWER_SUPPLY_CAPACITY=87\n")
        escreve(self.sys / "devices/virtual/disp/disp/attr/lcdbl", "128\n")
        escreve(z / "trip_point_0_temp", "90000\n")
        escreve(self.sys / "class/thermal/cooling_device0/type", "thermal-cpufreq-0\n")
        escreve(self.sys / "class/thermal/cooling_device0/cur_state", "2\n")
        escreve(self.sys / "class/thermal/cooling_device0/max_state", "4\n")
        self.sysinfo = self.roms / "r36-sysinfo.txt"

        self.bin.mkdir()
        self.stub("df", 'echo "Filesystem 1K-blocks Used Available Use% Mounted on"\n'
                        'echo "/dev/x 1000000 1 $R36_TEST_FREE_KB 1% /roms"\n')
        self.stub("mountpoint", '[ -z "$R36_TEST_NOMOUNT" ]\n')
        self.stub("dmesg", "")  # sem linhas axp, a menos que o teste troque o stub
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
            "date,uptime_s,boot,temp_soc_thermal,cpu_mhz,cpu_max_mhz,governor,cpus_online,"
            "cpu0,cpu1,cpu2,cpu3,dram_scene,dram_mhz,bat_status,bat_pct,bat_voltage,"
            "bat_current,bat_pct_pub,lcdbl,"
            "system,emulator,core,rom",
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
        self.assertEqual(c["cpu_max_mhz"], "1104")
        self.assertEqual(c["bat_voltage"], "3950")  # µV viram mV
        self.assertEqual(c["dram_mhz"], "")  # sem devfreq na árvore falsa

    def test_corrente_e_brilho(self):
        self.run_once()
        cab, linha = self.linhas()
        self.assertEqual(len(cab.split(",")), len(linha.split(",")))
        c = self.colunas()
        self.assertEqual(c["bat_current"], "-450")  # µA com sinal viram mA
        self.assertEqual(c["lcdbl"], "128")
        for removida in ("bat_charge_now", "bat_charge_full", "bat_pct_est"):
            self.assertNotIn(removida, c)

    def test_percentual_do_kernel_e_o_publicado(self):
        # o capacity está sobreposto pelo valor publicado; o uevent mostra o do kernel
        bat = self.sys / "class/power_supply/battery"
        for kernel, pub in (("5", "41"), ("100", "73")):
            escreve(bat / "uevent", f"POWER_SUPPLY_NAME=battery\nPOWER_SUPPLY_CAPACITY={kernel}\n")
            escreve(bat / "capacity", pub + "\n")
            self.log.unlink(missing_ok=True)
            self.run_once()
            c = self.colunas()
            self.assertEqual((c["bat_pct"], c["bat_pct_pub"]), (kernel, pub))

    def test_sem_uevent_o_percentual_do_kernel_fica_vazio(self):
        (self.sys / "class/power_supply/battery/uevent").unlink()
        self.run_once()
        c = self.colunas()
        self.assertEqual((c["bat_pct"], c["bat_pct_pub"]), ("", "87"))

    def test_corrente_positiva(self):
        escreve(self.sys / "class/power_supply/battery/current_now", "300000\n")
        self.run_once()
        self.assertEqual(self.colunas()["bat_current"], "300")

    def test_corrente_e_brilho_ilegiveis_ficam_vazios(self):
        (self.sys / "class/power_supply/battery/current_now").unlink()
        (self.sys / "devices/virtual/disp/disp/attr/lcdbl").unlink()
        self.run_once()
        cab, linha = self.linhas()
        self.assertEqual(len(cab.split(",")), len(linha.split(",")))
        c = self.colunas()
        self.assertEqual((c["bat_current"], c["lcdbl"]), ("", ""))
        self.assertEqual(c["bat_voltage"], "3950")
        self.assertEqual(c["bat_pct"], "87")

    def test_corrente_invalida_fica_vazia(self):
        escreve(self.sys / "class/power_supply/battery/current_now", "abc\n")
        self.run_once()
        self.assertEqual(self.colunas()["bat_current"], "")

    def test_dram_mhz_em_hz_e_em_khz(self):
        d = self.sys / "devices/platform/sunxi-ddrfreq/devfreq/sunxi-ddrfreq"
        (self.sys / "devices/platform/sunxi-ddrfreq/dsm/scene").unlink()
        escreve(d / "dsm/scene", "0\n")
        for bruto in ("360000000", "360000"):
            escreve(d / "cur_freq", bruto + "\n")
            self.log.unlink(missing_ok=True)
            self.run_once()
            self.assertEqual(self.colunas()["dram_mhz"], "360", bruto)

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

    def test_dram_no_caminho_com_devfreq(self):
        # onde o maxperf/normperf escrevem de fato
        (self.sys / "devices/platform/sunxi-ddrfreq/dsm/scene").unlink()
        escreve(self.sys / "devices/platform/sunxi-ddrfreq/devfreq/sunxi-ddrfreq/dsm/scene", "1\n")
        self.run_once()
        self.assertEqual(self.colunas()["dram_scene"], "1")

    def test_cpu_busy_sem_chamada_de_funcao_falsa(self):
        # o awk do busybox 1.32.1 lê "out (...)" como chamada da função out
        corpo = SCRIPT.read_text().split("cpu_busy() {")[1].split("\n}\n")[0]
        self.assertIsNone(re.search(r"\b(out|sep|v|dt|di) \(", corpo))

    @unittest.skipUnless(shutil.which("busybox"), "sem busybox no PATH")
    def test_cpu_busy_com_busybox_awk(self):
        bb = self.tmp / "bbbin"
        bb.mkdir()
        (bb / "awk").symlink_to(shutil.which("busybox"))
        self.run_once(PATH=f"{bb}:{self.bin}:{os.environ['PATH']}")
        self.assertEqual(self.colunas()["cpu0"], "75")

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
        (self.sys / "class/power_supply/battery/uevent").unlink()
        (self.sys / "class/power_supply/battery/voltage_now").unlink()
        (self.sys / "devices/system/cpu/cpu0/cpufreq/scaling_max_freq").unlink()
        (self.sys / "devices/platform/sunxi-ddrfreq/dsm/scene").unlink()
        self.run_once()
        cab, linha = self.linhas()
        self.assertEqual(len(cab.split(",")), len(linha.split(",")))
        c = self.colunas()
        self.assertEqual((c["bat_pct"], c["dram_scene"], c["bat_voltage"], c["cpu_max_mhz"]), ("", "", "", ""))

    def test_anexa_sem_repetir_cabecalho(self):
        self.run_once()
        self.run_once()
        linhas = self.linhas()
        self.assertEqual(len(linhas), 3)
        self.assertEqual(sum(1 for x in linhas if x.startswith("date,")), 1)


class SemEfeitos(ThermalLogCase):
    def test_sem_bateria_as_colunas_ficam_vazias(self):
        (self.sys / "class/power_supply/battery/type").unlink()
        self.run_once()
        c = self.colunas()
        self.assertEqual((c["bat_voltage"], c["bat_pct"], c["bat_pct_pub"]), ("", "", ""))

    def test_nao_publica_nada_alem_do_csv_e_do_retrato(self):
        antes = {p for p in self.sys.rglob("*")}
        self.run_once()
        self.assertEqual({p.name for p in self.roms.iterdir()}, {"r36-thermal.csv", "r36-sysinfo.txt"})
        self.assertEqual({p for p in self.sys.rglob("*")}, antes)


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


class Retrato(ThermalLogCase):
    def test_retrato_com_valores_e_caminhos(self):
        self.run_once()
        txt = self.sysinfo.read_text()
        self.assertEqual(txt.splitlines()[0], "boot_id: abcdef01-2345-6789-abcd-ef0123456789")
        cpu = self.sys / "devices/system/cpu"
        self.assertIn(f"{cpu}/cpu0/cpufreq/scaling_available_governors: ondemand performance", txt)
        self.assertIn(f"{cpu}/cpu0/cpufreq/scaling_max_freq: 1104000", txt)
        self.assertIn(f"{cpu}/cpufreq/ondemand/up_threshold: 30", txt)
        self.assertIn(f"{self.sys}/class/thermal/thermal_zone0/trip_point_0_temp: 90000", txt)
        self.assertIn(f"{self.sys}/class/thermal/cooling_device0/cur_state: 2", txt)
        self.assertIn(f"{self.sys}/class/power_supply/battery/voltage_now: 3950000", txt)
        self.assertFalse((self.roms / "r36-sysinfo.txt.tmp").exists())

    def test_secao_da_bateria_com_uevent_e_dmesg(self):
        ps = self.sys / "class/power_supply"
        escreve(ps / "battery/uevent", "POWER_SUPPLY_NAME=battery\nPOWER_SUPPLY_CAPACITY=87\n")
        escreve(ps / "ac/uevent", "POWER_SUPPLY_NAME=ac\nPOWER_SUPPLY_ONLINE=0\n")
        escreve(ps / "battery/charge_full_design", "2200000\n")
        escreve(ps / "battery/capacity_level", "Normal\n")
        linhas = [f"[    {i}.000] axp22: linha {i}" for i in range(100)]
        linhas.insert(10, "[    1.000] mmc0: outra coisa")
        self.stub("dmesg", "cat <<'EOT'\n" + "\n".join(linhas) + "\nEOT\n")
        self.run_once()
        txt = self.sysinfo.read_text()
        sec = txt.split("== bateria ==\n")[1]
        self.assertIn(f"{ps}/battery/uevent: POWER_SUPPLY_NAME=battery", sec)
        self.assertIn(f"{ps}/battery/uevent: POWER_SUPPLY_CAPACITY=87", sec)
        self.assertIn(f"{ps}/ac/uevent: POWER_SUPPLY_ONLINE=0", sec)
        for n, v in (("status", "Discharging"), ("capacity", "87"), ("voltage_now", "3950000"),
                     ("current_now", "-450000"), ("charge_full_design", "2200000"), ("capacity_level", "Normal")):
            self.assertIn(f"{ps}/battery/{n}: {v}", sec)
        dm = [l for l in sec.splitlines() if l.startswith("dmesg: ")]
        self.assertEqual(len(dm), 80)
        self.assertTrue(all("axp" in l for l in dm))
        self.assertEqual(dm[-1], "dmesg: [    99.000] axp22: linha 99")
        self.assertNotIn("outra coisa", txt)

    def test_atributos_do_axppower_no_retrato(self):
        ax = self.sys / "class/axppower"
        escreve(ax / "axpdebug", "reg 0x01 = 0x40\n")
        escreve(ax / "ocv", "4012\n")
        (ax / "sub").mkdir()
        self.run_once()
        sec = self.sysinfo.read_text().split("== bateria ==\n")[1]
        self.assertIn(f"{ax}/axpdebug: reg 0x01 = 0x40", sec)
        self.assertIn(f"{ax}/ocv: 4012", sec)
        self.assertNotIn(f"{ax}/sub", sec)

    def test_axppower_ausente_marcado_e_demais_seguem(self):
        self.run_once()
        sec = self.sysinfo.read_text().split("== bateria ==\n")[1]
        self.assertIn(f"{self.sys}/class/axppower: (ausente)", sec)
        self.assertIn("dmesg (axp): (ausente)", sec)
        self.assertEqual(len(self.linhas()), 2)

    def test_secao_da_bateria_ausente_nao_trava(self):
        (self.sys / "class/power_supply/battery/type").unlink()
        (self.sys / "class/power_supply/battery/uevent").unlink()
        self.run_once()  # check=True: termina com sucesso
        sec = self.sysinfo.read_text().split("== bateria ==\n")[1]
        self.assertIn(f"{self.sys}/class/power_supply/<Battery>: (ausente)", sec)
        self.assertIn("dmesg (axp): (ausente)", sec)
        self.assertIn(f"{self.sys}/class/power_supply/*/uevent: (ausente)", sec)
        self.assertEqual(len(self.linhas()), 2)

    def test_item_ausente_marcado_e_demais_seguem(self):
        self.run_once()
        txt = self.sysinfo.read_text()
        cpu = self.sys / "devices/system/cpu"
        self.assertIn(f"{cpu}/cpu0/cpufreq/scaling_available_frequencies: (ausente)", txt)
        self.assertIn(f"{cpu}/cpu0/cpufreq/scaling_governor: performance", txt)
        self.assertEqual(len(self.linhas()), 2)  # a linha do CSV também sai

    def test_dram_com_devfreq_no_retrato(self):
        d = self.sys / "devices/platform/sunxi-ddrfreq/devfreq/sunxi-ddrfreq"
        (self.sys / "devices/platform/sunxi-ddrfreq/dsm/scene").unlink()
        escreve(d / "dsm/scene", "1\n")
        escreve(d / "cur_freq", "360000\n")
        escreve(d / "available_frequencies", "168000 360000\n")
        self.run_once()
        txt = self.sysinfo.read_text()
        self.assertIn(f"{d}/cur_freq: 360000", txt)
        self.assertIn(f"{d}/available_frequencies: 168000 360000", txt)
        self.assertIn(f"{d}/dsm/scene: 1", txt)

    def test_nao_grava_sem_roms_montadas_ou_sem_espaco(self):
        self.mounted = False
        self.run_once()
        self.assertFalse(self.sysinfo.exists())
        self.mounted = True
        self.free_kb = 100
        self.run_once()
        self.assertFalse(self.sysinfo.exists())
        self.assertFalse(self.log.exists())

    def test_nao_regrava_no_mesmo_boot(self):
        self.run_once()
        self.sysinfo.write_text(self.sysinfo.read_text() + "marca\n")
        self.run_once()
        self.assertIn("marca", self.sysinfo.read_text())
        self.assertEqual(len(self.linhas()), 3)

    def test_novo_boot_substitui(self):
        self.run_once()
        escreve(self.proc / "sys/kernel/random/boot_id", "99999999-0000-0000-0000-000000000000\n")
        self.run_once()
        self.assertEqual(self.sysinfo.read_text().splitlines()[0], "boot_id: 99999999-0000-0000-0000-000000000000")


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
        self.assertEqual(d["After"], ["emuelec-autostart.service r36-cpu-ondemand.service"])
        self.assertNotIn("Requires", d)
        self.assertNotIn("Wants", d)
        self.assertEqual(d["WantedBy"], ["emuelec.target"])

    def test_link(self):
        self.assert_link(F43, "emuelec.target.wants", "r36-thermal-log.service")

    def test_script(self):
        self.assert_script(SCRIPT)
        subprocess.run(["sh", "-n", str(SCRIPT)], check=True)
