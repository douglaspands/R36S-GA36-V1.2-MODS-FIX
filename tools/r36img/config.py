"""Leitura de config/base.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import REPO_ROOT
from .errors import R36Error

SECTOR = 512


@dataclass(frozen=True)
class Partition:
    key: str
    number: int
    start: int  # setor
    sectors: int  # tamanho no MBR da base
    fs: str
    label: str | None = None
    write_sectors: int | None = None

    @property
    def offset(self):
        return self.start * SECTOR

    @property
    def size(self):
        return self.sectors * SECTOR

    @property
    def write_size(self):
        return (self.write_sectors or self.sectors) * SECTOR


@dataclass(frozen=True)
class Config:
    root: Path
    base_path: Path
    base_sha256: str
    base_size: int
    image_prefix: str
    default_size_mib: int
    min_size_mib: int
    align_mib: int
    bootarea_sectors: int
    softw411_sector: int
    extended: Partition
    partitions: dict

    def part(self, key) -> Partition:
        return self.partitions[key]

    @property
    def bootarea_size(self):
        return self.bootarea_sectors * SECTOR


def load(root: Path | None = None, path: Path | None = None) -> Config:
    root = Path(root or REPO_ROOT)
    path = Path(path or root / "config" / "base.toml")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise R36Error(f"configuração não encontrada: {path}")
    except tomllib.TOMLDecodeError as e:
        raise R36Error(f"{path}: TOML inválido: {e}")
    try:
        lay = data["layout"]
        if lay.get("sector_size", SECTOR) != SECTOR:
            raise R36Error("só setores de 512 bytes são suportados")
        parts = {
            key: Partition(key=key, **vals) for key, vals in data["partitions"].items()
        }
        for key in ("boot", "env", "kernel", "system", "storage", "roms"):
            if key not in parts:
                raise R36Error(f"{path}: partição '{key}' ausente")
        ext = lay["extended"]
        return Config(
            root=root,
            base_path=root / data["base"]["path"],
            base_sha256=data["base"]["sha256"].lower(),
            base_size=data["base"]["size_bytes"],
            image_prefix=data["output"]["image_prefix"],
            default_size_mib=data["card"]["default_size_mib"],
            min_size_mib=data["card"]["min_size_mib"],
            align_mib=data["card"]["align_mib"],
            bootarea_sectors=lay["bootarea_sectors"],
            softw411_sector=lay["softw411_sector"],
            extended=Partition(key="extended", fs="extended", **ext),
            partitions=parts,
        )
    except (KeyError, TypeError) as e:
        raise R36Error(f"{path}: campo ausente ou inválido: {e}")
