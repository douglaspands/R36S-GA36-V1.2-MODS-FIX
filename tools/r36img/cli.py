"""argparse com mensagens em pt-BR."""

import argparse
import re
import sys

_TRANSLATIONS = [
    (r"unrecognized arguments: (.*)", r"opção(ões) não reconhecida(s): \1"),
    (r"argument (\S+): expected one argument", r"a opção \1 exige um valor"),
    (r"argument (\S+): invalid choice: (.*?) \(choose from (.*)\)", r"a opção \1 não aceita \2 (use: \3)"),
    (r"argument (\S+): not allowed with argument (\S+)", r"as opções \1 e \2 não podem ser usadas juntas"),
    (r"argument (\S+): (.*)", r"opção \1: \2"),
    (r"the following arguments are required: (.*)", r"faltam os argumentos: \1"),
]


class PtFormatter(argparse.RawDescriptionHelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, prefix or "uso: ")


class PtParser(argparse.ArgumentParser):
    def __init__(self, **kw):
        kw.setdefault("formatter_class", PtFormatter)
        kw.setdefault("add_help", False)
        super().__init__(**kw)
        self._optionals.title = "opções"
        self._positionals.title = "argumentos"
        self.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")

    def error(self, message):
        for pat, rep in _TRANSLATIONS:
            new = re.sub(pat, rep, message)
            if new != message:
                message = new
                break
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: erro: {message}\n")


def positive_int(name):
    def conv(v):
        try:
            n = int(v)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} deve ser um número inteiro, recebido {v!r}")
        if n <= 0:
            raise argparse.ArgumentTypeError(f"{name} deve ser maior que zero")
        return n
    return conv
