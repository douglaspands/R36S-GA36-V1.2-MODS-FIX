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
        for opt in ("--size-mib", "--features", "--no-features", "--fast", "--help"):
            self.assertIn(opt, out)
        self.assertIn("uso: ./build.sh", out)
        self.assertNotIn("--version", out)
        self.assertNotIn("--force", out)

    def test_defaults(self):
        a, code, *_ = parse()
        self.assertEqual((a.size_mib, a.features, a.no_features, a.fast), (None, None, False, False))

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
        ]
        for argv, msg in cases:
            with self.subTest(argv=argv):
                _a, code, _o, err = parse(*argv)
                self.assertEqual(code, 2)
                self.assertIn("erro:", err)
                self.assertIn(msg, err)

    def test_size_below_minimum_via_script(self):
        p = subprocess.run([str(ROOT / "build.sh"), "--size-mib", "6000"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn("mínimo de 7000 MiB", p.stderr)


if __name__ == "__main__":
    unittest.main()
