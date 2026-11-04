Available in: English | [Português](DESENVOLVIMENTO.md) | [Español](DESARROLLO.md)

# R36S Clone (GA36-MB V1.2) Image Factory

This repository builds SD card images for an **R36S clone** handheld console with motherboard
**GA36-MB V1.2**. Every enhancement is packaged as a versioned *feature*, and each build
generates a fresh image identified by its generation timestamp.

## Who It Is For

This device is tailored for a **6-year-old child** (the son of this repository's maintainer).
This guides every design choice: interface completely in his native language (Brazilian Portuguese
across the system, EmulationStation, and the RetroArch menu with `./build.sh --lang pt_BR`), because
reading in one's native language makes learning so much easier; minimal warnings and animations
between power-on and gameplay; pleasant visuals and sound (tailored shaders for GBA, Game Boy,
and Game Boy Color, elimination of LCD ghosting, clean hiss-free audio); and simple menus. When
proposing any change, ask yourself: does this help a child of this age find and launch a game on their own?

## The Device and Why Only This Base Works

- The SoC is an **Allwinner A33**, remarketed as an RK3326. Generic R36S firmware images
  (ArkOS, AmberELEC, ROCKNIX, etc.) are built for Rockchip and **will not boot**.
- The device only boots with the factory **EmuELEC 4.7 "Nexus"** image (sunxi 3.4.39 kernel,
  `script.bin`). The source code of this fork is not public, so the OS cannot be recompiled.
- Therefore, the build **always starts from the stock factory image** (`base/`), which is never
  modified directly, safely replacing only target partition contents: SYSTEM files (squashfs),
  STORAGE (ext4), ROMs (FAT32), and the boot partition (FAT16).
- **No network, SSH, or Wi-Fi: everything goes through the SD card.** The handheld has no
  connectivity. To transfer files (cores, logs, profiling data), insert the card into your PC:
  `R36-ROMS` (FAT32) mounts without root; `R36-STORAGE` (ext4) contains root-owned system files.

SD card layout (512-byte sectors):

| Partition | Start   | Contents                                         | PC Label       |
|-----------|---------|--------------------------------------------------|----------------|
| bootarea  | 0       | MBR, EBRs, boot0, U-Boot, softw411 table         | —              |
| p2        | 73728   | FAT16 read by U-Boot (only 16 MiB allocated)     | `R36-BOOT`     |
| p5        | 139264  | U-Boot environment variables                     | —              |
| p6        | 172032  | kernel + initramfs                               | —              |
| p7        | 237568  | FAT16 containing `SYSTEM` (squashfs) & `R36-BUILD.txt` | `R36-SYSTEM` |
| p8        | 1810432 | ext4 `/storage`: saves, configurations           | `R36-STORAGE`  |
| p1        | 4956160 | FAT32 `/storage/roms`, spans to the end of card  | `R36-ROMS`     |

## Prerequisites

Linux (tested on Fedora) with Python 3.11 or newer:

```bash
sudo dnf install squashfs-tools mtools dosfstools e2fsprogs util-linux xz coreutils
```

`squashfs-tools` must be version 4.6 or newer with LZO support (standard in modern distributions).
The build script validates these dependencies upfront and reports any missing tools.

The factory image comes from this r/R36S post:
<https://www.reddit.com/r/R36S/comments/1w2i8em/r36s_ga36mb_v1220260416_emuelec_no_roms/>

Place it inside `base/`, with the exact filename:

```
base/R36S GA36-MB V1.2-20260416 - Emuelec - No ROMS.img
```

The expected sha256 checksum is configured in `config/base.toml`. If it does not match, the build will reject it.
The `base/` directory and all generated disk images are excluded from git.

## Generating an Image

**Language: English is default.** Running `./build.sh` without arguments builds an image set to
English (`en_US`) across EmuELEC, EmulationStation, and the RetroArch menu. For Brazilian Portuguese,
pass `--lang pt_BR`. For Spanish, pass `--lang es_ES`. The image comes preconfigured in the user's
desired language out of the box without manual file tweaking.

```bash
./build.sh                    # 16 GB card (15000 MiB), enabled features, English
./build.sh --lang pt_BR       # the same, in Brazilian Portuguese
./build.sh --no-features      # clean factory-equivalent image (reference benchmark)
./build.sh --offline          # uses only local external cache (no network access)
./build.sh --test             # marks the build as a test image (-test suffix)
./build.sh --help             # display all options
```

The build runs as an unprivileged user (no root/sudo needed) and takes about 2 minutes.
Output files are placed in `out/<YYYYMMDD-HHMMSS>/`:

- `r36s_ga36-mb_v1.2-20260416_<lang>_build_<timestamp>.img.xz`: complete flashable compressed disk image (Etcher / dd). `<lang>` is the lowercase hyphenated language code (`en-us` by default, `pt-br` with `--lang pt_BR`). A build without language features (`--no-features`) is named `r36s_ga36-mb_v1.2-20260416_build_<timestamp>.img.xz`;
- `parts/*.img`: individual partition images used by `./flash.sh`;
- `manifest.json`: timestamp, language (`"language"`), card size, partition offsets, sha256 hashes, and applied features;
- `changes.txt`: granular report of files added, replaced, or removed by each feature.

With `--test`, the build is marked as a test build (intermediate testing iteration): the directory becomes `out/<timestamp>-test/` and the image `..._<lang>_build_<timestamp>-test.img.xz`. Partition contents remain identical. `manifest.json` includes `"test": true` and `R36-BUILD.txt` adds `teste: sim`. `./flash.sh` handles test builds seamlessly: they show up in `--list-builds` with the `test` tag and can be flashed via `--build <timestamp>-test`.

### Language

`--lang <code>` (or `--idioma <code>`, supported as a backwards-compatible alias) configures the factory system language. Accepted codes: `pt_BR`, `pt_PT`, `en_US` (default), `en_GB`, `es_ES`, `fr_FR`, `de_DE`, and `it_IT`. The build swaps three configuration keys in working copies staged in `work/`: `system.language` in `emuelec.conf`, `Language` in `es_settings.cfg`, and `user_language` in `retroarch.cfg` (`en_US`/`en_GB` = `0`, `fr_FR` = `2`, `es_ES` = `3`, `de_DE` = `4`, `it_IT` = `5`, `pt_BR` = `7`, `pt_PT` = `8`). The source files in `features/10-ptbr-sao-paulo` remain intact in the repository.

- Invalid code: build stops immediately before creating files and displays the accepted list.
- `--no-features --lang ...`: error (language configuration files are supplied by features).
- `--features` without `10-ptbr-sao-paulo`: without `--lang`, the build finishes without a language tag in the filename; with `--lang`, it fails indicating the missing configuration file.
- Language defaults apply to clean storage partitions (`--wipe-storage`). When flashing with `--keep-storage`, EmuELEC and EmulationStation retain existing settings, and RetroArch syncs automatically upon launching the first game (handled by `idioma-aplica` in feature `56-retroarch-ajustes`).

| Target Language           | Command                       | Generated Image Name    |
|---------------------------|-------------------------------|-------------------------|
| English (default)         | `./build.sh`                  | `..._en-us_build_...`   |
| Brazilian Portuguese      | `./build.sh --lang pt_BR`     | `..._pt-br_build_...`   |
| Spanish                   | `./build.sh --lang es_ES`     | `..._es-es_build_...`   |

### Card Size

The ROMs partition stretches to the end of the SD card, so images must be generated for the exact card capacity. Check your card with the card reader plugged in:

```bash
lsblk -b -d -o NAME,SIZE,RM,MODEL
```

Divide the byte `SIZE` by 1048576 to get MiB and use an **equal or slightly smaller** value:

| Marketed Card Size  | Typical Real Size   | Command                         |
|---------------------|---------------------|---------------------------------|
| 8 GB                | 7300 to 7800 MiB    | `./build.sh --size-mib 7400`    |
| 16 GB (stock card)  | 15000 MiB           | `./build.sh`                    |
| 32 GB               | ~29800 MiB          | `./build.sh --size-mib 29800`   |

The minimum allowed card size is 7000 MiB, automatically aligned downwards to a multiple of 4 MiB.

## Flashing the Card

Run `./flash.sh` **in a normal terminal session** (it requests sudo password to access block devices). Always begin with `--dry-run` to preview the flashing plan safely:

```bash
./flash.sh --device /dev/sdc --all --wipe-roms --wipe-storage --dry-run
```

### Choosing the Build

To inspect available builds inside `out/` with their sizes and feature sets (does not need sudo or SD card):

```bash
./flash.sh --list-builds
```

When run interactively without `--build`, if multiple builds exist in `out/`, the script presents a numbered menu. Option 1 is the latest build, selected by pressing Enter. Press Ctrl+D to cancel. Non-interactively (scripts, pipes), it picks the newest build automatically.

To bypass the menu, specify the build timestamp directly: `--build 20261013-153045`.

### Full Flash

Flashes bootarea, p2 (16 MiB), p5, p6, p7, p8, and p1 (only active data sectors are written, making it significantly faster than writing 15 GB):

```bash
./flash.sh --device /dev/sdc --all --wipe-roms --wipe-storage     # fresh card: erase all
./flash.sh --device /dev/sdc --all --keep-roms --keep-storage     # update OS, keep ROMs & saves
./flash.sh --device /dev/sdc --all --keep-roms --wipe-storage     # keep ROMs, reset configs
```

- Full flash **always** requires either `--keep-storage` or `--wipe-storage` because p8 stores saves, savestates, and configurations.
- If p1 contains games beyond the stock factory image, the script refuses until you explicitly pass `--keep-roms` or `--wipe-roms`.
- `--keep-roms` and `--keep-storage` require a card previously partitioned by this repository.

### Partial Flash

Flashes only selected partitions and zero bytes outside them. Requires a card already formatted with this repository's layout:

```bash
./flash.sh --device /dev/sdc --part system                  # SYSTEM only (p7)
./flash.sh --device /dev/sdc --part boot                    # p2 boot partition only (16 MiB)
./flash.sh --device /dev/sdc --part storage --wipe-storage  # p8: resets configs & saves
./flash.sh --device /dev/sdc --part roms --wipe-roms        # p1: resets ROMs
```

### flash.sh Safety Protections and Health Diagnosis

- Accepts only **removable whole disks** (`RM=1`) or internal SD readers (`mmcblk`). Rejects single partitions (`/dev/sdc1`), the PC's internal SSD, and devices with mounted OS partitions.
- **Physical Health & Reader Diagnostics**:
  - Checks kernel logs (`dmesg`) for I/O errors or bus disconnects (`buffer I/O error`, `reset high-speed USB device`).
  - Executes atomic hardware read-only lock verification on the last sector before writing, stopping silent flash memory failures.
  - Verifies non-destructive FAT32 filesystem health (`fsck.fat -n`) when selecting `--keep-roms`.
- **Analytical & Canonical MBR Reconstruction**:
  - With `--keep-roms`, MBR does not copy corrupted legacy bytes: partition `p1` is reconstructed canonically starting at sector `4956160`, type `0x0C` (FAT32 LBA), aligned to 4 MiB.
- Previews device name, capacity, labels, and target operations, requiring explicit device confirmation (typing e.g. `sdc`).
- Automatic unmounting before writes, sha256 verification before and after flashing.
- **Strict Sync and Safe Hardware Ejection**:
  - Calls `sync`, `blockdev --flushbufs`, and `udevadm settle`.
  - Automatically executes `udisksctl power-off -b /dev/sdX` upon completion to safely power down the SD reader for immediate physical removal (pass `--no-eject` to keep it mounted for inspection).

To test without a physical SD card, flash to a sparse image file:

```bash
mkdir -p work
truncate -s 15000M work/cartao-teste.img
./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage
```

## Enabled Features

- **`10-ptbr-sao-paulo`**: factory localization across system, EmulationStation, and RetroArch RGUI; timezone `America/Sao_Paulo`. Ships complete EmulationStation translation catalogs for `pt_BR` and `es_MX` (`.po` and `.mo`), preserving gaming terms (*Save State*, *Core*, *Shader*, *Bezel*, *BIOS*, *ROMs*, *RetroAchievements*) and formatting menus to fit 3.5" 640x480. Builds default to English unless configured via `./build.sh --lang`. Sets optimal defaults:
  - Core-provided aspect ratio (`global.ratio=core`);
  - Standard OK/Cancel button layout (`menu_swap_ok_cancel_buttons = "false"`);
  - gpSP as default GBA core (`gba.emulator=libretro`, `gba.core=gpsp`);
  - Recompiled snes9x2005_plus_a33 as default SNES core (`53-cores-a33`);
  - fceumm as NES core (`nes.core=fceumm`);
  - fbalpha2012 as CPS2 core (`cps2.core=fbalpha2012`);
  - Disabled maximum performance governor by default (`global.maxperf=0`) to keep temperatures cool;
  - Disabled unused services (SSH, Bluetooth, online updates, netplay, rewind);
  - Savestates with screenshots saved directly to `savestates/<system>/` on `R36-ROMS` where EmulationStation detects them;
  - Unused hardware drivers set to `"null"` (`wifi_driver`, `bluetooth_driver`, `microphone_driver`, `midi_driver`).

- **`20-controle-posicional`**: physical face button mapping in RetroArch (bottom = B, right = A, top = X, left = Y) and FN configured as hotkey:

| In-Game Shortcut  | Action                 |
|-------------------|------------------------|
| FN + X            | RetroArch Quick Menu   |
| FN + Y            | Take Screenshot        |
| FN + L / R        | Load / Save State      |
| FN + L2           | Slow Motion            |
| FN + R2           | Fast Forward           |
| FN + Down         | Pause Game             |
| FN + Right        | Toggle FPS Counter     |
| FN + Start        | Quit Game              |

  - **FN Button:** on boot, remaps `fn_key` from 464 to 316 (`BTN_MODE`) and configures `input_enable_hotkey_btn = "10"` in `micro_gamepad.cfg`. Select remains unencumbered for in-game use. Create empty file `r36-fn-original` on `R36-ROMS` root to revert to stock 464 code.

- **`30-telas-icone-controle`**: unified minimalist controller icon screen from cold boot through game launch and exit, replacing loud factory art ("R36S / Please Wait.....").

- **`40-zram-swap`**: replaces 300 MB disk swapfile with high-priority zram compressed RAM swap (priority 32767).

- **`41-servicos-enxutos`**: disables unneeded boot services: IR remote (`lircd`), `cron`, network time sync (`systemd-timesyncd`), and `pulseaudio` (ALSA handles audio directly).

- **`42-roms-noatime`**: remounts `/storage/roms` (FAT32) with `noatime` after boot, cutting flash wear when loading games.

- **`43-registro-termico`**: passive 5-second hardware telemetry logger writing to `R36-ROMS/r36-thermal.csv` (temperatures, CPU frequencies, battery voltage, current, LCD brightness, active core/system). Generates `r36-sysinfo.txt` at boot with full SoC state. Includes battery analysis and curve fitting tools (`tools/analisa_bateria.py`, `tools/ajusta_curva_bateria.py`).

- **`44-cpu-ondemand`**: tunes `ondemand` CPU governor (`up_threshold` 30, `sampling_down_factor` 10, `scaling_min_freq` 600000) and sets DRAM scene 0 during games, avoiding stutter without forcing full thermal load.

- **`46-audio`**: true mute at volume 0 (`speaker volume control = 0`), applies saved volume at cold boot (`r36-audio.volume`), raises RetroArch `audio_latency` to 96 and lowers `audio_resampler_quality` to 1 to eliminate crackles. Revert via empty file `r36-audio-original` on `R36-ROMS`.

- **`48-bateria-percentual`**: battery charge estimation based on voltage and current curve lookup (`bateria-curva.conf`) bind-mounted over `/sys/class/power_supply/battery/capacity`, preventing the stock driver's premature red LED and shutdown errors. Revert via `r36-bateria-original`.

- **`50-temas-extras`**: installs extra EmulationStation themes:
  - System partition (p8 ext4): **Minimal EmuELEC**, **Graphite OGA**, **Epic Cody ML** (default 4:3 multilingual theme with `_languages/` support for Brazilian Portuguese, Latin Spanish, and English);
  - ROMs partition (p1 FAT32): media-rich **Switch** and **Crystal** themes located under `themes/` on FAT32.

- **`52-psp-desempenho`**: optimized global `ppsspp.ini` for Allwinner A33 (1x native 480x272 resolution, 4 threads, nearest texture filtering, skip GPU readback).

- **`53-cores-a33`**: libretro cores natively recompiled for Cortex-A7 A33 with LTO (`snes9x2005_plus_a33`).

- **`54-shaders-gba`**: lightweight single-pass `gba-modern-remaster` shader with vibrant color curve, sharp-bilinear scaling, and subtle LCD pixel grid. Enabled by default for GBA games. Disable via `r36-gba-sem-shader` on `R36-ROMS`.

- **`55-shaders-gb-gbc`**: single-pass shaders for Game Boy (`gb-modern-dmg`, olive green DMG palette with dot-matrix grid) and Game Boy Color (`gbc-modern-remaster`). Applied per content directory (`<Core>/gb.glslp`, `<Core>/gbc.glslp`). Disable via `r36-gb-sem-shader` or `r36-gbc-sem-shader`.

- **`56-retroarch-ajustes`**: sets EmulationStation "SHADER SET" via `shaderset-aplica` (`--set-shader`), synchronizes RetroArch language with EmuELEC via `idioma-aplica`, fixes directory paths for saving core overrides/presets (`rgui_config_directory`), and enables interframe blending in gpSP to eliminate ghosting (`gpsp_frame_mixing = "enabled"`, revert via `r36-gpsp-sem-ghost`).

- **`58-ports-exec`**: automatically manages executable permissions for standalone ports on FAT32 by bind-mounting staged copies from p8. It also covers the `*-recomp` folders of recompiled games (matched by name, sharing the same cache and log).

- **`60-port-classicube`**: native ClassiCube 1.3.9 port (C-based Minecraft Classic recreation) with hardware GLES2 acceleration, tuned analogue stick deadzones, and custom controller bindings.

- **`62-brilho-fn`**: on-the-fly screen brightness control using `FN + D-pad Up/Down` (range 10 to 100, step 5), saved across boots in `r36-brilho.level`. Reset to default (80) with `FN + L3 click` or empty file `r36-brilho-original`.

- **`64-love2d`**: official standalone **LÖVE 11.5** runtime for Allwinner A33 (ARMv7-A / NEON / GLES 2.0). Integrates Lua indie games as a first-class console in EmulationStation (`roms/love/` accepting `.love` and `.zip`). Full direct framebuffer GLES2 rendering (`/dev/fb0`), native SDL2 controller mapping, background `FN + Start` exit daemon, glitch-free OpenAL Soft audio (native 48000 Hz, int16, bsinc12), and language environment propagation (`CONSOLE_LANG`, `CONSOLE_LANG_SHORT`, `LANG`, `LANGUAGE`). Includes bundled *Mr. Rescue* demo with D-pad isolated menu navigation (immune to analog drift/calibration issues) and analog gameplay movement.

- **`66-recomp`**: consoles for recompiled games, i.e. a ROM converted into a native armhf executable, with no core and no RetroArch. Only `gba-recomp` exists today; the recompiler itself is a future change.
  - **EmulationStation system:** `gba-recomp` reads `/storage/roms/gba-recomp/` (the `R36-ROMS` partition) and lists the `.sh` (or `.SH`) at the root of the folder (a game is `Game.sh` plus a `Game/` folder next to it with `launch.sh` and the `.elf`). A `*-recomp` system with no games does not show up in the menu. The folder ships a three-language `LEIAME.txt`.
  - **Game format:** the `.sh` runs (with explicit `bash`) an armhf ELF (ARMv7-A, hard-float) that only uses libraries present in the image (glibc up to 2.36, libstdc++ up to `GLIBCXX_3.4.29`; newer C++ needs `-static-libstdc++`). It opens the window and sound through the system libraries (SDL2, GLES2, ALSA).
  - **Execution:** `r36-ports-exec` (feature `58-ports-exec`) keeps a `0755` copy on p8 and bind-mounts it over the p1 file. `/usr/bin/recomp.sh "%ROM%" "%SYSTEM%"`, the same for every console, checks the ELF signature and runs the game directly, with no `emuelecRunEmu.sh` or `--core`, through a `/tmp/r36-recomp-game` symlink (15 characters: the process name `gptokeyb` looks for, even when the ELF has a long or arbitrary name).
  - **Leaving a game:** `FN + Start` ends the game with `SIGTERM` through `gptokeyb` (profile `/usr/config/gptokeyb/recomp.gptk`: only `hotkey`, `start` and `back`, no keyboard action keys over the game buttons). `Select` reaches the game and FN alone does nothing. There is no new `es_input.cfg`: FN stays unbound in ES.
  - **Audio, language and log:** as in LÖVE (`Speaker Function` route, `audio-ganho aplica` before and after; `CONSOLE_LANG`, `CONSOLE_LANG_SHORT`, `LANG` and `LANGUAGE`). The log lives at `R36-ROMS/<console>-recomp/recomp.log` (rotates to `recomp.log.1` past 100 KB) with the game, the system, the `ldd` output (a missing library shows as `not found`) and the exit code; extra records only appear with the `r36-diagnostico` key.
  - **Theme:** `gba-recomp/` in the Epic Cody ML theme (`theme.xml`, `logo.png`, `poster.png`, `system.png`, plus the art in `_art/posters` and `_art/controllers`), derived from the GBA art with a RECOMP badge by `tools/gera_arte_gba_recomp.py`, with the `gba-recomp.*` variables in the three languages.
  - **Adding a console:** declare the `<console>-recomp` system (both copies of `es_systems.cfg`, command `/usr/bin/recomp.sh "%ROM%" "%SYSTEM%"`, extension `.sh`), the folder under `roms/` and the theme folder. Neither the launcher nor `r36-ports-exec` changes. The test ELF (`tools/recomp_teste/`) validates it on the device.

### Diagnostics

Diagnostic logging is disabled by default to prevent unnecessary SD card writes. To activate diagnostics, create an empty file named `r36-diagnostico` on the root of `R36-ROMS`:

```sh
touch /run/media/douglas/R36-ROMS/r36-diagnostico
```

When present, the system writes `r36-audio.log`, `r36-bateria.log`, `r36-shader-gba.log`, `r36-shader-gb-gbc.log`, `r36-idioma.log`, and `r36-brilho.log`. Thermal logs (`r36-thermal.csv`, `r36-sysinfo.txt`) operate independently.

## Creating a Feature

A feature is simply a directory within `features/`. See the documented template in `features/00-exemplo/`.

1. Copy the template:

   ```bash
   cp -r features/00-exemplo features/10-my-feature
   ```

2. Edit `features/10-my-feature/feature.toml`: configure `name`, `description`, `order`, and set `enabled = true`.
3. Populate partition layers:
   - `system/`: target root `/` of the system (read-only squashfs);
   - `storage/`: target `/storage` (configs, e.g. `storage/.config/emuelec/configs/emuelec.conf`);
   - `roms/`: target `/storage/roms`;
   - `boot/`: target p2 boot partition (`bootlogo.bmp`, etc.; respect the 16 MiB boundary).
4. Declare file deletions in `feature.toml` using `[[remove]]`.
5. For large external assets, define an `[[external]]` archive download with sha256 checksum.
6. Test and verify:

   ```bash
   ./build.sh --features 10-my-feature       # build only this feature
   ./build.sh                                # build with all enabled features
   cat out/<timestamp>/changes.txt
   ```

Important rules:
- Files in `system/` and `storage/` default to ownership `0:0`, permissions `0755` for executables, `0644` otherwise.
- Two features cannot modify the same path unless the later feature explicitly declares `[[override]]`.
- Every new feature gets its own OpenSpec change and git branch.

## Where to See Which Build Is on the Card

`R36-BUILD.txt` contains the image name, card size, language (`idioma: en_US`), and applied features:
- On PC: located on the **R36-SYSTEM** partition;
- On console: accessible at `/flash/R36-BUILD.txt`.

Test builds display `teste: sim`.

## Rollback

- Re-flash a previous build: `./flash.sh --device /dev/sdc --all --keep-roms --keep-storage --build <timestamp>`.
- Or restore the stock factory image, kept intact in `base/`:

  ```bash
  sudo dd if="base/R36S GA36-MB V1.2-20260416 - Emuelec - No ROMS.img" of=/dev/sdc bs=4M conv=fsync status=progress
  ```

## What Never to Do

- **Never let Windows "scan and repair" or format the SD card.** It can corrupt partition tables and MBR structures.
- **Never write more than 16 MiB to p2.** While MBR declares 128 MiB, sectors above 16 MiB overlap the kernel and SYSTEM.
- **Never create `.please_resize_me`** on any partition: it triggers a destructive format of p1 and p8 on boot.
- **Never flash generic R36S images** (ArkOS, AmberELEC, etc.): they target Rockchip RK3326 and will not boot on this Allwinner A33 hardware.
- Never edit the base image inside `base/`.

## For Developers

```bash
uv run python -I -m unittest discover -s tests              # quick unit tests (~30 s)
R36_SLOW=1 uv run python -I -m unittest discover -s tests   # full end-to-end image builds (~5 min)
```

Python environment is managed via [uv](https://docs.astral.sh/uv/) (`uv sync`). Core logic lives in `tools/r36img/` (pure standard library).

### Compiling a Core

`./cores.sh` compiles libretro cores for Allwinner A33 using versioned recipes in rootless containers:

```bash
./cores.sh compilar snes9x2005_plus o3                              # compile, verify ABI, stage in feature
./cores.sh verificar                                                # verify ABI and sha256 against registry
./cores.sh perfil snes9x2005_plus <R36-ROMS>/pgo/snes9x2005_plus   # import PGO profiling data
./cores.sh resumo <R36-ROMS>/r36-thermal.csv --roms <R36-ROMS>      # session performance summary
```
