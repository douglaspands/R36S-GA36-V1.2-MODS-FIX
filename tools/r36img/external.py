"""Conteúdo externo das features: download com cache por sha256, extração segura e orçamento."""

import fnmatch
import hashlib
import os
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

from .errors import R36Error

MIB = 1024 * 1024
CACHE_SUBDIR = ("cache", "external")


def cache_dir(work_root) -> Path:
    return Path(work_root).joinpath(*CACHE_SUBDIR)


def cached_path(cache, ext) -> Path:
    return Path(cache) / f"{ext.sha256}.tar.gz"


def _sha256_of(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(feature, ext, cache) -> Path:
    """Garante o arquivo no cache (baixando se preciso) e devolve o caminho."""
    cache = Path(cache)
    dst = cached_path(cache, ext)
    if dst.is_file():
        got = _sha256_of(dst)
        if got != ext.sha256:
            raise R36Error(f"feature '{feature.id}': o cache {dst} está corrompido "
                           f"(sha256 {got}, esperado {ext.sha256}); apague-o e rode de novo")
        return dst
    cache.mkdir(parents=True, exist_ok=True)
    tmp = cache / f".{ext.sha256}.{os.getpid()}.part"
    h = hashlib.sha256()
    try:
        try:
            with urllib.request.urlopen(ext.url, timeout=60) as resp, open(tmp, "wb") as out:
                for chunk in iter(lambda: resp.read(1 << 20), b""):
                    h.update(chunk)
                    out.write(chunk)
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise R36Error(f"feature '{feature.id}': falha ao baixar {ext.url}: {e}")
        if h.hexdigest() != ext.sha256:
            raise R36Error(f"feature '{feature.id}': sha256 divergente para {ext.url}\n"
                           f"  esperado: {ext.sha256}\n  recebido: {h.hexdigest()}")
        os.replace(tmp, dst)
    finally:
        if tmp.exists():
            tmp.unlink()
    return dst


def _strip(name, n):
    parts = [p for p in name.split("/") if p not in ("", ".")]
    return "/".join(parts[n:]) if len(parts) > n else None


def extract(feature, ext, archive, dest):
    """Extrai `archive` em `dest` aplicando strip/exclude, recusando entradas inseguras."""
    dest = Path(dest)
    dest.mkdir(parents=True)
    with tarfile.open(archive) as tar:
        for m in tar:
            name = _strip(m.name, ext.strip)
            if name is None:
                continue
            if ".." in name.split("/") or m.name.startswith("/"):
                raise R36Error(f"feature '{feature.id}': {ext.url}: entrada recusada: {m.name!r} (caminho inseguro)")
            if m.islnk():
                raise R36Error(f"feature '{feature.id}': {ext.url}: entrada recusada: {m.name!r} (hard link)")
            if any(fnmatch.fnmatch(name, pat) for pat in ext.exclude):
                continue
            try:
                tar.extract(m.replace(name=name, deep=False), dest, filter="data")
            except tarfile.FilterError as e:
                raise R36Error(f"feature '{feature.id}': {ext.url}: entrada recusada: {m.name!r} ({e})")
    return dest


def tree_bytes(root) -> int:
    total = 0
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(dirpath, f)
            if not os.path.islink(p):
                total += os.lstat(p).st_size
    return total


def prepare(feats, cache, stage, offline=False):
    """Baixa, extrai e confere o orçamento dos externos das features. Preenche `feature.staged`
    com [(External, árvore extraída, bytes)]."""
    if offline:
        missing = [(f, x) for f in feats for x in f.externals if not cached_path(cache, x).is_file()]
        if missing:
            lines = [f"  {x.url}  (feature {f.id}, sha256 {x.sha256})" for f, x in missing]
            raise R36Error("modo --offline: faltam no cache (work/cache/external):\n" + "\n".join(lines))
    for f in feats:
        f.staged = []
        for n, x in enumerate(f.externals, 1):
            archive = fetch(f, x, cache)
            tree = extract(f, x, archive, Path(stage) / f.id / str(n))
            f.staged.append((x, tree, tree_bytes(tree)))
        if f.budget_mib is not None:
            total = sum(b for _x, _t, b in f.staged)
            if total > f.budget_mib * MIB:
                lines = [f"  {b / MIB:8.1f} MiB  {x.dest}" for x, _t, b in f.staged]
                raise R36Error(f"feature '{f.id}': conteúdo externo de {total / MIB:.1f} MiB passa do orçamento "
                               f"de {f.budget_mib} MiB:\n" + "\n".join(lines))
