"""MBR, cadeia de EBRs e tabela Allwinner softw411.

A bootarea nunca é regenerada: só a entrada 1 do MBR (p1) é editada.
"""

import struct
import zlib
from dataclasses import dataclass

from .errors import R36Error

SECTOR = 512
ENTRY_OFF = 0x1BE
ENTRY_SIZE = 16
SIG = b"\x55\xaa"
LBA_ONLY_CHS = b"\xfe\xff\xff"
EXTENDED_TYPES = (0x05, 0x0F, 0x85)

P1_CANONICAL_START = 4956160
P1_TYPE_FAT32_LBA = 0x0C
P1_ALIGNMENT_BYTES = 4 * 1024 * 1024

SOFTW411_MAGIC = b"softw411"
SOFTW411_SIZE = 16 * 1024
SOFTW411_PART_OFF = 0x20
SOFTW411_PART_SIZE = 128


@dataclass(frozen=True)
class MbrEntry:
    index: int  # 1..4
    status: int
    chs_start: bytes
    type: int
    chs_end: bytes
    start: int
    sectors: int

    @property
    def empty(self):
        return self.type == 0 and self.start == 0 and self.sectors == 0


@dataclass(frozen=True)
class Logical:
    number: int  # 5, 6, ...
    ebr_sector: int
    type: int
    start: int  # absoluto
    sectors: int


def parse_mbr(sector0: bytes) -> list:
    if len(sector0) < SECTOR or sector0[510:512] != SIG:
        raise R36Error("MBR inválido: assinatura 55AA ausente no setor 0")
    entries = []
    for i in range(4):
        e = sector0[ENTRY_OFF + i * ENTRY_SIZE: ENTRY_OFF + (i + 1) * ENTRY_SIZE]
        start, sectors = struct.unpack_from("<II", e, 8)
        entries.append(MbrEntry(i + 1, e[0], bytes(e[1:4]), e[4], bytes(e[5:8]), start, sectors))
    return entries


def parse_ebr_chain(read_sector, ext_start, max_logicals=32) -> list:
    """Segue a cadeia de EBRs. Para quando o link está vazio ou o EBR não tem assinatura
    (a base aponta para um EBR vazio no setor 5: quirk mantido)."""
    logicals = []
    ebr = ext_start
    seen = set()
    while len(logicals) < max_logicals and ebr not in seen:
        seen.add(ebr)
        data = read_sector(ebr)
        if data[510:512] != SIG:
            break
        e1 = data[ENTRY_OFF: ENTRY_OFF + 16]
        e2 = data[ENTRY_OFF + 16: ENTRY_OFF + 32]
        rel, size = struct.unpack_from("<II", e1, 8)
        if e1[4] != 0 and size:
            logicals.append(Logical(5 + len(logicals), ebr, e1[4], ebr + rel, size))
        nrel, nsize = struct.unpack_from("<II", e2, 8)
        if e2[4] not in EXTENDED_TYPES or nrel == 0:
            break
        ebr = ext_start + nrel
    return logicals


def set_p1(sector0: bytes, start: int, sectors: int) -> bytes:
    """Devolve o setor 0 com só a entrada 1 alterada: mesmo LBA de início, novo tamanho,
    CHS final FE FF FF (LBA-only). Status, tipo e CHS inicial ficam como estão."""
    parse_mbr(sector0)
    b = bytearray(sector0)
    off = ENTRY_OFF
    b[off + 5: off + 8] = LBA_ONLY_CHS
    struct.pack_into("<II", b, off + 8, start, sectors)
    return bytes(b)


def p1_entry_bytes(sector0: bytes) -> bytes:
    return bytes(sector0[ENTRY_OFF: ENTRY_OFF + ENTRY_SIZE])


def replace_p1_entry(sector0: bytes, entry: bytes) -> bytes:
    assert len(entry) == ENTRY_SIZE
    b = bytearray(sector0)
    b[ENTRY_OFF: ENTRY_OFF + ENTRY_SIZE] = entry
    return bytes(b)


def build_canonical_p1_entry(target_size_bytes: int) -> bytes:
    p1_start_bytes = P1_CANONICAL_START * SECTOR
    if target_size_bytes <= p1_start_bytes:
        raise R36Error(f"tamanho do alvo insuficiente para a partição p1 ({target_size_bytes} bytes)")
    available_bytes = target_size_bytes - p1_start_bytes
    sectors = (available_bytes // P1_ALIGNMENT_BYTES) * (P1_ALIGNMENT_BYTES // SECTOR)
    if sectors <= 0:
        raise R36Error(f"tamanho do alvo insuficiente para a partição p1 ({target_size_bytes} bytes)")
    return struct.pack("<B3sB3sII", 0x00, LBA_ONLY_CHS, P1_TYPE_FAT32_LBA, LBA_ONLY_CHS, P1_CANONICAL_START, sectors)


@dataclass(frozen=True)
class SunxiPart:
    name: str
    classname: str
    addr: int  # setores, relativo ao início da softw411
    length: int  # setores (0 = até o fim)

    def absolute_start(self, softw411_sector):
        return softw411_sector + self.addr


@dataclass(frozen=True)
class Softw411:
    crc_ok: bool
    version: int
    copy: int
    parts: tuple


def _cstr(b):
    return b.split(b"\0", 1)[0].decode("ascii", errors="replace")


def parse_softw411(data: bytes) -> Softw411:
    if len(data) < SOFTW411_PART_OFF or data[8:16] != SOFTW411_MAGIC:
        raise R36Error("tabela softw411 não encontrada (assinatura ausente)")
    crc, version = struct.unpack_from("<II", data, 0)
    copy, _index, count, _stamp = struct.unpack_from("<IIII", data, 16)
    if count > 120:
        raise R36Error(f"softw411: número de partições absurdo ({count})")
    need = SOFTW411_PART_OFF + count * SOFTW411_PART_SIZE
    if len(data) < need:
        raise R36Error(f"softw411: dados insuficientes ({len(data)} < {need})")
    parts = []
    for i in range(count):
        o = SOFTW411_PART_OFF + i * SOFTW411_PART_SIZE
        addrhi, addrlo, lenhi, lenlo = struct.unpack_from("<IIII", data, o)
        parts.append(SunxiPart(
            name=_cstr(data[o + 32: o + 48]),
            classname=_cstr(data[o + 16: o + 32]),
            addr=(addrhi << 32) | addrlo,
            length=(lenhi << 32) | lenlo,
        ))
    crc_ok = len(data) >= SOFTW411_SIZE and zlib.crc32(data[4:SOFTW411_SIZE]) == crc
    return Softw411(crc_ok, version, copy, tuple(parts))


def read_layout(read):
    """Lê MBR, lógicas e softw411. `read(offset, length) -> bytes`."""
    sector0 = read(0, SECTOR)
    entries = parse_mbr(sector0)
    ext = next((e for e in entries if e.type in EXTENDED_TYPES), None)
    logicals = []
    if ext:
        logicals = parse_ebr_chain(lambda s: read(s * SECTOR, SECTOR), ext.start)
    return sector0, entries, logicals


def describe(entries, logicals, sw=None, softw411_sector=40960):
    """Tabela legível (usada em testes e no dry-run)."""
    lines = []
    for e in entries:
        if not e.empty:
            lines.append(f"p{e.index}  tipo {e.type:02x}  início {e.start:>9}  setores {e.sectors:>9}")
    for lg in logicals:
        lines.append(f"p{lg.number}  tipo {lg.type:02x}  início {lg.start:>9}  setores {lg.sectors:>9}  (EBR {lg.ebr_sector})")
    if sw:
        for p in sw.parts:
            lines.append(f"softw411 {p.name:<10} início {p.absolute_start(softw411_sector):>9}  setores {p.length:>9}")
    return "\n".join(lines)
