"""Testes da feature 58-ports-exec: executáveis dos ports rodam de uma cópia na p8."""

import hashlib
import os
import shutil
import stat
import subprocess
import tomllib
import unittest
from pathlib import Path

from context import ROOT, TempDirCase
from test_otimizacoes import UnitCase, diretivas

FEATURE = ROOT / "features" / "58-ports-exec"
SCRIPT = FEATURE / "system" / "usr" / "lib" / "r36" / "ports-exec"
UNIT = FEATURE / "system" / "usr" / "lib" / "systemd" / "system" / "r36-ports-exec.service"

ELF = b"\x7fELF\x01\x01\x01\x00" + b"\x00" * 8 + b"conteudo-"


def elf(marca):
    return ELF + marca.encode()


def sha(dados):
    return hashlib.sha256(dados).hexdigest()


# Montagem falsa: registra os argumentos e recusa qualquer destino chamado "recusado".
MOUNT_FALSO = """#!/bin/sh
printf "%s\t%s\t%s\n" "$1" "$2" "$3" >> "$R36_MOUNT_LOG"
case "$3" in
    *recusado*) echo "mount: permissão negada" >&2; exit 1 ;;
esac
exit 0
"""


class Feature(UnitCase):
    def test_toml(self):
        t = tomllib.loads((FEATURE / "feature.toml").read_text(encoding="utf-8"))
        self.assertEqual((t["schema"], t["order"], t["enabled"]), (1, 58, True))

    def test_script_executavel_e_valido(self):
        self.assertTrue(os.access(SCRIPT, os.X_OK), "ports-exec sem bit de execução")
        self.assertEqual(stat.S_IMODE(SCRIPT.stat().st_mode) & 0o755, 0o755)
        subprocess.run(["sh", "-n", str(SCRIPT)], check=True)
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)
        if shutil.which("shellcheck"):
            subprocess.run(["shellcheck", "-s", "sh", str(SCRIPT)], check=True)

    def test_unit(self):
        d = diretivas(UNIT)
        self.assertEqual(d["Type"], ["oneshot"])
        self.assertEqual(d["ExecStart"], ["/usr/lib/r36/ports-exec"])
        self.assertEqual(d["Before"], ["emustation.service"])
        self.assertEqual(d["TimeoutStartSec"], ["60"])
        self.assertEqual(d["WantedBy"], ["emuelec.target"])
        # O autostart só termina depois de "systemctl start emustation": ordenar
        # depois dele e antes do ES trava o boot no splash.
        self.assertNotIn("After", d)

    def test_link(self):
        self.assert_link(FEATURE, "emuelec.target.wants", "r36-ports-exec.service")


class PortsExec(TempDirCase):
    """Roda o ports-exec com R36_ROOT temporário e uma montagem falsa."""

    def setUp(self):
        super().setUp()
        self.root = self.tmp / "raiz"
        self.roms = self.root / "storage" / "roms"
        self.ports = self.roms / "ports"
        self.store = self.root / "storage" / ".config" / "r36-ports-exec"
        self.mounts = self.root / "proc" / "mounts"
        self.mounts.parent.mkdir(parents=True)
        self.mounts.write_text("", encoding="utf-8")
        self.ports.mkdir(parents=True)
        self.mount_log = self.tmp / "mount.log"
        self.mount_log.write_text("", encoding="utf-8")
        self.mount_cmd = self.tmp / "mount-falso"
        self.mount_cmd.write_text(MOUNT_FALSO, encoding="utf-8")
        self.mount_cmd.chmod(0o755)

    def escreve(self, rel, dados):
        p = self.ports / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(dados)
        return p

    def roda(self, path_extra=None):
        path = os.environ["PATH"] if path_extra is None else f"{path_extra}:{os.environ['PATH']}"
        proc = subprocess.run(
            ["sh", str(SCRIPT)], capture_output=True, text=True,
            env={
                "PATH": path, "R36_ROOT": str(self.root),
                "R36_MOUNT": str(self.mount_cmd), "R36_MOUNT_LOG": str(self.mount_log),
            },
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        return proc

    def montagens(self):
        return [linha.split("\t") for linha in self.mount_log.read_text(encoding="utf-8").splitlines()]

    def copias(self):
        return sorted(p.name for p in self.store.iterdir()) if self.store.is_dir() else []

    def log(self):
        return (self.ports / "r36-ports-exec.log").read_text(encoding="utf-8")

    # --- seleção (1.2) ---

    def test_so_elf_e_tratado(self):
        binario = self.escreve("jogo/jogo", elf("a"))
        lib = self.escreve("jogo/libjogo.so", elf("lib"))
        self.escreve("jogo/dados.bin", b"dados sem cabecalho")
        self.escreve("jogo/LEIAME.txt", b"texto")
        self.escreve("jogo/curto", b"\x7fEL")
        self.escreve("jogo/vazio", b"")
        self.roda()
        destinos = sorted(m[2] for m in self.montagens())
        self.assertEqual(destinos, sorted([str(binario), str(lib)]))
        self.assertEqual(self.copias(), sorted([sha(elf("a")), sha(elf("lib"))]))

    def test_sem_roms_termina_sem_montar(self):
        shutil.rmtree(self.roms)
        self.roda()
        self.assertEqual(self.montagens(), [])
        self.assertFalse(self.store.exists())

    def test_espera_20s_pela_p1_e_sai_sem_montar(self):
        # Sem R36_ROOT o script vigia /storage/roms: um mountpoint que nunca vira
        # ponto de montagem e um sleep que só conta devem terminar com 0 e sem montar.
        shim = self.tmp / "shim"
        shim.mkdir()
        contagem = self.tmp / "sleeps"
        (shim / "mountpoint").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        (shim / "sleep").write_text(f'#!/bin/sh\necho "$1" >> "{contagem}"\n', encoding="utf-8")
        (shim / "mount").write_text(f'#!/bin/sh\necho "$@" >> "{self.mount_log}"\n', encoding="utf-8")
        for f in shim.iterdir():
            f.chmod(0o755)
        proc = subprocess.run(
            ["sh", str(SCRIPT)], capture_output=True, text=True,
            env={"PATH": f"{shim}:{os.environ['PATH']}"},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(contagem.read_text(encoding="utf-8").split()), 20)
        self.assertEqual(self.montagens(), [])

    # --- cópias por sha256 (1.3) ---

    def test_binario_novo_vira_copia_executavel(self):
        dados = elf("novo")
        binario = self.escreve("jogo/jogo", dados)
        self.roda()
        copia = self.store / sha(dados)
        self.assertEqual(copia.read_bytes(), dados)
        self.assertEqual(stat.S_IMODE(copia.stat().st_mode), 0o755)
        self.assertEqual(self.montagens(), [["--bind", str(copia), str(binario)]])
        # O arquivo da p1 não é alterado
        self.assertEqual(binario.read_bytes(), dados)
        self.assertEqual([p for p in self.store.iterdir() if p.name.startswith(".tmp.")], [])

    def test_boot_repetido_nao_copia_de_novo(self):
        self.escreve("jogo/jogo", elf("x"))
        self.roda()
        copia = self.store / sha(elf("x"))
        antes = copia.stat().st_mtime_ns
        os.utime(copia, ns=(antes - 10**9, antes - 10**9))
        marcado = copia.stat().st_mtime_ns
        self.roda()
        self.assertEqual(copia.stat().st_mtime_ns, marcado, "cópia refeita sem necessidade")
        self.assertEqual(len(self.montagens()), 2)

    def test_binario_trocado_cria_copia_nova_e_apaga_a_antiga(self):
        binario = self.escreve("jogo/jogo", elf("v1"))
        self.roda()
        self.assertEqual(self.copias(), [sha(elf("v1"))])
        binario.write_bytes(elf("v2"))
        self.roda()
        self.assertEqual(self.copias(), [sha(elf("v2"))])

    def test_port_removido_apaga_as_copias(self):
        self.escreve("jogo/jogo", elf("a"))
        self.escreve("outro/outro", elf("b"))
        self.roda()
        self.assertEqual(len(self.copias()), 2)
        shutil.rmtree(self.ports / "jogo")
        self.roda()
        self.assertEqual(self.copias(), [sha(elf("b"))])
        shutil.rmtree(self.ports / "outro")
        self.roda()
        self.assertEqual(self.copias(), [])

    def test_resto_de_copia_interrompida_e_apagado(self):
        self.escreve("jogo/jogo", elf("a"))
        self.store.mkdir(parents=True)
        (self.store / ".tmp.abandonado").write_bytes(b"truncado")
        self.roda()
        self.assertEqual(self.copias(), [sha(elf("a"))])

    def test_mesmo_conteudo_em_dois_caminhos_divide_uma_copia(self):
        a = self.escreve("um/jogo", elf("igual"))
        b = self.escreve("dois/jogo", elf("igual"))
        self.roda()
        self.assertEqual(self.copias(), [sha(elf("igual"))])
        copia = str(self.store / sha(elf("igual")))
        self.assertEqual(sorted(m[1:] for m in self.montagens()), sorted([[copia, str(a)], [copia, str(b)]]))

    def test_caminho_com_espaco(self):
        binario = self.escreve("meu jogo/meu jogo", elf("espaco"))
        self.roda()
        self.assertEqual(self.copias(), [sha(elf("espaco"))])
        self.assertIn(str(binario), self.mount_log.read_text(encoding="utf-8"))

    # --- montagem idempotente e falha parcial (1.4) ---

    def test_caminho_ja_montado_nao_e_montado_de_novo(self):
        self.escreve("meu jogo/meu jogo", elf("a"))
        self.escreve("outro/outro", elf("b"))
        # /proc/mounts escreve o espaço como \040 e não leva o prefixo do R36_ROOT
        self.mounts.write_text("/dev/mmcblk0p8 /storage/roms/ports/meu\\040jogo/meu\\040jogo ext4 rw 0 0\n", encoding="utf-8")
        self.roda()
        self.assertEqual([m[2] for m in self.montagens()], [str(self.ports / "outro" / "outro")])
        self.assertIn("(já montado)", self.log())
        # A cópia do arquivo já coberto continua existindo
        self.assertIn(sha(elf("a")), self.copias())

    def test_erro_em_um_arquivo_nao_impede_os_outros(self):
        self.escreve("a/jogo", elf("a"))
        self.escreve("recusado/jogo", elf("r"))
        self.escreve("z/jogo", elf("z"))
        self.roda()
        montados = sorted(m[2] for m in self.montagens())
        self.assertEqual(len(montados), 3)  # o laço continuou depois da recusa
        linhas = self.log().splitlines()
        erros = [linha for linha in linhas if linha.startswith("ERRO")]
        self.assertEqual(len(erros), 1)
        self.assertIn("/storage/roms/ports/recusado/jogo", erros[0])
        self.assertIn("mount: mount: permissão negada", erros[0])
        self.assertEqual(sum(linha.startswith("ok ") for linha in linhas), 2)

    def test_copia_falha_nao_impede_os_outros(self):
        self.escreve("a/ruim", elf("ruim"))
        self.escreve("b/bom", elf("bom"))
        shim = self.tmp / "shim"
        shim.mkdir()
        cp_falso = shim / "cp"
        cp_falso.write_text(
            '#!/bin/sh\ncase "$*" in *ruim*) echo "cp: sem espaço no dispositivo" >&2; exit 1 ;; esac\n'
            f'exec {shutil.which("cp")} "$@"\n',
            encoding="utf-8",
        )
        cp_falso.chmod(0o755)
        self.roda(path_extra=shim)
        self.assertIn(sha(elf("bom")), self.copias())
        self.assertNotIn(sha(elf("ruim")), self.copias())
        self.assertEqual([m[2] for m in self.montagens()], [str(self.ports / "b" / "bom")])
        erros = [linha for linha in self.log().splitlines() if linha.startswith("ERRO")]
        self.assertEqual(len(erros), 1)
        self.assertIn("/storage/roms/ports/a/ruim", erros[0])
        self.assertIn("sem espaço no dispositivo", erros[0])

    # --- log (1.5) ---

    def test_log_com_sha256_e_ok(self):
        self.escreve("jogo/jogo", elf("log"))
        self.roda()
        log = self.log()
        self.assertIn(f"ok /storage/roms/ports/jogo/jogo {sha(elf('log'))}", log)
        self.assertNotIn(str(self.root), log)

    def test_log_traz_opcoes_de_montagem(self):
        self.mounts.write_text(
            "/dev/mmcblk0p8 /storage ext4 rw,noatime 0 0\n/dev/mmcblk0p1 /storage/roms vfat rw,noexec,fmask=0022 0 0\n",
            encoding="utf-8",
        )
        self.escreve("jogo/jogo", elf("a"))
        self.roda()
        log = self.log()
        self.assertIn("# /storage: ext4 rw,noatime", log)
        self.assertIn("# /storage/roms: vfat rw,noexec,fmask=0022", log)

    def test_log_so_do_ultimo_boot(self):
        self.escreve("a/a", elf("a"))
        self.roda()
        self.assertIn("/storage/roms/ports/a/a", self.log())
        shutil.rmtree(self.ports / "a")
        self.escreve("b/b", elf("b"))
        self.roda()
        log = self.log()
        self.assertIn("/storage/roms/ports/b/b", log)
        self.assertNotIn("/storage/roms/ports/a/a", log)
        self.assertEqual(log.count("r36-ports-exec:"), 1)

    def test_log_nao_e_tratado_como_executavel(self):
        self.roda()
        self.roda()
        self.assertEqual(self.montagens(), [])

    def test_ports_somente_leitura_termina_com_0(self):
        binario = self.escreve("jogo/jogo", elf("ro"))
        self.ports.chmod(0o555)
        try:
            if os.access(self.ports, os.W_OK):
                self.skipTest("o teste roda como root: chmod 555 não impede a escrita")
            self.roda()
        finally:
            self.ports.chmod(0o755)
        self.assertFalse((self.ports / "r36-ports-exec.log").exists())
        self.assertEqual(self.montagens(), [["--bind", str(self.store / sha(elf("ro"))), str(binario)]])

    # --- binário entregue pela imagem e port novo (2.5) ---

    def test_binario_entregue_pela_imagem_como_o_de_qualquer_port(self):
        entregue = ROOT / "features" / "60-port-classicube" / "roms" / "ports" / "classicube" / "ClassiCube"
        if not entregue.is_file():
            self.skipTest("a feature 60-port-classicube ainda não entrega o binário na p1")
        destino = self.escreve("classicube/ClassiCube", entregue.read_bytes())
        destino.chmod(0o644)  # a FAT32 não guarda o bit de execução
        self.roda()
        soma = sha(entregue.read_bytes())
        self.assertEqual(self.montagens(), [["--bind", str(self.store / soma), str(destino)]])
        self.assertEqual(stat.S_IMODE((self.store / soma).stat().st_mode), 0o755)
        self.assertIn(f"ok /storage/roms/ports/classicube/ClassiCube {soma}", self.log())

    def test_port_novo_nao_precisa_de_lista_nem_configuracao(self):
        # Só script em ports_scripts/ e executável em ports/<nome>/: nada mais na imagem.
        scripts = self.roms / "ports_scripts"
        scripts.mkdir()
        (scripts / "OutroJogo.sh").write_text("#!/bin/bash\ncd /storage/roms/ports/outrojogo\n./outrojogo\n", encoding="utf-8")
        binario = self.escreve("outrojogo/outrojogo", elf("outro"))
        self.escreve("outrojogo/data/nivel1.dat", b"dados")
        self.roda()
        self.assertEqual(self.montagens(), [["--bind", str(self.store / sha(elf("outro"))), str(binario)]])
        self.assertFalse(list(FEATURE.rglob("*outrojogo*")))
        # Nada fora de ports/ e da p8 foi tocado
        self.assertEqual(sorted(p.name for p in scripts.iterdir()), ["OutroJogo.sh"])


if __name__ == "__main__":
    unittest.main()
