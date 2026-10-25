#!/usr/bin/env python3
"""
generate_playlist.py
Gera playlists do RetroArch (.lpl) e EmulationStation (gamelist.xml)
e baixa thumbnails/boxarts oficiais do Libretro Thumbnails.
"""

import argparse
import difflib
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SYSTEMS_MAP = {
    "sega32x": {
        "libretro_name": "Sega - 32X",
        "core_path": "/tmp/cores/picodrive_libretro.so",
        "core_name": "Sega - MS/GG/MD/CD/32X (PicoDrive)",
        "exts": {".zip", ".7z", ".32x", ".bin"}
    },
    "megadrive": {
        "libretro_name": "Sega - Mega Drive - Genesis",
        "core_path": "/tmp/cores/genesis_plus_gx_libretro.so",
        "core_name": "Sega - MS/GG/MD/CD (Genesis Plus GX)",
        "exts": {".zip", ".7z", ".gen", ".bin", ".smd", ".md"}
    },
    "segacd": {
        "libretro_name": "Sega - Mega-CD - Sega CD",
        "core_path": "/tmp/cores/genesis_plus_gx_libretro.so",
        "core_name": "Sega - MS/GG/MD/CD (Genesis Plus GX)",
        "exts": {".chd", ".iso", ".cue", ".bin"}
    },
    "mastersystem": {
        "libretro_name": "Sega - Master System - Mark III",
        "core_path": "/tmp/cores/genesis_plus_gx_libretro.so",
        "core_name": "Sega - MS/GG/MD/CD (Genesis Plus GX)",
        "exts": {".zip", ".7z", ".sms", ".bin"}
    },
    "gamegear": {
        "libretro_name": "Sega - Game Gear",
        "core_path": "/tmp/cores/genesis_plus_gx_libretro.so",
        "core_name": "Sega - MS/GG/MD/CD (Genesis Plus GX)",
        "exts": {".zip", ".7z", ".gg", ".bin"}
    },
    "sg-1000": {
        "libretro_name": "Sega - SG-1000",
        "core_path": "/tmp/cores/genesis_plus_gx_libretro.so",
        "core_name": "Sega - MS/GG/MD/CD (Genesis Plus GX)",
        "exts": {".zip", ".7z", ".sg", ".bin"}
    },
    "saturn": {
        "libretro_name": "Sega - Saturn",
        "core_path": "/tmp/cores/yabause_libretro.so",
        "core_name": "Sega - Saturn (Yabause)",
        "exts": {".chd", ".iso", ".cue"}
    },
    "dreamcast": {
        "libretro_name": "Sega - Dreamcast",
        "core_path": "/tmp/cores/flycast_libretro.so",
        "core_name": "Sega - Dreamcast/NAOMI (Flycast)",
        "exts": {".chd", ".cdi", ".gdi"}
    },
    "snes": {
        "libretro_name": "Nintendo - Super Nintendo Entertainment System",
        "core_path": "/tmp/cores/snes9x2005_plus_libretro.so",
        "core_name": "Nintendo - SNES / SFC (Snes9x 2005 Plus)",
        "exts": {".zip", ".7z", ".sfc", ".smc"}
    },
    "nes": {
        "libretro_name": "Nintendo - Nintendo Entertainment System",
        "core_path": "/tmp/cores/fceumm_libretro.so",
        "core_name": "Nintendo - NES / Famicom (FCEUmm)",
        "exts": {".zip", ".7z", ".nes"}
    },
    "gba": {
        "libretro_name": "Nintendo - Game Boy Advance",
        "core_path": "/tmp/cores/mgba_libretro.so",
        "core_name": "Nintendo - Game Boy Advance (mGBA)",
        "exts": {".zip", ".7z", ".gba"}
    },
    "gb": {
        "libretro_name": "Nintendo - Game Boy",
        "core_path": "/tmp/cores/gambatte_libretro.so",
        "core_name": "Nintendo - Game Boy / Color (Gambatte)",
        "exts": {".zip", ".7z", ".gb"}
    },
    "gbc": {
        "libretro_name": "Nintendo - Game Boy Color",
        "core_path": "/tmp/cores/gambatte_libretro.so",
        "core_name": "Nintendo - Game Boy / Color (Gambatte)",
        "exts": {".zip", ".7z", ".gbc"}
    },
    "n64": {
        "libretro_name": "Nintendo - Nintendo 64",
        "core_path": "/tmp/cores/parallel_n64_libretro.so",
        "core_name": "Nintendo - Nintendo 64 (ParaLLEl N64)",
        "exts": {".zip", ".7z", ".n64", ".z64", ".v64"}
    },
    "nds": {
        "libretro_name": "Nintendo - Nintendo DS",
        "core_path": "/tmp/cores/desmume_libretro.so",
        "core_name": "Nintendo - DS (DeSmuME)",
        "exts": {".zip", ".7z", ".nds"}
    },
    "virtualboy": {
        "libretro_name": "Nintendo - Virtual Boy",
        "core_path": "/tmp/cores/mednafen_vb_libretro.so",
        "core_name": "Nintendo - Virtual Boy (Beetle VB)",
        "exts": {".zip", ".7z", ".vb"}
    },
    "psx": {
        "libretro_name": "Sony - PlayStation",
        "core_path": "/tmp/cores/pcsx_rearmed_libretro.so",
        "core_name": "Sony - PlayStation (PCSX ReARMed)",
        "exts": {".chd", ".pbp", ".cue", ".iso"}
    },
    "psp": {
        "libretro_name": "Sony - PlayStation Portable",
        "core_path": "/tmp/cores/ppsspp_libretro.so",
        "core_name": "Sony - PlayStation Portable (PPSSPP)",
        "exts": {".iso", ".cso", ".pbp"}
    },
    "pcengine": {
        "libretro_name": "NEC - PC Engine - TurboGrafx 16",
        "core_path": "/tmp/cores/mednafen_pce_fast_libretro.so",
        "core_name": "NEC - PC Engine / CD (Beetle PCE FAST)",
        "exts": {".zip", ".7z", ".pce"}
    },
    "atari2600": {
        "libretro_name": "Atari - 2600",
        "core_path": "/tmp/cores/stella_libretro.so",
        "core_name": "Atari - 2600 (Stella)",
        "exts": {".zip", ".7z", ".a26", ".bin"}
    },
    "atari7800": {
        "libretro_name": "Atari - 7800",
        "core_path": "/tmp/cores/prosystem_libretro.so",
        "core_name": "Atari - 7800 (ProSystem)",
        "exts": {".zip", ".7z", ".a78", ".bin"}
    },
    "atarilynx": {
        "libretro_name": "Atari - Lynx",
        "core_path": "/tmp/cores/handy_libretro.so",
        "core_name": "Atari - Lynx (Handy)",
        "exts": {".zip", ".7z", ".lnx"}
    },
    "neogeo": {
        "libretro_name": "SNK - Neo Geo",
        "core_path": "/tmp/cores/fbneo_libretro.so",
        "core_name": "Arcade (FinalBurn Neo)",
        "exts": {".zip", ".7z"}
    }
}

KNOWN_ALIASES = {
    "36 great holes starring fred couples": "36 great holes starring fred couples",
    "brutal unleashed": "brutal above the claw",
    "fifa international soccer 96": "fifa soccer 96",
    "knuckles chaotix": "chaotix",
    "pitfall": "pitfall the mayan adventure",
    "rbi baseball 95": "rbi baseball",
    "romance of the three kingdoms iv": "sangokushi iv",
    "shadow squadron": "stellar assault",
    "spider man web of fire": "web of fire",
    "star trek starfleet academy bridge simulator": "star trek starfleet academy",
    "world series baseball 95": "world series baseball starring deion sanders",
    "wwf raw": "wwf raw",
    "wwf wrestlemania arcade": "wwf wrestlemania the arcade game",
    "zaxxon motherbase 2000": "zaxxon s motherbase 2000"
}


def clean_rom_filename(filename: str, system_key: str = "") -> str:
    """Extrai um nome legível do jogo a partir do nome do arquivo da ROM."""
    stem = re.sub(r"\.[a-zA-Z0-9]+$", "", filename)
    # Remove tags entre colchetes como [!], [c], [a1], [Unl]
    stem = re.sub(r"\[.*?\]", "", stem)
    # Remove tags comuns de região / dump entre parênteses
    stem = re.sub(
        r"\((JU|JUE|U|E|J|A|F|4|5|1|Dec\s+\d+|c|b|UE|World|USA|Europe|Japan|En|Fr|De|Es|It|Beta|Proto|Unl)\)",
        "",
        stem,
        flags=re.IGNORECASE
    )
    # Remove redundância de sistema
    if system_key == "sega32x":
        stem = re.sub(r"\b32X\b", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"\(\s*\)", "", stem)
    return " ".join(stem.split()).strip()


def normalize_string(s: str) -> str:
    """Normaliza para comparação insensível a caracteres especiais e caixa."""
    s = s.lower()
    s = re.sub(r"\(.*?\)|\[.*?\]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def fetch_libretro_thumbnail_list(system_name: str, thumb_type: str = "Named_Boxarts") -> list[str]:
    """Obtém a lista de nomes de thumbnails disponíveis no servidor Libretro."""
    url = f"https://thumbnails.libretro.com/{urllib.parse.quote(system_name)}/{urllib.parse.quote(thumb_type)}/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Erro ao acessar {url}: {e}", file=sys.stderr)
        return []

    # Extrai links href="*.png"
    matches = re.findall(r'href="([^"]+\.png)"', content)
    clean_list = [urllib.parse.unquote(m) for m in matches]
    return clean_list


def match_thumbnail(rom_name: str, clean_name: str, thumb_list: list[str]) -> str | None:
    """Encontra a melhor thumbnail correspondente para uma ROM."""
    norm_clean = normalize_string(clean_name)
    target = KNOWN_ALIASES.get(norm_clean, norm_clean)

    candidates = []
    for thumb in thumb_list:
        thumb_no_ext = thumb[:-4] if thumb.endswith(".png") else thumb
        # Penaliza arquivos duplicados ou de cópia
        if "- copy" in thumb.lower():
            continue

        is_beta = any(b in thumb.lower() for b in ["beta", "proto", "demo", "sample", "alt"])
        norm_t = normalize_string(thumb_no_ext)

        score = 0
        if target == norm_t:
            score += 200
        elif target in norm_t or norm_t in target:
            score += 100
        else:
            sim = difflib.SequenceMatcher(None, target, norm_t).ratio()
            if sim > 0.65:
                score += sim * 90

        if score > 0:
            if not is_beta:
                score += 50
            # Prioridade de região
            if "(World)" in thumb or "(Japan, USA)" in thumb or "(USA, Europe)" in thumb:
                score += 30
            elif "(USA)" in thumb:
                score += 25
            elif "(Europe)" in thumb:
                score += 20
            elif "(Japan)" in thumb:
                score += 10
            candidates.append((score, thumb))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def download_file(url: str, dest_path: Path):
    """Baixa um arquivo da web salvando no caminho especificado."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(dest_path, "wb") as f:
            f.write(resp.read())


def update_emulationstation_gamelist(roms_dir: Path, games_info: list[dict]):
    """Cria ou atualiza o gamelist.xml com imagens corretas."""
    gamelist_path = roms_dir / "gamelist.xml"
    root = ET.Element("gameList")

    for info in games_info:
        game_elem = ET.SubElement(root, "game")
        path_elem = ET.SubElement(game_elem, "path")
        path_elem.text = f"./{info['rom_filename']}"

        name_elem = ET.SubElement(game_elem, "name")
        name_elem.text = info["clean_name"]

        if info.get("img_rel_path"):
            img_elem = ET.SubElement(game_elem, "image")
            img_elem.text = f"./{info['img_rel_path']}"
            thumb_elem = ET.SubElement(game_elem, "thumbnail")
            thumb_elem.text = f"./{info['img_rel_path']}"

    # Formata XML com indentação
    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write(gamelist_path, encoding="utf-8", xml_declaration=True)
    print(f"Gamelist do EmulationStation atualizada: {gamelist_path}")


def update_retroarch_playlist(storage_dir: Path, system_info: dict, system_key: str, games_info: list[dict]):
    """Gera a playlist do RetroArch (JSON 1.5) e salva em storage/playlists/."""
    playlists_dir = storage_dir / "playlists"
    playlists_dir.mkdir(parents=True, exist_ok=True)
    lpl_path = playlists_dir / f"{system_info['libretro_name']}.lpl"

    items = []
    for info in games_info:
        items.append({
            "path": f"/storage/roms/{system_key}/{info['rom_filename']}",
            "label": info["clean_name"],
            "core_path": system_info["core_path"],
            "core_name": system_info["core_name"],
            "crc32": "DETECT",
            "db_name": f"{system_info['libretro_name']}.lpl"
        })

    lpl_data = {
        "version": "1.5",
        "default_core_path": system_info["core_path"],
        "default_core_name": system_info["core_name"],
        "label_display_mode": 0,
        "right_thumbnail_mode": 0,
        "left_thumbnail_mode": 0,
        "sort_mode": 0,
        "items": items
    }

    with open(lpl_path, "w", encoding="utf-8") as f:
        json.dump(lpl_data, f, indent=2, ensure_ascii=False)
    print(f"Playlist do RetroArch atualizada: {lpl_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Gera playlists do RetroArch e EmulationStation e baixa boxarts oficiais do Libretro."
    )
    parser.add_argument("--roms-dir", required=True, help="Diretório de ROMs (ex.: /run/media/douglas/R36-ROMS/sega32x)")
    parser.add_argument("--system", help="Identificador do console (ex.: sega32x, snes, megadrive). Se omitido, deduz pelo diretório.")
    parser.add_argument("--storage-dir", help="Diretório da partição R36-STORAGE para gravar playlist e thumbnails do RetroArch.")
    parser.add_argument("--thumb-type", default="Named_Boxarts", choices=["Named_Boxarts", "Named_Snaps", "Named_Titles"], help="Tipo de thumbnail")
    parser.add_argument("--dry-run", action="store_true", help="Apenas exibe o plano sem baixar nem gravar arquivos.")
    parser.add_argument("--force", action="store_true", help="Sobrescreve imagens locais existentes.")
    args = parser.parse_args()

    roms_dir = Path(args.roms_dir).resolve()
    if not roms_dir.is_dir():
        print(f"Diretório não encontrado: {roms_dir}", file=sys.stderr)
        sys.exit(1)

    system_key = args.system or roms_dir.name.lower()
    if system_key not in SYSTEMS_MAP:
        print(f"Console desconhecido '{system_key}'. Consoles suportados: {', '.join(SYSTEMS_MAP.keys())}", file=sys.stderr)
        sys.exit(1)

    sys_info = SYSTEMS_MAP[system_key]
    print(f"Console: {system_key} -> Libretro System: '{sys_info['libretro_name']}'")

    # Coleta arquivos de ROMs
    valid_exts = sys_info["exts"]
    rom_files = sorted([
        f.name for f in roms_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_exts and not f.name.startswith(".")
    ])

    if not rom_files:
        print(f"Nenhuma ROM encontrada em {roms_dir} com extensões {valid_exts}")
        sys.exit(0)

    print(f"Encontradas {len(rom_files)} ROMs.")

    # Busca thumbnails do Libretro
    print(f"Consultando thumbnails em https://thumbnails.libretro.com/{urllib.parse.quote(sys_info['libretro_name'])}/{args.thumb_type}/...")
    thumb_list = fetch_libretro_thumbnail_list(sys_info["libretro_name"], args.thumb_type)
    print(f"Encontradas {len(thumb_list)} thumbnails disponíveis no Libretro.")

    games_info = []
    base_thumb_url = f"https://thumbnails.libretro.com/{urllib.parse.quote(sys_info['libretro_name'])}/{urllib.parse.quote(args.thumb_type)}/"

    img_dir = roms_dir / "img"

    for rom in rom_files:
        clean_name = clean_rom_filename(rom, system_key)
        matched_thumb = match_thumbnail(rom, clean_name, thumb_list) if thumb_list else None

        rom_stem = re.sub(r"\.[a-zA-Z0-9]+$", "", rom)
        es_img_filename = f"{rom_stem}.png"
        es_img_path = img_dir / es_img_filename

        games_info.append({
            "rom_filename": rom,
            "clean_name": clean_name,
            "matched_thumb": matched_thumb,
            "es_img_path": es_img_path,
            "img_rel_path": f"img/{es_img_filename}"
        })

        status = f"-> {matched_thumb}" if matched_thumb else "-> [SEM CORRESPONDÊNCIA]"
        print(f"  {rom[:35]:<36} {status}")

    if args.dry_run:
        print("\nModo Dry-Run concluído. Nenhuma modificação realizada no disco.")
        return

    # Baixar thumbnails e gravar
    print("\nBaixando thumbnails e atualizando imagens locais...")
    downloaded = 0
    for g in games_info:
        if not g["matched_thumb"]:
            continue

        thumb_url = base_thumb_url + urllib.parse.quote(g["matched_thumb"])

        # 1. Imagem para o EmulationStation (em roms/system/img/<rom_stem>.png)
        if args.force or not g["es_img_path"].is_file():
            try:
                download_file(thumb_url, g["es_img_path"])
                downloaded += 1
            except Exception as e:
                print(f"Falha ao baixar para ES {g['es_img_path']}: {e}", file=sys.stderr)

        # 2. Imagem para o RetroArch (em storage/thumbnails/<Libretro_System>/Named_Boxarts/<Matched_Name>.png)
        if args.storage_dir:
            ra_thumb_path = Path(args.storage_dir) / "thumbnails" / sys_info["libretro_name"] / args.thumb_type / g["matched_thumb"]
            if args.force or not ra_thumb_path.is_file():
                try:
                    download_file(thumb_url, ra_thumb_path)
                except Exception as e:
                    print(f"Falha ao baixar para RetroArch {ra_thumb_path}: {e}", file=sys.stderr)

    print(f"Download concluído: {downloaded} imagens gravadas.")

    # Atualiza gamelist.xml
    update_emulationstation_gamelist(roms_dir, games_info)

    # Atualiza playlist do RetroArch se storage_dir fornecido
    if args.storage_dir:
        storage_path = Path(args.storage_dir).resolve()
        if storage_path.is_dir():
            update_retroarch_playlist(storage_path, sys_info, system_key, games_info)


if __name__ == "__main__":
    main()
