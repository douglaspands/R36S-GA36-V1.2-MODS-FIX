#!/usr/bin/env bash
# Inicializador do ClassiCube para EmuELEC no Allwinner A33 (R36S clone)
# Mapeado no menu "Ports" do EmulationStation (/storage/roms/ports_scripts/ClassiCube.sh)
set -euo pipefail

PORT_DIR="/storage/roms/ports/classicube"
TMP_DIR="/tmp/classicube"

# Garante acesso às bibliotecas gráficas e de controle da imagem base
export LD_LIBRARY_PATH="/usr/lib:${LD_LIBRARY_PATH:-}"
export SDL_VIDEO_GL_DRIVER="/usr/lib/libGLESv2.so.2"
export SDL_VIDEO_EGL_DRIVER="/usr/lib/libEGL.so.1"

# Base de mapeamentos de controle para SDL2
if [ -f "/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt" ]; then
    export SDL_GAMECONTROLLERCONFIG_FILE="/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt"
fi

if [ ! -d "$PORT_DIR" ]; then
    echo "ERRO: Diretório do jogo não encontrado: $PORT_DIR" >&2
    exit 1
fi

cd "$PORT_DIR"

# Determina se o binário na partição FAT32 tem permissão de execução direta.
# Em caso de montagem com noatime/noexec, executa a partir de /tmp mantendo
# o diretório de trabalho em /storage/roms/ports/classicube para salvar mapas e opções.
BIN="$PORT_DIR/ClassiCube"
if [ ! -x "$BIN" ]; then
    mkdir -p "$TMP_DIR"
    cp -u "$PORT_DIR/ClassiCube" "$TMP_DIR/ClassiCube" 2>/dev/null || cp "$PORT_DIR/ClassiCube" "$TMP_DIR/ClassiCube"
    chmod 0755 "$TMP_DIR/ClassiCube"
    BIN="$TMP_DIR/ClassiCube"
fi

# Executa o ClassiCube diretamente em modo singleplayer sem repassar argumentos externos do ES
"$BIN" --singleplayer
exit 0
