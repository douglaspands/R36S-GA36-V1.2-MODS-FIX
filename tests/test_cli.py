import contextlib
import io
import subprocess
import unittest

from context import ROOT
from r36img import build


def parse(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            return build.parse_args(list(argv)), 0, out.getvalue(), err.getvalue()
        except SystemExit as e:
            return None, e.code, out.getvalue(), err.getvalue()


class BuildCliTest(unittest.TestCase):
    def test_help_lists_options(self):
        _a, code, out, _e = parse("--help")
        self.assertEqual(code, 0)
        for opt in ("--size-mib", "--features", "--no-features", "--fast", "--idioma", "--timestamp", "--help"):
            self.assertIn(opt, out)
        self.assertIn("uso: ./build.sh", out)
        # o padrão é inglês, e português pede --idioma pt_BR
        self.assertIn("padrão en_US", out)
        self.assertIn("--idioma pt_BR", out)
        # a ressalva: só vale se as features trazem os arquivos de idioma
        self.assertIn("se as features selecionadas trazem", out)
        for codigo in ("pt_BR", "pt_PT", "en_US", "en_GB", "es_ES", "fr_FR", "de_DE", "it_IT"):
            self.assertIn(codigo, out)
        self.assertNotIn("--version", out)
        self.assertNotIn("--force", out)

    def test_defaults(self):
        a, code, *_ = parse()
        self.assertEqual((a.size_mib, a.features, a.no_features, a.fast, a.timestamp), (None, None, False, False, None))
        self.assertEqual(a.idioma, "en_US")

    def test_timestamp(self):
        self.assertEqual(parse("--timestamp", "20261030-120000")[0].timestamp, "20261030-120000")

    def test_idioma(self):
        self.assertEqual(parse("--idioma", "pt_BR")[0].idioma, "pt_BR")
        self.assertEqual(parse("--idioma", "es_ES", "--features", "10-ptbr-sao-paulo")[0].idioma, "es_ES")
        # sem features não há idioma (imagem igual à base)
        self.assertIsNone(parse("--no-features")[0].idioma)

    def test_features_list(self):
        a, *_ = parse("--features", "00-exemplo, 10-tema")
        self.assertEqual(a.features, ["00-exemplo", "10-tema"])

    def test_invalid_values(self):
        cases = [
            (("--size-mib", "abc"), "deve ser um número inteiro"),
            (("--size-mib", "0"), "maior que zero"),
            (("--size-mib",), "exige um valor"),
            (("--features", " , "), "ao menos um nome"),
            (("--features", "a", "--no-features"), "não podem ser usadas juntas"),
            (("--version",), "não reconhecida"),
            (("--force",), "não reconhecida"),
            (("--idioma", "xx_YY"), "pt_BR, pt_PT, en_US, en_GB, es_ES, fr_FR, de_DE, it_IT"),
            (("--idioma", "pt_br"), "idioma 'pt_br' desconhecido"),
            (("--idioma",), "exige um valor"),
            (("--no-features", "--idioma", "en_US"), "o idioma exige as features"),
            (("--timestamp", "20261030"), "formato AAAAMMDD-HHMMSS"),
            (("--timestamp", "2026-10-30-12:00:00"), "formato AAAAMMDD-HHMMSS"),
            (("--timestamp",), "exige um valor"),
        ]
        for argv, msg in cases:
            with self.subTest(argv=argv):
                _a, code, _o, err = parse(*argv)
                self.assertEqual(code, 2)
                self.assertIn("erro:", err)
                self.assertIn(msg, err)

    def test_idioma_invalido_via_script(self):
        p = subprocess.run([str(ROOT / "build.sh"), "--idioma", "xx_YY"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("en_US", p.stderr)

    def test_size_below_minimum_via_script(self):
        p = subprocess.run([str(ROOT / "build.sh"), "--size-mib", "6000"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn("mínimo de 7000 MiB", p.stderr)


if __name__ == "__main__":
    unittest.main()
