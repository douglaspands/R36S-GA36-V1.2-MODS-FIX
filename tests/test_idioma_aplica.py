"""Testes do idioma-aplica (56-retroarch-ajustes): o menu do RetroArch segue o idioma do EmuELEC."""

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from context import ROOT

SCRIPT = ROOT / "features" / "56-retroarch-ajustes" / "system" / "usr" / "lib" / "r36" / "idioma-aplica"
RUNEMU = ROOT / "features" / "10-ptbr-sao-paulo" / "system" / "usr" / "bin" / "emuelecRunEmu.sh"

TABELA = {"pt_BR": "7", "pt_PT": "8", "en_US": "0", "en_GB": "0",
          "es_ES": "3", "fr_FR": "2", "de_DE": "4", "it_IT": "5"}

CFG_RESTO = 'menu_driver = "rgui"\nvideo_threaded = "true"\n'


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.ra = self.root / "storage" / ".config" / "retroarch"
        self.ra.mkdir(parents=True)
        self.cfg = self.ra / "retroarch.cfg"
        self.estado = self.ra / "r36-idioma"
        self.conf = self.root / "storage" / ".config" / "emuelec" / "configs" / "emuelec.conf"
        self.conf.parent.mkdir(parents=True)
        self.es = self.root / "storage" / ".config" / "emulationstation" / "es_settings.cfg"
        self.es.parent.mkdir(parents=True)
        self.roms = self.root / "storage" / "roms"
        self.roms.mkdir(parents=True)
        self.log = self.roms / "r36-idioma.log"
        self.path = os.environ["PATH"]

    def idioma_emuelec(self, codigo, extra="\r"):
        self.conf.write_text(f"# system.language=fr_FR\nsystem.hostname=EMUELEC\nsystem.language={codigo}{extra}\n"
                             "global.maxperf=0\n", encoding="utf-8")

    def ra_com(self, numero):
        self.cfg.write_text(f'{CFG_RESTO}user_language = "{numero}"\nvideo_smooth = "false"\n', encoding="utf-8")

    def user_language(self):
        linhas = [l for l in self.cfg.read_text(encoding="utf-8").splitlines() if l.startswith("user_language")]
        self.assertEqual(len(linhas), 1, linhas)
        return linhas[0].split('"')[1]

    def estado_par(self):
        linhas = self.estado.read_text(encoding="utf-8").split("\n")
        self.assertEqual(linhas[2:], [""], linhas)  # exatamente duas linhas
        return tuple(linhas[:2])

    def estado_conf(self):
        return self.estado_par()[0]

    def roda(self):
        proc = subprocess.run(["sh", str(SCRIPT)], capture_output=True, text=True,
                              env={"PATH": self.path, "R36_ROOT": str(self.root)})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")  # o emuelecRunEmu.sh não usa a saída
        return proc


class TestScript(unittest.TestCase):
    def test_executavel_e_valido(self):
        self.assertEqual(oct(stat.S_IMODE(SCRIPT.stat().st_mode)), oct(0o755))
        subprocess.run(["sh", "-n", str(SCRIPT)], check=True)

    def test_chamada_no_runemu(self):
        txt = RUNEMU.read_text()
        self.assertEqual(txt.count("/usr/lib/r36/idioma-aplica"), 2)  # o [ -x ] e a chamada
        self.assertIn("if [ -x /usr/lib/r36/idioma-aplica ]; then\n    /usr/lib/r36/idioma-aplica\nfi\n", txt)
        chamada = txt.index("    /usr/lib/r36/idioma-aplica\n")
        # ao lado do shaderset-aplica, depois do setsettings.sh e antes do jogo
        self.assertLess(txt.index('/usr/lib/r36/shaderset-aplica "${PLATFORM}"'), chamada)
        self.assertLess(chamada, txt.index("if [[ ${SHADERSET} != 0 ]]"))
        self.assertLess(chamada, txt.index("eval ${RUNTHIS} >> ${EMUELECLOG}"))
        comentario = txt.index("# R36: o menu do RetroArch segue o idioma do EmuELEC")
        self.assertLess(txt.index('/usr/lib/r36/shaderset-aplica "${PLATFORM}"'), comentario)
        self.assertLess(comentario, chamada)


class TestIdiomaAplica(Base):
    def test_troca_pt_br_para_en_us_e_volta(self):
        self.idioma_emuelec("pt_BR")
        self.ra_com("7")
        self.estado.write_text("pt_BR\n")
        self.idioma_emuelec("en_US")
        self.roda()
        self.assertEqual(self.user_language(), "0")
        self.assertEqual(self.estado_conf() + "\n", "en_US\n")
        self.idioma_emuelec("pt_BR")
        self.roda()
        self.assertEqual(self.user_language(), "7")
        self.assertEqual(self.estado_conf() + "\n", "pt_BR\n")
        # o resto do arquivo fica igual
        self.assertEqual(self.cfg.read_text(), f'{CFG_RESTO}user_language = "7"\nvideo_smooth = "false"\n')

    def test_cada_codigo_da_tabela(self):
        for codigo, numero in TABELA.items():
            with self.subTest(codigo=codigo):
                self.estado.unlink(missing_ok=True)
                self.ra_com("9")
                self.idioma_emuelec(codigo)
                self.roda()
                self.assertEqual(self.user_language(), numero)
                self.assertEqual(self.estado_conf() + "\n", codigo + "\n")

    def test_primeiro_jogo_acerta_cartao_que_manteve_a_p8(self):
        self.idioma_emuelec("pt_BR")
        self.ra_com("0")
        self.assertFalse(self.estado.exists())
        self.roda()
        self.assertEqual(self.user_language(), "7")
        self.assertEqual(self.estado_conf() + "\n", "pt_BR\n")

    def test_escolha_no_retroarch_dura_ate_trocar_no_emuelec(self):
        self.idioma_emuelec("pt_BR")
        self.ra_com("7")
        self.roda()
        self.ra_com("3")  # o usuário escolheu espanhol no menu do RetroArch
        self.roda()
        self.roda()
        self.assertEqual(self.user_language(), "3")
        self.idioma_emuelec("en_US")
        self.roda()
        self.assertEqual(self.user_language(), "0")

    def test_caminho_comum_nao_escreve_nem_chama_sed(self):
        self.idioma_emuelec("pt_BR")
        self.ra_com("3")
        self.estado.write_text("pt_BR\n")
        antigo = 1_000_000_000
        for f in (self.cfg, self.estado):
            os.utime(f, (antigo, antigo))
        falsos = self.root / "bin"
        falsos.mkdir()
        marca = self.root / "chamou"
        for prog in ("sed", "grep", "cat", "mv", "cp", "tr"):
            p = falsos / prog
            p.write_text(f'#!/bin/sh\necho {prog} >> "{marca}"\nexit 1\n')
            p.chmod(0o755)
        self.path = f"{falsos}:{self.path}"
        self.roda()
        self.assertFalse(marca.exists(), marca.read_text() if marca.exists() else "")
        for f in (self.cfg, self.estado):
            self.assertEqual(f.stat().st_mtime, antigo, f.name)
        self.assertEqual(self.user_language(), "3")

    def test_caminho_comum_sem_nenhum_processo_externo(self):
        # PATH com um diretório vazio: qualquer processo externo falharia com 127
        self.idioma_emuelec("pt_BR")
        self.es_com("pt_BR")
        self.ra_com("3")
        self.estado.write_text("pt_BR\npt_BR\n")
        antigo = 1_000_000_000
        for f in (self.cfg, self.estado):
            os.utime(f, (antigo, antigo))
        vazio = self.root / "vazio"
        vazio.mkdir()
        self.path = str(vazio)
        proc = subprocess.run(["/bin/sh", str(SCRIPT)], capture_output=True, text=True,
                              env={"PATH": self.path, "R36_ROOT": str(self.root)})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertEqual(proc.stderr, "")
        for f in (self.cfg, self.estado):
            self.assertEqual(f.stat().st_mtime, antigo, f.name)
        self.assertEqual(self.user_language(), "3")

    def test_estado_de_duas_linhas_sem_fim_de_linha(self):
        self.idioma_emuelec("pt_BR")
        self.es_com("pt_BR")  # o ES voltou de en_US para pt_BR
        self.estado.write_text("pt_BR\nen_US")
        self.ra_com("3")
        self.roda()
        self.assertEqual(self.user_language(), "7")
        self.assertEqual(self.estado_par(), ("pt_BR", "pt_BR"))

    def test_estado_de_uma_linha_sem_fim_de_linha(self):
        self.idioma_emuelec("pt_BR")
        self.es_com("pt_BR")
        self.estado.write_text("pt_BR")
        self.ra_com("3")
        antes = self.cfg.read_bytes()
        self.roda()  # vale para as duas fontes: nada mudou
        self.assertEqual(self.cfg.read_bytes(), antes)

    def test_ultima_linha_dos_arquivos_sem_fim_de_linha(self):
        self.conf.write_text("system.hostname=EMUELEC\nsystem.language=en_US")
        self.ra_com("7")
        self.roda()
        self.assertEqual(self.user_language(), "0")
        self.estado.unlink()
        self.conf.write_text("system.hostname=EMUELEC\n")
        self.es.write_text('\t<string name="Language" value="de_DE" />')
        self.roda()
        self.assertEqual(self.user_language(), "4")

    def test_idempotente(self):
        self.idioma_emuelec("fr_FR")
        self.ra_com("7")
        self.roda()
        depois = self.cfg.read_bytes()
        self.roda()
        self.assertEqual(self.cfg.read_bytes(), depois)
        self.assertEqual(self.user_language(), "2")

    def test_idioma_fora_da_tabela_nao_muda(self):
        self.ra_com("7")
        antes = self.cfg.read_bytes()
        for codigo in ("eu_ES", "tr_TR", "zh_CN"):
            with self.subTest(codigo=codigo):
                self.idioma_emuelec(codigo)
                self.roda()
                self.assertEqual(self.cfg.read_bytes(), antes)

    def test_volta_de_idioma_fora_da_tabela_conta_como_troca(self):
        self.idioma_emuelec("pt_BR")
        self.ra_com("7")
        self.roda()
        self.idioma_emuelec("eu_ES")
        self.roda()
        self.ra_com("3")  # escolha manual enquanto o EmuELEC estava em basco
        self.idioma_emuelec("pt_BR")
        self.roda()
        self.assertEqual(self.user_language(), "7")

    def test_emuelec_conf_ausente_ou_sem_idioma_nao_muda(self):
        self.ra_com("3")
        antes = self.cfg.read_bytes()
        self.roda()  # sem emuelec.conf nem es_settings.cfg
        self.assertEqual(self.cfg.read_bytes(), antes)
        self.conf.write_text("system.hostname=EMUELEC\n#system.language=en_US\n")
        self.roda()
        self.assertEqual(self.cfg.read_bytes(), antes)
        self.assertFalse(self.estado.exists())

    def es_com(self, codigo):
        self.es.write_text(f'<?xml version="1.0"?>\n<config>\n\t<string name="Language" value="{codigo}" />\n</config>\n')

    def test_es_settings_quando_o_emuelec_conf_nao_tem_idioma(self):
        self.conf.write_text("system.hostname=EMUELEC\n")
        self.es_com("de_DE")
        self.ra_com("7")
        self.roda()
        self.assertEqual(self.user_language(), "4")

    def test_so_o_es_settings_mudou(self):
        # o emuelec.conf sempre tem a chave (build e feature 10): a troca gravada só no ES vale
        self.idioma_emuelec("pt_BR")
        self.es_com("en_US")
        self.estado.write_text("pt_BR\npt_BR\n")
        self.ra_com("7")
        self.roda()
        self.assertEqual(self.user_language(), "0")
        self.assertEqual(self.estado_par(), ("pt_BR", "en_US"))

    def test_so_o_emuelec_conf_mudou(self):
        self.idioma_emuelec("es_ES")
        self.es_com("pt_BR")
        self.estado.write_text("pt_BR\npt_BR\n")
        self.ra_com("7")
        self.roda()
        self.assertEqual(self.user_language(), "3")
        self.assertEqual(self.estado_par(), ("es_ES", "pt_BR"))

    def test_ambos_mudaram_o_emuelec_conf_vence(self):
        self.idioma_emuelec("it_IT")
        self.es_com("de_DE")
        self.estado.write_text("pt_BR\npt_BR\n")
        self.ra_com("7")
        self.roda()
        self.assertEqual(self.user_language(), "5")
        self.assertEqual(self.estado_par(), ("it_IT", "de_DE"))

    def test_emuelec_conf_vence_o_es_settings_sem_estado(self):
        self.idioma_emuelec("it_IT")
        self.es_com("de_DE")
        self.ra_com("7")
        self.roda()
        self.assertEqual(self.user_language(), "5")
        self.assertEqual(self.estado_par(), ("it_IT", "de_DE"))

    def test_nenhum_mudou_nao_faz_nada(self):
        self.idioma_emuelec("pt_BR")
        self.es_com("pt_BR")
        self.estado.write_text("pt_BR\npt_BR\n")
        self.ra_com("3")
        antes = self.cfg.read_bytes()
        self.roda()
        self.assertEqual(self.cfg.read_bytes(), antes)
        self.assertEqual(self.estado_par(), ("pt_BR", "pt_BR"))

    def test_fontes_divergentes_nao_oscilam(self):
        # conf pt_BR, ES en_US, sem estado: só a primeira rodada escreve
        self.idioma_emuelec("pt_BR")
        self.es_com("en_US")
        self.ra_com("7")
        self.roda()
        self.assertEqual(self.user_language(), "7")
        self.assertEqual(self.estado_par(), ("pt_BR", "en_US"))
        antigo = 1_000_000_000
        for f in (self.cfg, self.estado):
            os.utime(f, (antigo, antigo))
        depois = self.cfg.read_bytes()
        for _ in range(4):
            self.roda()
            self.assertEqual(self.user_language(), "7")
            self.assertEqual(self.cfg.read_bytes(), depois)
            for f in (self.cfg, self.estado):
                self.assertEqual(f.stat().st_mtime, antigo, f.name)
        # a escolha manual no RetroArch dura
        self.ra_com("3")
        self.roda()
        self.roda()
        self.assertEqual(self.user_language(), "3")

    def test_ambos_mudaram_divergentes_nao_oscilam(self):
        self.idioma_emuelec("it_IT")
        self.es_com("de_DE")
        self.estado.write_text("pt_BR\npt_BR\n")
        self.ra_com("7")
        for _ in range(4):
            self.roda()
            self.assertEqual(self.user_language(), "5")
        self.assertEqual(self.estado_par(), ("it_IT", "de_DE"))

    def test_depois_de_divergir_trocar_so_o_es_aplica_uma_vez(self):
        self.idioma_emuelec("pt_BR")
        self.es_com("en_US")
        self.ra_com("7")
        self.roda()
        self.es_com("fr_FR")
        self.roda()
        self.assertEqual(self.user_language(), "2")
        self.ra_com("3")
        self.roda()
        self.roda()
        self.assertEqual(self.user_language(), "3")
        self.assertEqual(self.estado_par(), ("pt_BR", "fr_FR"))

    def test_estado_antigo_de_uma_linha(self):
        # r36-idioma de versão anterior: só o idioma aplicado, sem quebrar
        self.idioma_emuelec("pt_BR")
        self.es_com("pt_BR")
        self.estado.write_text("pt_BR\n")
        self.ra_com("3")
        antes = self.cfg.read_bytes()
        self.roda()  # nada mudou
        self.assertEqual(self.cfg.read_bytes(), antes)
        self.idioma_emuelec("en_US")
        self.roda()
        self.assertEqual(self.user_language(), "0")
        self.assertEqual(self.estado_par(), ("en_US", "pt_BR"))

    def test_espacos_e_cr_no_valor(self):
        self.conf.write_text("system.language= es_ES \r\n")
        self.ra_com("7")
        self.roda()
        self.assertEqual(self.user_language(), "3")

    def test_retroarch_cfg_ausente(self):
        self.idioma_emuelec("en_US")
        self.roda()
        self.assertFalse(self.cfg.exists())
        self.assertFalse(self.estado.exists())  # o primeiro jogo com o arquivo ainda acerta
        self.ra_com("7")
        self.roda()
        self.assertEqual(self.user_language(), "0")

    def test_retroarch_cfg_sem_a_linha_ganha_a_linha(self):
        self.idioma_emuelec("en_US")
        self.cfg.write_text(CFG_RESTO)
        self.roda()
        self.assertEqual(self.cfg.read_text(), CFG_RESTO + 'user_language = "0"\n')

    def test_retroarch_cfg_sem_fim_de_linha(self):
        self.idioma_emuelec("en_US")
        self.cfg.write_text('menu_driver = "rgui"')
        self.roda()
        self.assertEqual(self.cfg.read_text(), 'menu_driver = "rgui"\nuser_language = "0"\n')

    def test_sem_chave_de_diagnostico_sem_log(self):
        self.idioma_emuelec("en_US")
        self.ra_com("7")
        self.roda()
        self.roda()
        self.assertFalse(self.log.exists())
        self.assertEqual(sorted(p.name for p in self.roms.iterdir()), [])

    def test_com_chave_uma_linha_por_jogo(self):
        (self.roms / "r36-diagnostico").write_text("")
        self.idioma_emuelec("en_US")
        self.ra_com("7")
        self.roda()
        self.roda()
        self.idioma_emuelec("eu_ES")
        self.roda()
        linhas = self.log.read_text().splitlines()
        self.assertEqual(len(linhas), 3, linhas)
        self.assertIn("idioma-aplica idioma=en_US", linhas[0])
        self.assertIn("user_language=0", linhas[0])
        self.assertIn("mantido", linhas[1])
        self.assertIn("idioma=eu_ES", linhas[2])
        self.assertIn("sem tradução", linhas[2])


if __name__ == "__main__":
    unittest.main()
