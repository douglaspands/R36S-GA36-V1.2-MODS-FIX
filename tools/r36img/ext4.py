"""STORAGE (p8, ext4) editado com debugfs, sem montar (D5)."""

import os
import re

from .errors import R36Error
from .squash import Entry
from .util import run

_LS_P = re.compile(r"^/(\d+)/(\d+)/(\d+)/(\d+)/(.*)/(\d*)/$")
_PROMPT = "debugfs: "
_TYPES = {0o040000: "d", 0o100000: "-", 0o120000: "l", 0o020000: "c", 0o060000: "b",
          0o010000: "p", 0o140000: "s"}


def _q(path: str) -> str:
    if '"' in path or "\n" in path:
        raise R36Error(f"debugfs: nome não suportado: {path!r}")
    return f'"/{path}"' if path else '"/"'


def _run_script(image, lines, write=False):
    """Roda comandos debugfs; devolve [(comando, [linhas de saída])]."""
    script = "\n".join(lines) + "\n"
    cmd = ["debugfs", *(["-w"] if write else []), "-f", "-", str(image)]
    out = run(cmd, input=script).stdout
    results = []
    for line in out.splitlines():
        if line.startswith(_PROMPT):
            results.append((line[len(_PROMPT):], []))
        elif results:
            results[-1][1].append(line)
    return results


def listing(image) -> dict:
    """{caminho: Entry} de todo o filesystem (raiz = ''), via `ls -p` por nível."""
    entries = {"": None}
    level = [""]
    while level:
        res = _run_script(image, [f"ls -p {_q(d)}" for d in level])
        if len(res) != len(level):
            raise R36Error("debugfs: saída inesperada ao listar o STORAGE")
        nxt = []
        for d, (_cmd, out) in zip(level, res):
            for line in out:
                m = _LS_P.match(line)
                if not m:
                    if line.strip():
                        raise R36Error(f"debugfs ls -p {d!r}: {line}")
                    continue
                _ino, mode_s, uid, gid, name, size = m.groups()
                mode = int(mode_s, 8)
                type_ = _TYPES.get(mode & 0o170000, "?")
                if name == ".":
                    if d == "":
                        entries[""] = Entry("d", mode & 0o7777, int(uid), int(gid), "")
                    continue
                if name == "..":
                    continue
                path = f"{d}/{name}" if d else name
                entries[path] = Entry(type_, mode & 0o7777, int(uid), int(gid),
                                      "" if type_ == "d" else size)
                if type_ == "d":
                    nxt.append(path)
        level = nxt
    return entries


_OK_OUTPUT = re.compile(r"^(Allocated inode: \d+)?$")


def apply_plan(image, plan) -> None:
    """Aplica as mudanças da camada storage com um script `debugfs -w`."""
    lines = []
    final = plan.final
    for c in plan.changes:
        q = _q(c.path)
        if c.op == "removed":
            if c.kind == "dir":
                # filhos primeiro (os mais fundos antes)
                kids = sorted((p for p in plan.base if p.startswith(c.path + "/")),
                              key=lambda p: -p.count("/"))
                for p in kids:
                    e = plan.base[p]
                    lines.append(f"{'rmdir' if e.type == 'd' else 'rm'} {_q(p)}")
                lines.append(f"rmdir {q}")
            else:
                lines.append(f"rm {q}")
            continue
        if c.op in ("added", "replaced"):
            if c.kind == "dir":
                lines.append(f"mkdir {q}")
            else:
                if c.op == "replaced":
                    lines.append(f"rm {q}")
                if c.kind == "symlink":
                    target = os.readlink(c.src)
                    if '"' in target:
                        raise R36Error(f"debugfs: alvo de symlink não suportado: {target!r}")
                    lines.append(f'symlink {q} "{target}"')
                else:
                    lines.append(f'write "{c.src}" {q}')
                    mt = int(os.stat(c.src).st_mtime)
                    # "@" = segundos desde a época; sem ele o debugfs tenta ler o número
                    # como data (ex.: 1791918978 vira 2472)
                    lines.append(f"sif {q} mtime @{mt}")
        e = final.get(c.path)
        if e is None:
            continue
        type_bits = {"d": 0o040000, "-": 0o100000, "l": 0o120000}[e.type]
        lines.append(f"sif {q} mode 0{type_bits | e.mode:o}")
        lines.append(f"sif {q} uid {e.uid}")
        lines.append(f"sif {q} gid {e.gid}")
    if not lines:
        return
    errors = []
    for cmd, out in _run_script(image, lines, write=True):
        bad = [l for l in out if not _OK_OUTPUT.match(l.strip())]
        if bad:
            errors.append(f"{cmd}: {' '.join(bad)}")
    if errors:
        raise R36Error("debugfs falhou ao aplicar o STORAGE:\n  " + "\n  ".join(errors))


def fsck(image) -> None:
    p = run(["e2fsck", "-fn", str(image)], check=False)
    if p.returncode != 0:
        raise R36Error(f"e2fsck -fn falhou no STORAGE (código {p.returncode}):\n{p.stdout}{p.stderr}")


def set_label(image, label) -> None:
    run(["tune2fs", "-L", label, str(image)])


def get_label(image) -> str:
    out = run(["dumpe2fs", "-h", str(image)]).stdout
    m = re.search(r"^Filesystem volume name:\s*(.*)$", out, re.M)
    v = m.group(1).strip() if m else ""
    return "" if v == "<none>" else v
