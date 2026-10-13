"""Parser mínimo de FAT12/16/32: geometria, extensão de FATs/raiz e último cluster usado.

Offsets devolvidos são relativos ao início do filesystem (partição).
"""

import struct
from array import array
from dataclasses import dataclass

from .errors import R36Error


@dataclass(frozen=True)
class FatInfo:
    fat_type: int  # 12, 16 ou 32
    bytes_per_sector: int
    sectors_per_cluster: int
    reserved_sectors: int
    num_fats: int
    fat_sectors: int
    root_entries: int
    total_sectors: int
    hidden_sectors: int
    root_cluster: int  # só FAT32

    @property
    def cluster_bytes(self):
        return self.bytes_per_sector * self.sectors_per_cluster

    @property
    def fat_start(self):
        return self.reserved_sectors * self.bytes_per_sector

    @property
    def fats_end(self):
        return self.fat_start + self.num_fats * self.fat_sectors * self.bytes_per_sector

    @property
    def root_dir_bytes(self):
        return self.root_entries * 32

    @property
    def root_dir_end(self):
        """Fim do diretório raiz fixo (FAT12/16). Em FAT32 = fim dos FATs."""
        return self.fats_end + self.root_dir_bytes

    @property
    def data_start(self):
        rd = (self.root_dir_bytes + self.bytes_per_sector - 1) // self.bytes_per_sector
        return self.fats_end + rd * self.bytes_per_sector

    @property
    def cluster_count(self):
        data_sectors = self.total_sectors - self.data_start // self.bytes_per_sector
        return data_sectors // self.sectors_per_cluster

    @property
    def size(self):
        return self.total_sectors * self.bytes_per_sector

    def cluster_end(self, n):
        return self.data_start + (n - 1) * self.cluster_bytes


def parse_boot_sector(bs: bytes) -> FatInfo:
    if len(bs) < 512:
        raise R36Error("FAT: setor de boot curto")
    bps, spc, rsv, nfats, rootent, tot16, _media, fatsz16 = struct.unpack_from("<HBHBHHBH", bs, 11)
    hidden, tot32 = struct.unpack_from("<II", bs, 28)
    if bps not in (512, 1024, 2048, 4096) or spc == 0 or spc & (spc - 1) or nfats == 0:
        raise R36Error("FAT: BPB inválido")
    fatsz = fatsz16
    root_cluster = 0
    if fatsz16 == 0:
        fatsz, _flags, _ver, root_cluster = struct.unpack_from("<IHHI", bs, 36)
    total = tot16 or tot32
    info = FatInfo(0, bps, spc, rsv, nfats, fatsz, rootent, total, hidden, root_cluster)
    n = info.cluster_count
    fat_type = 12 if n < 4085 else 16 if n < 65525 else 32
    if fat_type == 32 and fatsz16 != 0:
        raise R36Error("FAT: BPB inconsistente (FAT32 com tamanho de FAT de 16 bits)")
    return FatInfo(fat_type, bps, spc, rsv, nfats, fatsz, rootent, total, hidden, root_cluster)


def _open(path, offset):
    f = open(path, "rb")
    f.seek(offset)
    return f


def read_info(path, offset=0) -> FatInfo:
    with _open(path, offset) as f:
        return parse_boot_sector(f.read(512))


def read_fat(path, info: FatInfo, offset=0):
    """Entradas do primeiro FAT (índice = número do cluster)."""
    n = info.cluster_count + 2
    with _open(path, offset + info.fat_start) as f:
        if info.fat_type == 12:
            raw = f.read((n * 3 + 1) // 2)
            out = []
            for i in range(n):
                b = (i * 3) // 2
                v = raw[b] | (raw[b + 1] << 8) if b + 1 < len(raw) else 0
                out.append(v >> 4 if i & 1 else v & 0xFFF)
            return out
        width = 2 if info.fat_type == 16 else 4
        raw = f.read(n * width)
    arr = array("H" if width == 2 else "I")
    arr.frombytes(raw[: len(raw) // width * width])
    if width == 4:
        return [v & 0x0FFFFFFF for v in arr]
    return list(arr)


def last_allocated_cluster(fat) -> int:
    for i in range(len(fat) - 1, 1, -1):
        if fat[i]:
            return i
    return 0


def free_clusters(fat) -> int:
    return sum(1 for v in fat[2:] if v == 0)


@dataclass(frozen=True)
class Extent:
    info: FatInfo
    fats_end: int
    root_dir_end: int
    last_cluster: int
    last_cluster_end: int  # 0 se nenhum cluster alocado
    used_end: int  # max(metadados, último cluster)
    free_clusters: int


def extent(path, offset=0) -> Extent:
    info = read_info(path, offset)
    fat = read_fat(path, info, offset)
    last = last_allocated_cluster(fat)
    last_end = info.cluster_end(last) if last else 0
    meta_end = info.data_start
    return Extent(
        info=info,
        fats_end=info.fats_end,
        root_dir_end=info.root_dir_end,
        last_cluster=last,
        last_cluster_end=last_end,
        used_end=max(meta_end, last_end),
        free_clusters=free_clusters(fat),
    )


def align_up(n, a):
    return (n + a - 1) // a * a
