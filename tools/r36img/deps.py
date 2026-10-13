"""Checagem das dependências do host (Linux/Fedora)."""

import re
import shutil
import subprocess

from .errors import R36Error

# comando -> pacote do Fedora
BUILD_TOOLS = {
    "mksquashfs": "squashfs-tools",
    "unsquashfs": "squashfs-tools",
    "mcopy": "mtools",
    "mdir": "mtools",
    "mlabel": "mtools",
    "mmd": "mtools",
    "mdel": "mtools",
    "mdeltree": "mtools",
    "mkfs.fat": "dosfstools",
    "fsck.fat": "dosfstools",
    "debugfs": "e2fsprogs",
    "e2fsck": "e2fsprogs",
    "tune2fs": "e2fsprogs",
    "xz": "xz",
}

FLASH_TOOLS = {
    "lsblk": "util-linux",
    "dd": "coreutils",
    "sudo": "sudo",
    "mdir": "mtools",
}

MIN_SQUASHFS = (4, 6)


def _which_missing(tools, path):
    return {cmd: pkg for cmd, pkg in tools.items() if shutil.which(cmd, path=path) is None}


def _squashfs_problems(path):
    problems = []
    for cmd in ("mksquashfs", "unsquashfs"):
        exe = shutil.which(cmd, path=path)
        if exe is None:
            continue
        out = subprocess.run([exe, "-version"], capture_output=True, text=True)
        m = re.search(r"version (\d+)\.(\d+)", out.stdout + out.stderr)
        if not m or (int(m.group(1)), int(m.group(2))) < MIN_SQUASHFS:
            found = m.group(0) if m else "desconhecida"
            problems.append(f"{cmd}: versão {found}, é preciso ≥ {'.'.join(map(str, MIN_SQUASHFS))}")
    exe = shutil.which("mksquashfs", path=path)
    if exe is not None:
        out = subprocess.run([exe, "-help"], capture_output=True, text=True)
        text = out.stdout + out.stderr
        section = text.split("Compressors available", 1)[-1] if "Compressors available" in text else ""
        if not re.search(r"^\s+lzo\b", section, re.M):
            problems.append("mksquashfs: sem suporte a compressão LZO")
    return problems


def check(tools=BUILD_TOOLS, path=None, squashfs=True):
    """Falha com a lista do que falta e o `dnf install` sugerido."""
    missing = _which_missing(tools, path)
    problems = [f"{cmd} (pacote {pkg}) não encontrado" for cmd, pkg in sorted(missing.items())]
    if squashfs:
        problems += _squashfs_problems(path)
    if problems:
        pkgs = sorted(set(missing.values()) | ({"squashfs-tools"} if squashfs and len(problems) > len(missing) else set()))
        msg = "dependências do host faltando ou inadequadas:\n"
        msg += "\n".join(f"  - {p}" for p in problems)
        msg += f"\n\nInstale com:\n  sudo dnf install {' '.join(pkgs)}"
        raise R36Error(msg)


def check_build(path=None):
    check(BUILD_TOOLS, path=path, squashfs=True)


def check_flash(path=None):
    check(FLASH_TOOLS, path=path, squashfs=False)
