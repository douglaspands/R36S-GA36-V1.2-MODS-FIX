#!/usr/bin/env bash
# Gera as molduras do Game Boy (DMG) e do Game Boy Color (Atomic Purple) e os
# .cfg de overlay do RetroArch, a partir da fonte desta pasta.
# Precisa do ImageMagick 7 (magick). Não é usado pelo build: o resultado fica
# versionado em system/usr/share/retroarch-overlays/r36-gameboy/. Quem regerar
# atualiza os sha256 do LEIA-ME.txt.
#
# Geometria (640x480, a tela inteira do aparelho):
#   jogo        x=53..586, y=0..479   (534x480, proporção 10:9) -> transparente
#   faixa esq.  x=0..52               (53x480) -> opaca, com LED e o texto
#   faixa dir.  x=587..639            (53x480) -> opaca e lisa
# Os custom_viewport_* dos overrides do RetroArch (feature storage) usam o mesmo
# retângulo do jogo.
set -euo pipefail

aqui="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fonte="$aqui/fonte-barlow-semibold.ttf"
destino="$aqui/system/usr/share/retroarch-overlays/r36-gameboy"

command -v magick >/dev/null || { echo "erro: ImageMagick 7 (magick) não encontrado" >&2; exit 1; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$destino"

LARG=53       # largura de cada faixa lateral
ALT=480
DIR_X=587     # x da faixa direita
LED_Y=172     # y do centro do LED
TEXTO_Y=190   # y do topo do texto

# faixa <cor> <realce> <texto> <saida>
#   Faixa esquerda (53x480): cor base com realce suave na borda externa e sombra
#   de 4 px junto ao jogo. Depende só de x, então a direita (espelho) fica lisa.
#   Com <texto> não vazio, desenha o LED e o texto.
faixa() {
    local cor="$1" realce="$2" texto="$3" saida="$4"
    # perfil horizontal (53x1): multiplicador por coluna (i = 0 é a borda externa)
    magick -size ${LARG}x1 "xc:$cor" \
        -fx "i>=49 ? u*(1-0.1*(i-48)) : u*(1+${realce}*max(0,10-i))" \
        -filter point -resize ${LARG}x${ALT}! "$tmp/base.png"
    if [ -z "$texto" ]; then
        magick "$tmp/base.png" -strip "PNG24:$saida"
        return
    fi
    magick -size ${LARG}x${ALT} xc:none -fill 'rgba(255,40,40,0.55)' \
        -draw "circle 26,$LED_Y 26,$((LED_Y + 9))" -blur 0x4 "$tmp/brilho.png"
    magick "$tmp/base.png" "$tmp/brilho.png" -compose over -composite \
        -fill '#e02020' -draw "circle 26,$LED_Y 26,$((LED_Y + 4))" \
        -fill '#ff9c9c' -draw "circle 25,$((LED_Y - 1)) 25,$((LED_Y - 1))" \
        -font "$fonte" -pointsize 9 -kerning 0.4 -fill '#d9dce6' \
        -gravity North -annotate "+0+$TEXTO_Y" "$texto" \
        -strip "PNG24:$saida"
}

# moldura <nome> <cor> <realce> <texto>
moldura() {
    local nome="$1" cor="$2" realce="$3" texto="$4"
    faixa "$cor" "$realce" "$texto" "$tmp/esq.png"
    faixa "$cor" "$realce" "" "$tmp/dir-base.png"
    magick "$tmp/dir-base.png" -flop "$tmp/dir.png"
    magick -size 640x${ALT} xc:none \
        "$tmp/esq.png" -geometry +0+0 -compose over -composite \
        "$tmp/dir.png" -geometry +${DIR_X}+0 -compose over -composite \
        -strip -define png:compression-level=9 "PNG32:$destino/$nome.png"
    cat > "$destino/$nome.cfg" <<EOF
overlays = 1
overlay0_overlay = $nome.png
overlay0_full_screen = true
overlay0_descs = 0
EOF
}

# DMG: lente cinza-azulada escura, LED "BATTERY".
moldura gb-dmg '#5d6070' 0.004 BATTERY
# GBC Atomic Purple: roxo translúcido, com realce maior na borda, LED "POWER".
moldura gbc-atomic-purple '#4b3b8f' 0.008 POWER

echo "molduras geradas em system/usr/share/retroarch-overlays/r36-gameboy"
