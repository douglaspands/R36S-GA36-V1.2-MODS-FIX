#!/usr/bin/env bash
# Compila o servidor Dropbear e dropbearkey para o Allwinner A33 (Cortex-A7)
# em container podman isolado (cores/toolchain).
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cache_dir="$root/work/cache/external"
work_dir="$root/work/services/dropbear"
src_dir="$work_dir/src"
dest_dir="$root/features/45-ssh-dropbear/system/usr/sbin"

url="https://matt.ucc.asn.au/dropbear/releases/dropbear-2024.86.tar.bz2"
sha256_esperado="e78936dffc395f2e0db099321d6be659190966b99712b55c530dd0a1822e0a5e"
tarball="$cache_dir/dropbear-2024.86.tar.bz2"

mkdir -p "$cache_dir" "$work_dir" "$dest_dir"

echo "==> Verificando código fonte upstream do Dropbear 2024.86"
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
tar -xjf "$tarball" -C "$src_dir" --strip-components=1

echo "==> Assegurando container da toolchain (localhost/r36-cores-a33)"
podman build -q -t localhost/r36-cores-a33 "$root/cores/toolchain"

echo "==> Compilando Dropbear para Cortex-A7 (ARMv7-A hard-float + NEON-VFPv4 + glibc 2.36)"
cflags="-pipe -O2 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -fvisibility=hidden -ffunction-sections -fdata-sections"
ldflags="-s -Wl,--gc-sections"

podman run --rm --userns=keep-id --network=none \
  -v "$src_dir":/build/src:Z \
  -w /build/src \
  localhost/r36-cores-a33 \
  sh -c "
    CC=arm-linux-gnueabihf-gcc \
    AR=arm-linux-gnueabihf-ar \
    RANLIB=arm-linux-gnueabihf-ranlib \
    CFLAGS='$cflags' \
    LDFLAGS='$ldflags' \
    ./configure --host=arm-linux-gnueabihf --prefix=/usr --disable-wtmp --disable-wtmpx --disable-utmp --disable-utmpx --disable-pam && \
    make -j\$(nproc) PROGRAMS='dropbear dropbearkey'
  "

bin_dropbear="$src_dir/dropbear"
bin_dropbearkey="$src_dir/dropbearkey"
if [ ! -f "$bin_dropbear" ] || [ ! -f "$bin_dropbearkey" ]; then
  echo "ERRO: Binários do Dropbear não foram gerados corretamente." >&2
  exit 1
fi

echo "==> Instalando binários na feature 45-ssh-dropbear"
cp "$bin_dropbear" "$dest_dir/dropbear"
chmod 0755 "$dest_dir/dropbear"
cp "$bin_dropbearkey" "$dest_dir/dropbearkey"
chmod 0755 "$dest_dir/dropbearkey"

# Cria symlink de conveniência em /usr/bin/dropbearkey
mkdir -p "$root/features/45-ssh-dropbear/system/usr/bin"
ln -sf "../sbin/dropbearkey" "$root/features/45-ssh-dropbear/system/usr/bin/dropbearkey"

echo "    Destino: $dest_dir/dropbear"
echo "    Tamanho: $(stat -c%s "$dest_dir/dropbear") bytes"
echo "    sha256:  $(sha256sum "$dest_dir/dropbear" | awk '{print $1}')"

echo "    Destino: $dest_dir/dropbearkey"
echo "    Tamanho: $(stat -c%s "$dest_dir/dropbearkey") bytes"
echo "    sha256:  $(sha256sum "$dest_dir/dropbearkey" | awk '{print $1}')"

echo "==> Compilação do Dropbear concluída com sucesso."
