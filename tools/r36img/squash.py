"""Reempacotamento do SYSTEM (squashfs) preservando metadados via pseudo-file (D4)."""

import hashlib
import os
import re
import stat
import struct
from dataclasses import dataclass, replace

from .errors import R36Error
from .util import run

# Parâmetros da base (unsquashfs -s): lzo1x_999, nível 9, blocos de 512 KiB.
MKSQUASHFS_ARGS = [
    "-comp", "lzo", "-Xalgorithm", "lzo1x_999", "-Xcompression-level", "9",
    "-b", "524288", "-noappend", "-no-xattrs", "-quiet", "-no-progress",
]

_LLN_RE = re.compile(
    r"^(?P<perms>[-dlcbps][-rwxsStT]{9}) (?P<uid>\d+)/(?P<gid>\d+)\s+"
    r"(?P<size>\d+|\d+,\s*\d+) (?P<mtime>\d{4}-\d\d-\d\d \d\d:\d\d) (?P<path>.*)$"
)
ROOT_PREFIX = "squashfs-root"


@dataclass(frozen=True)
class Entry:
    type: str  # '-', 'd', 'l', 'c', 'b', 'p', 's'
    mode: int  # permissões + setuid/setgid/sticky (sem o tipo)
    uid: int
    gid: int
    size: str  # tamanho em bytes, ou "maj,min" para dispositivos
    mtime: str | None = None
    target: str | None = None

    def lsmode(self):
        return symbolic_mode(self.type, self.mode)

    def describe(self):
        s = f"{self.lsmode()} {self.uid}/{self.gid} {self.size}"
        if self.target is not None:
            s += f" -> {self.target}"
        return s


def parse_perms(perms: str) -> int:
    if len(perms) != 10:
        raise ValueError(perms)
    mode = 0
    bits = [(0o400, 0o200, 0o100, 0o4000), (0o040, 0o020, 0o010, 0o2000), (0o004, 0o002, 0o001, 0o1000)]
    for i, (r, w, x, special) in enumerate(bits):
        c = perms[1 + i * 3: 4 + i * 3]
        if c[0] == "r":
            mode |= r
        if c[1] == "w":
            mode |= w
        if c[2] in "xst":
            mode |= x
        if c[2] in "sStT":
            mode |= special
    return mode


def symbolic_mode(type_: str, mode: int) -> str:
    out = [type_]
    specials = ((0o4000, "s"), (0o2000, "s"), (0o1000, "t"))
    for i, shift in enumerate((6, 3, 0)):
        p = (mode >> shift) & 7
        out.append("r" if p & 4 else "-")
        out.append("w" if p & 2 else "-")
        sp, ch = specials[i]
        if mode & sp:
            out.append(ch if p & 1 else ch.upper())
        else:
            out.append("x" if p & 1 else "-")
    return "".join(out)


def parse_lln(text: str) -> dict:
    """Converte a saída de `unsquashfs -lln` em {caminho relativo: Entry}. Raiz = ''."""
    entries = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        m = _LLN_RE.match(line)
        if not m:
            continue  # cabeçalhos/avisos do unsquashfs
        type_ = m["perms"][0]
        path = m["path"]
        target = None
        if type_ == "l":
            path, sep, target = path.partition(" -> ")
            if not sep:
                raise R36Error(f"unsquashfs: symlink sem alvo na linha: {line!r}")
        if path == ROOT_PREFIX:
            path = ""
        elif path.startswith(ROOT_PREFIX + "/"):
            path = path[len(ROOT_PREFIX) + 1:]
        else:
            raise R36Error(f"unsquashfs: caminho inesperado: {line!r}")
        size = re.sub(r"\s+", "", m["size"])
        entries[path] = Entry(
            type=type_, mode=parse_perms(m["perms"]), uid=int(m["uid"]), gid=int(m["gid"]),
            size=size, mtime=m["mtime"], target=target,
        )
    if "" not in entries:
        raise R36Error("unsquashfs -lln: raiz não encontrada na listagem")
    return entries


def listing(sq_path) -> dict:
    out = run(["unsquashfs", "-lln", "-d", ROOT_PREFIX, sq_path]).stdout
    return parse_lln(out)


def mkfs_time(sq_path) -> int:
    with open(sq_path, "rb") as f:
        sb = f.read(96)
    magic, _inodes, mtime = struct.unpack_from("<III", sb, 0)
    if magic != 0x73717368:
        raise R36Error(f"{sq_path}: não é um squashfs")
    return mtime


def superblock_info(sq_path) -> str:
    return run(["unsquashfs", "-s", sq_path]).stdout


def extract(sq_path, dest) -> dict:
    """Extrai como usuário comum e deixa tudo gravável pelo dono (os metadados reais
    ficam na tabela). Devolve {caminho: (atime, mtime) em ns} de diretórios, para
    restaurar depois da aplicação das features."""
    if os.path.exists(dest):
        raise R36Error(f"destino de extração já existe: {dest}")
    run(["unsquashfs", "-no-xattrs", "-quiet", "-no-progress", "-d", dest, sq_path])
    dir_times = {}
    for root, dirs, files in os.walk(dest):
        st = os.lstat(root)
        rel = os.path.relpath(root, dest)
        dir_times["" if rel == "." else rel] = st.st_mtime_ns
        os.chmod(root, stat.S_IMODE(st.st_mode) | 0o700)
        for name in files:
            p = os.path.join(root, name)
            st = os.lstat(p)
            if stat.S_ISREG(st.st_mode):
                os.chmod(p, stat.S_IMODE(st.st_mode) | 0o600)
    return dir_times


def restore_dir_times(tree, dir_times) -> None:
    """Restaura as mtimes dos diretórios que ainda existem (a aplicação de features
    altera as mtimes dos pais)."""
    for rel, mtime_ns in sorted(dir_times.items(), key=lambda kv: -kv[0].count("/")):
        p = os.path.join(tree, rel) if rel else tree
        if os.path.isdir(p) and not os.path.islink(p):
            os.utime(p, ns=(mtime_ns, mtime_ns), follow_symlinks=False)


def _quote(path: str) -> str:
    if "\n" in path:
        raise R36Error(f"nome com quebra de linha não suportado: {path!r}")
    return '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_pseudo_file(entries: dict, pf_path) -> None:
    """Uma linha `"<caminho>" m <modo> <uid> <gid>` para todo caminho (exceto a raiz)."""
    with open(pf_path, "w", encoding="utf-8", errors="surrogateescape") as f:
        for path in sorted(entries):
            if path == "":
                continue
            e = entries[path]
            f.write(f"{_quote(path)} m {e.mode:o} {e.uid} {e.gid}\n")


def mksquashfs(tree, out, pf_path, root: Entry, mkfs_time_value: int | None = None) -> None:
    if os.path.exists(out):
        os.unlink(out)
    cmd = ["mksquashfs", tree, out, "-pf", pf_path, *MKSQUASHFS_ARGS,
           "-root-mode", f"{root.mode:o}", "-root-uid", str(root.uid), "-root-gid", str(root.gid)]
    if mkfs_time_value is not None:
        cmd += ["-mkfs-time", str(mkfs_time_value)]
    run(cmd)


def compare(expected: dict, got: dict, *, check_mtime_for=()) -> list:
    """Lista divergências de metadados (tipo, modo, dono, tamanho, alvo; mtime para os
    caminhos em `check_mtime_for`)."""
    diffs = []
    for path in sorted(set(expected) | set(got)):
        shown = path or "/"
        e, g = expected.get(path), got.get(path)
        if g is None:
            diffs.append(f"{shown}: ausente no resultado (esperado {e.describe()})")
            continue
        if e is None:
            diffs.append(f"{shown}: inesperado no resultado ({g.describe()})")
            continue
        fields = ["type", "mode", "uid", "gid", "target"]
        if e.type != "d" and e.size is not None:
            fields.append("size")
        if path in check_mtime_for and e.mtime is not None:
            fields.append("mtime")
        bad = [f for f in fields if getattr(e, f) != getattr(g, f)]
        if bad:
            exp = e.describe() + (f" {e.mtime}" if "mtime" in bad else "")
            obt = g.describe() + (f" {g.mtime}" if "mtime" in bad else "")
            diffs.append(f"{shown}: esperado {exp}, obtido {obt}")
    return diffs


def tree_hashes(tree) -> dict:
    """sha256 de cada arquivo regular de uma árvore."""
    out = {}
    for root, _dirs, files in os.walk(tree):
        for name in files:
            p = os.path.join(root, name)
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            h = hashlib.sha256()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            out[os.path.relpath(p, tree)] = h.hexdigest()
    return out


def verify(sq_path, expected: dict, *, untouched=(), content_tree=None, work_dir=None) -> None:
    """Verificação pós-empacotamento. Metadados sempre; conteúdo se `content_tree`."""
    got = listing(sq_path)
    diffs = compare(expected, got, check_mtime_for=set(untouched))
    if diffs:
        raise R36Error(
            f"SYSTEM gerado diverge do esperado em {len(diffs)} caminho(s):\n  "
            + "\n  ".join(diffs[:200])
            + ("\n  ..." if len(diffs) > 200 else "")
        )
    if content_tree is not None:
        check_dir = os.path.join(work_dir, "system-check")
        extract(sq_path, check_dir)
        try:
            a, b = tree_hashes(content_tree), tree_hashes(check_dir)
        finally:
            run(["chmod", "-R", "u+rwX", check_dir])
            run(["rm", "-rf", check_dir])
        bad = sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p))
        if bad:
            raise R36Error(
                f"conteúdo do SYSTEM gerado diverge em {len(bad)} arquivo(s):\n  " + "\n  ".join(bad[:100])
            )


def with_mode(e: Entry, **kw) -> Entry:
    return replace(e, **kw)
