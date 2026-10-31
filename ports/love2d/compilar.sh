#!/usr/bin/env bash
# Compila o LÖVE 11.5 standalone para o Allwinner A33 (Cortex-A7)
# em container podman isolado (Debian Bookworm armhf).
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cache_dir="$root/work/cache/external"
work_dir="$root/work/ports/love2d"
src_dir="$work_dir/src"
dest_bin="$root/features/64-love2d/system/usr/bin"

url="https://github.com/love2d/love/releases/download/11.5/love-11.5-linux-src.tar.gz"
sha256_esperado="066e0843f71aa9fd28b8eaf27d41abb74bfaef7556153ac2e3cf08eafc874c39"
tarball="$cache_dir/love-11.5-linux-src.tar.gz"

mkdir -p "$cache_dir" "$work_dir" "$dest_bin"

echo "==> Verificando código fonte upstream do LÖVE 11.5"
if [ ! -f "$tarball" ]; then
  echo "    Baixando $url..."
  python3 -I -c "import urllib.request; req=urllib.request.Request('$url', headers={'User-Agent': 'Mozilla/5.0'}); open('$tarball', 'wb').write(urllib.request.urlopen(req).read())"
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

echo "==> Aplicando patches para R36S (viewport 640x480 e controles)"
if [ -d "$root/ports/love2d/patches" ]; then
  for patch_file in "$root/ports/love2d/patches"/*.patch; do
    if [ -f "$patch_file" ]; then
      echo "    Aplicando $(basename "$patch_file")..."
      patch -d "$src_dir" -p1 < "$patch_file"
    fi
  done
fi

echo "==> Construindo container de compilação (localhost/r36-love2d-builder)"
podman build -q -t localhost/r36-love2d-builder "$root/ports/love2d"

echo "==> Compilando LÖVE 11.5 para ARMv7-A hard-float (Cortex-A7, NEON, GLES2)"
cflags="-pipe -fno-math-errno -O3 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -DLOVE_GRAPHICS_USE_OPENGLES=1"
cxxflags="-pipe -fno-math-errno -O3 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -DLOVE_GRAPHICS_USE_OPENGLES=1 -static-libstdc++"
ldflags="-s -Wl,--gc-sections -static-libstdc++"

podman run --rm --userns=keep-id \
  -v "$src_dir":/build/src:Z \
  -w /build/src \
  localhost/r36-love2d-builder \
  bash -c "
    export PKG_CONFIG_PATH=/usr/lib/arm-linux-gnueabihf/pkgconfig
    export PKG_CONFIG_LIBDIR=/usr/lib/arm-linux-gnueabihf/pkgconfig
    ./configure \
      --host=arm-linux-gnueabihf \
      --prefix=/usr \
      --with-lua=luajit \
      --enable-shared=no \
      --enable-static=yes \
      CC=arm-linux-gnueabihf-gcc \
      CXX=arm-linux-gnueabihf-g++ \
      CFLAGS='$cflags' \
      CXXFLAGS='$cxxflags' \
      LDFLAGS='$ldflags'
    make -j\$(nproc)
    arm-linux-gnueabihf-strip --strip-unneeded src/love
  "

bin_gerado="$src_dir/src/love"
if [ ! -f "$bin_gerado" ]; then
  echo "ERRO: O executável $bin_gerado não foi gerado." >&2
  exit 1
fi

echo "==> Instalando executável na feature 64-love2d"
cp "$bin_gerado" "$dest_bin/love"
chmod 0755 "$dest_bin/love"

tamanho="$(stat -c%s "$dest_bin/love")"
sha_bin="$(sha256sum "$dest_bin/love" | awk '{print $1}')"
echo "    Destino: $dest_bin/love"
echo "    Tamanho: $tamanho bytes"
echo "    sha256:  $sha_bin"
echo "==> Compilação concluída com sucesso."
