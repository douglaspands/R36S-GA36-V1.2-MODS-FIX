import difflib
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from context import CFG, ROOT, TempDirCase, needs_base
from r36img import mtools

F10 = ROOT / "features" / "10-ptbr-sao-paulo" / "storage" / ".config"
RUNEMU = ROOT / "features" / "10-ptbr-sao-paulo" / "system" / "usr" / "bin" / "emuelecRunEmu.sh"
F20 = ROOT / "features" / "20-controle-posicional" / "storage" / "joypads" / "micro_gamepad.cfg"


def parse_cfg(path):
    out = {}
    for line in path.read_text().splitlines():
        m = re.match(r'^\s*([\w.]+)\s*=\s*"?([^"]*)"?\s*$', line)
        if m and not line.lstrip().startswith("#"):
            out[m.group(1)] = m.group(2)
    return out


class PtBrSaoPaulo(unittest.TestCase):
    def test_emuelec_conf(self):
        c = parse_cfg(F10 / "emuelec" / "configs" / "emuelec.conf")
        self.assertEqual(c["system.language"], "pt_BR")
        self.assertEqual(c["system.timezone"], "America/Sao_Paulo")
        self.assertEqual(c["global.retroarch.menu_driver"], "rgui")
        self.assertEqual(c["global.ratio"], "core")
        self.assertEqual(c["gba.emulator"], "libretro")
        self.assertEqual(c["gba.core"], "gpsp")
        self.assertEqual(c["global.maxperf"], "0")
        self.assertEqual([k for k in c if k.endswith(".maxperf")], ["global.maxperf"])
        self.assertEqual(c["cps2.emulator"], "libretro")
        self.assertEqual(c["cps2.core"], "fbalpha2012")
        for k in ("cps1.core", "cps3.core", "fbn.core"):
            self.assertNotIn(k, c)
        self.assertEqual(c["snes.emulator"], "libretro")
        self.assertEqual(c["snes.core"], "snes9x2005_plus_a33")  # da 53-cores-a33 (test_cores_a33)
        for k in ("snesh.core", "snesmsu1.core"):
            self.assertNotIn(k, c)
        self.assertEqual(c["nes.emulator"], "libretro")
        self.assertEqual(c["nes.core"], "fceumm")
        self.assertNotIn("fds.core", c)

    def test_es_settings(self):
        txt = (F10 / "emulationstation" / "es_settings.cfg").read_text()
        self.assertIn('<string name="Language" value="pt_BR" />', txt)
        self.assertIn('<string name="FolderViewMode" value="never" />', txt)
        self.assertIn('<bool name="FavoritesFirst" value="true" />', txt)
        self.assertIn('<string name="ThemeSet" value="Epic Cody ML" />', txt)
        self.assertIn('<string name="ShowBattery" value="text" />', txt)


    def test_retroarch_cfg(self):
        c = parse_cfg(F10 / "retroarch" / "retroarch.cfg")
        self.assertEqual(c["user_language"], "7")  # português do Brasil: a criança lê o menu na própria língua
        c2 = parse_cfg(F10 / "emuelec" / "configs" / "emuelec.conf")
        self.assertEqual(c2["system.language"], "pt_BR")
        self.assertEqual(c["menu_driver"], "rgui")
        self.assertEqual(c["menu_swap_ok_cancel_buttons"], "false")

    def test_retroarch_cfg_padroes_de_aparencia_e_uso(self):
        c = parse_cfg(F10 / "retroarch" / "retroarch.cfg")
        self.assertEqual(c["custom_viewport_width"], "768")
        self.assertEqual(c["custom_viewport_height"], "672")
        self.assertEqual(c["rgui_aspect_ratio"], "11")
        self.assertEqual(c["menu_show_load_content_animation"], "false")
        self.assertEqual(c["notification_show_autoconfig"], "false")

    def test_retroarch_cfg_pastas_existem_e_sao_graveis(self):
        c = parse_cfg(F10 / "retroarch" / "retroarch.cfg")
        self.assertEqual(c["rgui_config_directory"], "~/.config/retroarch/config")
        self.assertEqual(c["savefile_directory"], "~/savefiles")
        self.assertEqual(c["log_dir"], "~/.config/emuelec/logs")
        self.assertEqual(c["osk_overlay_directory"], "~/overlays/keyboards")
        for chave, valor in c.items():
            if not re.search(r"_(directory|dir)$", chave) or chave == "recording_config_directory":
                continue
            if valor in ("", "default", "true", "false"):  # não são caminhos
                continue
            self.assertTrue(valor.startswith(("~", "/usr", "/tmp", "/storage")), f"{chave} = {valor}")
            self.assertNotRegex(valor, r"^/(config|saves|logs|overlays)\b", chave)


MICRO_GAMEPAD_CFG = '''input_device = "micro_gamepad"
input_driver = "sdl2"
input_vendor_id = "26989"
input_product_id = "24431"

input_gun_trigger_mbtn = "1"

input_b_btn = "1"
input_y_btn = "3"
input_a_btn = "0"
input_x_btn = "2"

input_up_btn = "13"
input_down_btn = "14"
input_left_btn = "15"
input_right_btn = "16"

input_select_btn = "8"
input_start_btn = "9"

input_l_btn = "4"
input_r_btn = "5"
input_l2_btn = "6"
input_r2_btn = "7"
input_l3_btn = "11"
input_r3_btn = "12"

input_l_x_minus_axis = "-0"
input_l_x_plus_axis = "+0"
input_l_y_minus_axis = "-1"
input_l_y_plus_axis = "+1"
input_r_x_minus_axis = "-2"
input_r_x_plus_axis = "+2"
input_r_y_minus_axis = "-3"
input_r_y_plus_axis = "+3"

input_enable_hotkey_btn = "8"
input_menu_toggle_btn = "2"
input_screenshot_btn = "3"
input_pause_toggle_btn = "1"
input_fps_toggle_btn = "0"
input_load_state_btn = "4"
input_save_state_btn = "5"
input_hold_slowmotion_btn = "6"
input_hold_fast_forward_btn = "7"
input_exit_emulator_btn = "9"
'''


class ControlePosicional(unittest.TestCase):
    def setUp(self):
        self.c = parse_cfg(F20)

    def test_driver_e_ids(self):
        self.assertEqual(self.c["input_driver"], "sdl2")
        self.assertEqual(self.c["input_vendor_id"], "26989")
        self.assertEqual(self.c["input_product_id"], "24431")

    def test_botoes_de_face(self):
        c = self.c
        self.assertEqual(
            (c["input_a_btn"], c["input_b_btn"], c["input_x_btn"], c["input_y_btn"]),
            ("0", "1", "2", "3"),
        )

    def test_hotkey_no_select(self):
        self.assertEqual(self.c["input_enable_hotkey_btn"], "8")

    def test_autoconfig_sem_bind_do_fn(self):
        # o FN vira o BTN_MODE no driver (feature 20, fn-remapeia), que grava o hotkey 10 no cfg
        # da p8 no boot; o arquivo da imagem não ganha bind novo e fica com o padrão seguro 8
        atual = F20.read_text()
        self.assertEqual(atual, MICRO_GAMEPAD_CFG)
        self.assertEqual(self.c["input_enable_hotkey_btn"], "8")
        self.assertEqual(self.c["input_menu_toggle_btn"], "2")

    def test_direcional_livre_de_atalhos(self):
        dpad = {f"input_{d}_btn" for d in ("up", "down", "left", "right")}
        for k, v in self.c.items():
            if k.endswith("_btn") and k not in dpad:
                self.assertNotIn(v, {"13", "14", "15", "16"}, k)


def bloco_maxperf(txt):
    i = txt.index("# R36: máximo desempenho")
    return txt[i:txt.index("\nfi\n", i) + 4]


class RunEmuMaxperf(TempDirCase):
    def roda(self, valor):
        """Executa só o bloco de escolha, com funções falsas; devolve a função chamada."""
        prog = (
            'get_ee_setting() { echo "$R36_VAL"; }\n'
            "maxperf() { echo maxperf; }\nnormperf() { echo normperf; }\n"
            'PLATFORM=gba; BASEROMNAME="a.zip"\n' + bloco_maxperf(RUNEMU.read_text())
        )
        return subprocess.run(
            ["bash", "-c", prog], check=True, capture_output=True, text=True,
            env=dict(os.environ, R36_VAL=valor),
        ).stdout.strip()

    def test_script_executavel_e_valido(self):
        self.assertTrue(os.access(RUNEMU, os.X_OK))
        subprocess.run(["bash", "-n", str(RUNEMU)], check=True)

    def test_shaderset_aplica_depois_do_setsettings_e_antes_do_jogo(self):
        txt = RUNEMU.read_text()
        chamada = txt.index('/usr/lib/r36/shaderset-aplica "${PLATFORM}" "${ROMNAME_SHADER}"')
        self.assertLess(txt.index('SHADERSET=$(setsettings.sh'), chamada)
        self.assertLess(chamada, txt.index("eval ${RUNTHIS} >> ${EMUELECLOG}"))
        self.assertIn("[ -x /usr/lib/r36/shaderset-aplica ]", txt)
        # a saída (--set-shader) entra no SHADERSET antes de ir para a linha do RetroArch
        self.assertIn('SHADERSET="${R36_SHADER}"', txt)
        self.assertLess(chamada, txt.index("if [[ ${SHADERSET} != 0 ]]"))

    def test_sem_maxperf_incondicional(self):
        linhas = [l.strip() for l in RUNEMU.read_text().splitlines()]
        antes = linhas[: linhas.index("# R36: máximo desempenho só quando a chave maxperf (jogo, sistema ou global) vale 1")]
        self.assertNotIn("maxperf", antes)

    def test_chave_um_liga(self):
        self.assertEqual(self.roda("1"), "maxperf")

    def test_chave_zero_vazia_ou_outra_desliga(self):
        for v in ("0", "", "2", "off"):
            self.assertEqual(self.roda(v), "normperf", v)

    @needs_base
    def test_so_difere_da_base_nos_pontos_esperados(self):
        sq = self.tmp / "SYSTEM"
        subprocess.run(
            ["mcopy", "-n", "-i", mtools.spec(CFG.base_path, CFG.part("system").offset), "::/SYSTEM", str(sq)],
            check=True, env=mtools.ENV, capture_output=True)
        base = subprocess.run(
            ["unsquashfs", "-cat", str(sq), "usr/bin/emuelecRunEmu.sh"],
            check=True, capture_output=True, text=True).stdout.splitlines()
        nova = RUNEMU.read_text().splitlines()
        mudou = [l for l in difflib.unified_diff(base, nova, lineterm="", n=0)
                 if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        self.assertEqual(
            [l for l in mudou if l.startswith("-")],
            [
                "-maxperf",
                "-mpv /storage/.config/splash/loading-game.png &",
                # parser de save state da base (esperava -state_slot antes de -autosave)
                '-if [[ "${arguments}" == *"-state_slot"* ]] && [[ "${arguments}" == *"-autosave"* ]]; then',
                '-    CONTROLLERCONFIG="${CONTROLLERCONFIG%% -state_slot*}"  # until -state is found',
                '-    SNAPSHOT="${arguments#*-state_slot *}" # -state_slot x -autosave 1',
                "-    SNAPSHOT=\"${SNAPSHOT%% -*}\"  # we don't need -autosave 1 we asume its always 1 if a state is loaded",
                "-else",
                '-    CONTROLLERCONFIG="${CONTROLLERCONFIG%% --*}"  # until a -- is found',
                '-    SNAPSHOT=""',
                "-fi",
                "-mpv /storage/.config/splash/loading-game.png",
            ],
        )
        # 17 + 2 linhas do audio-ganho por Speaker Function + 6 do shaderset-aplica
        # + 21 da limita-consumo-e-miniaturas-savestate (parser de save state, mkdir, guarda do netplay)
        # + 4 do idioma-aplica
        self.assertEqual(sum(1 for l in mudou if l.startswith("+")), 52)
        self.assertEqual(bloco_maxperf("\n".join(nova)).count("get_ee_setting maxperf"), 1)


# --- limita-consumo-e-miniaturas-savestate ---

def bloco_savestate(txt):
    """Do comentário do parser de save state até o mkdir da pasta do sistema."""
    i = txt.index("# R36: o ES manda o save state")
    fim = txt.index('mkdir -p "/storage/roms/savestates/${PLATFORM}"', i)
    return txt[i:txt.index("\n", fim) + 1]


def bloco_netplay(txt):
    i = txt.index("# R36: sem rede no R36S")
    return txt[i:txt.index("# End netplay\nfi\n", i) + len("# End netplay\nfi\n")]


CONTROLES = '-p1index 0 -p1guid 03000000 -p1name "micro_gamepad" -p1nbbuttons 17'
STATE_FILE = "/storage/roms/savestates/gba/Jogo Ação (BR).state2"


class EmuelecConfEnxuto(unittest.TestCase):
    def test_rede_atualizacao_e_rewind_desligados(self):
        c = parse_cfg(F10 / "emuelec" / "configs" / "emuelec.conf")
        for k in ("ee_ssh.enabled", "controllers.bluetooth.enabled", "updates.enabled",
                  "global.netplay", "global.rewind"):
            self.assertEqual(c[k], "0", k)


class RunEmuSaveState(unittest.TestCase):
    def roda(self, *extra, controles=CONTROLES):
        """Executa o parser como o RunEmu, com os argumentos separados como o ES os passa."""
        prog = (
            'mkdir() { echo "mkdir $*" >&2; }\n'
            'arguments="$@"\nPLATFORM="${arguments##*-P}"\nPLATFORM="${PLATFORM%% *}"\n'
            'CONTROLLERCONFIG="${arguments#*--controllers=*}"\n'
            + bloco_savestate(RUNEMU.read_text())
            + 'printf "%s\\n%s\\n" "${CONTROLLERCONFIG}" "${SNAPSHOT}"\n'
        )
        args = ["/storage/roms/gba/Jogo - Ação (BR).gba", "-Pgba", "--core=gpsp",
                "--emulator=libretro", f"--controllers={controles}", *extra]
        proc = subprocess.run(["bash", "-c", prog, "bash", *args],
                              check=True, capture_output=True, text=True)
        cc, snap = proc.stdout.split("\n")[:2]
        return cc, snap, proc.stderr

    def test_autosave_antes_do_state_slot(self):
        for auto in ("0", "1"):
            cc, snap, _ = self.roda("-autosave", auto, "-state_slot", "2", "-state_file", STATE_FILE)
            self.assertEqual(cc, CONTROLES, auto)
            self.assertEqual(snap, "2", auto)

    def test_slot_auto_so_com_autosave_1(self):
        # SNAPSHOT vazio faz o setsettings.sh desligar o savestate_auto_load; "0" o mantém
        cc, snap, _ = self.roda("-autosave", "1")
        self.assertEqual(cc, CONTROLES)
        self.assertEqual(snap, "0")

    def test_sem_save_state(self):
        cc, snap, _ = self.roda()
        self.assertEqual(cc, CONTROLES)
        self.assertEqual(snap, "")

    def test_ordem_antiga_continua_valendo(self):
        cc, snap, _ = self.roda("-state_slot", "5", "-autosave", "1")
        self.assertEqual((cc, snap), (CONTROLES, "5"))

    def test_corta_no_duplo_traco_do_netplay(self):
        cc, snap, _ = self.roda("--connect", "10.0.0.2", "--port", "55435", "--nick")
        self.assertEqual((cc, snap), (CONTROLES, ""))
        cc, snap, _ = self.roda("-autosave", "1", "-state_slot", "1", "--host", "--nick")
        self.assertEqual((cc, snap), (CONTROLES, "1"))

    def test_sem_controles(self):
        cc, snap, _ = self.roda("-autosave", "1", "-state_slot", "3", "-state_file", STATE_FILE, controles="")
        self.assertEqual((cc, snap), ("", "3"))

    def test_cria_a_pasta_do_sistema(self):
        _, _, err = self.roda()
        self.assertEqual(err, "mkdir -p /storage/roms/savestates/gba\n")

    def test_parser_no_ramo_libretro_antes_do_setsettings(self):
        txt = RUNEMU.read_text()
        i = txt.index("# R36: o ES manda o save state")
        self.assertLess(txt.index('elif [ ${LIBRETRO} == "yes" ]; then'), i)
        self.assertLess(i, txt.index("SHADERSET=$(setsettings.sh"))
        self.assertIn('--snapshot="${SNAPSHOT}"', txt)


class RunEmuNetplay(TempDirCase):
    def roda(self, *extra):
        """Executa o bloco de netplay com set_ee_setting falso; devolve as chamadas."""
        chamadas = self.tmp / "chamadas"
        prog = (
            f'set_ee_setting() {{ echo "$1=$2" >> "{chamadas}"; }}\n'
            'get_ee_setting() { echo; }\n'
            'arguments="$@"\nNETPLAY="No"\n'
            "RUNTHIS='${RABIN} ${VERBOSE} -L /storage/cores/${EMU}.so --config ${RACONF} \"${ROMNAME}\"'\n"
            + bloco_netplay(RUNEMU.read_text())
            + 'printf "%s\\n" "${NETPLAY}"\n'
        )
        args = ["/storage/roms/gba/Jogo.gba", "-Pgba", "--core=gpsp", "--emulator=libretro",
                f"--controllers={CONTROLES}", *extra]
        out = subprocess.run(["bash", "-c", prog, "bash", *args],
                             check=True, capture_output=True, text=True).stdout
        feitas = chamadas.read_text().splitlines() if chamadas.exists() else []
        chamadas.unlink(missing_ok=True)
        return feitas, out.strip()

    def test_jogo_local_nao_grava_no_emuelec_conf(self):
        for extra in ((), ("-autosave", "1"), ("-autosave", "1", "-state_slot", "2", "-state_file", STATE_FILE)):
            feitas, netplay = self.roda(*extra)
            self.assertEqual(feitas, [], extra)
            self.assertEqual(netplay, "No", extra)

    def test_netplay_continua_funcionando(self):
        feitas, netplay = self.roda("--connect", "10.0.0.2", "--port", "55435", "--nick")
        self.assertEqual(feitas[:3], ["netplay.server.ip=disable", "netplay.server.port=disable",
                                      "netplay.mode=disable"])
        self.assertIn("netplay.mode=client", feitas)
        self.assertIn("netplay.server.ip=10.0.0.2", feitas)
        self.assertIn("--connect", netplay)
        feitas, _ = self.roda("--host", "--nick")
        self.assertEqual(len(feitas), 3)
        feitas, _ = self.roda("--netplaymode", "spectator")
        self.assertIn("netplay.mode=spectator", feitas)

    def test_um_so_bloco_de_netplay(self):
        txt = RUNEMU.read_text()
        self.assertEqual(txt.count("# Netplay\n"), 1)
        self.assertEqual(txt.count('set_ee_setting "netplay.'), 7)
        bloco = bloco_netplay(txt)
        self.assertEqual(bloco.count('set_ee_setting "netplay.'), 7)


class RetroarchCfgEnxuto(unittest.TestCase):
    def setUp(self):
        self.c = parse_cfg(F10 / "retroarch" / "retroarch.cfg")

    def test_savestate_na_pasta_do_sistema_com_miniatura(self):
        self.assertEqual(self.c["sort_savestates_enable"], "false")
        self.assertEqual(self.c["savestate_thumbnail_enable"], "true")
        self.assertEqual(self.c["video_gpu_screenshot"], "false")  # glReadPixels trava quadros na Mali-400

    def test_sem_drivers_de_hardware_que_nao_existe(self):
        self.assertEqual(self.c["wifi_enabled"], "false")
        for k in ("wifi_driver", "bluetooth_driver", "microphone_driver", "midi_driver"):
            self.assertEqual(self.c[k], "null", k)

    def test_menus_de_rede_gravacao_e_rewind_ocultos(self):
        for k in ("menu_show_rewind", "menu_show_online_updater", "quick_menu_show_download_thumbnails",
                  "quick_menu_show_start_recording", "quick_menu_show_start_streaming",
                  "settings_show_network", "settings_show_achievements", "settings_show_ai_service"):
            self.assertEqual(self.c[k], "false", k)


class SnapshotZeroNoSetsettings(TempDirCase):
    """O ramo `snapshot` do setsettings.sh da base com SNAPSHOT="0" (o que o parser do RunEmu
    entrega para `-autosave 1` sem slot) tem de ligar o autosave e o autoload, como o SNAPSHOT
    vazio nunca faz. O script inteiro precisa de /etc/profile e de funções do sistema, então
    roda-se só o corpo do `case`."""

    @needs_base
    def setUp(self):
        super().setUp()
        sq = self.tmp / "SYSTEM"
        subprocess.run(
            ["mcopy", "-n", "-i", mtools.spec(CFG.base_path, CFG.part("system").offset), "::/SYSTEM", str(sq)],
            check=True, env=mtools.ENV, capture_output=True)
        self.sq = sq

    def ramo(self, snapshot):
        linhas = subprocess.run(
            ["unsquashfs", "-cat", str(self.sq), "usr/bin/setsettings.sh"], check=True, capture_output=True, text=True
        ).stdout.splitlines()
        ini = next(i for i, l in enumerate(linhas) if l.strip() == '"snapshot")')
        fim = next(i for i in range(ini, len(linhas)) if linhas[i].strip() == '"integerscale")')
        # o script usa ${RACONF} sem aspas: o caminho não pode ter espaço (o tmp do projeto tem)
        sem_espaco = Path(tempfile.mkdtemp(prefix="r36snap"))
        self.addCleanup(shutil.rmtree, sem_espaco, ignore_errors=True)
        cfg = sem_espaco / "retroarch.cfg"
        cfg.write_text('savestate_auto_save = "false"\nsavestate_auto_load = "false"\nstate_slot = "9"\nvideo_smooth = "true"\n')
        prog = f'RACONF="{cfg}"\nSNAPSHOT="{snapshot}"\nAUTOLOAD="false"\n' + "\n".join(linhas[ini + 1:fim - 1])
        subprocess.run(["bash", "-c", prog], check=True, capture_output=True, text=True)
        return parse_cfg(cfg)

    @needs_base
    def test_snapshot_0_liga_autosave_e_autoload_no_slot_0(self):
        c = self.ramo("0")
        self.assertEqual((c["savestate_auto_save"], c["savestate_auto_load"], c["state_slot"]), ("true", "true", "0"))
        self.assertEqual(c["video_smooth"], "true")

    @needs_base
    def test_snapshot_vazio_desliga_os_dois(self):
        c = self.ramo("")
        self.assertEqual((c["savestate_auto_save"], c["savestate_auto_load"], c["state_slot"]), ("false", "false", "0"))


if __name__ == "__main__":
    unittest.main()
