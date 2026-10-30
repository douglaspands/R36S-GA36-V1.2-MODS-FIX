"""Testes do brilho da tela por FN + D-pad (feature 62-brilho-fn)."""

import os
import stat
import struct
import subprocess
import time
import tomllib
import unittest

from context import ROOT, TempDirCase
from test_audio import escreve
from test_otimizacoes import UnitCase, diretivas

F62 = ROOT / "features" / "62-brilho-fn"
UNITS = "usr/lib/systemd/system"
APLICA = F62 / "system" / "usr" / "lib" / "r36" / "brilho-aplica"
ES_SYNC = F62 / "system" / "usr" / "lib" / "r36" / "brilho-es-sync"
LCDBL = "sys/devices/virtual/disp/disp/attr/lcdbl"
NIVEL = "storage/.config/emuelec/configs/r36-brilho.level"
EMUCONF = "storage/.config/emuelec/configs/emuelec.conf"
ATUAL = "run/r36-brilho.atual"
LOG = "storage/roms/r36-brilho.log"
DIAG = "storage/roms/r36-diagnostico"


LEITOR = F62 / "system" / "usr" / "lib" / "r36" / "brilho-leitor"


def escala(nivel):
    return (nivel * 255 + 50) // 100


# Linhas no formato do evtest da base (cadeias do binário: "Event: time %ld.%06ld, " e
# "type %d (%s), code %d (%s), value %d"), ver design.md D3.
def ev(tipo, code, nome, valor, t="1700000000.000000"):
    tipos = {1: "EV_KEY", 3: "EV_ABS", 4: "EV_MSC"}
    return f"Event: time {t}, type {tipo} ({tipos[tipo]}), code {code} ({nome}), value {valor}"


SYN = "Event: time 1700000000.000000, -------------- SYN_REPORT ------------"
FN = (316, "BTN_MODE")
DPAD_CIMA, DPAD_BAIXO = (544, "BTN_DPAD_UP"), (545, "BTN_DPAD_DOWN")
TECLA_CIMA, TECLA_BAIXO = (103, "KEY_UP"), (108, "KEY_DOWN")
HAT = (17, "ABS_HAT0Y")
L3 = (317, "BTN_THUMBL")
R3 = (318, "BTN_THUMBR")


def tecla(par, valor):
    return ev(1, par[0], par[1], valor)


def hat(valor):
    return ev(3, HAT[0], HAT[1], valor)


DEVICES = """I: Bus=0019 Vendor=0001 Product=0001 Version=0100
N: Name="axp22-supplyer"
P: Phys=m1kbd/input2
S: Sysfs=/devices/platform/axp22_board/axp22-supplyer.20/input/input0
U: Uniq=
H: Handlers=kbd event0
B: PROP=0
B: EV=3
B: KEY=100000 0 0 0

I: Bus=0019 Vendor=0001 Product=0001 Version=0100
N: Name="udt_keyboard"
P: Phys=
S: Sysfs=/devices/virtual/input/input1
U: Uniq=
H: Handlers=kbd event1
B: PROP=0
B: EV=3

I: Bus=0019 Vendor=696d Product=5f6f Version=0100
N: Name="micro_gamepad"
P: Phys=
S: Sysfs=/devices/platform/micro_gamepad/input/input2
U: Uniq=
H: Handlers=js0 event2
B: PROP=0
B: EV=b
"""


class BrilhoFeature(UnitCase):
    def test_descritor(self):
        dados = tomllib.loads((F62 / "feature.toml").read_text(encoding="utf-8"))
        self.assertEqual(dados["schema"], 1)
        self.assertEqual(dados["order"], 62)
        self.assertTrue(dados["enabled"])
        self.assertIn("brilho", dados["description"])

    def test_aplica_e_sh_executavel(self):
        self.assert_script(APLICA)
        self.assertEqual(stat.S_IMODE(APLICA.stat().st_mode), 0o755)
        self.assertTrue(APLICA.read_text().startswith("#!/bin/sh\n"))
        proc = subprocess.run(["sh", "-n", str(APLICA)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class BrilhoCase(TempDirCase):
    def setUp(self):
        super().setUp()
        self.root = self.tmp / "root"
        (self.root / "storage/roms").mkdir(parents=True)
        escreve(self.root / LCDBL, "204\n")

    def aplica(self, *args, **extra):
        env = dict(os.environ, R36_ROOT=str(self.root), R36_BRILHO_ESPERA_P1="1")
        env.update(extra)
        return subprocess.run(["sh", str(APLICA), *args], env=env, capture_output=True, text=True, timeout=30)

    def ok(self, *args, **extra):
        proc = self.aplica(*args, **extra)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        return proc

    def lcdbl(self):
        return int((self.root / LCDBL).read_text().strip())

    def nivel(self):
        return (self.root / NIVEL).read_text()


class BrilhoAplica(BrilhoCase):
    def test_sem_arquivo_usa_o_emuelec_conf(self):
        escreve(self.root / EMUCONF, "audio.volume=29\nbrightness.level=60\n")
        self.ok("aplica")
        self.assertEqual(self.lcdbl(), escala(60))
        self.assertFalse((self.root / NIVEL).exists())

    def test_sem_arquivo_e_sem_emuelec_conf_usa_80(self):
        self.ok("aplica")
        self.assertEqual(self.lcdbl(), escala(80))

    def test_emuelec_conf_sem_a_chave_usa_80(self):
        escreve(self.root / EMUCONF, "audio.volume=29\n")
        self.ok("aplica")
        self.assertEqual(self.lcdbl(), escala(80))

    def test_arquivo_valido_vale_mais_que_o_emuelec_conf(self):
        escreve(self.root / EMUCONF, "brightness.level=80\n")
        escreve(self.root / NIVEL, "35\n")
        self.ok("aplica")
        self.assertEqual(self.lcdbl(), escala(35))

    def test_escala(self):
        for nivel, valor in ((10, 26), (50, 128), (80, 204), (100, 255)):
            with self.subTest(nivel=nivel):
                escreve(self.root / NIVEL, f"{nivel}\n")
                self.ok("aplica")
                self.assertEqual(self.lcdbl(), valor)

    def test_valor_invalido_cai_no_padrao(self):
        # o emuelec.conf não vale quando o arquivo existe: o valor ruim vira o padrão (80)
        escreve(self.root / EMUCONF, "brightness.level=50\n")
        for ruim in ("", "\n", "abc\n", "-20\n", "101\n", "250\n", "5\n", "0\n", "9\n", "4 5\n", "99999999999999999999\n"):
            with self.subTest(ruim=ruim):
                escreve(self.root / NIVEL, ruim)
                self.ok("aplica")
                self.assertEqual(self.lcdbl(), escala(80))

    def test_emuelec_conf_abaixo_do_piso_cai_no_padrao(self):
        escreve(self.root / EMUCONF, "brightness.level=0\n")
        self.ok("aplica")
        self.assertEqual(self.lcdbl(), escala(80))

    def test_piso_e_teto_sao_validos(self):
        for nivel in (10, 100):
            with self.subTest(nivel=nivel):
                escreve(self.root / NIVEL, f"{nivel}\n")
                self.ok("aplica")
                self.assertEqual(self.lcdbl(), escala(nivel))

    def test_ajusta_anda_5_pontos(self):
        escreve(self.root / NIVEL, "50\n")
        self.ok("aplica")
        self.ok("ajusta", "+")
        self.assertEqual(self.lcdbl(), escala(55))
        self.ok("ajusta", "+")
        self.assertEqual(self.lcdbl(), escala(60))
        self.ok("ajusta", "-")
        self.assertEqual(self.lcdbl(), escala(55))
        # ajusta só muda a tela: o arquivo fica para o salva
        self.assertEqual(self.nivel(), "50\n")

    def test_ajusta_sem_aplica_parte_do_nivel_salvo(self):
        escreve(self.root / NIVEL, "40\n")
        self.ok("ajusta", "-")
        self.assertEqual(self.lcdbl(), escala(35))

    def test_ajusta_para_no_teto(self):
        escreve(self.root / NIVEL, "95\n")
        self.ok("aplica")
        for _ in range(3):
            self.ok("ajusta", "+")
        self.assertEqual(self.lcdbl(), escala(100))

    def test_ajusta_para_no_piso(self):
        escreve(self.root / NIVEL, "20\n")
        self.ok("aplica")
        for _ in range(5):
            self.ok("ajusta", "-")
        self.assertEqual(self.lcdbl(), escala(10))
        self.assertGreater(self.lcdbl(), 0)

    def test_ajusta_de_nivel_fora_do_passo(self):
        # 83 do emuelec.conf: anda 5 e para no teto sem passar de 100
        escreve(self.root / EMUCONF, "brightness.level=83\n")
        self.ok("aplica")
        self.ok("ajusta", "+")
        self.assertEqual(self.lcdbl(), escala(88))
        for _ in range(4):
            self.ok("ajusta", "+")
        self.assertEqual(self.lcdbl(), escala(100))

    def test_ajusta_com_argumento_ruim_nao_muda(self):
        escreve(self.root / NIVEL, "50\n")
        self.ok("aplica")
        proc = self.aplica("ajusta", "x")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(self.lcdbl(), escala(50))

    def test_salva_sincroniza_arquivo_e_emuelec_conf(self):
        escreve(self.root / EMUCONF, "brightness.level=80\n")
        self.ok("aplica")
        self.ok("ajusta", "-")
        self.ok("ajusta", "-")
        self.ok("salva")
        self.assertEqual(self.nivel(), "70\n")
        # o emuelec.conf sincroniza em tempo real
        self.assertEqual((self.root / EMUCONF).read_text(), "brightness.level=70\n")
        self.assertEqual(self.lcdbl(), escala(70))

    def test_salva_sem_mudanca_nao_cria_o_arquivo(self):
        self.ok("aplica")
        self.ok("salva")
        self.assertFalse((self.root / NIVEL).exists())

    def test_salva_sem_mudanca_nao_regrava(self):
        escreve(self.root / NIVEL, "45\n")
        os.utime(self.root / NIVEL, ns=(1_000_000_000, 1_000_000_000))
        self.ok("aplica")
        self.ok("salva")
        self.assertEqual((self.root / NIVEL).stat().st_mtime_ns, 1_000_000_000)

    def test_segunda_rodada_de_aplica_nao_regrava_o_arquivo(self):
        escreve(self.root / NIVEL, "45\n")
        os.utime(self.root / NIVEL, ns=(1_000_000_000, 1_000_000_000))
        self.ok("aplica")
        self.ok("aplica")
        self.assertEqual((self.root / NIVEL).stat().st_mtime_ns, 1_000_000_000)
        self.assertEqual(self.nivel(), "45\n")

    def test_padrao_apaga_o_arquivo_e_aplica_80(self):
        escreve(self.root / NIVEL, "30\n")
        self.ok("aplica")
        self.ok("padrao")
        self.assertFalse((self.root / NIVEL).exists())
        self.assertEqual(self.lcdbl(), escala(80))
        # o próximo ajuste parte do 80
        self.ok("ajusta", "+")
        self.assertEqual(self.lcdbl(), escala(85))

    def test_padrao_com_emuelec_conf_diferente_persiste_80(self):
        escreve(self.root / EMUCONF, "brightness.level=50\n")
        escreve(self.root / NIVEL, "30\n")
        self.ok("padrao")
        self.assertEqual((self.root / EMUCONF).read_text(), "brightness.level=80\n")

    def test_lcdbl_ausente_sai_com_zero_sem_gravar(self):
        (self.root / LCDBL).unlink()
        escreve(self.root / DIAG, "")
        for args in (("aplica",), ("ajusta", "+"), ("salva",), ("padrao",), ("boot",)):
            with self.subTest(args=args):
                self.ok(*args)
        self.assertFalse((self.root / LCDBL).exists())
        self.assertFalse((self.root / NIVEL).exists())

    def test_subcomando_desconhecido_sai_com_zero(self):
        proc = self.aplica("outro")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(self.lcdbl(), 204)


class LeitorFeature(UnitCase):
    def test_leitor_e_bash_executavel(self):
        self.assert_script(LEITOR)
        self.assertEqual(stat.S_IMODE(LEITOR.stat().st_mode), 0o755)
        self.assertTrue(LEITOR.read_text().startswith("#!/bin/bash\n"))


def interpreta(*linhas):
    """Roda a função interpreta do leitor (em bash, com o script carregado por '.')."""
    prog = (
        '. "$1"; shift; for l in "$@"; do '
        'if interpreta "$l"; then echo "$EV_NOME $EV_VALOR $EV_CODE"; else echo -; fi; done'
    )
    proc = subprocess.run(["bash", "-c", prog, "_", str(LEITOR), *linhas], capture_output=True, text=True, timeout=10)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.splitlines()


class LeitorParser(unittest.TestCase):
    def test_fn(self):
        self.assertEqual(interpreta(tecla(FN, 1), tecla(FN, 0)), ["fn 1 BTN_MODE", "fn 0 BTN_MODE"])

    def test_dpad_como_botao(self):
        self.assertEqual(
            interpreta(tecla(DPAD_CIMA, 1), tecla(DPAD_CIMA, 0), tecla(DPAD_BAIXO, 1), tecla(DPAD_BAIXO, 0)),
            ["cima 1 BTN_DPAD_UP", "cima 0 BTN_DPAD_UP", "baixo 1 BTN_DPAD_DOWN", "baixo 0 BTN_DPAD_DOWN"],
        )

    def test_dpad_como_tecla(self):
        self.assertEqual(
            interpreta(tecla(TECLA_CIMA, 1), tecla(TECLA_BAIXO, 0)),
            ["cima 1 KEY_UP", "baixo 0 KEY_DOWN"],
        )

    def test_dpad_como_eixo(self):
        self.assertEqual(
            interpreta(hat(-1), hat(0), hat(1)),
            ["eixo -1 ABS_HAT0Y", "eixo 0 ABS_HAT0Y", "eixo 1 ABS_HAT0Y"],
        )

    def test_l3_pelo_nome_ou_pelo_codigo(self):
        self.assertEqual(
            interpreta(tecla(L3, 1), tecla(L3, 0), tecla((317, "BTN_QUALQUER"), 1), tecla(L3, 2)),
            ["l3 1 BTN_THUMBL", "l3 0 BTN_THUMBL", "l3 1 BTN_QUALQUER", "-"],
        )

    def test_r3_nao_e_l3(self):
        self.assertEqual(interpreta(tecla(R3, 1)), ["-"])

    def test_ignora_o_resto(self):
        linhas = [
            SYN,
            tecla(FN, 2),  # repetição automática do kernel
            tecla(DPAD_CIMA, 2),
            ev(4, 4, "MSC_SCAN", "90001"),
            ev(1, 304, "BTN_SOUTH", 1),
            ev(1, 464, "KEY_FN", 1),  # FN sem o remapeamento da feature 20
            ev(3, 16, "ABS_HAT0X", -1),
            ev(3, 1, "ABS_Y", 300),
            "Input device name: \"micro_gamepad\"",
            "    Event code 316 (BTN_MODE)",
            "    Event code 17 (ABS_HAT0Y)",
            "      Value      0",
            "Testing ... (interrupt to exit)",
            "",
        ]
        self.assertEqual(interpreta(*linhas), ["-"] * len(linhas))

    def test_carregar_o_script_nao_roda_o_leitor(self):
        proc = subprocess.run(["bash", "-c", '. "$1"; echo carregado', "_", str(LEITOR)],
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.stdout, "carregado\n")


class LeitorCase(TempDirCase):
    def setUp(self):
        super().setUp()
        self.root = self.tmp / "root"
        self.bin = self.tmp / "bin"
        (self.root / "storage/roms").mkdir(parents=True)
        escreve(self.root / "proc/bus/input/devices", DEVICES)
        self.chamadas_arq = self.tmp / "chamadas"
        self.eventos = self.tmp / "eventos"
        self.evtest_arg = self.tmp / "evtest.arg"
        # evtest falso: repete as linhas do arquivo de eventos; "sleep N" vira uma pausa
        escreve(self.bin / "evtest",
                '#!/bin/sh\nprintf "%s\\n" "$1" > "$R36_TESTE_EVTEST_ARG"\n'
                'while IFS= read -r l; do case "$l" in "sleep "*) sleep "${l#sleep }" ;; '
                '*) printf "%s\\n" "$l" ;; esac; done < "$R36_TESTE_EVENTOS"\n', 0o755)
        # brilho-aplica falso: só registra a chamada
        self.falso = self.tmp / "brilho-aplica"
        escreve(self.falso, '#!/bin/sh\nprintf "%s\\n" "$*" >> "$R36_TESTE_CHAMADAS"\n', 0o755)

    def leitor(self, linhas, **extra):
        self.eventos.write_text("\n".join(linhas) + "\n")
        env = dict(
            os.environ,
            PATH=f"{self.bin}:{os.environ['PATH']}",
            R36_ROOT=str(self.root),
            R36_BRILHO_APLICA=str(self.falso),
            R36_BRILHO_REPETE="0.1",
            R36_BRILHO_ESPERA="1",
            R36_TESTE_EVENTOS=str(self.eventos),
            R36_TESTE_CHAMADAS=str(self.chamadas_arq),
            R36_TESTE_EVTEST_ARG=str(self.evtest_arg),
        )
        env.update(extra)
        proc = subprocess.run(["bash", str(LEITOR)], env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    def toque(self, linhas):
        # toques curtos (0,03 s): repetição lenta para a contagem exata não depender da máquina
        return self.leitor(linhas, R36_BRILHO_REPETE="0.5")

    def chamadas(self):
        if not self.chamadas_arq.exists():
            return []
        return self.chamadas_arq.read_text().splitlines()

    def assert_ajusta_e_salva(self, op):
        c = self.chamadas()
        self.assertGreaterEqual(len(c), 2, c)
        self.assertEqual(c[-1], "salva", c)
        self.assertEqual(c.count("salva"), 1, c)
        self.assertEqual(set(c[:-1]), {f"ajusta {op}"}, c)
        return c


class LeitorCenarios(LeitorCase):
    def test_le_o_micro_gamepad_pelo_nome(self):
        self.leitor([])
        self.assertEqual(self.evtest_arg.read_text().strip(), "/dev/input/event2")

    def test_toque_sobe_um_passo_e_salva_ao_soltar(self):
        for cima in (DPAD_CIMA, TECLA_CIMA):
            with self.subTest(cima=cima[1]):
                self.chamadas_arq.unlink(missing_ok=True)
                self.toque([tecla(FN, 1), SYN, tecla(cima, 1), SYN, "sleep 0.03", tecla(cima, 0), SYN,
                             tecla(FN, 0), SYN])
                self.assertEqual(self.chamadas(), ["ajusta +", "salva"])

    def test_toque_desce_um_passo(self):
        for baixo in (DPAD_BAIXO, TECLA_BAIXO):
            with self.subTest(baixo=baixo[1]):
                self.chamadas_arq.unlink(missing_ok=True)
                self.toque([tecla(FN, 1), tecla(baixo, 1), "sleep 0.03", tecla(baixo, 0), tecla(FN, 0)])
                self.assertEqual(self.chamadas(), ["ajusta -", "salva"])

    def test_eixo_sobe_e_desce(self):
        self.toque([tecla(FN, 1), hat(-1), SYN, "sleep 0.03", hat(0), SYN, tecla(FN, 0)])
        self.assertEqual(self.chamadas(), ["ajusta +", "salva"])
        self.chamadas_arq.unlink()
        self.toque([tecla(FN, 1), hat(1), "sleep 0.03", hat(0), tecla(FN, 0)])
        self.assertEqual(self.chamadas(), ["ajusta -", "salva"])

    def test_eixo_que_troca_de_lado_sem_passar_pelo_zero(self):
        self.toque([tecla(FN, 1), hat(-1), "sleep 0.03", hat(1), "sleep 0.03", hat(0), tecla(FN, 0)])
        self.assertEqual(self.chamadas(), ["ajusta +", "salva", "ajusta -", "salva"])

    def test_segurar_repete(self):
        self.leitor([tecla(FN, 1), tecla(DPAD_CIMA, 1), "sleep 0.65", tecla(DPAD_CIMA, 0), tecla(FN, 0)])
        c = self.assert_ajusta_e_salva("+")
        self.assertGreaterEqual(len(c) - 1, 4, c)

    def test_segurar_repete_no_eixo(self):
        self.leitor([tecla(FN, 1), hat(1), "sleep 0.65", hat(0), tecla(FN, 0)])
        c = self.assert_ajusta_e_salva("-")
        self.assertGreaterEqual(len(c) - 1, 4, c)

    def test_soltar_a_seta_para_a_repeticao(self):
        self.leitor([tecla(FN, 1), tecla(DPAD_CIMA, 1), "sleep 0.35", tecla(DPAD_CIMA, 0), "sleep 0.5",
                     tecla(FN, 0)])
        c = self.assert_ajusta_e_salva("+")
        # 0,35 s a 0,1 s por passo: o primeiro e mais uns 3, nunca os 8 de 0,85 s
        self.assertLessEqual(len(c) - 1, 6, c)

    def test_dpad_sem_fn_nao_age(self):
        self.leitor([tecla(DPAD_CIMA, 1), "sleep 0.3", tecla(DPAD_CIMA, 0), hat(1), "sleep 0.2", hat(0),
                     tecla(TECLA_BAIXO, 1), tecla(TECLA_BAIXO, 0)])
        self.assertEqual(self.chamadas(), [])

    def test_seta_antes_do_fn_nao_age(self):
        self.leitor([tecla(DPAD_CIMA, 1), tecla(FN, 1), "sleep 0.3", tecla(DPAD_CIMA, 0), tecla(FN, 0)])
        self.assertEqual(self.chamadas(), [])

    def test_fn_sem_remapeamento_nao_age(self):
        fn_fabrica = (464, "KEY_FN")
        self.leitor([tecla(fn_fabrica, 1), tecla(DPAD_CIMA, 1), "sleep 0.2", tecla(DPAD_CIMA, 0),
                     tecla(fn_fabrica, 0)])
        self.assertEqual(self.chamadas(), [])

    def test_fn_l3_chama_padrao_uma_vez_por_clique(self):
        self.leitor([tecla(FN, 1), tecla(L3, 1), "sleep 0.3", tecla(L3, 0), tecla(L3, 1), tecla(L3, 0),
                     tecla(FN, 0)])
        c = self.chamadas()
        self.assertEqual(c, ["padrao", "padrao", "salva"], c)

    def test_l3_segurado_nao_repete(self):
        self.leitor([tecla(FN, 1), tecla(L3, 1), "sleep 0.6", tecla(L3, 0), tecla(FN, 0)])
        c = self.chamadas()
        self.assertEqual(c.count("padrao"), 1, c)
        self.assertEqual(c, ["padrao", "salva"], c)

    def test_l3_sem_o_fn_nao_age(self):
        self.leitor([tecla(L3, 1), "sleep 0.2", tecla(L3, 0)])
        self.assertEqual(self.chamadas(), [])

    def test_l3_apertado_antes_do_fn_nao_age(self):
        self.leitor([tecla(L3, 1), tecla(FN, 1), "sleep 0.2", tecla(L3, 0), tecla(FN, 0)])
        self.assertEqual(self.chamadas(), [])

    def test_l3_com_o_dpad_como_eixo(self):
        self.leitor([tecla(FN, 1), hat(1), "sleep 0.05", hat(0), tecla(L3, 1), tecla(L3, 0), tecla(FN, 0)],
                    R36_BRILHO_REPETE="0.5")
        c = self.chamadas()
        self.assertEqual(c.count("padrao"), 1, c)
        self.assertEqual(c[-1], "salva", c)

    def test_l3_para_a_repeticao_e_a_seta_apertada_nao_volta(self):
        self.leitor([tecla(FN, 1), tecla(DPAD_CIMA, 1), "sleep 0.25", tecla(L3, 1), tecla(L3, 0), "sleep 0.5",
                     tecla(DPAD_CIMA, 0), tecla(FN, 0)])
        c = self.chamadas()
        self.assertEqual(c.count("padrao"), 1, c)
        # nada de ajusta depois do padrao, mesmo com a seta ainda apertada
        self.assertNotIn("ajusta +", c[c.index("padrao") + 1:], c)

    def test_r3_nao_reseta(self):
        self.leitor([tecla(FN, 1), tecla(R3, 1), tecla(R3, 0), tecla(FN, 0)])
        self.assertEqual(self.chamadas(), [])

    def test_soltar_o_fn_interrompe(self):
        self.leitor([tecla(FN, 1), tecla(DPAD_CIMA, 1), "sleep 0.35", tecla(FN, 0), "sleep 0.5",
                     tecla(DPAD_CIMA, 0)])
        c = self.assert_ajusta_e_salva("+")
        self.assertLessEqual(len(c) - 1, 6, c)

    def test_salva_so_ao_soltar(self):
        # enquanto a seta está apertada não há salva: o registro só tem ajustes até o fim
        self.leitor([tecla(FN, 1), tecla(DPAD_CIMA, 1), "sleep 0.45", tecla(DPAD_CIMA, 0), "sleep 0.3",
                     tecla(FN, 0)])
        c = self.assert_ajusta_e_salva("+")
        self.assertGreaterEqual(len(c) - 1, 3, c)

    def test_fim_dos_eventos_com_a_seta_apertada_para_e_salva(self):
        # o evtest acabou (dispositivo sumiu): a repetição para e o nível não se perde
        self.leitor([tecla(FN, 1), tecla(DPAD_CIMA, 1), "sleep 0.25"])
        antes = len(self.assert_ajusta_e_salva("+"))
        time.sleep(0.3)
        self.assertEqual(len(self.chamadas()), antes, "repetição sobreviveu ao leitor")

    def test_sem_dispositivo_sai_com_zero_depois_da_espera(self):
        escreve(self.root / "proc/bus/input/devices", DEVICES.split("\n\n")[0] + "\n")
        self.leitor([tecla(FN, 1), tecla(DPAD_CIMA, 1)], R36_BRILHO_ESPERA="1")
        self.assertFalse(self.evtest_arg.exists())
        self.assertEqual(self.chamadas(), [])

    def test_sem_proc_devices_sai_com_zero(self):
        (self.root / "proc/bus/input/devices").unlink()
        self.leitor([], R36_BRILHO_ESPERA="1")
        self.assertFalse(self.evtest_arg.exists())


class LeitorComAplica(LeitorCase):
    """O leitor com o brilho-aplica de verdade, e o r36-brilho.log sob a chave."""

    def setUp(self):
        super().setUp()
        escreve(self.root / LCDBL, "204\n")
        escreve(self.root / EMUCONF, "brightness.level=80\n")
        self.log = self.root / LOG

    def leitor(self, linhas, **extra):
        return super().leitor(linhas, R36_BRILHO_APLICA=str(APLICA), **extra)

    def toque_cima(self, cima=DPAD_CIMA):
        self.toque([tecla(FN, 1), tecla(cima, 1), "sleep 0.03", tecla(cima, 0), tecla(FN, 0)])

    def toque(self, linhas):
        return self.leitor(linhas, R36_BRILHO_REPETE="0.5")

    def test_sem_a_chave_ajusta_e_nao_cria_o_log(self):
        self.toque_cima()
        self.assertEqual((self.root / NIVEL).read_text(), "85\n")
        self.assertEqual(int((self.root / LCDBL).read_text()), escala(85))
        self.assertFalse(self.log.exists())

    def test_sem_a_chave_o_log_antigo_fica_intacto(self):
        escreve(self.log, "boot antigo\n")
        self.toque_cima()
        self.assertEqual(self.log.read_text(), "boot antigo\n")

    def test_com_a_chave_registra_dispositivo_eventos_e_nivel(self):
        escreve(self.root / DIAG, "")
        self.toque_cima()
        log = self.log.read_text()
        self.assertIn("dispositivo micro_gamepad em /dev/input/event2", log)
        self.assertIn("FN visto: BTN_MODE (botao)", log)
        self.assertIn("D-pad visto: BTN_DPAD_UP (botao)", log)
        self.assertIn("salva nivel=85", log)
        self.assertEqual((self.root / NIVEL).read_text(), "85\n")

    def test_com_a_chave_registra_o_eixo(self):
        escreve(self.root / DIAG, "")
        self.toque([tecla(FN, 1), hat(1), "sleep 0.03", hat(0), tecla(FN, 0)])
        log = self.log.read_text()
        self.assertIn("D-pad visto: ABS_HAT0Y (eixo)", log)
        self.assertIn("salva nivel=75", log)
        # cada forma entra uma vez só
        self.assertEqual(log.count("ABS_HAT0Y"), 1, log)

    def test_com_a_chave_registra_o_reset_por_fn_l3(self):
        escreve(self.root / DIAG, "")
        escreve(self.root / NIVEL, "30\n")
        self.leitor([tecla(FN, 1), tecla(L3, 1), tecla(L3, 0), tecla(L3, 1), tecla(L3, 0), tecla(FN, 0)])
        log = self.log.read_text()
        self.assertIn("padrao nivel=80", log)
        self.assertEqual(log.count("L3 visto: BTN_THUMBL (botao)"), 1, log)
        self.assertFalse((self.root / NIVEL).exists())
        self.assertEqual(int((self.root / LCDBL).read_text()), escala(80))

    def test_ajusta_repetido_nao_escreve_o_log_na_p1(self):
        escreve(self.root / DIAG, "")
        env = dict(os.environ, R36_ROOT=str(self.root))
        for _ in range(5):
            subprocess.run(["sh", str(APLICA), "ajusta", "+"], env=env, check=True)
        self.assertFalse(self.log.exists())
        self.assertEqual(int((self.root / LCDBL).read_text()), escala(100))

    def test_com_a_chave_registra_a_falta_do_dispositivo(self):
        escreve(self.root / DIAG, "")
        escreve(self.root / "proc/bus/input/devices", DEVICES.split("\n\n")[0] + "\n")
        self.leitor([])
        self.assertIn("sem micro_gamepad", self.log.read_text())

    def test_aplica_registra_o_nivel_com_a_chave(self):
        escreve(self.root / DIAG, "")
        escreve(self.root / NIVEL, "60\n")
        env = dict(os.environ, R36_ROOT=str(self.root))
        subprocess.run(["sh", str(APLICA), "aplica"], env=env, check=True)
        self.assertIn("aplica nivel=60 lcdbl=153", self.log.read_text())

    def test_aplica_sem_a_chave_nao_escreve_na_p1(self):
        escreve(self.root / NIVEL, "60\n")
        env = dict(os.environ, R36_ROOT=str(self.root))
        for args in (("aplica",), ("ajusta", "+"), ("salva",), ("padrao",)):
            subprocess.run(["sh", str(APLICA), *args], env=env, check=True)
        self.assertEqual(sorted(p.name for p in (self.root / "storage/roms").iterdir()), [])


class BrilhoUnits(UnitCase):
    def test_unit_do_boot(self):
        d = diretivas(F62 / "system" / UNITS / "r36-brilho.service")
        self.assertEqual(d["Type"], ["oneshot"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/brilho-aplica boot"])
        self.assertEqual(d["RemainAfterExit"], ["yes"])
        # 20 s de espera da p1, com folga
        self.assertGreaterEqual(int(d["TimeoutStartSec"][0]), 40)
        self.assertEqual(d["WantedBy"], ["emuelec.target"])
        # esperar o autostart, que espera o ES, trava o boot no splash; o script espera a p1
        self.assertNotIn("After", d)
        self.assertNotIn("Before", d)

    def test_unit_do_leitor(self):
        d = diretivas(F62 / "system" / UNITS / "r36-brilho-leitor.service")
        self.assertEqual(d["Type"], ["simple"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/brilho-leitor"])
        self.assertEqual(d["Nice"], ["10"])
        # se o evtest terminar, o atalho volta; RestartSec evita laço rápido (o script ainda
        # espera o dispositivo por conta própria)
        self.assertEqual(d["Restart"], ["always"])
        self.assertEqual(d["RestartSec"], ["5"])
        self.assertEqual(d["WantedBy"], ["emuelec.target"])
        self.assertNotIn("After", d)
        self.assertNotIn("Before", d)

    def test_nenhuma_unit_espera_o_autostart(self):
        units = list((F62 / "system" / UNITS).glob("*.service"))
        self.assertEqual(len(units), 2)
        for unit in units:
            for chave in ("After", "Before", "Requires", "BindsTo"):
                for valor in diretivas(unit).get(chave, []):
                    self.assertNotIn("emuelec-autostart", valor, unit)
                    self.assertNotIn("emustation", valor, unit)

    def test_links(self):
        self.assert_link(F62, "emuelec.target.wants", "r36-brilho.service")
        self.assert_link(F62, "emuelec.target.wants", "r36-brilho-leitor.service")

    def test_modos(self):
        for p in (F62 / "system" / UNITS).glob("*.service"):
            self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o644, p)
        self.assertEqual(stat.S_IMODE((F62 / "feature.toml").stat().st_mode), 0o644)


class BrilhoBoot(BrilhoCase):
    def test_boot_aplica_o_nivel_salvo(self):
        escreve(self.root / EMUCONF, "brightness.level=80\n")
        escreve(self.root / NIVEL, "35\n")
        self.ok("boot")
        self.assertEqual(self.lcdbl(), escala(35))
        self.assertEqual(self.nivel(), "35\n")
        self.assertEqual((self.root / EMUCONF).read_text(), "brightness.level=35\n")

    def test_boot_sem_nivel_salvo_usa_o_emuelec_conf(self):
        escreve(self.root / EMUCONF, "brightness.level=60\n")
        self.ok("boot")
        self.assertEqual(self.lcdbl(), escala(60))

    def test_chave_descarta_o_nivel_e_fica_em_80(self):
        escreve(self.root / NIVEL, "35\n")
        escreve(self.root / "storage/roms/r36-brilho-original", "")
        self.ok("boot")
        self.assertFalse((self.root / NIVEL).exists())
        self.assertEqual(self.lcdbl(), escala(80))
        # o ajuste continua funcionando depois
        self.ok("ajusta", "-")
        self.assertEqual(self.lcdbl(), escala(75))

    def test_sem_p1_trata_a_chave_como_ausente(self):
        escreve(self.root / NIVEL, "35\n")
        (self.root / "storage/roms").rmdir()
        inicio = time.monotonic()
        self.ok("boot", R36_BRILHO_ESPERA_P1="2")
        self.assertGreaterEqual(time.monotonic() - inicio, 2)
        self.assertEqual(self.lcdbl(), escala(35))
        self.assertEqual(self.nivel(), "35\n")

    def test_boot_registra_com_a_chave_de_diagnostico(self):
        escreve(self.root / DIAG, "")
        escreve(self.root / "storage/roms/r36-brilho-original", "")
        self.ok("boot")
        log = (self.root / LOG).read_text()
        self.assertIn("r36-brilho-original encontrado", log)
        self.assertIn("padrao nivel=80", log)

    def test_boot_sem_a_chave_de_diagnostico_nao_escreve_na_p1(self):
        escreve(self.root / "storage/roms/r36-brilho-original", "")
        self.ok("boot")
        self.assertEqual(sorted(p.name for p in (self.root / "storage/roms").iterdir()), ["r36-brilho-original"])


UDT_PWR = ROOT / "features" / "46-audio" / "system" / "usr" / "bin" / "udt_pwr_events.sh"
LINHA_ACORDAR = "[ -x /usr/lib/r36/brilho-aplica ] && /usr/lib/r36/brilho-aplica aplica  # R36: brilho salvo (feature 62)"


class BrilhoAoAcordar(unittest.TestCase):
    def test_udt_pwr_events_reaplica_o_brilho_ao_acordar(self):
        linhas = [l.strip() for l in UDT_PWR.read_text().splitlines()]
        self.assertEqual(sum("brilho-aplica" in l for l in linhas), 1)
        i = linhas.index(LINHA_ACORDAR)
        # no ramo de acordar, logo depois do restore do lcdbl pelo emuelec.conf
        lcdbl = linhas.index("echo $scaled_value  > /sys/devices/virtual/disp/disp/attr/lcdbl")
        self.assertEqual(i, lcdbl + 1)
        self.assertLess(linhas.index("system_sleeping=0"), i)


class BrilhoEsSyncTest(TempDirCase):
    def test_script_executavel(self):
        self.assertTrue(ES_SYNC.exists())
        self.assertEqual(stat.S_IMODE(ES_SYNC.stat().st_mode), 0o755)
        self.assertTrue(ES_SYNC.read_text().startswith("#!/usr/bin/env python3\n"))
        proc = subprocess.run(["python3", "-I", "-m", "py_compile", str(ES_SYNC)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_sincroniza_memoria_com_sucesso(self):
        proc_dir = self.tmp / "mock_proc"
        pid_dir = proc_dir / "1234"
        pid_dir.mkdir(parents=True)
        (pid_dir / "comm").write_text("emulationstation\n")

        mem_file = pid_dir / "mem"
        sysconf_addr = 0x1000
        root_node = 0x2000
        node_bright = 0x3000

        with open(mem_file, "wb") as f:
            f.seek(0x006f0f0c)
            f.write(struct.pack("<I", sysconf_addr))
            f.seek(sysconf_addr + 8)
            f.write(struct.pack("<I", root_node))

            # root_node ("emulator.default", esq=node_bright, dir=0)
            f.seek(root_node + 8)
            f.write(struct.pack("<IIII", node_bright, 0, root_node + 24, len(b"emulator.default")))
            f.seek(root_node + 24)
            f.write(b"emulator.default")

            # node_bright ("brightness.level", esq=0, dir=0, val="80")
            f.seek(node_bright + 8)
            f.write(struct.pack("<IIII", 0, 0, node_bright + 24, len(b"brightness.level")))
            f.seek(node_bright + 24)
            f.write(b"brightness.level")
            f.seek(node_bright + 40)
            f.write(struct.pack("<II", node_bright + 48, 2))
            f.seek(node_bright + 48)
            f.write(b"80\x00")

        env = dict(os.environ, R36_PROC=str(proc_dir), R36_ROOT=str(self.tmp))
        res = subprocess.run(["python3", "-I", str(ES_SYNC), "45"], env=env, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)

        with open(mem_file, "rb") as f:
            f.seek(node_bright + 40)
            val_ptr, val_len = struct.unpack("<II", f.read(8))
            f.seek(val_ptr)
            val = f.read(val_len)
            self.assertEqual(val, b"45")
            self.assertEqual(val_len, 2)
            self.assertEqual(val_ptr, node_bright + 48)

    def test_processo_ausente_sai_com_zero(self):
        proc_dir = self.tmp / "mock_proc"
        proc_dir.mkdir(parents=True)
        env = dict(os.environ, R36_PROC=str(proc_dir), R36_ROOT=str(self.tmp))
        res = subprocess.run(["python3", "-I", str(ES_SYNC), "75"], env=env, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)



if __name__ == "__main__":
    unittest.main()
