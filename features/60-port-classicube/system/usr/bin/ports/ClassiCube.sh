#!/usr/bin/env bash
# Inicializador do ClassiCube para EmuELEC no Allwinner A33 (R36S clone)
# Mapeado no menu "Ports" do EmulationStation (/storage/roms/ports_scripts/ClassiCube.sh)
set -euo pipefail

PORT_DIR="/storage/roms/ports/classicube"
SHARE_DIR="/usr/share/classicube"
TMP_DIR="/tmp/classicube"
DB_FILE="/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt"

export LD_LIBRARY_PATH="/usr/lib:${LD_LIBRARY_PATH:-}"
export SDL_VIDEO_GL_DRIVER="/usr/lib/libGLESv2.so.2"
export SDL_VIDEO_EGL_DRIVER="/usr/lib/libEGL.so.1"

if [ -f "$DB_FILE" ]; then
    export SDL_GAMECONTROLLERCONFIG_FILE="$DB_FILE"
    SDL_CFG="$(grep -E 'micro_gamepad|retrogame_joypad' "$DB_FILE" || true)"
    if [ -n "$SDL_CFG" ]; then
        export SDL_GAMECONTROLLERCONFIG="$SDL_CFG"
    fi
fi

mkdir -p "$PORT_DIR/texpacks" "$PORT_DIR/audio" "$PORT_DIR/maps"

if [ -d "$SHARE_DIR" ]; then
    [ ! -f "$PORT_DIR/options.txt" ] && cp -f "$SHARE_DIR/options.txt" "$PORT_DIR/options.txt"
    [ ! -f "$PORT_DIR/texpacks/default.zip" ] && cp -f "$SHARE_DIR/texpacks/default.zip" "$PORT_DIR/texpacks/default.zip"
    if [ ! -f "$PORT_DIR/audio/default.zip" ] && [ -f "$SHARE_DIR/audio/default.zip" ]; then
        cp -f "$SHARE_DIR/audio/default.zip" "$PORT_DIR/audio/default.zip"
    fi
fi

if [ -f "$PORT_DIR/audio/default.zip" ] && ! compgen -G "$PORT_DIR/audio/*.wav" >/dev/null; then
    unzip -oq "$PORT_DIR/audio/default.zip" -d "$PORT_DIR/audio" 2>/dev/null || true
fi

if [ -f "$PORT_DIR/options.txt" ] && ! grep -q '^auto-pause' "$PORT_DIR/options.txt"; then
    echo "auto-pause = false" >> "$PORT_DIR/options.txt"
fi

cd "$PORT_DIR"

if [ -x "$SHARE_DIR/ClassiCube" ]; then
    BIN="$SHARE_DIR/ClassiCube"
elif [ -x "$PORT_DIR/ClassiCube" ]; then
    BIN="$PORT_DIR/ClassiCube"
else
    mkdir -p "$TMP_DIR"
    cp -f "$PORT_DIR/ClassiCube" "$TMP_DIR/ClassiCube"
    chmod 0755 "$TMP_DIR/ClassiCube"
    BIN="$TMP_DIR/ClassiCube"
fi

"$BIN" --singleplayer
exit 0
