"""Idioma padrão escolhido no build (--idioma): troca das três chaves nas cópias em work/."""

import difflib
import hashlib
import json
import os
import subprocess
import unittest
from pathlib import Path

from context import CFG, ROOT, TempDirCase, needs_base, slow
from r36img import build, features, mtools
from r36img.errors import R36Error

F10 = ROOT / "features" / "10-ptbr-sao-paulo"
EMUCONF = ".config/emuelec/configs/emuelec.conf"
ESCFG = ".config/emulationstation/es_settings.cfg"
RACFG = ".config/retroarch/retroarch.cfg"
ESPERADO = {
    "en_US": ("system.language=en_US", '<string name="Language" value="en_US" />', 'user_language = "0"'),
    "pt_BR": ("system.language=pt_BR", '<string name="Language" value="pt_BR" />', 'user_language = "7"'),
}


def hashes(d):
    out = {}
    for raiz, _dirs, arquivos in os.walk(d):
        for n in arquivos:
            p = Path(raiz, n)
            if not p.is_symlink():
                out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def plano(*dirs):
    return features.plan_layer("storage", [features.load_feature(d) for d in dirs], {})


def mudancas(plan):
    return {c.path: c for c in plan.changes if c.op in ("added", "replaced") and c.kind == "file"}


class AplicaIdioma(TempDirCase):
    def test_tabela_e_padrao(self):
        self.assertEqual(build.IDIOMA_PADRAO, "en_US")
        self.assertEqual(build.IDIOMAS, {"pt_BR": 7, "pt_PT": 8, "en_US": 0, "en_GB": 0,
                                         "es_ES": 3, "fr_FR": 2, "de_DE": 4, "it_IT": 5})

    def test_arquivos_da_feature_10(self):
        antes = hashes(ROOT / "features")
        for idioma, numero in build.IDIOMAS.items():
            with self.subTest(idioma=idioma):
                plan = plano(F10)
                build.aplica_idioma(plan, idioma, self.tmp / idioma)
                ch = mudancas(plan)
                esperado = {EMUCONF: f"system.language={idioma}",
                            ESCFG: f'<string name="Language" value="{idioma}" />',
                            RACFG: f'user_language = "{numero}"'}
                for path, linha in esperado.items():
                    c = ch[path]
                    # a entrada do plano aponta para a cópia em work/, nunca para features/
                    self.assertTrue(str(c.src).startswith(str(self.tmp / idioma)), c.src)
                    original = (F10 / "storage" / path).read_text(encoding="utf-8").splitlines()
                    nova = c.src.read_text(encoding="utf-8").splitlines()
                    diff = [l for l in difflib.unified_diff(original, nova, lineterm="", n=0)
                            if l[:1] in "+-" and l[:3] not in ("+++", "---")]
                    if idioma == "pt_BR":
                        self.assertEqual(diff, [], path)
                    else:
                        self.assertEqual(len(diff), 2, diff)
                        self.assertEqual(diff[1][1:].strip(), linha)
                    self.assertIn(linha, c.src.read_text(encoding="utf-8"))
                    # tamanho do plano (conferido contra a p8 gerada) igual ao da cópia
                    self.assertEqual(c.entry.size, str(c.src.stat().st_size))
                    self.assertEqual(plan.final[path].size, str(c.src.stat().st_size))
                    self.assertEqual(int(c.src.stat().st_mtime), int((F10 / "storage" / path).stat().st_mtime))
        self.assertEqual(hashes(ROOT / "features"), antes)

    def fake_feature(self, emuconf, escfg, racfg, nome="99-falsa"):
        d = self.tmp / nome
        for rel, txt in ((EMUCONF, emuconf), (ESCFG, escfg), (RACFG, racfg)):
            p = d / "storage" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(txt.encode())
        (d / "feature.toml").write_text('schema = 1\nname = "falsa"\ndescription = ""\norder = 99\n')
        return d

    def test_crlf_e_resto_do_arquivo_preservados(self):
        d = self.fake_feature("a=1\r\nsystem.language=pt_BR\r\nb=2\r\n",
                              '<config>\n\t<string name="Language" value="pt_BR" />\n</config>\n',
                              'x = "1"\nuser_language = "7"\ny = "2"')
        plan = plano(d)
        build.aplica_idioma(plan, "de_DE", self.tmp / "w")
        ch = mudancas(plan)
        self.assertEqual(ch[EMUCONF].src.read_bytes(), b"a=1\r\nsystem.language=de_DE\r\nb=2\r\n")
        self.assertEqual(ch[RACFG].src.read_bytes(), b'x = "1"\nuser_language = "4"\ny = "2"')
        self.assertIn(b'value="de_DE"', ch[ESCFG].src.read_bytes())

    def test_chave_ausente_e_erro_claro(self):
        casos = [
            (("#system.language=pt_BR\n", '<string name="Language" value="pt_BR" />', 'user_language = "7"\n'),
             EMUCONF, "system.language"),
            (("system.language=pt_BR\n", '<string name="Idioma" value="pt_BR" />', 'user_language = "7"\n'),
             ESCFG, "Language"),
            (("system.language=pt_BR\n", '<string name="Language" value="pt_BR" />', '# user_language = "7"\n'),
             RACFG, "user_language"),
            (("system.language=pt_BR\n", '<string name="Language" value="pt_BR" />',
              'user_language = "7"\nuser_language = "0"\n'), RACFG, "user_language"),
        ]
        for i, ((emu, es, ra), arquivo, chave) in enumerate(casos):
            with self.subTest(arquivo=arquivo, ra=ra):
                d = self.fake_feature(emu, es, ra, f"99-falsa{i}")
                antes = hashes(d)
                with self.assertRaises(R36Error) as cm:
                    build.aplica_idioma(plano(d), "en_US", self.tmp / "w")
                self.assertIn(arquivo, str(cm.exception))
                self.assertIn(chave, str(cm.exception))
                self.assertEqual(hashes(d), antes)

    def test_features_sem_os_arquivos(self):
        with self.assertRaises(R36Error) as cm:
            build.aplica_idioma(plano(ROOT / "features" / "00-exemplo"), "en_US", self.tmp / "w")
        self.assertIn("emuelec.conf", str(cm.exception))
        self.assertIn("10-ptbr-sao-paulo", str(cm.exception))

    def test_padrao_so_vale_com_os_arquivos_de_idioma(self):
        f10 = features.load_feature(F10)
        exemplo = features.load_feature(ROOT / "features" / "00-exemplo")
        self.assertTrue(build.traz_idioma([f10]))
        self.assertTrue(build.traz_idioma([exemplo, f10]))
        self.assertFalse(build.traz_idioma([exemplo]))
        self.assertFalse(build.traz_idioma([]))
        # sem --lang o padrão é opcional (um --features de outra feature sai sem idioma);
        # com --lang explícito, a falta dos arquivos é erro
        a = build.parse_args(["--features", "00-exemplo"])
        self.assertEqual((a.lang, a.lang_opcional), ("en_US", True))
        a = build.parse_args(["--lang", "en_US"])
        self.assertEqual((a.lang, a.lang_opcional), ("en_US", False))
        a = build.parse_args(["--idioma", "en_US"])
        self.assertEqual((a.lang, a.lang_opcional), ("en_US", False))
        a = build.parse_args(["--no-features"])
        self.assertEqual((a.lang, a.lang_opcional), (None, False))

    def test_build_recusa_idioma_sem_features_e_codigo_invalido(self):
        with self.assertRaises(R36Error) as cm:
            build.build(CFG, none=True, lang="en_US", out_root=self.tmp / "out", work_root=self.tmp / "work")
        self.assertIn("exige as features", str(cm.exception))
        with self.assertRaises(R36Error) as cm:
            build.build(CFG, lang="xx_YY", out_root=self.tmp / "out", work_root=self.tmp / "work")
        self.assertIn("pt_BR", str(cm.exception))
        self.assertFalse((self.tmp / "out").exists())


@needs_base
@slow
class BuildComIdioma(TempDirCase):
    """Build de teste só com a feature 10 (a que traz os três arquivos), sem compressão."""

    def gera(self, idioma):
        ts = "20261013-153045"
        return build.build(CFG, size_mib=7000, names=["10-ptbr-sao-paulo"], lang=idioma, timestamp=ts,
                           test=True, fast=True, compress=False,
                           out_root=self.tmp / idioma / "out", work_root=self.tmp / idioma / "work")

    def le_p8(self, out_dir, path):
        return subprocess.run(["debugfs", "-R", f"cat /{path}", str(out_dir / "parts" / "storage.img")],
                              check=True, capture_output=True, text=True).stdout

    def test_padrao_en_us_e_pt_br(self):
        antes = hashes(ROOT / "features")
        for idioma in ("en_US", "pt_BR"):
            with self.subTest(idioma=idioma):
                out_dir = self.gera(idioma)
                tag = idioma.lower().replace("_", "-")
                self.assertEqual(out_dir.name, "20261013-153045-test")
                manifest = json.loads((out_dir / "manifest.json").read_text())
                self.assertEqual(manifest["image"]["file"],
                                 f"r36s_ga36-mb_v1.2-20260416_{tag}_build_20261013-153045-test.img.xz")
                self.assertEqual(manifest["language"], idioma)
                txt = subprocess.run(["mtype", "-i", str(out_dir / "parts/system.img"), "::/R36-BUILD.txt"],
                                     capture_output=True, text=True, check=True,
                                     env=dict(os.environ, **mtools.ENV)).stdout
                self.assertEqual(txt, manifest["build_info"]["text"])
                self.assertIn(f"idioma: {idioma}\n", txt)
                emu, es, ra = ESPERADO[idioma]
                self.assertIn(emu + "\n", self.le_p8(out_dir, EMUCONF))
                self.assertIn(es, self.le_p8(out_dir, ESCFG))
                self.assertIn(ra + "\n", self.le_p8(out_dir, RACFG))
        self.assertEqual(hashes(ROOT / "features"), antes)
        st = subprocess.run(["git", "status", "--porcelain", "--", "features"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout
        self.assertEqual(st, "")


if __name__ == "__main__":
    unittest.main()
