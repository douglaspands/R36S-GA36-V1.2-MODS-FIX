#!/usr/bin/env python3
"""Baixa e extrai as bibliotecas compartilhadas ausentes (libmodplug, libogg, libluajit) do Debian Bookworm armhf."""

import io
import re
import struct
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "work" / "cache" / "debs"
DEST_LIB = ROOT / "features" / "64-love2d" / "system" / "usr" / "lib"

URLS = [
    "http://deb.debian.org/debian/pool/main/libm/libmodplug/libmodplug1_0.8.9.0-3_armhf.deb",
    "http://deb.debian.org/debian/pool/main/libo/libogg/libogg0_1.3.5-3_armhf.deb",
    "http://deb.debian.org/debian/pool/main/l/luajit/libluajit-5.1-2_2.1.0~beta3+git20220320+dfsg-4.1+deb12u1_armhf.deb",
    # Fallback para luajit sem deb12u1 caso o espelho use a versão base
    "http://deb.debian.org/debian/pool/main/l/luajit/libluajit-5.1-2_2.1.0~beta3+git20220320+dfsg-4.1_armhf.deb",
]

def extract_ar(deb_bytes):
    """Extrai membros de um arquivo .deb (formato ar do Unix)."""
    if deb_bytes[:8] != b"!<arch>\n":
        raise ValueError("Não é um arquivo ar válido")
    pos = 8
    members = {}
    while pos < len(deb_bytes):
        header = deb_bytes[pos:pos+60]
        if len(header) < 60:
            break
        name = header[:16].decode("ascii", errors="ignore").strip().rstrip("/")
        size_str = header[48:58].decode("ascii", errors="ignore").strip()
        size = int(size_str)
        pos += 60
        data = deb_bytes[pos:pos+size]
        members[name] = data
        pos += size
        if size % 2 != 0:
            pos += 1
    return members

def download_file(url, dest_path):
    print(f"Baixando: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(data)
    return data

def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DEST_LIB.mkdir(parents=True, exist_ok=True)

    extracted_files = []

    # 1. libmodplug1
    deb_modplug = CACHE_DIR / "libmodplug1.deb"
    if not deb_modplug.is_file():
        download_file(URLS[0], deb_modplug)
    data = deb_modplug.read_bytes()
    ar = extract_ar(data)
    data_tar_key = [k for k in ar if k.startswith("data.tar")][0]
    with tarfile.open(fileobj=io.BytesIO(ar[data_tar_key]), mode="r:*") as tar:
        for member in tar.getmembers():
            if "libmodplug.so" in member.name and member.isfile():
                f = tar.extractfile(member)
                dest = DEST_LIB / Path(member.name).name
                dest.write_bytes(f.read())
                extracted_files.append(dest)
                print(f"Extraído: {dest}")

    # 2. libogg0
    deb_ogg = CACHE_DIR / "libogg0.deb"
    if not deb_ogg.is_file():
        download_file(URLS[1], deb_ogg)
    data = deb_ogg.read_bytes()
    ar = extract_ar(data)
    data_tar_key = [k for k in ar if k.startswith("data.tar")][0]
    with tarfile.open(fileobj=io.BytesIO(ar[data_tar_key]), mode="r:*") as tar:
        for member in tar.getmembers():
            if "libogg.so" in member.name and member.isfile():
                f = tar.extractfile(member)
                dest = DEST_LIB / Path(member.name).name
                dest.write_bytes(f.read())
                extracted_files.append(dest)
                print(f"Extraído: {dest}")

    # 3. libluajit-5.1-2
    deb_lua = CACHE_DIR / "libluajit.deb"
    if not deb_lua.is_file():
        try:
            download_file(URLS[2], deb_lua)
        except Exception:
            download_file(URLS[3], deb_lua)
    data = deb_lua.read_bytes()
    ar = extract_ar(data)
    data_tar_key = [k for k in ar if k.startswith("data.tar")][0]
    with tarfile.open(fileobj=io.BytesIO(ar[data_tar_key]), mode="r:*") as tar:
        for member in tar.getmembers():
            if "libluajit-5.1.so" in member.name and member.isfile():
                f = tar.extractfile(member)
                dest = DEST_LIB / Path(member.name).name
                dest.write_bytes(f.read())
                extracted_files.append(dest)
                print(f"Extraído: {dest}")

    # Criação dos symlinks padrão SONAME se necessário
    # libmodplug.so.1 -> libmodplug.so.1.0.0
    mod_real = list(DEST_LIB.glob("libmodplug.so.1.*"))
    if mod_real:
        soname = DEST_LIB / "libmodplug.so.1"
        if not soname.exists():
            import shutil
            shutil.copy2(mod_real[0], soname)
            print(f"Copiado soname: {soname}")

    # libogg.so.0 -> libogg.so.0.8.5
    ogg_real = list(DEST_LIB.glob("libogg.so.0.*"))
    if ogg_real:
        soname = DEST_LIB / "libogg.so.0"
        if not soname.exists():
            import shutil
            shutil.copy2(ogg_real[0], soname)
            print(f"Copiado soname: {soname}")

    # libluajit-5.1.so.2 -> libluajit-5.1.so.2.1.0
    lua_real = list(DEST_LIB.glob("libluajit-5.1.so.2.*"))
    if lua_real:
        soname = DEST_LIB / "libluajit-5.1.so.2"
        if not soname.exists():
            import shutil
            shutil.copy2(lua_real[0], soname)
            print(f"Copiado soname: {soname}")

    print("Concluído!")

if __name__ == "__main__":
    main()
