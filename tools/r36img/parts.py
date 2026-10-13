"""Construção das imagens de partição (D5, D6, D8)."""

import os
import shutil

from . import ext4, fat, mtools, squash
from .errors import R36Error
from .util import MIB, extract_region, fmt_mib, run

WRITE_ALIGN = 4 * MIB


# ------------------------------------------------------------------ BOOT (p2)

def check_boot_limit(img, limit) -> fat.Extent:
    """Todo cluster alocado, FATs e raiz da p2 dentro de `limit` bytes; arquivo com `limit` bytes."""
    ext = fat.extent(img)
    end = max(ext.used_end, ext.root_dir_end, os.path.getsize(img))
    if end > limit:
        raise R36Error(
            f"BOOT (p2) excede o limite de {fmt_mib(limit)}: ocupa até o byte {end} "
            f"({end - limit} bytes = {fmt_mib(end - limit)} além do permitido)"
        )
    return ext


def fsck_boot(img, declared_size, work):
    """fsck.fat na p2. A FAT declara 128 MiB e a imagem tem 16 MiB: checa uma cópia
    esparsa completada com zeros até o tamanho declarado (nada é alocado além de 16 MiB)."""
    padded = work / "boot-fsck.img"
    shutil.copyfile(img, padded)
    with open(padded, "r+b") as f:
        f.truncate(declared_size)
    try:
        p = run(["fsck.fat", "-n", str(padded)], check=False)
    finally:
        padded.unlink()
    if p.returncode == 0:
        return
    # A p2 de fábrica não tem a assinatura 0x29 no setor de boot, então o label só
    # existe no diretório raiz; o fsck.fat reclama disso já na base. Só isso é tolerado.
    issues = [l for l in (p.stdout + p.stderr).splitlines()
              if l.strip() and not l.startswith("fsck.fat ") and not l.startswith(str(padded))
              and "Leaving filesystem unchanged" not in l]
    tolerated = ("stored in root directory and label '' stored in boot sector and different",
                 "Auto-copying volume label from root directory to boot sector")
    if p.returncode != 1 or any(not any(t in l for t in tolerated) for l in issues):
        raise R36Error("fsck.fat encontrou problemas na p2:\n" + p.stdout + p.stderr)


def build_boot(cfg, base, work, plan):
    p = cfg.part("boot")
    out = work / "boot.img"
    extract_region(base, out, p.offset, p.write_size)
    mtools.apply_plan(out, plan)
    mtools.set_label(out, p.label)
    check_boot_limit(out, p.write_size)
    fsck_boot(out, fat.read_info(out).size, work)
    return out


# ------------------------------------------------------------ SYSTEM (p7, FAT)

SYSTEM_NAME = "SYSTEM"
BUILD_INFO_NAME = "R36-BUILD.txt"


def _clusters(n, cb):
    return (n + cb - 1) // cb


def build_system_part(cfg, base, work, system_sq, build_info_text):
    p = cfg.part("system")
    out = work / "system.img"
    extract_region(base, out, p.offset, p.size)
    return update_system_part(out, system_sq, build_info_text, p.label, work)


def update_system_part(img, system_sq, build_info_text, label, work):
    """Substitui o SYSTEM, grava R36-BUILD.txt e aplica o label, checando a capacidade."""
    ext = fat.extent(img)
    cb = ext.info.cluster_bytes
    entries = mtools.listing(img)
    by_key = {k.casefold(): (k, e) for k, e in entries.items()}
    if SYSTEM_NAME.casefold() not in by_key:
        raise R36Error("p7 não contém o arquivo SYSTEM")
    old_sys = int(by_key[SYSTEM_NAME.casefold()][1].size)
    old_txt = int(by_key[BUILD_INFO_NAME.casefold()][1].size) if BUILD_INFO_NAME.casefold() in by_key else 0
    txt_path = work / BUILD_INFO_NAME
    txt_path.write_text(build_info_text, encoding="utf-8")
    new_sys = os.path.getsize(system_sq)
    new_txt = os.path.getsize(txt_path)
    available = (ext.free_clusters + _clusters(old_sys, cb) + _clusters(old_txt, cb)) * cb
    needed = (_clusters(new_sys, cb) + _clusters(new_txt, cb)) * cb
    if needed > available:
        raise R36Error(
            f"SYSTEM grande demais para a p7: precisa de {needed} bytes ({fmt_mib(needed)}), "
            f"disponível {available} bytes ({fmt_mib(available)}); SYSTEM gerado tem {new_sys} bytes"
        )
    mtools.copy_in(img, system_sq, SYSTEM_NAME)
    mtools.copy_in(img, txt_path, BUILD_INFO_NAME)
    mtools.set_label(img, label)
    return img


# ------------------------------------------------------------- STORAGE (p8)

def finish_storage(img, plan, label):
    """Aplica a camada storage numa cópia da p8 já extraída, confere e aplica o label."""
    ext4.apply_plan(img, plan)
    diffs = squash.compare(plan.final, ext4.listing(img))
    if diffs:
        raise R36Error("STORAGE gerado diverge do esperado:\n  " + "\n  ".join(diffs[:200]))
    ext4.set_label(img, label)
    ext4.fsck(img)
    return img


# --------------------------------------------------------------- ROMS (p1)

def build_roms(cfg, base, work, plan, card_sectors, volume_id: int):
    """Recria a p1 em FAT32 do tamanho do cartão e copia o conteúdo da base + camada roms.
    Devolve (caminho, write_length, Extent)."""
    p = cfg.part("roms")
    sectors = card_sectors - p.start
    size = sectors * 512
    out = work / "roms.img"
    with open(out, "wb") as f:
        f.truncate(size)
    run(["mkfs.fat", "-F", "32", "-S", "512", "-h", str(p.start), "-n", p.label,
         "-i", f"{volume_id & 0xFFFFFFFF:08x}", str(out)])
    staging = work / "roms-base"
    staging.mkdir()
    mtools.copy_tree_out(base, staging, p.offset)
    mtools.copy_tree_in(out, staging)
    mtools.apply_plan(out, plan)
    run(["fsck.fat", "-n", str(out)])
    ext = fat.extent(out)
    write_length = min(fat.align_up(ext.used_end, WRITE_ALIGN), size)
    return out, write_length, ext
