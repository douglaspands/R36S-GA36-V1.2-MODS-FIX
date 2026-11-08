# ELF de teste do `gba-recomp`

`teste.c` (o `Teste.elf`) abre a tela (SDL2 + GLES2), toca 440 Hz e espera `SIGTERM`. Serve para validar
no aparelho a lista, o `recomp.sh`, o som e o FN + Start sem o recompilador.

**Estado:** compilado e conferido com `readelf` (ARMv7, VFPv4, hard-float, GLIBC até
2.34, NEEDED `libSDL2-2.0.so.0` e `libGLESv2.so.2`), **mas nunca rodado no aparelho**.
Compila em container Debian Bookworm (podman), a partir da raiz do projeto:

```
podman run --rm -v ./tools/recomp_teste:/src:Z docker.io/library/debian:bookworm sh /src/compila.sh
```

O pacote segue o formato dos jogos recompilados: `pacote/Teste.sh` e `pacote/Teste/`
(`launch.sh` e `Teste.elf`). Copie os dois para `roms/gba-recomp/` na p1 (o ES lista o `Teste.sh`).
O nome do processo (`comm`) do ELF sai na primeira linha do `recomp.log` (`teste: processo=...`);
esperado `Teste.elf`, o mesmo nome que o `recomp.log` mostra em "processo que o FN + Start encerra".
