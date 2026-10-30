"""Interação dos scripts de boot das changes integradas (A, B, C e D) sobre um mesmo R36_ROOT.

Roda em sequência retroarch-prepara, shaderset-aplica, idioma-aplica (feature 56),
shader-gba-prepara (54), shader-gb-gbc-prepara (55) e brilho-aplica aplica (62), duas vezes,
sobre um cartão de fábrica simulado: retroarch.cfg e emuelec.conf da feature 10 (com as chaves
de A voltadas ao valor da base) e as cópias do SYSTEM e da p8 dos shaders.

Fora do teste (precisa do aparelho ou de root): bind mount de /tmp/shaders, mountpoint da p1
e o /sys real (R36_ROOT não vazio pula o bind e trata a p1 como montada se a pasta existir).
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from context import ROOT

F10 = ROOT / "features" / "10-ptbr-sao-paulo"
F54 = ROOT / "features" / "54-shaders-gba"
F55 = ROOT / "features" / "55-shaders-gb-gbc"
F56 = ROOT / "features" / "56-retroarch-ajustes"
F62 = ROOT / "features" / "62-brilho-fn"

SCRIPTS = {
    "retroarch-prepara": F56 / "system/usr/lib/r36/retroarch-prepara",
    "shaderset-aplica": F56 / "system/usr/lib/r36/shaderset-aplica",
    "idioma-aplica": F56 / "system/usr/lib/r36/idioma-aplica",
    "shader-gba-prepara": F54 / "system/usr/lib/r36/shader-gba-prepara",
    "shader-gb-gbc-prepara": F55 / "system/usr/lib/r36/shader-gb-gbc-prepara",
    "brilho-aplica": F62 / "system/usr/lib/r36/brilho-aplica",
}

# Chaves de A: valor da base (de fábrica) -> valor que o retroarch-prepara deve deixar.
CHAVES_A = {
    "rgui_config_directory": ("/config", "~/.config/retroarch/config"),
    "savefile_directory": ("/saves", "~/savefiles"),
    "log_dir": ("/logs", "~/.config/emuelec/logs"),
    "osk_overlay_directory": ("/overlays/keyboards", "~/overlays/keyboards"),
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

CORES_GBA = ("gpSP", "mGBA", "VBA-M", "VBA Next")
CORES_GB = ("Gambatte", "Gearboy", "SameBoy", "TGB Dual", "mGBA", "VBA-M", "VBA Next")
REF_GBA = '#reference "/usr/share/common-shaders/gba/gba-modern-remaster.glslp"\n'
REF_GB = '#reference "/usr/share/common-shaders/gb/gb-modern-dmg.glslp"\n'
REF_GBC = '#reference "/usr/share/common-shaders/gbc/gbc-modern-remaster.glslp"\n'
LCDBL = "sys/devices/virtual/disp/disp/attr/lcdbl"
NIVEL = "storage/.config/emuelec/configs/r36-brilho.level"
ATUAL = "run/r36-brilho.atual"
# brilho-aplica regrava o lcdbl e o /run a cada chamada (o nível é reaplicado, por projeto);
# nenhum dos dois é o SD.
SO_RUNTIME = {LCDBL, ATUAL}


def valor(texto, chave):
    achadas = re.findall(rf'^{re.escape(chave)} = "([^"]*)"$', texto, re.MULTILINE)
    assert len(achadas) == 1, (chave, achadas)
    return achadas[0]


class TestIntegracao3Changes(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        r = self.root
        self.ra = r / "storage/.config/retroarch"
        self.cfg = self.ra / "retroarch.cfg"
        self.conf = r / "storage/.config/emuelec/configs/emuelec.conf"
        self.roms = r / "storage/roms"
        for d in (self.ra, self.conf.parent, self.roms, r / "storage/.config/emulationstation",
                  r / "run", (r / LCDBL).parent):
            d.mkdir(parents=True, exist_ok=True)

        # retroarch.cfg da feature 10 com as chaves de A de volta ao valor da base
        texto = (F10 / "storage/.config/retroarch/retroarch.cfg").read_text(encoding="utf-8")
        for chave, (fabrica, atual) in CHAVES_A.items():
            texto, n = re.subn(rf'^{chave} = "{re.escape(atual)}"$', f'{chave} = "{fabrica}"', texto, flags=re.M)
            self.assertEqual(n, 1, chave)
        texto, n = re.subn(r'^user_language = "\d+"$', 'user_language = "0"', texto, flags=re.M)
        self.assertEqual(n, 1)
        self.cfg.write_text(texto, encoding="utf-8")
        shutil.copy(F10 / "storage/.config/emuelec/configs/emuelec.conf", self.conf)
        shutil.copy(F10 / "storage/.config/emulationstation/es_settings.cfg",
                    r / "storage/.config/emulationstation/es_settings.cfg")
        (r / LCDBL).write_text("0\n", encoding="utf-8")

        # shaders do SYSTEM e a cópia da p8 (rsync --ignore-existing do autostart)
        for f, arqs in ((F54, "gba"), (F55, "gb"), (F55, "gbc")):
            origem = f / "system/usr/share/common-shaders" / arqs
            for sub in ("usr/share/common-shaders", "storage/shaders"):
                shutil.copytree(origem, r / sub / arqs)

        self.env = {"PATH": os.environ["PATH"], "R36_ROOT": str(r)}
        self.assertEqual(self.conf.read_text(encoding="utf-8").splitlines().count("system.language=pt_BR"), 1)

    # --- execução e fotografia do cartão ---
    def roda(self, nome, *args):
        proc = subprocess.run(["sh", str(SCRIPTS[nome]), *args], env=self.env, capture_output=True,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, (nome, proc.stdout, proc.stderr))
        self.assertEqual(proc.stderr, "", nome)
        return proc.stdout

    def sequencia(self):
        """Um boot e um jogo de um sistema sem shaderset (nes)."""
        self.roda("retroarch-prepara")
        self.roda("shaderset-aplica", "nes", "/storage/roms/nes/jogo.nes")
        self.roda("idioma-aplica")
        self.roda("shader-gba-prepara")
        self.roda("shader-gb-gbc-prepara")
        self.roda("brilho-aplica", "aplica")

    def foto(self):
        """caminho relativo -> (conteúdo, mtime_ns) de todo arquivo do R36_ROOT."""
        f = {}
        for p in self.root.rglob("*"):
            if p.is_file():
                f[str(p.relative_to(self.root))] = (p.read_bytes(), p.stat().st_mtime_ns)
        return f

    def congela_mtimes(self):
        for p in self.root.rglob("*"):
            if p.is_file():
                os.utime(p, ns=(946684800 * 10**9, 946684800 * 10**9))

    def texto(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")

    def preset_esperado(self, base, core, nome, ref):
        p = self.root / "storage/.config/retroarch" / base / core / nome if base else self.ra / core / nome
        self.assertEqual(p.read_text(encoding="utf-8"), ref, str(p))

    # --- cenários ---
    def test_primeira_rodada_resultado_esperado(self):
        self.sequencia()
        cfg = self.cfg.read_text(encoding="utf-8")
        # A: todas as chaves no valor novo, uma linha cada, e nada de shader/idioma de B/C no lugar
        for chave, (_, novo) in CHAVES_A.items():
            self.assertEqual(valor(cfg, chave), novo, chave)
        # B: user_language coerente com system.language=pt_BR
        self.assertEqual(valor(cfg, "user_language"), "7")
        self.assertEqual(self.texto("storage/.config/retroarch/r36-idioma"), "pt_BR\npt_BR\n")
        # nes sem shaderset: sem linhas de shader no cfg
        self.assertNotIn("\nvideo_shader =", cfg)
        self.assertNotIn("video_shader_enable", cfg)
        # gpSP.opt (A)
        opt = self.texto("storage/.config/retroarch/config/gpSP/gpSP.opt")
        self.assertIn('gpsp_boot_mode = "bios"\n', opt)
        self.assertIn('gpsp_frame_mixing = "enabled"\n', opt)

        # emuelec.conf: as três chaves de shaderset, uma vez cada; idioma intocado
        conf = self.conf.read_text(encoding="utf-8")
        for linha in ("gba.shaderset=gba/gba-modern-remaster.glslp",
                      "gb.shaderset=gb/gb-modern-dmg.glslp",
                      "gbc.shaderset=gbc/gbc-modern-remaster.glslp"):
            self.assertEqual(conf.splitlines().count(linha), 1, linha)
        self.assertEqual(conf.splitlines().count("system.language=pt_BR"), 1)

        # presets de GBA (por core) e de GB/GBC (por pasta de conteúdo), em config/ e na pasta do cfg
        for core in CORES_GBA:
            self.preset_esperado("config", core, f"{core}.glslp", REF_GBA)
            self.preset_esperado(None, core, f"{core}.glslp", REF_GBA)
        for core in CORES_GB:
            for nome, ref in (("gb.glslp", REF_GB), ("gbc.glslp", REF_GBC)):
                self.preset_esperado("config", core, nome, ref)
                self.preset_esperado(None, core, nome, ref)
        # sem colisão: mGBA/VBA têm os dois tipos de preset, cada um com a própria referência
        for core in ("mGBA", "VBA-M", "VBA Next"):
            nomes = sorted(p.name for p in (self.ra / core).glob("*.glslp"))
            self.assertEqual(nomes, sorted([f"{core}.glslp", "gb.glslp", "gbc.glslp"]), core)
        # opções do Gambatte por pasta de conteúdo
        self.assertIn('gambatte_gb_colorization = "disabled"', self.texto("storage/.config/retroarch/config/Gambatte/gb.opt"))
        self.assertIn('gambatte_gbc_color_correction = "disabled"', self.texto("storage/.config/retroarch/config/Gambatte/gbc.opt"))

        # D: lcdbl = (80*255+50)/100 = 204, nível em uso 80, nenhum r36-brilho.level criado
        self.assertEqual(self.texto(LCDBL), "204\n")
        self.assertEqual(self.texto(ATUAL), "80\n")
        self.assertFalse((self.root / NIVEL).exists())

    def test_segunda_rodada_idempotente(self):
        self.sequencia()
        antes = self.foto()
        self.congela_mtimes()
        congeladas = {k: (c, self.root.joinpath(k).stat().st_mtime_ns) for k, (c, _) in antes.items()}

        # segunda rodada, passo a passo: só o shaderset-aplica (reescreve o retroarch.cfg com o
        # mesmo conteúdo, a cada jogo) e o brilho-aplica (lcdbl e /run) podem tocar arquivos
        passos = (
            ("retroarch-prepara", ()),
            ("shaderset-aplica", ("nes", "/storage/roms/nes/jogo.nes")),
            ("idioma-aplica", ()),
            ("shader-gba-prepara", ()),
            ("shader-gb-gbc-prepara", ()),
            ("brilho-aplica", ("aplica",)),
        )
        tocados = {}
        anterior = congeladas
        for nome, args in passos:
            self.roda(nome, *args)
            agora = {k: (c, m) for k, (c, m) in self.foto().items()}
            self.assertEqual(set(agora), set(anterior), f"{nome}: arquivos criados ou apagados")
            tocados[nome] = {k for k in agora if agora[k][1] != anterior[k][1]}
            anterior = agora

        for nome in ("retroarch-prepara", "idioma-aplica", "shader-gba-prepara", "shader-gb-gbc-prepara"):
            self.assertEqual(tocados[nome], set(), f"{nome} escreveu na segunda rodada")
        self.assertLessEqual(tocados["shaderset-aplica"], {"storage/.config/retroarch/retroarch.cfg"})
        self.assertEqual(tocados["brilho-aplica"], SO_RUNTIME)

        # conteúdo: idêntico em tudo
        final = self.foto()
        for k, (conteudo, _) in antes.items():
            self.assertEqual(final[k][0], conteudo, k)

    def test_brilho_nao_toca_no_retroarch_cfg(self):
        self.sequencia()
        cfg_antes = self.cfg.read_bytes()
        mtime = self.cfg.stat().st_mtime_ns
        (self.root / NIVEL).write_text("55\n", encoding="utf-8")
        self.roda("brilho-aplica", "aplica")
        self.assertEqual(self.texto(LCDBL), "140\n")  # (55*255+50)/100
        self.assertEqual(self.texto(ATUAL), "55\n")
        self.assertEqual(self.cfg.read_bytes(), cfg_antes)
        self.assertEqual(self.cfg.stat().st_mtime_ns, mtime)
        self.assertEqual(self.texto(NIVEL), "55\n")

    def test_idioma_acompanha_troca_sem_desfazer_o_resto(self):
        self.sequencia()
        texto = self.conf.read_text(encoding="utf-8").replace("system.language=pt_BR", "system.language=fr_FR")
        self.conf.write_text(texto, encoding="utf-8")
        self.sequencia()
        self.assertEqual(valor(self.cfg.read_text(encoding="utf-8"), "user_language"), "2")
        cfg = self.cfg.read_text(encoding="utf-8")
        for chave, (_, novo) in CHAVES_A.items():
            self.assertEqual(valor(cfg, chave), novo, chave)
        conf = self.conf.read_text(encoding="utf-8")
        self.assertEqual(conf.splitlines().count("gba.shaderset=gba/gba-modern-remaster.glslp"), 1)

    def test_shaderset_de_gba_com_os_presets_e_o_idioma(self):
        """No jogo de GBA: shaderset-aplica põe o shader no cfg e o idioma-aplica não o desfaz."""
        self.sequencia()
        saida = self.roda("shaderset-aplica", "gba", "/storage/roms/gba/jogo.gba")
        self.assertEqual(saida, '--set-shader "/tmp/shaders/gba/gba-modern-remaster.glslp"\n')
        self.roda("idioma-aplica")
        cfg = self.cfg.read_text(encoding="utf-8")
        self.assertEqual(valor(cfg, "video_shader"), "/tmp/shaders/gba/gba-modern-remaster.glslp")
        self.assertEqual(valor(cfg, "video_shader_enable"), "true")
        self.assertEqual(valor(cfg, "user_language"), "7")
        for chave, (_, novo) in CHAVES_A.items():
            self.assertEqual(valor(cfg, chave), novo, chave)
        # o preset apontado existe na p8 (bind em /tmp/shaders) e os dois de GB/GBC também
        for arq in ("gba/gba-modern-remaster.glslp", "gb/gb-modern-dmg.glslp", "gbc/gbc-modern-remaster.glslp"):
            self.assertTrue((self.root / "storage/shaders" / arq).is_file(), arq)
        # um jogo de GB depois limpa as linhas de shader do jogo anterior e usa o do próprio sistema
        saida = self.roda("shaderset-aplica", "gb", "/storage/roms/gb/jogo.gb")
        self.assertEqual(saida, '--set-shader "/tmp/shaders/gb/gb-modern-dmg.glslp"\n')
        cfg = self.cfg.read_text(encoding="utf-8")
        self.assertEqual(valor(cfg, "video_shader"), "/tmp/shaders/gb/gb-modern-dmg.glslp")

    def test_servicos_gba_e_gb_nao_apagam_o_que_o_outro_criou(self):
        """Ordem invertida e chave de desligar de um sistema: os presets dos outros ficam."""
        self.roda("shader-gb-gbc-prepara")
        self.roda("shader-gba-prepara")
        (self.roms / "r36-gba-sem-shader").write_text("")
        self.roda("shader-gba-prepara")
        self.roda("shader-gb-gbc-prepara")
        for core in CORES_GB:
            self.preset_esperado("config", core, "gb.glslp", REF_GB)
            self.preset_esperado(None, core, "gbc.glslp", REF_GBC)
        for core in CORES_GBA:
            for base in ("config", None):
                p = (self.ra / base / core if base else self.ra / core) / f"{core}.glslp"
                self.assertFalse(p.exists(), str(p))
        conf = self.conf.read_text(encoding="utf-8")
        self.assertNotIn("gba.shaderset=", conf)
        self.assertIn("gb.shaderset=gb/gb-modern-dmg.glslp", conf)
        self.assertIn("gbc.shaderset=gbc/gbc-modern-remaster.glslp", conf)
        # desligar o GB não mexe no GBA recriado
        os.remove(self.roms / "r36-gba-sem-shader")
        (self.roms / "r36-gb-sem-shader").write_text("")
        self.roda("shader-gba-prepara")
        self.roda("shader-gb-gbc-prepara")
        for core in CORES_GBA:
            self.preset_esperado("config", core, f"{core}.glslp", REF_GBA)
        for core in CORES_GB:
            self.assertFalse((self.ra / core / "gb.glslp").exists(), core)
            self.preset_esperado(None, core, "gbc.glslp", REF_GBC)


if __name__ == "__main__":
    unittest.main()
