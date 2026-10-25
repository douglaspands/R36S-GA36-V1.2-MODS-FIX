#!/usr/bin/env bash
# Inicializador do ClassiCube para EmuELEC no Allwinner A33 (R36S clone)
# Mapeado no menu "Ports" do EmulationStation (/storage/roms/ports_scripts/ClassiCube.sh)
set -euo pipefail

PORT_DIR="/storage/roms/ports/classicube"
SHARE_DIR="/usr/share/classicube"
BIN="$SHARE_DIR/ClassiCube"
DB_FILE="/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt"

export LD_LIBRARY_PATH="/usr/lib:${LD_LIBRARY_PATH:-}"
export SDL_VIDEO_GL_DRIVER="/usr/lib/libGLESv2.so.2"
export SDL_VIDEO_EGL_DRIVER="/usr/lib/libEGL.so.1"

# O SDL 2.0.9 da base só lê o mapeamento como string (a variável com caminho
# de arquivo é do 2.0.10).
if [ -f "$DB_FILE" ]; then
    SDL_CFG="$(grep -E 'micro_gamepad|retrogame_joypad' "$DB_FILE" || true)"
    if [ -n "$SDL_CFG" ]; then
        export SDL_GAMECONTROLLERCONFIG="$SDL_CFG"
    fi
fi

mkdir -p "$PORT_DIR/texpacks" "$PORT_DIR/audio" "$PORT_DIR/maps"

[ ! -f "$PORT_DIR/options.txt" ] && cp -f "$SHARE_DIR/options.txt" "$PORT_DIR/options.txt"
[ ! -f "$PORT_DIR/texpacks/default.zip" ] && cp -f "$SHARE_DIR/texpacks/default.zip" "$PORT_DIR/texpacks/default.zip"
[ ! -f "$PORT_DIR/audio/default.zip" ] && cp -f "$SHARE_DIR/audio/default.zip" "$PORT_DIR/audio/default.zip"

if ! compgen -G "$PORT_DIR/audio/*.wav" >/dev/null; then
    unzip -oq "$PORT_DIR/audio/default.zip" -d "$PORT_DIR/audio" 2>/dev/null || true
fi

# Sensibilidade da câmera do preset novo chega a cartões antigos (--keep-roms),
# mas só se o valor ainda for o padrão antigo; ajuste do jogador é preservado.
if grep -q '^mousesensitivity = 30[[:space:]]*$' "$PORT_DIR/options.txt"; then
    sed -i 's/^mousesensitivity = 30[[:space:]]*$/mousesensitivity = 120/' "$PORT_DIR/options.txt"
elif ! grep -q '^mousesensitivity' "$PORT_DIR/options.txt"; then
    echo "mousesensitivity = 120" >> "$PORT_DIR/options.txt"
fi

if ! grep -q '^auto-pause' "$PORT_DIR/options.txt"; then
    echo "auto-pause = false" >> "$PORT_DIR/options.txt"
fi

cd "$PORT_DIR"
"$BIN" --singleplayer
exit 0
