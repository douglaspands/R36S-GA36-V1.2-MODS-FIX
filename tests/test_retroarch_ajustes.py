"""Testes da feature de ajustes do RetroArch (56-retroarch-ajustes)."""

import os
import stat
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

from context import ROOT

FEATURE_DIR = ROOT / "features" / "56-retroarch-ajustes"
LIB = FEATURE_DIR / "system" / "usr" / "lib" / "r36"
SHADERSET = LIB / "shaderset-aplica"
PREPARA = LIB / "retroarch-prepara"
SERVICE_DIR = FEATURE_DIR / "system" / "usr" / "lib" / "systemd" / "system"

CFG_FABRICA = (
    'audio_driver = "sdl2"\n'
    'log_dir = "/logs"\n'
    'osk_overlay_directory = "/overlays/keyboards"\n'
    'rgui_config_directory = "/config"\n'
    'savefile_directory = "/saves"\n'
    'video_shader_dir = "~/shaders"\n'
    'video_threaded = "true"\n'
)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.ra = self.root / "storage" / ".config" / "retroarch"
        self.ra.mkdir(parents=True)
        self.cfg = self.ra / "retroarch.cfg"
        self.conf = self.root / "storage" / ".config" / "emuelec" / "configs" / "emuelec.conf"
        self.conf.parent.mkdir(parents=True)
        self.roms = self.root / "storage" / "roms"
        self.roms.mkdir(parents=True)

    def roda(self, script, *args):
        proc = subprocess.run(
            ["sh", str(script), *args], capture_output=True, text=True,
            env={"PATH": os.environ["PATH"], "R36_ROOT": str(self.root)},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc


class TestFeature(unittest.TestCase):
    def test_descriptor(self):
        dados = tomllib.loads((FEATURE_DIR / "feature.toml").read_text(encoding="utf-8"))
        self.assertEqual(dados["schema"], 1)
        self.assertEqual(dados["order"], 56)
        self.assertTrue(dados["enabled"])

    def test_scripts_executaveis_e_validos(self):
        for script in (SHADERSET, PREPARA):
            self.assertEqual(oct(stat.S_IMODE(script.stat().st_mode)), oct(0o755), script.name)
            subprocess.run(["sh", "-n", str(script)], check=True)

    def test_servico_e_link(self):
        unit = (SERVICE_DIR / "r36-retroarch-prepara.service").read_text(encoding="utf-8")
        self.assertIn("Type=oneshot", unit)
        self.assertIn("Before=emustation.service", unit)
        self.assertIn("ExecStart=/usr/lib/r36/retroarch-prepara", unit)
        self.assertIn("WantedBy=emuelec.target", unit)
        # After=emuelec-autostart.service trava o boot no splash
        sem_comentarios = "".join(l for l in unit.splitlines(True) if not l.startswith("#"))
        self.assertNotIn("emuelec-autostart", sem_comentarios)
        link = SERVICE_DIR / "emuelec.target.wants" / "r36-retroarch-prepara.service"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(link), "../r36-retroarch-prepara.service")


class TestShadersetAplica(Base):
    def setUp(self):
        super().setUp()
        self.cfg.write_text(CFG_FABRICA, encoding="utf-8")

    def conf_com(self, *linhas):
        self.conf.write_text("".join(l + "\n" for l in linhas), encoding="utf-8")

    def aplica(self, sistema="snes", rom="/storage/roms/snes/Jogo.sfc"):
        self.roda(SHADERSET, sistema, rom)
        return self.cfg.read_text(encoding="utf-8")

    def test_preset_por_sistema(self):
        self.conf_com("snes.shaderset=crt/crt-easymode.glslp")
        txt = self.aplica()
        self.assertIn('video_shader = "/tmp/shaders/crt/crt-easymode.glslp"\n', txt)
        self.assertIn('video_shader_enable = "true"\n', txt)
        self.assertIn('video_shader_dir = "~/shaders"\n', txt)  # não confunde com video_shader

    def test_imprime_o_set_shader_so_para_um_caminho(self):
        # o RetroArch 1.17 não carrega o video_shader do cfg; o preset entra por --set-shader
        self.conf_com("snes.shaderset=crt/CRT Royale Mini.glslp")
        saida = self.roda(SHADERSET, "snes", "/storage/roms/snes/Jogo.sfc").stdout
        self.assertEqual(saida, '--set-shader "/tmp/shaders/crt/CRT Royale Mini.glslp"\n')
        for valor in ("none", "false", "0", "", "true", "1"):
            self.conf_com(f"snes.shaderset={valor}")
            self.assertEqual(self.roda(SHADERSET, "snes", "/x/Jogo.sfc").stdout, "", valor)

    def test_jogo_vence_sistema_e_sistema_vence_global(self):
        self.conf_com(
            "global.shaderset=g.glslp",
            "snes.shaderset=s.glslp",
            'snes["Jogo.sfc"].shaderset=j.glslp',
        )
        self.assertIn('"/tmp/shaders/j.glslp"', self.aplica())
        self.assertIn('"/tmp/shaders/s.glslp"', self.aplica(rom="/x/Outro.sfc"))
        self.assertIn('"/tmp/shaders/g.glslp"', self.aplica(sistema="nes", rom="/x/a.nes"))

    def test_sem_shader_apaga_o_do_jogo_anterior(self):
        for valor in ("none", "false", "0", ""):
            self.cfg.write_text(CFG_FABRICA + 'video_shader = "/tmp/shaders/x.glslp"\nvideo_shader_enable = "true"\n')
            self.conf_com(f"snes.shaderset={valor}")
            txt = self.aplica()
            self.assertEqual(txt, CFG_FABRICA, valor)
        # ausência de escolha
        self.cfg.write_text(CFG_FABRICA + 'video_shader = "/tmp/shaders/x.glslp"\nvideo_shader_enable = "true"\n')
        self.conf_com("nes.shaderset=a.glslp")
        self.assertEqual(self.aplica(), CFG_FABRICA)

    def test_true_e_um_ficam_com_o_setsettings(self):
        for valor in ("true", "1"):
            self.conf_com(f"snes.shaderset={valor}")
            self.assertEqual(self.aplica(), CFG_FABRICA, valor)

    def test_nome_com_espaco(self):
        self.conf_com("snes.shaderset=crt/CRT Royale Mini.glslp")
        self.assertIn('video_shader = "/tmp/shaders/crt/CRT Royale Mini.glslp"\n', self.aplica())

    def test_padrao_do_gba(self):
        self.conf_com("gba.shaderset=gba/gba-modern-remaster.glslp")
        txt = self.aplica("GBA", "/storage/roms/gba/Jogo.gba")
        self.assertIn('video_shader = "/tmp/shaders/gba/gba-modern-remaster.glslp"\n', txt)
        self.assertIn('video_shader_enable = "true"\n', txt)

    def test_sem_retroarch_cfg_ou_emuelec_conf(self):
        self.cfg.unlink()
        self.conf_com("snes.shaderset=a.glslp")
        self.roda(SHADERSET, "snes", "/x/a.sfc")
        self.assertFalse(self.cfg.exists())
        self.cfg.write_text(CFG_FABRICA)
        self.conf.unlink()
        self.assertEqual(self.aplica(), CFG_FABRICA)

    def test_log_so_com_a_chave(self):
        self.conf_com("gba.shaderset=gba/x.glslp")
        log = self.roms / "r36-shader-gba.log"
        self.aplica("gba", "/x/a.gba")
        self.assertFalse(log.exists())
        (self.roms / "r36-diagnostico").touch()
        self.aplica("gba", "/x/a.gba")
        self.aplica("gba", "/x/b.gba")
        linhas = log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(linhas), 2)
        self.assertIn("sistema=gba rom=b.gba shaderset=gba/x.glslp -> video_shader=/tmp/shaders/gba/x.glslp", linhas[1])


class TestRetroarchPrepara(Base):
    def prepara(self):
        self.roda(PREPARA)

    def valores(self):
        return {l.split(" = ")[0]: l.split(" = ")[1].strip('"') for l in self.cfg.read_text().splitlines()}

    def test_troca_os_quatro_valores(self):
        self.cfg.write_text(CFG_FABRICA)
        self.prepara()
        v = self.valores()
        self.assertEqual(v["rgui_config_directory"], "~/.config/retroarch/config")
        self.assertEqual(v["savefile_directory"], "~/savefiles")
        self.assertEqual(v["log_dir"], "~/.config/emuelec/logs")
        self.assertEqual(v["osk_overlay_directory"], "~/overlays/keyboards")
        # as demais linhas ficam como estavam
        self.assertEqual(v["audio_driver"], "sdl2")
        self.assertEqual(v["video_threaded"], "true")
        self.assertEqual(len(self.cfg.read_text().splitlines()), len(CFG_FABRICA.splitlines()))

    def test_valor_diferente_do_de_fabrica_fica(self):
        self.cfg.write_text(CFG_FABRICA.replace('"/saves"', '"/storage/meus-saves"'))
        self.prepara()
        v = self.valores()
        self.assertEqual(v["savefile_directory"], "/storage/meus-saves")
        self.assertEqual(v["rgui_config_directory"], "~/.config/retroarch/config")

    def test_segunda_execucao_nao_muda_nada(self):
        self.cfg.write_text(CFG_FABRICA)
        self.prepara()
        antes = self.cfg.read_bytes()
        self.prepara()
        self.assertEqual(self.cfg.read_bytes(), antes)

    def test_sem_retroarch_cfg(self):
        self.prepara()  # roda() confere o código de saída 0
        self.assertFalse(self.cfg.exists())

    def opt(self):
        return self.ra / "config" / "gpSP" / "gpSP.opt"

    def test_gpsp_opt_criado(self):
        self.prepara()
        self.assertEqual(self.opt().read_text(), 'gpsp_boot_mode = "bios"\ngpsp_frame_mixing = "enabled"\n')

    def test_gpsp_opt_acrescentado_com_e_sem_quebra_de_linha(self):
        self.opt().parent.mkdir(parents=True)
        for conteudo in ('gpsp_bios = "auto"\n', 'gpsp_bios = "auto"'):
            self.opt().write_text(conteudo)
            self.prepara()
            self.assertEqual(self.opt().read_text(), 'gpsp_bios = "auto"\ngpsp_boot_mode = "bios"\ngpsp_frame_mixing = "enabled"\n')

    def test_gpsp_opt_com_a_chave_e_preservado(self):
        self.opt().parent.mkdir(parents=True)
        conteudo = 'gpsp_frame_mixing = "disabled"\ngpsp_bios = "auto"\ngpsp_boot_mode = "game"\n'
        self.opt().write_text(conteudo)
        self.prepara()
        self.assertEqual(self.opt().read_text(), conteudo)

    def test_chave_sem_ghost_remove_so_a_linha_e_ela_nao_volta(self):
        self.opt().parent.mkdir(parents=True)
        self.opt().write_text('gpsp_bios = "auto"\ngpsp_frame_mixing = "enabled"\n')
        (self.roms / "r36-gpsp-sem-ghost").touch()
        esperado = 'gpsp_bios = "auto"\ngpsp_boot_mode = "bios"\n'
        self.prepara()
        self.assertEqual(self.opt().read_text(), esperado)
        self.prepara()
        self.assertEqual(self.opt().read_text(), esperado)

    def test_chave_sem_ghost_nao_liga_o_blending_nem_toca_em_disabled(self):
        (self.roms / "r36-gpsp-sem-ghost").touch()
        self.prepara()
        self.assertEqual(self.opt().read_text(), 'gpsp_boot_mode = "bios"\n')
        self.opt().write_text('gpsp_frame_mixing = "disabled"\n')
        self.prepara()
        self.assertEqual(self.opt().read_text(), 'gpsp_frame_mixing = "disabled"\ngpsp_boot_mode = "bios"\n')

    def test_log_so_com_a_chave(self):
        self.cfg.write_text(CFG_FABRICA)
        log = self.roms / "r36-retroarch.log"
        self.prepara()
        self.assertFalse(log.exists())
        self.cfg.write_text(CFG_FABRICA)
        (self.roms / "r36-diagnostico").touch()
        self.prepara()
        txt = log.read_text(encoding="utf-8")
        self.assertIn("rgui_config_directory trocada de /config para ~/.config/retroarch/config", txt)
        self.assertIn('savefile_directory = "~/savefiles"', txt)


# --- limita-consumo-e-miniaturas-savestate ---

# chave: (valor do retroarch.cfg de fábrica na p8, valor novo)
TROCAS_NOVAS = {
    "sort_savestates_enable": ("true", "false"),
    "wifi_enabled": ("true", "false"),
    "wifi_driver": ("connmanctl", "null"),
    "bluetooth_driver": ("bluetoothctl", "null"),
    "microphone_driver": ("alsathread", "null"),
    "midi_driver": ("alsa", "null"),
    "menu_show_rewind": ("true", "false"),
    "menu_show_online_updater": ("true", "false"),
    "quick_menu_show_download_thumbnails": ("true", "false"),
    "quick_menu_show_start_recording": ("true", "false"),
    "quick_menu_show_start_streaming": ("true", "false"),
    "settings_show_network": ("true", "false"),
    "settings_show_achievements": ("true", "false"),
    "settings_show_ai_service": ("true", "false"),
}
CFG_FABRICA_COMPLETO = CFG_FABRICA + "".join(
    f'{k} = "{velho}"\n' for k, (velho, _) in TROCAS_NOVAS.items()
) + 'savestate_thumbnail_enable = "true"\n'
RACFG_F10 = ROOT / "features" / "10-ptbr-sao-paulo" / "storage" / ".config" / "retroarch" / "retroarch.cfg"


def trocas_do_prepara():
    """[(chave, de, para)] das chamadas troca do retroarch-prepara."""
    out = []
    for linha in PREPARA.read_text(encoding="utf-8").splitlines():
        partes = linha.split()
        if partes[:1] == ["troca"] and len(partes) == 4:
            out.append(tuple(p.strip("'\"") for p in partes[1:]))
    return out


class TestRetroarchPreparaEnxuto(Base):
    prepara = TestRetroarchPrepara.prepara
    valores = TestRetroarchPrepara.valores

    def test_troca_drivers_menus_e_savestates(self):
        self.cfg.write_text(CFG_FABRICA_COMPLETO)
        self.prepara()
        v = self.valores()
        for k, (_, novo) in TROCAS_NOVAS.items():
            self.assertEqual(v[k], novo, k)
        self.assertEqual(v["savestate_thumbnail_enable"], "true")
        self.assertEqual(v["rgui_config_directory"], "~/.config/retroarch/config")
        self.assertEqual(len(self.cfg.read_text().splitlines()), len(CFG_FABRICA_COMPLETO.splitlines()))

    def test_segunda_execucao_com_as_chaves_novas_nao_muda_nada(self):
        self.cfg.write_text(CFG_FABRICA_COMPLETO)
        self.prepara()
        antes = self.cfg.read_bytes()
        self.prepara()
        self.assertEqual(self.cfg.read_bytes(), antes)

    def test_valor_escolhido_pelo_usuario_fica(self):
        self.cfg.write_text(CFG_FABRICA_COMPLETO.replace('microphone_driver = "alsathread"', 'microphone_driver = "sdl2"')
                            .replace('menu_show_rewind = "true"', 'menu_show_rewind = "false"'))
        self.prepara()
        v = self.valores()
        self.assertEqual(v["microphone_driver"], "sdl2")
        self.assertEqual(v["menu_show_rewind"], "false")
        self.assertEqual(v["midi_driver"], "null")

    def test_trocas_batem_com_o_retroarch_cfg_da_feature_10(self):
        # cartão novo (feature 10) e cartão com --keep-storage (prepara) terminam iguais
        f10 = {}
        for linha in RACFG_F10.read_text(encoding="utf-8").splitlines():
            if " = " in linha and not linha.startswith("#"):
                k, v = linha.split(" = ", 1)
                f10[k] = v.strip('"')
        trocas = {k: (de, para) for k, de, para in trocas_do_prepara()}
        for k, (velho, novo) in TROCAS_NOVAS.items():
            self.assertEqual(trocas.get(k), (velho, novo), k)
        for k, (_, para) in trocas.items():
            self.assertEqual(f10[k], para, k)
        self.assertEqual(f10["savestate_thumbnail_enable"], "true")


class TestMigraSavestates(Base):
    def setUp(self):
        super().setUp()
        self.saves = self.roms / "savestates"

    def poe(self, rel, conteudo):
        p = self.saves / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(conteudo)
        return p

    def foto(self):
        return {str(p.relative_to(self.saves)): p.read_bytes() for p in self.saves.rglob("*") if p.is_file()}

    def test_cria_a_pasta_de_savestates(self):
        self.roda(PREPARA)
        self.assertTrue(self.saves.is_dir())

    def test_move_state_e_miniatura_da_subpasta_do_core(self):
        self.poe("gba/gpSP/Jogo.state", b"s0")
        self.poe("gba/gpSP/Jogo.state.png", b"p0")
        self.poe("gba/gpSP/Jogo.state1", b"s1")
        self.poe("gba/gpSP/Jogo.state.auto", b"a")
        self.roda(PREPARA)
        self.assertEqual(self.foto(), {"gba/Jogo.state": b"s0", "gba/Jogo.state.png": b"p0",
                                       "gba/Jogo.state1": b"s1", "gba/Jogo.state.auto": b"a"})
        self.assertFalse((self.saves / "gba" / "gpSP").exists())  # subpasta vazia sai

    def test_nao_sobrescreve_o_que_ja_esta_na_pasta_do_sistema(self):
        self.poe("gba/Jogo.state", b"novo")
        self.poe("gba/gpSP/Jogo.state", b"velho")
        self.poe("gba/gpSP/Jogo.state.png", b"png")
        self.roda(PREPARA)
        self.assertEqual(self.foto(), {"gba/Jogo.state": b"novo", "gba/Jogo.state.png": b"png",
                                       "gba/gpSP/Jogo.state": b"velho"})

    def test_nomes_com_espaco_e_acento(self):
        self.poe("snes/Snes9x 2005 Plus/Jogo - Ação (BR).state2", b"s")
        self.poe("snes/Snes9x 2005 Plus/Jogo - Ação (BR).state2.png", b"p")
        self.roda(PREPARA)
        self.assertEqual(self.foto(), {"snes/Jogo - Ação (BR).state2": b"s",
                                       "snes/Jogo - Ação (BR).state2.png": b"p"})

    def test_segunda_execucao_nao_muda_nada(self):
        self.poe("gba/Jogo.state", b"novo")
        self.poe("gba/gpSP/Jogo.state", b"velho")
        self.poe("nes/FCEUmm/Outro.state", b"o")
        self.roda(PREPARA)
        antes = self.foto()
        self.roda(PREPARA)
        self.assertEqual(self.foto(), antes)

    def test_nao_mexe_no_que_nao_e_save_state(self):
        self.poe("gba/gpSP/Jogo.srm", b"x")
        self.poe("gba/Jogo.state", b"s")
        (self.saves / "gba" / "Vazia").mkdir()
        self.roda(PREPARA)
        self.assertEqual(self.foto(), {"gba/gpSP/Jogo.srm": b"x", "gba/Jogo.state": b"s"})
        self.assertTrue((self.saves / "gba" / "Vazia").is_dir())

    def test_sem_p1_montada_nao_cria_nada(self):
        self.roms.rmdir()
        self.roda(PREPARA)
        self.assertFalse(self.roms.exists())

    def test_log_so_com_a_chave(self):
        self.poe("gba/gpSP/Jogo.state", b"s")
        (self.roms / "r36-diagnostico").touch()
        self.roda(PREPARA)
        txt = (self.roms / "r36-retroarch.log").read_text(encoding="utf-8")
        self.assertIn("savestates: gba/gpSP/Jogo.state movido para gba/Jogo.state", txt)


if __name__ == "__main__":
    unittest.main()
