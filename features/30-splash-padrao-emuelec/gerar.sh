#!/usr/bin/env bash
# Gera as telas da feature 30 a partir das fontes desta pasta.
# Precisa do ImageMagick 7 (magick). Não é usado pelo build: as imagens geradas
# ficam versionadas nas camadas system/ e storage/. Quem regerar atualiza os
# sha256 do LEIA-ME.txt.
set -euo pipefail

aqui="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fonte_boot="$aqui/fonte-splash-distribuicao-1080.png"
fonte_icone="$aqui/fonte-gamepad-2.svg"

command -v magick >/dev/null || { echo "erro: ImageMagick 7 (magick) não encontrado" >&2; exit 1; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Boot: recorte central 4:3 (1440x1080) do original 16:9, reduzido para 640x480.
magick "$fonte_boot" -gravity center -crop 1440x1080+0+0 +repage \
    -resize 640x480! -background black -alpha remove -alpha off \
    -strip -define png:color-type=2 -depth 8 "PNG24:$tmp/boot.png"

# O .raw que o lsb_release toca com ffplay (rawvideo rgb24 640x480).
magick "$tmp/boot.png" -depth 8 "rgb:$tmp/boot.raw"

# Jogo: ícone em traço #d8dce6, 190x190, centrado num gradiente radial escuro.
# O ícone passa por um PNG intermediário de 16 bits (RGBA), como nas prévias
# aprovadas: compor direto do SVG muda alguns pixels da borda do traço.
sed 's/currentColor/#d8dce6/' "$fonte_icone" > "$tmp/icone.svg"
magick -background none -density 1200 "$tmp/icone.svg" -resize 190x190 "PNG64:$tmp/icone.png"
magick -size 640x480 radial-gradient:'#2b2f36-#0b0c0f' "$tmp/icone.png" \
    -gravity center -composite -alpha off \
    -strip -define png:color-type=2 -depth 8 "PNG24:$tmp/jogo.png"

for destino in "$aqui/system/usr/config/splash" "$aqui/storage/.config/splash"; do
    mkdir -p "$destino"
    for nome in splash-std.png splash-1080.png retroarch.png; do
        cp "$tmp/boot.png" "$destino/$nome"
    done
    cp "$tmp/boot.raw" "$destino/splash-1080.raw"
    for nome in loading-game-std.png loading-game.png; do
        cp "$tmp/jogo.png" "$destino/$nome"
    done
done

echo "telas geradas em system/usr/config/splash e storage/.config/splash"
