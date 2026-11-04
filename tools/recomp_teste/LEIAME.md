# ELF de teste do `gba-recomp`

`teste.c` abre a tela (SDL2 + GLES2), toca 440 Hz e espera `SIGTERM`. Serve para validar
no aparelho a lista, o `recomp.sh`, o som e o FN + Start sem o recompilador.

**Estado:** o fonte **não foi compilado nem conferido** (o PC não tem sysroot armhf com
glibc 2.36 e SDL2: sem `arm-linux-gnueabihf-gcc`, `crt1.o` nem cabeçalhos; só o `clang`
sem alvo ARM completo). Quem tiver a toolchain compila assim, de um diretório com o
sysroot da imagem (glibc 2.36, SDL2 do SYSTEM):

```
arm-linux-gnueabihf-gcc -O2 -mfpu=neon-vfpv4 -mfloat-abi=hard \
    --sysroot=<sysroot-armhf> teste.c -o Teste.recomp $(sdl2-config --cflags --libs) -lm
readelf -A Teste.recomp   # Tag_CPU_arch: v7, Tag_ABI_VFP_args: VFP registers
readelf -V Teste.recomp   # GLIBC_ até 2.36
```

Copie `Teste.recomp` para `roms/gba-recomp/` na p1. O nome do processo (`comm`) sai na
primeira linha do `recomp.log` (`teste: processo=...`); esperado `r36-recomp-game`.
