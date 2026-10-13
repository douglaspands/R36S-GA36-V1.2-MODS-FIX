"""Bootarea, montagem da imagem completa e verificação estrutural contra a base (D7)."""

import hashlib
import os
import subprocess

from . import layout
from .errors import R36Error
from .util import CHUNK, copy_region, sha256_file

SECTOR = 512


def make_bootarea(cfg, base, card_sectors) -> bytes:
    """Setores 0..73727 da base byte a byte, só com a entrada 1 do MBR ajustada."""
    with open(base, "rb") as f:
        data = f.read(cfg.bootarea_size)
    roms = cfg.part("roms")
    sector0 = layout.set_p1(data[:SECTOR], roms.start, card_sectors - roms.start)
    return sector0 + data[SECTOR:]


def assemble(out_img, card_bytes, regions) -> None:
    """regions: [(arquivo, offset no cartão, bytes a copiar)]. Resultado esparso."""
    with open(out_img, "wb") as f:
        f.truncate(card_bytes)
    for src, offset, length in regions:
        if offset + length > card_bytes:
            raise R36Error(f"região {src} passa do fim da imagem")
        copy_region(src, out_img, dst_offset=offset, length=length)


def verify_structure(cfg, img, base, card_sectors) -> None:
    """Falha se a imagem divergir da base fora do permitido."""
    errors = []
    with open(img, "rb") as fi, open(base, "rb") as fb:
        a = fi.read(cfg.bootarea_size)
        b = fb.read(cfg.bootarea_size)
    lo, hi = layout.ENTRY_OFF, layout.ENTRY_OFF + layout.ENTRY_SIZE
    if len(a) != len(b):
        errors.append("bootarea com tamanho diferente")
    else:
        masked = a[:lo] + b[lo:hi] + a[hi:]  # ignora só a entrada da p1
        if masked != b:
            sectors = [s for s in range(len(a) // SECTOR)
                       if masked[s * SECTOR:(s + 1) * SECTOR] != b[s * SECTOR:(s + 1) * SECTOR]]
            errors.append(
                f"bootarea difere da base em {len(sectors)} setor(es): {sectors[:10]}"
                + ("..." if len(sectors) > 10 else "")
            )
    ea, eb = layout.parse_mbr(a[:SECTOR]), layout.parse_mbr(b[:SECTOR])
    roms = cfg.part("roms")
    p1 = ea[0]
    if p1.start != eb[0].start or p1.start != roms.start:
        errors.append(f"p1 começa em {p1.start}, esperado {roms.start}")
    if p1.sectors != card_sectors - roms.start:
        errors.append(f"p1 tem {p1.sectors} setores, esperado {card_sectors - roms.start} (até o fim)")
    if p1.type != eb[0].type:
        errors.append(f"tipo da p1 mudou: {p1.type:02x} != {eb[0].type:02x}")
    for x, y in zip(ea[1:], eb[1:]):
        if x != y:
            errors.append(f"entrada {x.index} do MBR difere da base")

    def read_from(path):
        def read(off, n):
            with open(path, "rb") as f:
                f.seek(off)
                return f.read(n)
        return read

    _, _, la = layout.read_layout(read_from(img))
    _, _, lb = layout.read_layout(read_from(base))
    if la != lb:
        errors.append("partições lógicas (EBRs) diferem da base")
    off = cfg.softw411_sector * SECTOR
    swa = layout.parse_softw411(a[off: off + layout.SOFTW411_SIZE])
    swb = layout.parse_softw411(b[off: off + layout.SOFTW411_SIZE])
    if swa != swb:
        errors.append("tabela softw411 difere da base")
    for key in ("env", "kernel"):
        p = cfg.part(key)
        if sha256_file(img, p.size, p.offset) != sha256_file(base, p.size, p.offset):
            errors.append(f"p{p.number} ({key}) difere da base")
    if os.path.getsize(img) != card_sectors * SECTOR:
        errors.append(f"imagem com {os.path.getsize(img)} bytes, esperado {card_sectors * SECTOR}")
    if errors:
        raise R36Error("verificação estrutural falhou:\n  " + "\n  ".join(errors))


def compress(img, out_xz) -> tuple:
    """xz -T0 da imagem completa; devolve (sha256 da imagem crua, sha256 do .xz)."""
    raw = hashlib.sha256()
    with open(out_xz, "wb") as fo:
        proc = subprocess.Popen(["xz", "-T0", "-c", "-z", "-"], stdin=subprocess.PIPE, stdout=fo)
        try:
            with open(img, "rb") as fi:
                for buf in iter(lambda: fi.read(CHUNK), b""):
                    raw.update(buf)
                    proc.stdin.write(buf)
            proc.stdin.close()
        except BaseException:
            proc.kill()
            proc.wait()
            raise
        if proc.wait() != 0:
            raise R36Error(f"xz falhou (código {proc.returncode})")
    return raw.hexdigest(), sha256_file(out_xz)
