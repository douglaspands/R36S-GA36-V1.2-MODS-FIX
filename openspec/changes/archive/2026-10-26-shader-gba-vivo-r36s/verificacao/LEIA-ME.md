# Verificação do shader gba-modern-remaster

Os números dos cenários da spec (`specs/gba-emulation/spec.md`) saem da réplica numérica
`replica.py`, não do aparelho. A réplica espelha o `.glsl` à mão: ao mudar o shader, mude
`shader()` e `DEF` aqui e confira que as medidas ainda cumprem a spec.

## Rodar

```
uv run --with pillow --with numpy python -I openspec/changes/shader-gba-vivo-r36s/verificacao/replica.py \
    CAPTURA_MARIO_KART.png CAPTURA_SMA3.png var/exemplos-lcd
```

`pillow` e `numpy` vêm por `--with`: o projeto não os declara (`pyproject.toml` sem dependências).
O último argumento é opcional e grava comparações em 640x427 (a tela do R36S, GBA em 2,67x).

## Capturas de entrada

São capturas do mGBA **sem shader**, em 480x320 (2x de 240x160), de:
- *Mario Kart: Super Circuit*, tela de título, frame 1200;
- *Super Mario Advance 3: Yoshi's Island*, tela "Choose a Language", frame 500.

Foram feitas com o RetroArch Flatpak 1.22.2 (que **não está mais instalado** na máquina do
usuário) e ficaram em `~/.cache/shader-gba-test/{mk,sma}_sem/shots/`. Para refazer:
`flatpak run org.libretro.RetroArch -L <mgba_libretro.so> --appendconfig <cfg> --max-frames=<N> --max-frames-ss <rom.zip>`
com `video_gpu_screenshot = "true"`, `video_scale = "2.0"`, `video_scale_integer = "true"`,
`audio_enable = "false"` e `screenshot_directory` num diretório próprio. Não commite capturas
de jogos nem ROMs: ficam fora do git.

## O que NÃO se consegue medir no PC

- **Captura com o shader no RetroArch do PC:** sai ampliada e esticada de forma desigual, tanto
  com o shader novo quanto com o antigo (problema da captura de GPU do RetroArch/mGBA, não do
  shader), então a comparação posição a posição precisa da réplica.
- **Precisão `mediump` real do Mali-400 e tempo de quadro:** só no aparelho. A réplica emula fp16
  com arredondamento nos pontos críticos (`fp16=True`) e dá PSNR de 35 dB (Mario Kart) e 41 dB
  (SMA3) em 640x427; é estimativa.
- **O que o EmuELEC faz com `gba.shaderset` e com o preset de core:** ver `design.md`, Decisão 10.
