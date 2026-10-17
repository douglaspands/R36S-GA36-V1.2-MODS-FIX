import os
import re
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

from context import ROOT, TempDirCase

F44 = ROOT / "features" / "44-cpu-ondemand"
TUNE = F44 / "system" / "usr" / "lib" / "r36" / "cpu-ondemand-tune"
CPUFREQ = F44 / "system" / "usr" / "bin" / "cpufreq"
RUNEMU = ROOT / "features" / "10-ptbr-sao-paulo" / "system" / "usr" / "bin" / "emuelecRunEmu.sh"
CHAMADA = "if [ -x /usr/lib/r36/cpu-ondemand-tune ]; then /usr/lib/r36/cpu-ondemand-tune; fi"
CHAMADA_JOGO = "if [ -x /usr/lib/r36/cpu-ondemand-tune ]; then /usr/lib/r36/cpu-ondemand-tune jogo; fi"


class Feature(TempDirCase):
    def test_toml(self):
        t = tomllib.loads((F44 / "feature.toml").read_text())
        self.assertEqual((t["order"], t["enabled"]), (44, True))

    def test_scripts_executaveis_e_validos(self):
        for p in (TUNE, CPUFREQ):
            self.assertTrue(os.access(p, os.X_OK), p)
            subprocess.run(["sh", "-n", str(p)], check=True)


class Sysfs(TempDirCase):
    """Árvore sysfs falsa: 2 CPUs, tunable global e por policy."""

    def monta(self, gov, global_=True, policy=True):
        sys_ = self.tmp / "cpu"
        for n in (0, 1):
            d = sys_ / f"cpu{n}" / "cpufreq"
            d.mkdir(parents=True)
            (d / "scaling_governor").write_text(gov + "\n")
            (d / "scaling_min_freq").write_text("240000\n")
        base = sys_ / "cpufreq"
        alvos = []
        if global_:
            alvos.append(base / "ondemand")
        if policy:
            alvos.append(base / "policy0")
        for a in alvos:
            a.mkdir(parents=True)
            (a / "up_threshold").write_text("80\n")
            (a / "sampling_down_factor").write_text("1\n")
        return sys_, alvos

    def roda(self, script, sys_, *args, cena=None):
        env = dict(os.environ, R36_CPU_SYS=str(sys_))
        if cena is not None:
            env["R36_DRAM_SCENE"] = str(cena)
        subprocess.run(["sh", str(script), *args], check=True, env=env, capture_output=True)

    def le(self, p):
        return p.read_text().strip()


class Tune(Sysfs):
    def test_ondemand_aplica_valores(self):
        sys_, alvos = self.monta("ondemand")
        self.roda(TUNE, sys_)
        for a in alvos:
            self.assertEqual(self.le(a / "up_threshold"), "30")
            self.assertEqual(self.le(a / "sampling_down_factor"), "10")
        for n in (0, 1):
            self.assertEqual(self.le(sys_ / f"cpu{n}" / "cpufreq" / "scaling_min_freq"), "600000")

    def test_governor_performance_nao_toca_em_nada(self):
        sys_, alvos = self.monta("performance")
        self.roda(TUNE, sys_)
        for a in alvos:
            self.assertEqual(self.le(a / "up_threshold"), "80")
            self.assertEqual(self.le(a / "sampling_down_factor"), "1")
        self.assertEqual(self.le(sys_ / "cpu0" / "cpufreq" / "scaling_min_freq"), "240000")
        self.assertEqual(self.le(sys_ / "cpu0" / "cpufreq" / "scaling_governor"), "performance")

    def test_arquivo_ausente_e_ignorado(self):
        sys_, _ = self.monta("ondemand", global_=False, policy=False)
        self.roda(TUNE, sys_)  # check=True: não pode falhar
        self.assertEqual(self.le(sys_ / "cpu1" / "cpufreq" / "scaling_min_freq"), "600000")
        self.assertFalse((sys_ / "cpufreq" / "ondemand").exists())

    def test_so_global_ou_so_policy(self):
        for g, p in ((True, False), (False, True)):
            sys_, alvos = self.monta("ondemand", g, p)
            self.roda(TUNE, sys_)
            self.assertEqual(self.le(alvos[0] / "up_threshold"), "30")
            shutil.rmtree(sys_)


class Dram(Sysfs):
    def cena(self, valor="1\n"):
        c = self.tmp / "scene"
        c.write_text(valor)
        return c

    def test_jogo_com_ondemand_grava_cena_0(self):
        sys_, _ = self.monta("ondemand")
        c = self.cena()
        self.roda(TUNE, sys_, "jogo", cena=c)
        self.assertEqual(self.le(c), "0")

    def test_sem_argumento_nao_toca_na_cena(self):
        sys_, _ = self.monta("ondemand")
        c = self.cena()
        self.roda(TUNE, sys_, cena=c)
        self.assertEqual(self.le(c), "1")

    def test_jogo_com_performance_nao_toca_na_cena(self):
        sys_, _ = self.monta("performance")
        c = self.cena()
        self.roda(TUNE, sys_, "jogo", cena=c)
        self.assertEqual(self.le(c), "1")

    def test_cena_ausente_sai_com_0(self):
        sys_, _ = self.monta("ondemand")
        c = self.tmp / "nao-existe"
        self.roda(TUNE, sys_, "jogo", cena=c)  # check=True
        self.assertFalse(c.exists())


class Cpufreq(Sysfs):
    """O cpufreq substituído usa caminhos absolutos; roda uma cópia com o prefixo trocado.

    O script original não aspa variáveis; por isso o prefixo falso não pode ter espaços
    (o de work/tests tem), e se usa um temporário comum.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="r36cpufreq-"))

    def roda_cpufreq(self, gov):
        sys_, alvos = self.monta(gov)
        log = self.tmp / "chamadas"
        falso = self.tmp / "tune"
        falso.write_text(f"#!/bin/sh\necho x >> {log}\n")
        falso.chmod(0o755)
        txt = CPUFREQ.read_text()
        txt = txt.replace("/sys/devices/system/cpu", str(sys_)).replace("/usr/lib/r36/cpu-ondemand-tune", str(falso))
        s = self.tmp / "cpufreq"
        s.write_text(txt)
        subprocess.run(["sh", str(s)], check=True, capture_output=True)
        return alvos, log

    def test_ondemand_mantem_up_threshold_50_e_chama_afinamento(self):
        alvos, log = self.roda_cpufreq("ondemand")
        self.assertEqual(self.le(alvos[0] / "up_threshold"), "50")
        self.assertEqual(log.read_text().count("x"), 1)

    def test_outro_governor_nao_chama(self):
        alvos, log = self.roda_cpufreq("performance")
        self.assertEqual(self.le(alvos[0] / "up_threshold"), "80")
        self.assertFalse(log.exists())


class RunEmu(TempDirCase):
    def test_chamada_apos_cada_normperf(self):
        linhas = [l.strip() for l in RUNEMU.read_text().splitlines()]
        idx = [i for i, l in enumerate(linhas) if l == "normperf"]
        self.assertEqual(len(idx), 2)  # abertura (else do maxperf) e saída
        # só a abertura passa "jogo"; a saída deixa a DRAM na cena 1 do normperf
        self.assertIn(CHAMADA_JOGO, linhas[idx[0] + 1:idx[0] + 3])
        self.assertIn(CHAMADA, linhas[idx[1] + 1:idx[1] + 3])

    def test_ausencia_do_script_nao_quebra(self):
        prog = f"set -e\nnormperf() {{ echo ok; }}\nnormperf\n{CHAMADA}\necho depois\n"
        r = subprocess.run(["bash", "-c", prog], capture_output=True, text=True)
        self.assertEqual(r.stdout.split(), ["ok", "depois"])


class MaxperfIntacto(TempDirCase):
    def test_afinamento_nao_toca_no_modo_performance(self):
        for p in (TUNE, CPUFREQ):
            codigo = re.sub(r"#.*", "", p.read_text())
            self.assertNotIn("performance", codigo)
            self.assertNotIn("scaling_governor", re.sub(r"cat [^\n]*scaling_governor[^\n]*", "", codigo))
            self.assertNotIn("maxperf", codigo)
            self.assertNotIn("normperf", codigo)


if __name__ == "__main__":
    import unittest
    unittest.main()
