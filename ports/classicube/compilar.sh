#!/usr/bin/env bash
# Compila o port nativo ClassiCube para o Allwinner A33 (Cortex-A7)
# em container podman isolado (cores/toolchain).
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cache_dir="$root/work/cache/external"
work_dir="$root/work/ports/classicube"
src_dir="$work_dir/src"
dest_dir="$root/features/60-port-classicube/roms/ports/classicube"

url="https://github.com/ClassiCube/ClassiCube/archive/refs/tags/1.3.9.tar.gz"
sha256_esperado="5bb62dbb3ad27e1fbb09842f0cb1f4802b2686553b017e0b67ce09b36f908246"
tarball="$cache_dir/classicube-1.3.9.tar.gz"

mkdir -p "$cache_dir" "$work_dir" "$dest_dir"

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
cp "$bin_gerado" "$dest_dir/ClassiCube"
chmod 0755 "$dest_dir/ClassiCube"

tamanho="$(stat -c%s "$dest_dir/ClassiCube")"
sha_bin="$(sha256sum "$dest_dir/ClassiCube" | awk '{print $1}')"
echo "    Destino: $dest_dir/ClassiCube"
echo "    Tamanho: $tamanho bytes"
echo "    sha256:  $sha_bin"
echo "==> Compilação concluída com sucesso."
