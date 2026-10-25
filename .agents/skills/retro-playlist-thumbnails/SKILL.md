---
name: retro-playlist-thumbnails
description: Gera e atualiza playlists do RetroArch (.lpl) e do EmulationStation (gamelist.xml) para consoles retro, e baixa automaticamente as thumbnails e boxarts oficiais do Libretro Thumbnails (Named_Boxarts, Named_Snaps, Named_Titles). Use sempre que o usuário solicitar gerar, atualizar ou corrigir playlists, listas de jogos, capas, boxarts ou imagens de qualquer console no cartão SD (R36S / EmuELEC) ou em diretórios de ROMs.
---

# Retro Playlist & Libretro Thumbnails Generator

Esta skill automatiza o processo de:
1. Identificar o console a partir da pasta de ROMs ou argumento informado.
2. Limpar e normalizar os nomes dos arquivos de ROMs (removendo tags GoodTools como `(JU) [!]`, `[c]`, `(1)`, `32X`, etc.).
3. Realizar correspondência inteligente (*fuzzy matching* e dicionário de aliases) contra a base oficial do **Libretro Thumbnails** (`https://thumbnails.libretro.com/`).
4. Baixar as boxarts oficiais (`Named_Boxarts`) e salvá-las no formato e caminho esperado pelo EmulationStation (`<roms_dir>/img/<nome_da_rom>.png`) e opcionalmente pelo RetroArch (`<storage_dir>/thumbnails/<System>/Named_Boxarts/<Nome_Libretro>.png`).
5. Gerar ou atualizar o `gamelist.xml` do EmulationStation com tags `<game>`, `<path>`, `<name>`, `<image>` e `<thumbnail>`.
6. Gerar ou atualizar a playlist do RetroArch (`<Libretro_System>.lpl`, formato JSON 1.5) no diretório de playlists (`/storage/playlists`).

---

## Estrutura de Arquivos Gerados

### EmulationStation (p1 `R36-ROMS` / FAT32)
```text
/storage/roms/<console>/
├── gamelist.xml                <- XML com metadados e caminhos das imagens
├── img/                        <- Boxarts/capas dos jogos
│   ├── <Nome_Da_ROM_1>.png
│   └── <Nome_Da_ROM_2>.png
├── <Nome_Da_ROM_1>.zip
└── <Nome_Da_ROM_2>.zip
```

### RetroArch (p8 `R36-STORAGE` / ext4)
```text
/storage/
├── playlists/
│   └── <Libretro_System>.lpl   <- Playlist JSON 1.5 com cores e caminhos
└── thumbnails/
    └── <Libretro_System>/
        └── Named_Boxarts/      <- Boxarts oficiais nomeadas com o título No-Intro
            ├── <Nome_Libretro_1>.png
            └── <Nome_Libretro_2>.png
```

---

## Executando o Script da Skill

O script auxiliar está em `scripts/generate_playlist.py` (dentro da pasta desta skill).

### Sintaxe Básica

```bash
# Apenas simulação (Dry-Run): confere as correspondências sem alterar o disco
.agents/skills/retro-playlist-thumbnails/scripts/generate_playlist.py \
  --roms-dir "/run/media/$USER/R36-ROMS/<console>" \
  --dry-run

# Execução real: baixa as boxarts e atualiza o gamelist.xml do EmulationStation
.agents/skills/retro-playlist-thumbnails/scripts/generate_playlist.py \
  --roms-dir "/run/media/$USER/R36-ROMS/<console>" \
  --force

# Execução completa: EmulationStation + RetroArch (playlist .lpl e thumbnails)
.agents/skills/retro-playlist-thumbnails/scripts/generate_playlist.py \
  --roms-dir "/run/media/$USER/R36-ROMS/<console>" \
  --storage-dir "/run/media/$USER/R36-STORAGE" \
  --force
```

### Argumentos Suportados

| Argumento | Descrição |
|-----------|-----------|
| `--roms-dir <caminho>` | **(Obrigatório)** Caminho absoluto para a pasta do sistema (ex.: `/run/media/douglas/R36-ROMS/sega32x`). |
| `--system <id>` | Identificador do console (ex.: `sega32x`, `megadrive`, `snes`, `nes`, `gba`, `gb`, `gbc`, `psx`, etc.). Se omitido, deduz pelo nome da pasta. |
| `--storage-dir <caminho>` | Diretório da partição de sistema (`R36-STORAGE`) para gravar a playlist `.lpl` e thumbnails do RetroArch. |
| `--thumb-type <tipo>` | Tipo de imagem: `Named_Boxarts` (padrão), `Named_Snaps` (capturas de tela) ou `Named_Titles` (telas de título). |
| `--dry-run` | Mostra os jogos encontrados, a consulta no Libretro e as correspondências sem baixar imagens nem alterar arquivos. |
| `--force` | Força o download e substituição de imagens locais existentes (ideal para corrigir imagens incorretas ou corrompidas). |

---

## Tabela de Consoles e Cores Suportados

| Pasta / ID | Sistema Libretro | Core Padrão | Extensões |
|---|---|---|---|
| `sega32x` | `Sega - 32X` | `picodrive_libretro.so` | `.zip`, `.7z`, `.32x`, `.bin` |
| `megadrive` | `Sega - Mega Drive - Genesis` | `genesis_plus_gx_libretro.so` | `.zip`, `.7z`, `.gen`, `.smd`, `.md` |
| `segacd` | `Sega - Mega-CD - Sega CD` | `genesis_plus_gx_libretro.so` | `.chd`, `.iso`, `.cue` |
| `mastersystem` | `Sega - Master System - Mark III` | `genesis_plus_gx_libretro.so` | `.zip`, `.7z`, `.sms` |
| `gamegear` | `Sega - Game Gear` | `genesis_plus_gx_libretro.so` | `.zip`, `.7z`, `.gg` |
| `sg-1000` | `Sega - SG-1000` | `genesis_plus_gx_libretro.so` | `.zip`, `.7z`, `.sg` |
| `saturn` | `Sega - Saturn` | `yabause_libretro.so` | `.chd`, `.iso`, `.cue` |
| `dreamcast` | `Sega - Dreamcast` | `flycast_libretro.so` | `.chd`, `.cdi`, `.gdi` |
| `snes` | `Nintendo - Super Nintendo Entertainment System` | `snes9x2005_plus_libretro.so` | `.zip`, `.7z`, `.sfc`, `.smc` |
| `nes` | `Nintendo - Nintendo Entertainment System` | `fceumm_libretro.so` | `.zip`, `.7z`, `.nes` |
| `gba` | `Nintendo - Game Boy Advance` | `mgba_libretro.so` | `.zip`, `.7z`, `.gba` |
| `gb` | `Nintendo - Game Boy` | `gambatte_libretro.so` | `.zip`, `.7z`, `.gb` |
| `gbc` | `Nintendo - Game Boy Color` | `gambatte_libretro.so` | `.zip`, `.7z`, `.gbc` |
| `n64` | `Nintendo - Nintendo 64` | `parallel_n64_libretro.so` | `.zip`, `.7z`, `.z64`, `.n64` |
| `nds` | `Nintendo - Nintendo DS` | `desmume_libretro.so` | `.zip`, `.7z`, `.nds` |
| `virtualboy` | `Nintendo - Virtual Boy` | `mednafen_vb_libretro.so` | `.zip`, `.7z`, `.vb` |
| `psx` | `Sony - PlayStation` | `pcsx_rearmed_libretro.so` | `.chd`, `.pbp`, `.cue` |
| `psp` | `Sony - PlayStation Portable` | `ppsspp_libretro.so` | `.iso`, `.cso`, `.pbp` |
| `pcengine` | `NEC - PC Engine - TurboGrafx 16` | `mednafen_pce_fast_libretro.so` | `.zip`, `.7z`, `.pce` |
| `atari2600` | `Atari - 2600` | `stella_libretro.so` | `.zip`, `.7z`, `.a26` |
| `atari7800` | `Atari - 7800` | `prosystem_libretro.so` | `.zip`, `.7z`, `.a78` |
| `atarilynx` | `Atari - Lynx` | `handy_libretro.so` | `.zip`, `.7z`, `.lnx` |
| `neogeo` | `SNK - Neo Geo` | `fbneo_libretro.so` | `.zip`, `.7z` |

---

## Regras de Segurança e Execução no Ambiente

1. O script roda sem privilégios de `sudo`.
2. Como acessa a rede externa para consultar e baixar os thumbnails de `https://thumbnails.libretro.com/`, ele requer `BypassSandbox: true` quando executado via agente.
3. As alterações na partição de ROMs (`R36-ROMS`) são seguras e não tocam nos arquivos de ROM (`.zip`). Apenas atualizam a pasta `img/` e o `gamelist.xml`.
