"""Acesso a filesystems FAT via mtools, sem montar (MTOOLS_SKIP_CHECK=1: a p2 tem
geometria com heads/sectors zerados)."""

import os
import re
from dataclasses import dataclass

from .errors import R36Error
from .squash import Entry
from .util import run

ENV = {"MTOOLS_SKIP_CHECK": "1", "LC_ALL": "C"}

_LINE = re.compile(
    r"^(?P<short>.{8}) (?P<ext>.{3})\s+(?P<size><DIR>|\d+)\s+"
    r"(?P<date>\d{4}-\d\d-\d\d)\s+(?P<time>\d+:\d\d)(?:  (?P<long>.+))?$"
)
_DIR_HDR = re.compile(r"^Directory for ::(?P<path>/.*)$")


def spec(image, offset=0) -> str:
    """Argumento `-i` do mtools (com @@offset quando a FAT está dentro de uma imagem)."""
    return f"{image}@@{offset}" if offset else str(image)


def _m(cmd, prefix=()):
    """Roda um comando mtools. `prefix` (ex.: ["sudo"]) não herda o ambiente, então
    as variáveis vão via `env`."""
    if prefix:
        cmd = [*prefix, "env", *[f"{k}={v}" for k, v in ENV.items()], *cmd]
    return run(cmd, env=ENV)


def parse_mdir(text: str) -> dict:
    """Saída de `mdir -/ -a` -> {caminho: Entry('d'|'-', size)} (sem a raiz)."""
    entries = {}
    cur = None
    for line in text.splitlines():
        h = _DIR_HDR.match(line.rstrip())
        if h:
            cur = h["path"].strip("/")
            continue
        if cur is None:
            continue
        m = _LINE.match(line.rstrip())  # o mdir deixa um espaço após a hora
        if not m:
            continue
        name = m["long"]
        if not name:
            base, ext = m["short"].strip(), m["ext"].strip()
            name = f"{base}.{ext}" if ext else base
        if name in (".", ".."):
            continue
        path = f"{cur}/{name}" if cur else name
        is_dir = m["size"] == "<DIR>"
        entries[path] = Entry("d" if is_dir else "-", 0, 0, 0, "" if is_dir else m["size"])
    return entries


def listing(image, offset=0, prefix=()) -> dict:
    out = _m(["mdir", "-/", "-a", "-i", spec(image, offset), "::/"], prefix=prefix).stdout
    return parse_mdir(out)


def label(image, offset=0) -> str:
    out = _m(["mlabel", "-s", "-i", spec(image, offset), "::"]).stdout
    m = re.search(r"Volume label is (.*?)\s*$", out, re.M)
    return m.group(1).strip() if m else ""


def set_label(image, new_label, offset=0) -> None:
    _m(["mlabel", "-i", spec(image, offset), f"::{new_label}"])


def mkdir(image, path, offset=0) -> None:
    _m(["mmd", "-i", spec(image, offset), f"::/{path}"])


def copy_in(image, src, path, offset=0) -> None:
    """Copia um arquivo local para ::/path, sobrescrevendo (-o) e preservando a mtime (-m)."""
    _m(["mcopy", "-o", "-m", "-i", spec(image, offset), str(src), f"::/{path}"])


def copy_tree_in(image, src_dir, offset=0) -> None:
    """Copia o conteúdo de src_dir para a raiz, recursivo."""
    names = sorted(os.listdir(src_dir))
    if names:
        _m(["mcopy", "-s", "-o", "-m", "-i", spec(image, offset),
            *[os.path.join(src_dir, n) for n in names], "::/"])


def copy_tree_out(image, dest_dir, offset=0) -> None:
    """Copia todo o conteúdo da raiz para dest_dir (recursivo, inclui ocultos)."""
    top = [p for p in listing(image, offset) if "/" not in p]
    if top:
        _m(["mcopy", "-s", "-n", "-m", "-i", spec(image, offset),
            *[f"::/{p}" for p in top], str(dest_dir)])


def delete(image, path, is_dir, offset=0) -> None:
    _m(["mdeltree" if is_dir else "mdel", "-i", spec(image, offset), f"::/{path}"])


@dataclass
class ApplyResult:
    added: int = 0
    replaced: int = 0
    removed: int = 0


def apply_plan(image, plan, offset=0) -> ApplyResult:
    """Aplica as mudanças de uma camada FAT (boot/roms)."""
    r = ApplyResult()
    for c in plan.changes:
        if c.op == "removed":
            delete(image, c.path, c.kind == "dir", offset)
            r.removed += 1
        elif c.kind == "dir":
            mkdir(image, c.path, offset)
            r.added += 1
        elif c.op in ("added", "replaced"):
            copy_in(image, c.src, c.path, offset)
            r.added += c.op == "added"
            r.replaced += c.op == "replaced"
        else:
            raise R36Error(f"operação {c.op} não suportada em FAT ({c.path})")
    return r
