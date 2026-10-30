"""Testes da feature de áudio (46-audio)."""

import difflib
import os
import re
import stat
import subprocess
import tomllib
import unittest

from context import CFG, ROOT, TempDirCase, needs_base
from r36img import mtools
from test_otimizacoes import UnitCase, diretivas

F46 = ROOT / "features" / "46-audio"
UNITS = "usr/lib/systemd/system"
PREPARA = F46 / "system" / "usr" / "lib" / "r36" / "audio-prepara"
GANHO = F46 / "system" / "usr" / "lib" / "r36" / "audio-ganho"
AMOSTRA = F46 / "system" / "usr" / "lib" / "r36" / "audio-amostra"
CONFSYNC = F46 / "system" / "usr" / "lib" / "r36" / "conf-sync"
UDT_EVENTS = F46 / "system" / "usr" / "bin" / "udt_events.sh"
UDT_PWR = F46 / "system" / "usr" / "bin" / "udt_pwr_events.sh"
RUNEMU = ROOT / "features" / "10-ptbr-sao-paulo" / "system" / "usr" / "bin" / "emuelecRunEmu.sh"

RETROARCH_CFG = (
    'audio_driver = "sdl2"\n'
    'audio_latency = "64"\n'
    'audio_rate_control = "true"\n'
    'audio_resampler = "sinc"\n'
    'audio_resampler_quality = "2"\n'
    'audio_sync = "true"\n'
    'video_threaded = "true"\n'
    'config_save_on_exit = "true"\n'
)
EMUELEC_CONF = "ee_audio_device=spk\naudio.volume=29\naudio.bgmusic=1\n"
MIXER_CONTENTS = "numid=3,iface=MIXER,name='speaker volume control'\n  ; type=INTEGER,access=rw---R--,values=1,min=0,max=63,step=0\n  : values=32\n"


def escreve(path, texto, modo=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(texto)
    if modo:
        path.chmod(modo)


class AudioFeature(UnitCase):
    def test_descritor(self):
        dados = tomllib.loads((F46 / "feature.toml").read_text(encoding="utf-8"))
        self.assertEqual(dados["schema"], 1)
        self.assertEqual(dados["order"], 46)
        self.assertTrue(dados["enabled"])

    def test_scripts(self):
        for script in (PREPARA, GANHO, AMOSTRA, UDT_EVENTS, UDT_PWR, CONFSYNC):
            self.assert_script(script)
            self.assertEqual(stat.S_IMODE(script.stat().st_mode), 0o755, script)
        for script in (PREPARA, GANHO, AMOSTRA, CONFSYNC):
            proc = subprocess.run(["sh", "-n", str(script)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_unit(self):
        unit = F46 / "system" / UNITS / "r36-audio.service"
        d = diretivas(unit)
        self.assertEqual(d["Type"], ["oneshot"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/audio-prepara"])
        self.assertEqual(d["Before"], ["emustation.service"])
        self.assertEqual(d["After"], ["sound.target"])
        self.assertEqual(d["TimeoutStartSec"], ["60"])
        self.assertEqual(d["WantedBy"], ["emuelec.target"])
        # esperar o autostart, que espera o ES, trava o boot no splash
        ativas = [l for l in unit.read_text().splitlines() if l.strip() and not l.lstrip().startswith("#")]
        self.assertFalse([l for l in ativas if l.startswith("After=") and "emuelec-autostart" in l])

    def test_link(self):
        self.assert_link(F46, "emuelec.target.wants", "r36-audio.service")
        self.assert_link(F46, "emuelec.target.wants", "r36-audio-amostra.service")

    def test_unit_do_amostrador_nao_segura_o_boot(self):
        unit = F46 / "system" / UNITS / "r36-audio-amostra.service"
        d = diretivas(unit)
        self.assertEqual(d["Type"], ["simple"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/audio-amostra"])
        self.assertEqual(d["WantedBy"], ["emuelec.target"])
        # em paralelo ao boot: sem ordenar contra o ES nem o autostart
        self.assertNotIn("Before", d)
        self.assertNotIn("After", d)

    def test_unit_conf_sync(self):
        unit = F46 / "system" / UNITS / "r36-conf-sync.service"
        d = diretivas(unit)
        self.assertEqual(d["Type"], ["oneshot"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/conf-sync"])
        self.assertEqual(d["DefaultDependencies"], ["no"])
        self.assertIn("shutdown.target", d["Before"][0].split())
        self.assertIn("local-fs.target", d["After"][0].split())
        for want in ("shutdown.target.wants", "reboot.target.wants", "poweroff.target.wants", "halt.target.wants"):
            self.assert_link(F46, want, "r36-conf-sync.service")

    def test_launcher_chama_audio_ganho_depois_de_cada_speaker_function(self):
        linhas = RUNEMU.read_text().splitlines()
        trocas = [i for i, l in enumerate(linhas) if l.strip() == "current_state=$(cat /sys/class/switch/h2w/state)"]
        self.assertEqual(len(trocas), 2)
        chamada = "if [ -x /usr/lib/r36/audio-ganho ]; then /usr/lib/r36/audio-ganho aplica; fi"
        for i in trocas:
            fim = next(j for j in range(i, len(linhas)) if linhas[j].strip() == "esac")
            self.assertIn(chamada, [l.strip() for l in linhas[fim + 1 : fim + 3]])
        self.assertEqual(sum(1 for l in linhas if l.strip() == chamada), 2)


class AudioCase(TempDirCase):
    """Árvore falsa (R36_ROOT) com um amixer simulado no PATH."""

    def setUp(self):
        super().setUp()
        self.root = self.tmp / "root"
        self.bin = self.tmp / "bin"
        self.amixer_log = self.tmp / "amixer.log"
        self.devmem = False
        escreve(self.root / "storage/.config/emuelec/configs/emuelec.conf", EMUELEC_CONF)
        escreve(self.root / "storage/.config/retroarch/retroarch.cfg", RETROARCH_CFG)
        (self.root / "storage/roms").mkdir(parents=True)
        self.stub(
            "amixer",
            'echo "$*" >> "$R36_TEST_LOG"\n'
            'case "$1" in\n'
            f'  contents) printf %s "{MIXER_CONTENTS}" ;;\n'
            '  cget) echo "  : values=32" ;;\n'
            "esac\n",
        )
        self.stub("busybox", '[ "$1" = --list ] && [ -n "$R36_TEST_DEVMEM" ] && echo devmem\nexit 0\n')

    def stub(self, nome, corpo):
        p = self.bin / nome
        escreve(p, "#!/bin/sh\n" + corpo, 0o755)

    def roda(self, script, *args, **extra):
        env = dict(
            os.environ,
            PATH=f"{self.bin}:{os.environ['PATH']}",
            R36_ROOT=str(self.root), TMPDIR=str(self.tmp), R36_TEST_LOG=str(self.amixer_log),
        )
        if self.devmem:
            env["R36_TEST_DEVMEM"] = "1"
        env.update(extra)
        proc = subprocess.run(["sh", str(script), *args], env=env, capture_output=True, text=True, timeout=30)
        return proc

    def chamadas(self):
        return self.amixer_log.read_text().splitlines() if self.amixer_log.exists() else []

    def cfg(self):
        return (self.root / "storage/.config/retroarch/retroarch.cfg").read_text()

    def conf(self):
        return (self.root / "storage/.config/emuelec/configs/emuelec.conf").read_text()

    def modo(self, texto):
        escreve(self.root / "run/r36-audio.modo", texto + "\n")


class AudioPrepara(AudioCase):
    def prepara(self, diag=True, **extra):
        if diag:
            escreve(self.root / "storage/roms/r36-diagnostico", "")
        proc = self.roda(PREPARA, **extra)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    def log(self):
        return (self.root / "storage/roms/r36-audio.log").read_text()

    def test_valores_de_fabrica_viram_96_e_1(self):
        self.prepara()
        esperado = RETROARCH_CFG.replace('audio_latency = "64"', 'audio_latency = "96"').replace(
            'audio_resampler_quality = "2"', 'audio_resampler_quality = "1"'
        )
        self.assertEqual(self.cfg(), esperado)
        self.assertIn('video_threaded = "true"', self.cfg().splitlines())
        self.assertEqual((self.root / "run/r36-audio.modo").read_text().strip(), "corrigido")

    def test_valor_do_usuario_fica_como_esta(self):
        escreve(self.root / "storage/.config/retroarch/retroarch.cfg", RETROARCH_CFG.replace('"64"', '"128"'))
        self.prepara()
        self.assertIn('audio_latency = "128"', self.cfg().splitlines())
        self.assertIn('audio_resampler_quality = "1"', self.cfg().splitlines())

    def test_modo_original_volta_aos_valores_de_fabrica(self):
        self.prepara()  # corrigido: 96/1
        escreve(self.root / "storage/roms/r36-audio-original", "")
        self.prepara()
        self.assertEqual(self.cfg(), RETROARCH_CFG)
        self.assertEqual((self.root / "run/r36-audio.modo").read_text().strip(), "original")
        self.assertIn("modo: original", self.log())

    def test_modo_original_nao_mexe_em_valor_do_usuario(self):
        escreve(self.root / "storage/.config/retroarch/retroarch.cfg", RETROARCH_CFG.replace('"64"', '"128"'))
        escreve(self.root / "storage/roms/r36-audio-original", "")
        self.prepara()
        self.assertIn('audio_latency = "128"', self.cfg().splitlines())

    def test_religar_apagando_a_chave(self):
        escreve(self.root / "storage/roms/r36-audio-original", "")
        self.prepara()
        (self.root / "storage/roms/r36-audio-original").unlink()
        self.prepara()
        self.assertIn('audio_latency = "96"', self.cfg().splitlines())
        self.assertEqual((self.root / "run/r36-audio.modo").read_text().strip(), "corrigido")

    def test_sem_p1_termina_com_zero_e_sem_log(self):
        (self.root / "storage/roms").rmdir()
        proc = self.prepara(diag=False)
        self.assertFalse((self.root / "storage/roms").exists())
        # o buffer do RetroArch e o modo valem mesmo assim
        self.assertIn('audio_latency = "96"', self.cfg().splitlines())
        self.assertEqual((self.root / "run/r36-audio.modo").read_text().strip(), "corrigido")
        self.assertEqual(proc.stdout.strip(), "")

    def test_sem_retroarch_cfg(self):
        (self.root / "storage/.config/retroarch/retroarch.cfg").unlink()
        self.prepara()
        self.assertIn("retroarch.cfg ausente", self.log())

    def test_log_traz_todas_as_secoes(self):
        escreve(self.root / "sys/class/switch/h2w/state", "0\n")
        reg = self.root / "sys/devices/platform/sunxi-pcm-codec/audio_reg_debug"
        escreve(reg, "0x00: 0x8d8d\n")
        self.devmem = True
        self.modo("original")  # o prepara decide o modo sozinho e sobrescreve
        self.prepara()
        log = self.log()
        for trecho in (
            "modo: corrigido",
            "== retroarch.cfg ==",
            "== amixer contents ==",
            "speaker volume control",
            "== interface de registradores do driver (audio_reg*) ==",
            "/sys/devices/platform/sunxi-pcm-codec/audio_reg_debug",
            "0x00: 0x8d8d",
            "busybox tem o applet devmem",
            "h2w/state: 0 -> Speaker Function headset",
            "antes: speaker volume control=32",
            "dump antes",
            "depois: speaker volume control=32",
            "dump depois",
            "== audio-ganho aplica ==",
            "audio-ganho: modo=corrigido",
        ):
            self.assertIn(trecho, log)
        self.assertIn("cset name=Speaker Function headset", self.chamadas())

    def test_fone_conectado_vira_spk(self):
        escreve(self.root / "sys/class/switch/h2w/state", "2\n")
        self.prepara()
        self.assertIn("cset name=Speaker Function spk", self.chamadas())
        self.assertIn("h2w/state: 2 -> Speaker Function spk", self.log())

    def test_sem_interface_aparece_no_log_sem_erro(self):
        self.prepara()
        self.assertIn("nenhum arquivo audio_reg* em /sys", self.log())
        self.assertIn("busybox sem o applet devmem", self.log())
        # só lê: nenhuma escrita em registrador (o dump é só leitura de arquivo)
        self.assertFalse(list((self.root / "sys").rglob("audio_reg*")))

    def test_log_substitui_o_anterior(self):
        escreve(self.root / "storage/roms/r36-audio.log", "boot antigo\n")
        self.prepara()
        self.assertNotIn("boot antigo", self.log())
        self.assertEqual(self.log().count("r36-audio-prepara"), 1)

    def test_sem_a_chave_nao_grava_log_mas_aplica_o_audio(self):
        escreve(self.root / "sys/class/switch/h2w/state", "2\n")
        escreve(self.root / "sys/devices/platform/sunxi-pcm-codec/audio_reg_debug", "0x00: 0x8d8d\n")
        self.prepara(diag=False)
        self.assertFalse((self.root / "storage/roms/r36-audio.log").exists())
        self.assertIn('audio_latency = "96"', self.cfg().splitlines())
        self.assertIn("cset name=Speaker Function spk", self.chamadas())
        self.assertEqual((self.root / "run/r36-audio.modo").read_text().strip(), "corrigido")
        # nada de leitura de diagnostico: so o cset do Speaker Function e o audio-ganho
        self.assertNotIn("contents", self.chamadas())
        self.assertFalse([c for c in self.chamadas() if c.startswith("cget") and "Speaker Function" in c])
        self.assertTrue([c for c in self.chamadas() if c.startswith("cset")])

    def test_sem_a_chave_o_log_antigo_fica_intacto(self):
        escreve(self.root / "storage/roms/r36-audio.log", "boot antigo\n")
        self.prepara(diag=False)
        self.assertEqual(self.log(), "boot antigo\n")

    def test_nao_deixa_temporarios(self):
        self.prepara()
        self.assertEqual(sorted(p.name for p in self.tmp.glob("r36-audio.*")), [])
        self.assertFalse((self.root / "storage/.config/retroarch/retroarch.cfg.r36tmp").exists())


class AudioGanho(AudioCase):
    def ganho(self, *args, **extra):
        proc = self.roda(GANHO, *args, **extra)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    def analogico(self):
        return [l.split()[-1] for l in self.chamadas() if "speaker volume control" in l]

    def test_escala_de_fabrica_igual_a_da_base(self):
        for v, esperado in ((0, 20), (3, 21), (29, 32), (100, 63)):
            self.assertEqual((v * 43 + 50) // 100 + 20, esperado)  # a fórmula do udt_events.sh
            self.amixer_log.unlink(missing_ok=True)
            self.ganho("volume", str(v))
            self.assertEqual(self.analogico(), [str(esperado)], v)

    def test_modo_ausente_e_original(self):
        # sem /run/r36-audio.modo, o volume 0 não silencia: escala de fábrica
        self.ganho("volume", "0")
        self.assertEqual(self.analogico(), ["20"])

    def test_volume_limita_a_faixa_e_grava(self):
        for entrada, gravado in (("150", "100"), ("-5", "0"), ("42", "42")):
            self.ganho("volume", entrada)
            self.assertIn(f"audio.volume={gravado}\n", self.conf())
        self.assertEqual(self.conf().count("audio.volume="), 1)
        self.assertIn("ee_audio_device=spk\n", self.conf())
        self.assertIn("audio.bgmusic=1\n", self.conf())

    def test_volume_invalido_e_erro_de_uso(self):
        for entrada in ("abc", ""):
            proc = self.roda(GANHO, "volume", entrada)
            self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.analogico(), [])
        self.assertIn("audio.volume=29\n", self.conf())

    def test_aplica_usa_o_volume_salvo(self):
        self.ganho("aplica")
        self.assertEqual(self.analogico(), ["32"])  # 29 na escala de fábrica

    def test_aplica_sem_audio_volume_usa_o_padrao(self):
        escreve(self.root / "storage/.config/emuelec/configs/emuelec.conf", "ee_audio_device=spk\n")
        self.ganho("aplica")
        self.assertEqual(self.analogico(), ["32"])

    def test_volume_acrescenta_a_chave_se_faltar(self):
        escreve(self.root / "storage/.config/emuelec/configs/emuelec.conf", "ee_audio_device=spk")  # sem quebra final
        self.ganho("volume", "9")
        self.assertEqual(self.conf(), "ee_audio_device=spk\naudio.volume=9\n")

    def test_volume_sobrevive_ao_es_regravar_o_conf(self):
        # o ES regrava o emuelec.conf com o audio.volume antigo ao reiniciar pelo menu
        arq = self.root / "storage/.config/emuelec/configs/r36-audio.volume"
        self.ganho("volume", "9")
        self.assertEqual(arq.read_text(), "9\n")
        escreve(self.root / "storage/.config/emuelec/configs/emuelec.conf", "audio.volume=29\n")
        self.amixer_log.unlink(missing_ok=True)
        self.ganho("aplica")
        self.assertEqual(self.analogico(), [str((9 * 43 + 50) // 100 + 20)])

    def test_arquivo_proprio_invalido_cai_no_conf(self):
        escreve(self.root / "storage/.config/emuelec/configs/r36-audio.volume", "lixo\n")
        escreve(self.root / "storage/.config/emuelec/configs/emuelec.conf", "audio.volume=100\n")
        self.ganho("aplica")
        self.assertEqual(self.analogico(), ["63"])

    def test_mudo_com_volume_zero_e_volta_com_volume_3(self):
        self.modo("corrigido")
        self.ganho("volume", "0")
        self.ganho("volume", "3")
        self.assertEqual(self.analogico(), ["0", "21"])

    def test_volume_zero_no_modo_original_nao_muda_de_comportamento(self):
        self.modo("original")
        self.ganho("volume", "0")
        self.assertEqual(self.analogico(), ["20"])

    def test_subcomando_invalido(self):
        proc = self.roda(GANHO, "xyz")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.chamadas(), [])

    def test_conf_sync_preserva_audio_e_brilho(self):
        escreve(self.root / "storage/.config/emuelec/configs/emuelec.conf",
                "audio.volume=80\nbrightness.level=100\n")
        escreve(self.root / "storage/.config/emuelec/configs/r36-audio.volume", "25\n")
        escreve(self.root / "storage/.config/emuelec/configs/r36-brilho.level", "45\n")
        proc = self.roda(CONFSYNC)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        conteudo = (self.root / "storage/.config/emuelec/configs/emuelec.conf").read_text()
        self.assertIn("audio.volume=25\n", conteudo)
        self.assertIn("brightness.level=45\n", conteudo)


DUMP_PARADO = (
    "dump audio reg:\n"
    "DAC_Digital_Part_Control 0xf1c22c00: 0x0\n"
    "DAC_FIFO_Status 0xf1c22c08: 0x4020\n"
    "DAC_TX_Counter 0xf1c22c40: 0x0\n"
    "PA_Enable_and_HP_Control 0x7: 0xf4\n"
)
DUMP_TOCANDO = DUMP_PARADO.replace("00: 0x0", "00: 0x80003000")


class AudioAmostra(AudioCase):
    def setUp(self):
        super().setUp()
        self.reg = self.root / "sys/devices/platform/sunxi-pcm-codec/audio_reg_debug/audio_reg"
        escreve(self.reg, DUMP_PARADO)
        escreve(self.root / "proc/uptime", "12.50 40.00\n")
        self.log = self.root / "storage/roms/r36-audio-dac.log"

    def amostra(self, duracao="9", passo="3", diag=True, **extra):
        if diag:
            escreve(self.root / "storage/roms/r36-diagnostico", "")
        proc = self.roda(AMOSTRA, R36_AMOSTRA_DURACAO=duracao, R36_AMOSTRA_PASSO=passo, **extra)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_grava_so_quando_o_estado_muda(self):
        # o sleep falso troca o dump na segunda volta: parado, tocando, tocando
        self.stub("sleep", f'[ -f "{self.tmp}/voltas" ] && cp "{self.tmp}/tocando" "{self.reg}"\n: > "{self.tmp}/voltas"\n')
        escreve(self.tmp / "tocando", DUMP_TOCANDO)
        self.amostra()
        log = self.log.read_text()
        self.assertEqual(log.count("== t=12.50 s (uptime) =="), 2)
        self.assertIn("DAC_Digital_Part_Control 0xf1c22c00: 0x0\n", log)
        self.assertIn("DAC_Digital_Part_Control 0xf1c22c00: 0x80003000\n", log)
        self.assertIn("speaker volume control=32", log)

    def test_contador_que_muda_nao_gera_amostra_nova(self):
        self.stub("sleep", f'sed -i "s/Counter 0xf1c22c40: 0x0/Counter 0xf1c22c40: 0x$$/" "{self.reg}"\n')
        self.amostra()
        self.assertEqual(self.log.read_text().count("== t="), 1)

    def test_nao_escreve_no_codec(self):
        self.amostra()
        self.assertEqual(self.reg.read_text(), DUMP_PARADO)
        self.assertEqual([c for c in self.chamadas() if not c.startswith("cget")], [])

    def test_sem_interface_sai_sem_erro_e_sem_log(self):
        self.reg.unlink()
        self.amostra()
        self.assertFalse(self.log.exists())

    def test_sem_p1_nao_grava(self):
        (self.root / "storage/roms").rmdir()
        self.amostra(diag=False)
        self.assertFalse(self.log.exists())

    def test_sem_a_chave_nao_le_o_codec_nem_cria_o_log(self):
        self.amostra(diag=False)
        self.assertFalse(self.log.exists())
        self.assertEqual(self.chamadas(), [])

    def test_sem_a_chave_o_log_antigo_fica_intacto(self):
        escreve(self.log, "boot antigo\n")
        self.amostra(diag=False)
        self.assertEqual(self.log.read_text(), "boot antigo\n")

    def test_log_tem_tamanho_maximo(self):
        escreve(self.log, "x" * 70000)  # o log do boot anterior é substituído
        # cada volta muda o estado (e o PID do sleep falso): sem o limite, seriam ~100 KB
        self.stub("sleep", f'sed -i "s/^DAC_Digital_Part_Control .*/DAC_Digital_Part_Control 0xf1c22c00: 0x$$/" "{self.reg}"\n')
        self.amostra(duracao="400", passo="1")
        self.assertLess(self.log.stat().st_size, 70000)
        self.assertGreater(self.log.stat().st_size, 60000)


def diferencas(base, nova):
    mudou = [l for l in difflib.unified_diff(base, nova, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    return [l for l in mudou if l[0] == "-"], [l[1:].strip() for l in mudou if l[0] == "+"]


class ScriptsDaBase(TempDirCase):
    @needs_base
    def setUp(self):
        super().setUp()
        sq = self.tmp / "SYSTEM"
        subprocess.run(
            ["mcopy", "-n", "-i", mtools.spec(CFG.base_path, CFG.part("system").offset), "::/SYSTEM", str(sq)],
            check=True, env=mtools.ENV, capture_output=True)
        self.sq = sq

    def base(self, caminho):
        return subprocess.run(
            ["unsquashfs", "-cat", str(self.sq), caminho], check=True, capture_output=True, text=True
        ).stdout.splitlines()

    @needs_base
    def test_udt_events_so_acrescenta_a_chamada_ao_audio_ganho(self):
        removidas, acrescentadas = diferencas(self.base("usr/bin/udt_events.sh"), UDT_EVENTS.read_text().splitlines())
        self.assertEqual(removidas, [])
        self.assertEqual(
            acrescentadas,
            [
                "# R36: a escala e o mudo ficam no audio-ganho; sem ele vale a escala de fábrica abaixo",
                "if [ -x /usr/lib/r36/audio-ganho ]; then",
                "/usr/lib/r36/audio-ganho volume ${STEPVOL}",
                "return",
                "fi",
            ],
        )

    @needs_base
    def test_udt_pwr_events_so_acrescenta_a_reaplicacao(self):
        removidas, acrescentadas = diferencas(self.base("usr/bin/udt_pwr_events.sh"), UDT_PWR.read_text().splitlines())
        self.assertEqual(removidas, [])
        self.assertEqual(
            acrescentadas,
            [
                # feature 62-brilho-fn: o brilho salvo volta depois do restore do lcdbl pelo emuelec.conf
                "[ -x /usr/lib/r36/brilho-aplica ] && /usr/lib/r36/brilho-aplica aplica  # R36: brilho salvo (feature 62)",
                "# R36: reaplica o ganho de áudio depois da troca do Speaker Function",
                "if [ -x /usr/lib/r36/audio-ganho ]; then /usr/lib/r36/audio-ganho aplica; fi",
            ],
        )


if __name__ == "__main__":
    unittest.main()
