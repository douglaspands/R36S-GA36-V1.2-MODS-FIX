#!/bin/bash
# Pacote de teste do gba-recomp: mesmo formato dos jogos recompilados (Jogo.sh -> Jogo/launch.sh -> Jogo/Jogo.elf).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
mkdir -p "$SCRIPT_DIR/saves"
export SDL_NOMOUSE=1
if [ -f "./Teste.elf" ]; then
    chmod +x "./Teste.elf" 2>/dev/null
    "./Teste.elf" "$@"
else
    echo "Error: Binary ./Teste.elf not found!" >&2
    exit 1
fi
