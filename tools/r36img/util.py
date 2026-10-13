"""Utilitários comuns: subprocess, hashes e cópia de regiões."""

import hashlib
import os
import subprocess
import sys

from .errors import R36Error

CHUNK = 4 * 1024 * 1024
MIB = 1024 * 1024


def log(msg=""):
    print(msg, flush=True)


def warn(msg):
    print(f"AVISO: {msg}", file=sys.stderr, flush=True)


def run(cmd, *, env=None, input=None, check=True, capture=True, text=True):
    """Roda um comando (lista de argumentos, sem shell)."""
    full_env = None
    if env:
        full_env = dict(os.environ)
        full_env.update(env)
    try:
        proc = subprocess.run(
            [str(c) for c in cmd],
            env=full_env,
            input=input,
            capture_output=capture,
            text=text,
        )
    except FileNotFoundError:
        raise R36Error(f"comando não encontrado: {cmd[0]}")
    if check and proc.returncode != 0:
        out = ""
        if capture:
            out = (proc.stderr or "") + (proc.stdout or "")
            if not text:
                out = out.decode(errors="replace")
        raise R36Error(
            f"falha ao rodar {' '.join(str(c) for c in cmd)} (código {proc.returncode})\n{out.strip()}"
        )
    return proc


def sha256_file(path, length=None, offset=0):
    """sha256 de um arquivo, opcionalmente só de [offset, offset+length)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        f.seek(offset)
        remaining = length
        while remaining is None or remaining > 0:
            n = CHUNK if remaining is None else min(CHUNK, remaining)
            buf = f.read(n)
            if not buf:
                break
            h.update(buf)
            if remaining is not None:
                remaining -= len(buf)
        if remaining:
            raise R36Error(f"{path}: arquivo menor que o esperado ({remaining} bytes faltando)")
    return h.hexdigest()


def copy_region(src, dst, *, src_offset=0, dst_offset=0, length, sparse=True):
    """Copia `length` bytes de src para dst; blocos zerados viram buracos (esparso)."""
    zero = bytes(CHUNK)
    with open(src, "rb") as fi, open(dst, "r+b") as fo:
        fi.seek(src_offset)
        pos = 0
        while pos < length:
            n = min(CHUNK, length - pos)
            buf = fi.read(n)
            if len(buf) != n:
                raise R36Error(f"{src}: leitura curta em {src_offset + pos}")
            if not (sparse and buf == zero[:n]):
                fo.seek(dst_offset + pos)
                fo.write(buf)
            pos += n


def extract_region(src, dst, offset, length):
    """Cria dst com `length` bytes de src a partir de offset (esparso)."""
    with open(dst, "wb") as f:
        f.truncate(length)
    copy_region(src, dst, src_offset=offset, length=length)


def fmt_mib(n):
    s = f"{n / MIB:,.1f}"  # 15,000.0 -> 15.000,0 (pt-BR)
    return s.replace(",", "_").replace(".", ",").replace("_", ".") + " MiB"
