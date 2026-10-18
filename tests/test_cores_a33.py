import difflib
import hashlib
import os
import re
import subprocess
import unittest

from context import CFG, ROOT, TempDirCase, needs_base
from r36img import cores as C
from r36img import mtools

F53 = ROOT / "features" / "53-cores-a33"
LIBRETRO = F53 / "system" / "usr" / "lib" / "libretro"
ES_SYSTEM = F53 / "system" / "usr" / "config" / "emulationstation" / "es_systems.cfg"
ES_STORAGE = F53 / "storage" / ".config" / "emulationstation" / "es_systems.cfg"
EMUELEC_CONF = ROOT / "features" / "10-ptbr-sao-paulo" / "storage" / ".config" / "emuelec" / "configs" / "emuelec.conf"
# Core promovido: (core da receita, variante vencedora, versão no .info)
PROMOVIDO = "snes9x2005_plus_a33"
ORIGEM = ("snes9x2005_plus", "o2", "v1.36 fd45b0e a33-o2")
NOVA = f"\t\t\t\t\t<core>{PROMOVIDO}</core>"


def bloco(txt, sistema):
    i = txt.index(f"<name>{sistema}</name>")
    return txt[i:txt.index("</system>", i)]


class CoresA33(unittest.TestCase):
    def test_descritor(self):
        txt = (F53 / "feature.toml").read_text()
        self.assertIn("order = 53", txt)
        self.assertIn("enabled = true", txt)

    def test_camadas_iguais(self):
        self.assertEqual(ES_SYSTEM.read_bytes(), ES_STORAGE.read_bytes())

    def test_promovido_no_fim_do_bloco_snes(self):
        snes = bloco(ES_STORAGE.read_text(), "snes")
        linhas = snes.splitlines()
        i = linhas.index("\t\t\t\t\t<core>snes9x2005_plus</core>")
        self.assertEqual(linhas[i + 1], NOVA)
        self.assertEqual(linhas[i + 2].strip(), "</cores>")
        self.assertIn('<core default="true">snes9x</core>', snes)
        for outro in ("snesh", "snesmsu1"):
            self.assertNotIn("a33", bloco(ES_STORAGE.read_text(), outro))

    def test_so_o_promovido_na_feature(self):
        self.assertEqual(sorted(p.name for p in LIBRETRO.iterdir()),
                         [f"{PROMOVIDO}_libretro.info", f"{PROMOVIDO}_libretro.so"])

    def test_info_do_promovido(self):
        txt = (LIBRETRO / f"{PROMOVIDO}_libretro.info").read_text()
        self.assertIn('display_name = "Nintendo - SNES / SFC (Snes9x 2005 Plus A33)"', txt)
        self.assertIn(f'display_version = "{ORIGEM[2]}"', txt)
        self.assertIn('corename = "Snes9x 2005 Plus"', txt)

    def test_promovido_e_a_variante_vencedora_registrada(self):
        rec = C.carregar(ORIGEM[0])
        v = C.variante(rec, ORIGEM[1])
        self.assertEqual(v.nome, PROMOVIDO)
        so = LIBRETRO / C.nome_so(v)
        self.assertTrue(os.access(so, os.X_OK))
        reg = C.ultimos(rec)[ORIGEM[1]]
        self.assertEqual(reg["sha256"], hashlib.sha256(so.read_bytes()).hexdigest())
        self.assertEqual(reg["tamanho"], so.stat().st_size)
        self.assertEqual(reg["log"]["nivel"], "-O2")

    def test_padrao_do_snes_depende_da_53(self):
        conf = EMUELEC_CONF.read_text()
        core = re.search(r"^snes\.core=(\S+)$", conf, re.M).group(1)
        if core == PROMOVIDO:
            # a 10-ptbr-sao-paulo aponta para o core da 53: ela precisa estar ligada
            self.assertIn("enabled = true", (F53 / "feature.toml").read_text())
            self.assertTrue((LIBRETRO / f"{PROMOVIDO}_libretro.so").is_file())


@needs_base
class CoresA33ContraBase(TempDirCase):
    def base_system(self, caminho):
        sq = self.tmp / "SYSTEM"
        if not sq.exists():
            subprocess.run(
                ["mcopy", "-n", "-i", mtools.spec(CFG.base_path, CFG.part("system").offset), "::/SYSTEM", str(sq)],
                check=True, env=mtools.ENV, capture_output=True)
        return subprocess.run(["unsquashfs", "-cat", str(sq), caminho], check=True, capture_output=True,
                              text=True).stdout

    def test_es_systems_so_ganha_a_linha_do_promovido(self):
        base = self.base_system("usr/config/emulationstation/es_systems.cfg").splitlines()
        novo = ES_SYSTEM.read_text().splitlines()
        mudou = [l for l in difflib.unified_diff(base, novo, lineterm="", n=0)
                 if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        self.assertEqual(mudou, ["+" + NOVA])

    def test_info_so_muda_nome_e_versao(self):
        base = self.base_system("usr/lib/libretro/snes9x2005_plus_libretro.info").splitlines()
        novo = (LIBRETRO / f"{PROMOVIDO}_libretro.info").read_text().splitlines()
        self.assertEqual(len(base), len(novo))
        chaves = [a.partition(" = ")[0] for a, b in zip(base, novo) if a != b]
        self.assertEqual(chaves, ["display_name", "display_version"])


if __name__ == "__main__":
    unittest.main()
