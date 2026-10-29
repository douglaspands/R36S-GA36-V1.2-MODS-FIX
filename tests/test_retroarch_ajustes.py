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


if __name__ == "__main__":
    unittest.main()
