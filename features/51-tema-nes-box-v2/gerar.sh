#!/usr/bin/env bash
# Gera a camada storage da feature 51 (tema NES-BOX-V2).
# Precisa de debugfs (e2fsprogs) e da imagem base em base/. Não é usado pelo
# build: o resultado fica em storage/ e o build só o lê. A cópia do NES-BOX é
# extraída da p8 da base (só leitura, sem root) e fica fora do git, porque o
# Readme do tema proíbe compartilhar versões modificadas e reusar os gráficos.
set -euo pipefail

aqui="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
raiz="$(cd "$aqui/../.." && pwd)"
config="$raiz/config/base.toml"
destino="$aqui/storage/.config/emulationstation/themes/NES-BOX-V2"

command -v debugfs >/dev/null || { echo "erro: debugfs (e2fsprogs) não encontrado" >&2; exit 1; }

# Valor de uma chave dentro de uma seção do base.toml.
valor() {
    awk -v sec="[$1]" -v chave="$2" '
        /^\[/ { dentro = ($0 == sec) }
        dentro && $1 == chave { sub(/^[^=]*= */, ""); sub(/ *#.*$/, ""); print; exit }' "$config"
}

base="$raiz/$(valor base path | tr -d '"')"
[[ -f "$base" ]] || { echo "erro: imagem base não encontrada: $base" >&2; exit 1; }
inicio="$(valor partitions.storage start)"
setores="$(valor partitions.storage sectors)"

tmp="$(mktemp -d "$raiz/work/gerar-nes-box-v2.XXXXXX" 2>/dev/null || { mkdir -p "$raiz/work"; mktemp -d "$raiz/work/gerar-nes-box-v2.XXXXXX"; })"
trap 'rm -rf "$tmp"' EXIT

# Extrai a p8 da base e copia o NES-BOX para fora dela.
dd if="$base" of="$tmp/p8.img" bs=512 skip="$inicio" count="$setores" status=none
# O rdump quebra caminhos com espaço, então roda dentro de $tmp. Os avisos de chown
# (sem root) são esperados e não impedem a cópia dos arquivos.
(cd "$tmp" && debugfs -R "rdump /.config/emulationstation/themes/NES-BOX ." p8.img >/dev/null 2>&1) || true
[[ -f "$tmp/NES-BOX/theme.xml" ]] || { echo "erro: NES-BOX não encontrado na p8 da base" >&2; exit 1; }

mkdir -p "$destino"
cp -a "$tmp/NES-BOX/." "$destino/"

# .gitignore da feature (fora do tema, para não ir ao cartão): cada entrada do
# NES-BOX no nível raiz do V2. As pastas novas não existem no NES-BOX, então
# ficam versionadas.
rm -f "$destino/.gitignore"
{
    echo "# Gerado por gerar.sh: cópia do NES-BOX da base, fora do git (licença do tema)."
    (cd "$tmp/NES-BOX" && find . -mindepth 1 -maxdepth 1 -printf '/storage/.config/emulationstation/themes/NES-BOX-V2/%f\n' | LC_ALL=C sort)
} > "$aqui/.gitignore"

echo "NES-BOX copiado para ${destino#"$raiz/"}"

# theme.xml das pastas novas: o do NES-BOX (igual em todas as pastas) com os
# caminhos das imagens trocados (o ES só resolve caminho relativo que começa com
# "./", então a referência é "./../pasta/", nunca "../pasta/"). Esta função recebe a pasta e o prefixo dos PNGs.
escreve_theme_xml() {
    local sistema="$1" prefixo="$2"
    mkdir -p "$destino/$sistema"
    sed -e "s|<path>\./system\.png</path>|<path>${prefixo}system.png</path>|" \
        -e "s|<path>\./background_icon\.png</path>|<path>${prefixo}background_icon.png</path>|" \
        "$destino/3do/theme.xml" > "$destino/$sistema/theme.xml"
}

# Sistemas só com nome diferente: a pasta tem só o theme.xml, que aponta para a
# arte da pasta equivalente (tabela [referencias] do fontes.toml).
while IFS=' ' read -r sistema existente; do
    [[ -d "$destino/$existente" ]] || { echo "erro: pasta equivalente ausente: $existente" >&2; exit 1; }
    escreve_theme_xml "$sistema" "./../$existente/"
done < <(awk '
    /^\[/ { dentro = ($0 == "[referencias]"); next }
    dentro && /^"/ { gsub(/"/, ""); print $1, $3 }' "$aqui/fontes.toml")

echo "pastas por referência geradas"

# ---------------------------------------------------------------- arte nova
command -v magick >/dev/null || { echo "erro: ImageMagick 7 (magick) não encontrado" >&2; exit 1; }
command -v uv >/dev/null || { echo "erro: uv não encontrado" >&2; exit 1; }
cache="$raiz/work/cache/nes-box-v2"
mkdir -p "$cache"

# Itens do [[arte]] do fontes.toml, um por linha, campos separados por tab.
lista_arte() {
    uv run python -I -c '
import sys, tomllib
for a in tomllib.load(open(sys.argv[1], "rb"))["arte"]:
    print("\t".join(a.get(k, "-") or "-" for k in
          ("sistema", "arquivo", "tipo", "cache", "url", "sha256", "ajuste", "icone", "texto", "cor")))
' "$aqui/fontes.toml"
}

# Baixa o original (se ainda não estiver no cache) e confere o sha256.
baixa_original() {
    local arquivo="$1" url="$2" sha="$3"
    if [[ ! -f "$cache/$arquivo" ]]; then
        curl -sfL -A "r36s-theme-research/1.0" -o "$cache/$arquivo" "$url" \
            || { echo "erro: download falhou: $url" >&2; exit 1; }
    fi
    local obtido
    obtido="$(sha256sum "$cache/$arquivo" | cut -d' ' -f1)"
    [[ "$obtido" == "$sha" ]] || { echo "erro: sha256 divergente em $arquivo ($obtido, esperado $sha)" >&2; exit 1; }
}

# Logo: PNG transparente cortado rente, com 500 px de largura.
logo_oficial() {
    local origem="$1" saida="$2" ajuste="$3"
    local args=(-background none -density 300 "$origem")
    [[ "$ajuste" == "fundo-branco" ]] && args+=(-fuzz 12% -transparent white)
    magick "${args[@]}" -trim +repage -resize 500x "PNG32:$saida"
}

# Arte de personagem: 960x540 transparente, motivo cortado rente e encaixado
# na metade direita (caixa de 460x500 com margem).
arte_oficial() {
    local origem="$1" saida="$2"
    magick -background none -density 300 "$origem" -trim +repage -resize 460x500 \
        -background none -gravity center -extent 480x540 "PNG32:$saida.parte"
    magick -size 960x540 xc:none "$saida.parte" -gravity east -composite "PNG32:$saida"
    rm -f "$saida.parte"
}

# Ícone Lucide (fonte-<nome>.svg) rasterizado em traço da cor dada, no tamanho dado.
icone_png() {
    local nome="$1" cor="$2" tamanho="$3" saida="$4"
    sed "s/currentColor/$cor/" "$aqui/fonte-$nome.svg" > "$tmp/icone-$nome.svg"
    magick -background none -density 1200 "$tmp/icone-$nome.svg" -resize "${tamanho}x${tamanho}" "PNG32:$saida"
}

# Logo criado: ícone do assunto e o nome do sistema em texto, cinza escuro.
logo_criado() {
    local icone="$1" texto="$2" saida="$3"
    icone_png "$icone" "#3a3f4b" 100 "$tmp/logo-icone.png"
    magick -background none -fill "#3a3f4b" -font Liberation-Sans-Bold -size 380x90 -gravity west \
        "label:$texto" "PNG32:$tmp/logo-texto.png"
    magick "$tmp/logo-icone.png" -background none -gravity center -extent 120x100 "$tmp/logo-texto.png" \
        +append -background none -gravity center -trim +repage -resize 500x "PNG32:$saida"
}

# Arte de personagem criada: círculo colorido com o ícone do assunto em branco,
# com sombra suave, na metade direita do 960x540.
arte_criada() {
    local icone="$1" cor="$2" saida="$3"
    icone_png "$icone" "white" 230 "$tmp/arte-icone.png"
    magick -size 340x340 xc:none -fill "$cor" -draw "circle 170,170 170,2" \
        "$tmp/arte-icone.png" -gravity center -composite "PNG32:$tmp/arte-circulo.png"
    magick "$tmp/arte-circulo.png" \( +clone -background black -shadow 35x10+0+12 \) +swap \
        -background none -layers merge +repage -gravity center -extent 480x540 "PNG32:$tmp/arte-parte.png"
    magick -size 960x540 xc:none "$tmp/arte-parte.png" -gravity east -composite "PNG32:$saida"
}

while IFS=$'\t' read -r sistema arquivo tipo origem url sha ajuste icone texto cor; do
    mkdir -p "$destino/$sistema"
    saida="$destino/$sistema/$arquivo"
    if [[ "$tipo" == "oficial" ]]; then
        baixa_original "$origem" "$url" "$sha"
        case "$arquivo" in
            system.png)          logo_oficial "$cache/$origem" "$saida" "$ajuste" ;;
            background_icon.png) arte_oficial "$cache/$origem" "$saida" ;;
        esac
    else
        case "$arquivo" in
            system.png)          logo_criado "$icone" "$texto" "$saida" ;;
            background_icon.png) arte_criada "$icone" "$cor" "$saida" ;;
        esac
    fi
done < <(lista_arte)

# theme.xml das pastas com arte própria (caminhos "./", como nas pastas do NES-BOX).
while read -r sistema; do
    escreve_theme_xml "$sistema" "./"
done < <(lista_arte | cut -f1 | sort -u)

# LEIA-ME.txt: registro de origem, gerado do fontes.toml para os dois não divergirem.
uv run python -I - "$aqui/fontes.toml" "$aqui/LEIA-ME.txt" <<'PY'
import sys, tomllib
fontes = tomllib.load(open(sys.argv[1], "rb"))
linhas = [
    "Tema NES-BOX-V2",
    "===============",
    "",
    "Cópia do NES-BOX da imagem base (tema padrão, que continua intacto) mais uma pasta",
    "para cada sistema do es_systems.cfg que o NES-BOX não cobre. Escolha no aparelho:",
    "Menu > Configurações da interface > Tema > NES-BOX-V2. Fica no /storage, então só",
    "chega ao cartão com --wipe-storage. Para desligar: enabled = false no feature.toml.",
    "",
    "A cópia do NES-BOX não está no git: o Readme do tema (Travis Wilson) proíbe",
    "compartilhar versões modificadas e reusar os gráficos em outros projetos. Uso",
    "pessoal nesta imagem. Rode ./gerar.sh (precisa da imagem base em base/, de debugfs,",
    "ImageMagick 7 e uv) para recriar a cópia, as pastas novas e este arquivo.",
    "Logos e personagens de terceiros são marcas e obras dos donos, também para uso pessoal.",
    "Os ícones das artes criadas são do Lucide (ISC), em fonte-<nome>.svg.",
    "",
    "Origem da arte acrescentada",
    "---------------------------",
    "",
    "Pasta por referência (só theme.xml, aponta para a arte da pasta equivalente do V2):",
]
for novo, existente in fontes["referencias"].items():
    linhas.append(f"  {novo:<14} -> {existente}")
linhas += ["", "Arte própria (oficial = baixada, com URL e sha256; criado = feito pelo gerar.sh):"]
ultimo = None
for a in fontes["arte"]:
    if a["sistema"] != ultimo:
        linhas += ["", f"  {a['sistema']}"]
        ultimo = a["sistema"]
    linhas.append(f"    {a['arquivo']}: {a['tipo']}")
    if a["tipo"] == "oficial":
        linhas += [f"      fonte:  {a['fonte']}", f"      url:    {a['url']}", f"      sha256: {a['sha256']}"]
        if a.get("ajuste"):
            linhas.append(f"      ajuste: {a['ajuste']}")
    else:
        linhas.append(f"      motivo: {a['motivo']}")
open(sys.argv[2], "w").write("\n".join(linhas) + "\n")
PY

echo "arte gerada"
