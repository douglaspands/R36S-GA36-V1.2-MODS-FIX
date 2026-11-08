#!/bin/sh
# Roda DENTRO do container debian:bookworm (veja LEIAME.md). Gera pacote/Teste/Teste.elf (armhf).
set -eu
dpkg --add-architecture armhf
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq gcc-arm-linux-gnueabihf libsdl2-dev:armhf libgles-dev:armhf binutils-arm-linux-gnueabihf
cd /src
arm-linux-gnueabihf-gcc -O2 -march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard \
    -I/usr/include/SDL2 teste.c -o pacote/Teste/Teste.elf \
    -L/usr/lib/arm-linux-gnueabihf -lSDL2 -lGLESv2 -lm
arm-linux-gnueabihf-readelf -A pacote/Teste/Teste.elf
arm-linux-gnueabihf-readelf -d pacote/Teste/Teste.elf
arm-linux-gnueabihf-readelf -V pacote/Teste/Teste.elf
