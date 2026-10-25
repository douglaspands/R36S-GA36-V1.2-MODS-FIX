#!/usr/bin/env bash
# Compila o port nativo ClassiCube para o Allwinner A33 (Cortex-A7)
# em container podman isolado (cores/toolchain).
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cache_dir="$root/work/cache/external"
work_dir="$root/work/ports/classicube"
src_dir="$work_dir/src"
dest_roms="$root/features/60-port-classicube/roms/ports/classicube"
dest_system="$root/features/60-port-classicube/system/usr/share/classicube"

url="https://github.com/ClassiCube/ClassiCube/archive/refs/tags/1.3.9.tar.gz"
sha256_esperado="5bb62dbb3ad27e1fbb09842f0cb1f4802b2686553b017e0b67ce09b36f908246"
tarball="$cache_dir/classicube-1.3.9.tar.gz"

mkdir -p "$cache_dir" "$work_dir" "$dest_roms" "$dest_system"

echo "==> Verificando código fonte upstream do ClassiCube 1.3.9"
if [ ! -f "$tarball" ]; then
  echo "    Baixando $url..."
  curl -fsSL -o "$tarball" "$url"
fi

sha256_obtido="$(sha256sum "$tarball" | awk '{print $1}')"
if [ "$sha256_obtido" != "$sha256_esperado" ]; then
  echo "ERRO: sha256 do tarball ($sha256_obtido) difere do esperado ($sha256_esperado)" >&2
  exit 1
fi
echo "    sha256 conferido: $sha256_obtido"

echo "==> Preparando árvore de código em $src_dir"
rm -rf "$src_dir"
mkdir -p "$src_dir"
tar -xzf "$tarball" -C "$src_dir" --strip-components=1

echo "==> Aplicando patches para Mali-400 (RGBA), foco de janela e gamepad SDL 2.0.9"
uv run python -I -c '
from pathlib import Path
src = Path("'"$src_dir"'")

# 1. src/Bitmap.h: suporte a CC_BUILD_GLES na ordem RGBA
bitmap = src / "src" / "Bitmap.h"
content = bitmap.read_text(encoding="utf-8")
target = "#if defined CC_BUILD_WEB || defined CC_BUILD_ANDROID"
replacement = "#if defined CC_BUILD_GLES || defined CC_BUILD_WEB || defined CC_BUILD_ANDROID"
if target not in content:
    raise RuntimeError("Padrão não encontrado em src/Bitmap.h")
bitmap.write_text(content.replace(target, replacement, 1), encoding="utf-8")

# 2. src/_GLShared.h: PIXEL_FORMAT GL_RGBA para CC_BUILD_GLES
glshared = src / "src" / "_GLShared.h"
content = glshared.read_text(encoding="utf-8")
if target not in content:
    raise RuntimeError("Padrão não encontrado em src/_GLShared.h")
glshared.write_text(content.replace(target, replacement, 1), encoding="utf-8")

# 3. src/Window_SDL2.c: foco inicial ativo, gamecontrollerdb e Select/Start
win_sdl2 = src / "src" / "Window_SDL2.c"
content = win_sdl2.read_text(encoding="utf-8")
foco_alvo = "\tWindow_Main.Exists     = true;\n"
foco_subst = "\tWindow_Main.Exists     = true;\n\tWindow_Main.Focused    = true;\n"
if foco_alvo not in content:
    raise RuntimeError("Padrão Window_Main.Exists não encontrado em src/Window_SDL2.c")
content = content.replace(foco_alvo, foco_subst, 1)

db_alvo = "void Gamepads_PreInit(void) { }"
db_subst = """void Gamepads_PreInit(void) {
\tSDL_GameControllerAddMappingsFromFile("/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt");
\tSDL_GameControllerAddMappingsFromFile("/storage/.config/SDL-GameControllerDB/gamecontrollerdb.txt");
}"""
if db_alvo not in content:
    raise RuntimeError("Padrão Gamepads_PreInit não encontrado em src/Window_SDL2.c")
content = content.replace(db_alvo, db_subst, 1)

btn_alvo = """\tGamepad_SetButton(port, CCPAD_SELECT, SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_GUIDE));
\tGamepad_SetButton(port, CCPAD_START,  SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_START));"""
btn_subst = """\tint select_btn = SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_GUIDE) || SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_BACK);
\tint start_btn  = SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_START);
\tif (select_btn && start_btn) { Window_RequestClose(); return; }
\tGamepad_SetButton(port, CCPAD_SELECT, select_btn);
\tGamepad_SetButton(port, CCPAD_START,  start_btn);"""
if btn_alvo not in content:
    raise RuntimeError("Padrão botões Gamepad_SetButton não encontrado em src/Window_SDL2.c")
content = content.replace(btn_alvo, btn_subst, 1)

win_sdl2.write_text(content, encoding="utf-8")
print("    Patches aplicados com sucesso em Bitmap.h, _GLShared.h e Window_SDL2.c")
'

echo "==> Assegurando container da toolchain (localhost/r36-cores-a33)"
podman build -q -t localhost/r36-cores-a33 "$root/cores/toolchain"

echo "==> Compilando ClassiCube para Cortex-A7 (ARMv7-A hard-float + NEON-VFPv4 + GLES2 + SDL2)"
cflags="-pipe -fno-math-errno -O2 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -fvisibility=hidden -fno-ident -DCC_BUILD_SDL2 -DCC_BUILD_GLES -DCC_WIN_BACKEND=2 -DCC_GFX_BACKEND=3"
libs="-lSDL2 -lGLESv2 -lEGL -lpthread -ldl -lm"
ldflags="-s -Wl,--gc-sections"

podman run --rm --userns=keep-id --network=none \
  -v "$src_dir":/build/src:Z \
  -w /build/src \
  localhost/r36-cores-a33 \
  make -f misc/makefiles/linux.mk \
    CC=arm-linux-gnueabihf-gcc \
    LINK=arm-linux-gnueabihf-gcc \
    CFLAGS="$cflags" \
    LIBS="$libs" \
    LDFLAGS="$ldflags" \
    -j"$(nproc)"

bin_gerado="$src_dir/ClassiCube"
if [ ! -f "$bin_gerado" ]; then
  echo "ERRO: O binário $bin_gerado não foi gerado." >&2
  exit 1
fi

echo "==> Instalando binário na feature 60-port-classicube"
cp "$bin_gerado" "$dest_roms/ClassiCube"
chmod 0755 "$dest_roms/ClassiCube"
cp "$bin_gerado" "$dest_system/ClassiCube"
chmod 0755 "$dest_system/ClassiCube"

tamanho="$(stat -c%s "$dest_roms/ClassiCube")"
sha_bin="$(sha256sum "$dest_roms/ClassiCube" | awk '{print $1}')"
echo "    Destino ROMS:   $dest_roms/ClassiCube"
echo "    Destino SYSTEM: $dest_system/ClassiCube"
echo "    Tamanho: $tamanho bytes"
echo "    sha256:  $sha_bin"
echo "==> Compilação concluída com sucesso."
