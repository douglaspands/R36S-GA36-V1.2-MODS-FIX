"""Testes da feature 66-recomp: sistema gba-recomp, lançador recomp.sh e perfil do gptokeyb."""

import os
import shutil
import stat
import subprocess
import time
import tomllib
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from context import ROOT, TempDirCase

FEATURE = ROOT / "features" / "66-recomp"
LAUNCHER = FEATURE / "system" / "usr" / "bin" / "recomp.sh"
GPTK = FEATURE / "system" / "usr" / "config" / "gptokeyb" / "recomp.gptk"
ES_SYSTEM = FEATURE / "system" / "usr" / "config" / "emulationstation" / "es_systems.cfg"
ES_STORAGE = FEATURE / "storage" / ".config" / "emulationstation" / "es_systems.cfg"
LEIAME = FEATURE / "roms" / "gba-recomp" / "LEIAME.txt"

NOME_PROCESSO = "r36-recomp-game"


def sistemas(cfg):
    return {s.findtext("name"): s for s in ET.fromstring(cfg.read_text(encoding="utf-8")).findall("system")}


class Feature(unittest.TestCase):
    def test_toml(self):
        t = tomllib.loads((FEATURE / "feature.toml").read_text(encoding="utf-8"))
        self.assertEqual((t["schema"], t["order"], t["enabled"]), (1, 66, True))
        alvos = {(o["layer"], o["path"], o["feature"]) for o in t["override"]}
        self.assertEqual(alvos, {
            ("system", "usr/config/emulationstation/es_systems.cfg", "64-love2d"),
            ("storage", ".config/emulationstation/es_systems.cfg", "64-love2d"),
        })

    def test_es_systems_duas_copias_iguais(self):
        self.assertTrue(ES_SYSTEM.is_file() and ES_STORAGE.is_file())
        self.assertEqual(ES_SYSTEM.read_bytes(), ES_STORAGE.read_bytes())

    def test_sistema_gba_recomp(self):
        for cfg in (ES_SYSTEM, ES_STORAGE):
            s = sistemas(cfg)["gba-recomp"]
            self.assertEqual(s.findtext("path"), "/storage/roms/gba-recomp")
            self.assertEqual(s.findtext("extension").split(), [".sh", ".SH"])
            self.assertEqual(s.findtext("theme"), "gba-recomp")
            comando = s.findtext("command")
            self.assertEqual(comando, '/usr/bin/recomp.sh "%ROM%" "%SYSTEM%"')
            self.assertNotIn("emuelecRunEmu", comando)
            self.assertNotIn("--core", comando)

    def test_nenhum_outro_recomp_nem_sistema_perdido(self):
        for cfg in (ES_SYSTEM, ES_STORAGE):
            nomes = sistemas(cfg)
            self.assertEqual([n for n in nomes if n.endswith("-recomp")], ["gba-recomp"])
            self.assertIn("love", nomes)
            self.assertIn("gba", nomes)
        # Só o gba-recomp foi acrescentado em relação ao es_systems.cfg da 64-love2d
        base = sistemas(ROOT / "features" / "64-love2d" / "system" / "usr" / "config" / "emulationstation" / "es_systems.cfg")
        self.assertEqual(set(sistemas(ES_SYSTEM)) - set(base), {"gba-recomp"})
        self.assertEqual(set(base) - set(sistemas(ES_SYSTEM)), set())

    def test_sem_es_input(self):
        # O FN segue sem bind no ES: a feature não traz es_input.cfg
        self.assertEqual(list(FEATURE.rglob("es_input.cfg")), [])

    def test_leiame_da_pasta_do_console(self):
        self.assertTrue(LEIAME.is_file())
        texto = LEIAME.read_text(encoding="utf-8")
        for termo in (".sh", "FN", "Start"):
            self.assertIn(termo, texto)
        # Três idiomas
        for termo in ("English", "Português", "Español"):
            self.assertIn(termo, texto)


class Perfil(unittest.TestCase):
    def test_perfil_so_com_atalhos_do_sistema(self):
        linhas = {
            ln.split("=")[0].strip(): ln.split("=")[1].strip()
            for ln in GPTK.read_text(encoding="utf-8").splitlines()
            if "=" in ln and not ln.lstrip().startswith("#")
        }
        self.assertEqual(linhas["hotkey"], "guide")
        self.assertEqual(linhas["start"], "enter")
        self.assertEqual(linhas["back"], "esc")
        self.assertEqual(linhas["guide"], "esc")
        # Zonas mortas iguais às do LÖVE
        love = ROOT / "features" / "64-love2d" / "system" / "usr" / "config" / "gptokeyb" / "love.gptk"
        for chave in ("deadzone_x", "deadzone_y", "deadzone_triggers"):
            self.assertIn(chave, linhas)
            self.assertIn(f"{chave} = {linhas[chave]}", love.read_text(encoding="utf-8"))
        # Nenhuma tecla de ação ou direcional injetada sobre os botões do jogo
        permitidas = {"hotkey", "start", "back", "guide", "deadzone_x", "deadzone_y", "deadzone_triggers"}
        self.assertEqual(set(linhas) - permitidas, set())


class Lancador(unittest.TestCase):
    def test_permissao_e_sintaxe(self):
        self.assertTrue(LAUNCHER.is_file())
        self.assertTrue(os.access(LAUNCHER, os.X_OK), "recomp.sh sem bit de execução")
        self.assertEqual(stat.S_IMODE(LAUNCHER.stat().st_mode) & 0o755, 0o755)
        subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)
        if shutil.which("shellcheck"):
            subprocess.run(["shellcheck", "-s", "bash", "-S", "error", str(LAUNCHER)], check=True)

    def test_nome_do_processo_tem_15_caracteres(self):
        self.assertEqual(len(NOME_PROCESSO), 15)
        self.assertIn(NOME_PROCESSO, LAUNCHER.read_text(encoding="utf-8"))


# Comandos falsos do aparelho, no PATH do teste.
GPTOKEYB_FALSO = """#!/bin/sh
echo "$@" > "$R36_TESTE/gptokeyb.args"
echo $$ > "$R36_TESTE/gptokeyb.pid"
exec sleep 30
"""
AMIXER_FALSO = """#!/bin/sh
echo "$@" >> "$R36_TESTE/amixer.log"
"""
GANHO_FALSO = """#!/bin/sh
echo "$@" >> "$R36_TESTE/ganho.log"
"""
LDD_FALSO = """#!/bin/sh
echo "	libfaltando.so.9 => not found"
"""
KILLALL_FALSO = """#!/bin/sh
echo "$@" >> "$R36_TESTE/killall.log"
"""


class Execucao(TempDirCase):
    """Roda o recomp.sh com R36_ROOT temporário, comandos falsos e ELFs do próprio PC."""

    def setUp(self):
        super().setUp()
        self.root = self.tmp / "raiz"
        self.teste = self.tmp / "teste"
        self.shim = self.tmp / "shim"
        for d in (self.root / "tmp", self.root / "usr" / "lib" / "r36", self.root / "usr" / "config" / "gptokeyb",
                  self.teste, self.shim):
            d.mkdir(parents=True)
        shutil.copy(GPTK, self.root / "usr" / "config" / "gptokeyb" / "recomp.gptk")
        self.comando("gptokeyb", GPTOKEYB_FALSO)
        self.comando("amixer", AMIXER_FALSO)
        self.comando("killall", KILLALL_FALSO)
        ganho = self.root / "usr" / "lib" / "r36" / "audio-ganho"
        ganho.write_text(GANHO_FALSO, encoding="utf-8")
        ganho.chmod(0o755)
        self.roms = self.root / "storage" / "roms"
        self.pasta = self.roms / "gba-recomp"
        self.pasta.mkdir(parents=True)

    def comando(self, nome, corpo):
        p = self.shim / nome
        p.write_text(corpo, encoding="utf-8")
        p.chmod(0o755)

    def elf(self, nome="Jogo.recomp", como="env"):
        """ELF do PC (env imprime o ambiente; false sai com 1), sem bit de execução como na FAT32."""
        destino = self.pasta / nome
        shutil.copyfile(shutil.which(como), destino)
        destino.chmod(0o755)
        return destino

    def roda(self, *args, env_extra=None):
        env = {
            "PATH": f"{self.shim}:{os.environ['PATH']}", "R36_ROOT": str(self.root),
            "R36_TESTE": str(self.teste), "HOME": str(self.tmp),
        }
        env.update(env_extra or {})
        return subprocess.run(["bash", str(LAUNCHER), *map(str, args)], capture_output=True, text=True, env=env, timeout=60)

    def log(self, pasta=None):
        return ((pasta or self.pasta) / "recomp.log").read_text(encoding="utf-8")

    # --- execução direta ---

    def test_executa_o_elf_direto_pelo_symlink(self):
        jogo = self.elf()
        r = self.roda(jogo, "gba-recomp")
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.log()
        # printenv-like: "_" traz o caminho usado no exec, com o nome fixo de 15 caracteres
        self.assertIn(f"_={self.root}/tmp/{NOME_PROCESSO}", log)
        self.assertIn(NOME_PROCESSO, log)
        self.assertFalse((self.root / "tmp" / NOME_PROCESSO).exists(), "symlink não foi removido")
        self.assertEqual(sorted(p.name for p in self.pasta.iterdir() if p.name != "recomp.log"), ["Jogo.recomp"])

    def test_log_traz_jogo_sistema_codigo_de_saida_e_ldd(self):
        jogo = self.elf()
        self.roda(jogo, "gba-recomp")
        log = self.log()
        self.assertIn(f"jogo: {jogo}", log)
        self.assertIn("sistema: gba-recomp", log)
        self.assertIn("ldd", log)
        self.assertIn("saída: 0", log)

    def test_sistema_deduzido_pela_pasta_quando_falta_o_segundo_argumento(self):
        jogo = self.elf()
        r = self.roda(jogo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("sistema: gba-recomp", self.log())

    def test_sistema_novo_usa_a_pasta_dele(self):
        outra = self.roms / "snes-recomp"
        outra.mkdir()
        destino = outra / "X.recomp"
        shutil.copyfile(shutil.which("env"), destino)
        destino.chmod(0o755)
        r = self.roda(destino, "snes-recomp")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("sistema: snes-recomp", (outra / "recomp.log").read_text(encoding="utf-8"))
        self.assertFalse((self.pasta / "recomp.log").exists())

    def test_sem_argumento_falha_com_uso(self):
        r = self.roda()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Uso:", r.stderr)

    def test_arquivo_que_nao_e_elf_registra_erro_e_sai_limpo(self):
        falso = self.pasta / "Falso.recomp"
        falso.write_text("isto não é um ELF\n", encoding="utf-8")
        r = self.roda(falso, "gba-recomp")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("não é um script", self.log())
        self.assertFalse((self.teste / "gptokeyb.args").exists(), "gptokeyb não deveria subir")
        self.assertFalse((self.root / "tmp" / NOME_PROCESSO).exists())

    # --- jogo em .sh (o caso do ES) ---

    def script(self, nome="Jogo.sh", corpo="#!/bin/bash\necho SCRIPT_RODOU:$0:$PWD\n"):
        """.sh sem bit de execução, como na FAT32."""
        destino = self.pasta / nome
        destino.write_text(corpo, encoding="utf-8")
        destino.chmod(0o644)
        return destino

    def test_script_roda_com_bash_sem_bit_de_execucao(self):
        jogo = self.script()
        r = self.roda(jogo, "gba-recomp")
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.log()
        self.assertIn("tipo: script", log)
        self.assertIn(f"SCRIPT_RODOU:{jogo}:{self.pasta}", log)
        self.assertIn("saída: 0", log)
        self.assertNotIn("--- ldd", log)
        self.assertFalse((self.root / "tmp" / NOME_PROCESSO).exists())

    def test_script_mata_o_elf_da_pasta_com_o_nome_dele_em_15_caracteres(self):
        jogo = self.script("Donkey Kong Country.sh")
        (self.pasta / "Donkey Kong Country").mkdir()
        shutil.copyfile(shutil.which("env"), self.pasta / "Donkey Kong Country" / "Donkey Kong Country.elf")
        self.roda(jogo, "gba-recomp")
        args = (self.teste / "gptokeyb.args").read_text(encoding="utf-8").strip()
        self.assertEqual(args, f"1 Donkey Kong Cou -c {self.root}/usr/config/gptokeyb/recomp.gptk -killsignal 15")
        self.assertIn("processo que o FN + Start encerra: Donkey Kong Cou", self.log())

    def test_binario_com_qualquer_extensao_e_achado_pela_assinatura(self):
        # O .sh decide como disparar o binário: o nome e a extensão dele não importam
        jogo = self.script()
        (self.pasta / "Jogo").mkdir()
        (self.pasta / "Jogo" / "dados.txt").write_text("texto", encoding="utf-8")
        shutil.copyfile(shutil.which("env"), self.pasta / "Jogo" / "libmotor.so.1")
        shutil.copyfile(shutil.which("env"), self.pasta / "Jogo" / "Motor.bin")
        self.roda(jogo, "gba-recomp")
        args = (self.teste / "gptokeyb.args").read_text(encoding="utf-8").strip()
        self.assertTrue(args.startswith("1 Motor.bin -c "), args)

    def test_binario_sem_extensao_ao_lado_do_script(self):
        jogo = self.script()
        shutil.copyfile(shutil.which("env"), self.pasta / "motor")
        self.roda(jogo, "gba-recomp")
        args = (self.teste / "gptokeyb.args").read_text(encoding="utf-8").strip()
        self.assertTrue(args.startswith("1 motor -c "), args)

    def test_so_biblioteca_e_texto_nao_contam_como_binario(self):
        jogo = self.script()
        shutil.copyfile(shutil.which("env"), self.pasta / "libx.so")
        (self.pasta / "gamelist.xml").write_text("<gameList/>", encoding="utf-8")
        self.roda(jogo, "gba-recomp")
        self.assertFalse((self.teste / "gptokeyb.args").exists())

    def test_script_sem_elf_roda_mas_avisa_que_fn_start_nao_encerra(self):
        jogo = self.script()
        r = self.roda(jogo, "gba-recomp")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.teste / "gptokeyb.args").exists())
        log = self.log()
        self.assertIn("nenhum binário ELF", log)
        self.assertIn("SCRIPT_RODOU", log)

    def test_script_com_falha_devolve_o_codigo(self):
        jogo = self.script(corpo="#!/bin/bash\nexit 7\n")
        r = self.roda(jogo, "gba-recomp")
        self.assertEqual(r.returncode, 7)
        self.assertIn("saída: 7", self.log())

    def test_codigo_de_saida_de_falha_vai_para_o_log(self):
        jogo = self.elf(como="false")
        r = self.roda(jogo, "gba-recomp")
        self.assertEqual(r.returncode, 1)
        self.assertIn("saída: 1", self.log())
        # O áudio volta ao estado do sistema mesmo com a falha
        self.assertEqual(len((self.teste / "ganho.log").read_text(encoding="utf-8").splitlines()), 2)

    def test_ldd_mostra_biblioteca_faltando(self):
        self.comando("ldd", LDD_FALSO)
        jogo = self.elf()
        self.roda(jogo, "gba-recomp")
        self.assertIn("libfaltando.so.9 => not found", self.log())

    # --- gptokeyb ---

    def test_gptokeyb_com_nome_fixo_perfil_e_sigterm(self):
        jogo = self.elf()
        self.roda(jogo, "gba-recomp")
        # O fake grava "$@" numa linha (o caminho do projeto tem espaços: compara o texto inteiro)
        args = (self.teste / "gptokeyb.args").read_text(encoding="utf-8").strip()
        self.assertEqual(args, f"1 {NOME_PROCESSO} -c {self.root}/usr/config/gptokeyb/recomp.gptk -killsignal 15")

    def test_sem_processo_sobrando(self):
        jogo = self.elf()
        self.roda(jogo, "gba-recomp")
        pid = int((self.teste / "gptokeyb.pid").read_text(encoding="utf-8"))
        for _ in range(30):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            self.fail("gptokeyb continuou vivo depois do lançador")

    def test_sem_perfil_nao_sobe_gptokeyb_com_teclas_padrao(self):
        (self.root / "usr" / "config" / "gptokeyb" / "recomp.gptk").unlink()
        jogo = self.elf()
        r = self.roda(jogo, "gba-recomp")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.teste / "gptokeyb.args").exists())
        self.assertIn("recomp.gptk", self.log())

    # --- áudio ---

    def test_audio_antes_e_depois_alto_falante(self):
        (self.root / "sys" / "class" / "switch" / "h2w").mkdir(parents=True)
        (self.root / "sys" / "class" / "switch" / "h2w" / "state").write_text("0\n", encoding="utf-8")
        jogo = self.elf()
        self.roda(jogo, "gba-recomp")
        amixer = (self.teste / "amixer.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(amixer), 2)
        self.assertTrue(all("Speaker Function" in ln for ln in amixer))
        self.assertEqual(len((self.teste / "ganho.log").read_text(encoding="utf-8").splitlines()), 2)
        self.assertTrue(all(ln.strip() == "aplica" for ln in (self.teste / "ganho.log").read_text(encoding="utf-8").splitlines()))

    def test_rota_do_fone(self):
        (self.root / "sys" / "class" / "switch" / "h2w").mkdir(parents=True)
        (self.root / "sys" / "class" / "switch" / "h2w" / "state").write_text("1\n", encoding="utf-8")
        jogo = self.elf()
        self.roda(jogo, "gba-recomp")
        amixer = (self.teste / "amixer.log").read_text(encoding="utf-8")
        self.assertIn("spk", amixer)
        self.assertNotIn("headset", amixer)

    # --- idioma ---

    def test_idioma_exportado(self):
        conf = self.root / "storage" / ".config" / "emuelec" / "configs"
        conf.mkdir(parents=True)
        (conf / "emuelec.conf").write_text("system.language=pt_BR\n", encoding="utf-8")
        jogo = self.elf()
        self.roda(jogo, "gba-recomp")
        log = self.log()
        for linha in ("CONSOLE_LANG=pt_BR", "CONSOLE_LANG_SHORT=pt", "LANG=pt_BR.UTF-8", "LANGUAGE=pt_BR"):
            self.assertIn(linha, log.splitlines())

    def test_idioma_padrao_en_us_e_es_settings(self):
        jogo = self.elf()
        self.roda(jogo, "gba-recomp")
        self.assertIn("CONSOLE_LANG=en_US", self.log().splitlines())
        es = self.root / "storage" / ".config" / "emulationstation"
        es.mkdir(parents=True)
        (es / "es_settings.cfg").write_text('<config>\n<string name="Language" value="es_ES" />\n</config>\n', encoding="utf-8")
        self.roda(jogo, "gba-recomp")
        self.assertIn("CONSOLE_LANG=es_ES", self.log().splitlines())

    # --- log ---

    def test_rotacao_do_log_a_100kb(self):
        jogo = self.elf()
        (self.pasta / "recomp.log").write_text("ANTIGO_" + "X" * 105000, encoding="utf-8")
        self.roda(jogo, "gba-recomp")
        self.assertIn("ANTIGO_", (self.pasta / "recomp.log.1").read_text(encoding="utf-8"))
        novo = self.log()
        self.assertNotIn("ANTIGO_", novo)
        self.assertLess(len(novo), 102400)

    def test_log_pequeno_nao_rotaciona(self):
        jogo = self.elf()
        (self.pasta / "recomp.log").write_text("ANTIGO_curto\n", encoding="utf-8")
        self.roda(jogo, "gba-recomp")
        self.assertFalse((self.pasta / "recomp.log.1").exists())
        self.assertIn("ANTIGO_curto", self.log())

    def test_diagnostico_so_com_a_chave(self):
        jogo = self.elf()
        self.roda(jogo, "gba-recomp")
        self.assertNotIn("--- diagnóstico ---", self.log())
        (self.roms / "r36-diagnostico").touch()
        self.roda(jogo, "gba-recomp")
        self.assertIn("--- diagnóstico ---", self.log())
        self.assertIn("SDL_GAMECONTROLLERCONFIG=", self.log())
        self.assertIn("guide:b10", self.log())

    def test_p1_somente_leitura_nao_impede_o_jogo(self):
        jogo = self.elf()
        self.pasta.chmod(0o555)
        try:
            if os.access(self.pasta, os.W_OK):
                self.skipTest("o teste roda como root")
            r = self.roda(jogo, "gba-recomp")
        finally:
            self.pasta.chmod(0o755)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
