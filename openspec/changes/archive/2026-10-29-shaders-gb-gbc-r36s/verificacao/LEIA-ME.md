# Verificação dos shaders gb-modern-dmg e gbc-modern-remaster

Os números dos cenários da spec (`specs/gb-gbc-emulation/spec.md`) saem da réplica numérica
`replica.py`, não do aparelho. A réplica espelha os `.glsl` à mão: ao mudar um shader, mude
`cor_gb`/`cor_gbc`, a grade e os dicionários `DEF_GB`/`DEF_GBC` (e `T`, `SUBSTRATO`) e confira
que as medidas ainda cumprem a spec. `tests/test_shaders_gb_gbc.py` confere que os padrões, a
paleta e as constantes do `.glsl` são os da réplica.

## Rodar

Da raiz do projeto:

```
bash openspec/changes/shaders-gb-gbc-r36s/verificacao/capturar-sem-shader.sh gb "/mnt/backup/PC/R36S/roms/gb/Super Mario Land II - 6 Golden Coins.zip" sml2 600
uv run --with pillow --with numpy python -I openspec/changes/shaders-gb-gbc-r36s/verificacao/replica.py
```

`pillow` e `numpy` vêm por `--with`: o projeto não os declara. A réplica lê as capturas de
`~/.cache/shader-gb-gbc-test/` e grava as pranchas em `var/exemplos-gb-gbc/` (fora do git); os
dois caminhos podem ser passados como argumentos. Sai com código 1 se alguma medida falha.

## Capturas de entrada

Quadros **sem shader**, em 160x144, feitos com `~/AppImages/retroarch.appimage` (RetroArch 1.22.2)
por `capturar-sem-shader.sh`, que usa config própria (`--config`, sem tocar na do usuário) e
`video_gpu_screenshot = "false"` (o quadro do core, sem escala nem filtro):

| Nome | Sistema | ROM (`/mnt/backup/PC/R36S/roms/...`) | Quadro |
|---|---|---|---|
| `sml2-f600` | gb | `gb/Super Mario Land II - 6 Golden Coins.zip` | 600 (título) |
| `zelda-la-f1500` | gb | `gb/Legend of Zelda - Link's Awakening.zip` | 1500 (praia) |
| `pokemon-red-f700` | gb | `gb/Pokemon - Red Version.zip` | 700 (título) |
| `smb-deluxe-f500` | gbc | `gbc/Super Mario Bros. Deluxe (USA, Europe) (Rev B).zip` | 500 (título) |
| `zelda-dx-f1500` | gbc | `gbc/Legend of Zelda, The - Link's Awakening DX (USA, Europe) (Rev B) (SGB Enhanced).zip` | 1500 (praia) |
| `dkc-f700` | gbc | `gbc/Donkey Kong Country (USA, Europe) (En,Fr,De,Es,It).zip` | 700 (idioma) |

Comandos: `capturar-sem-shader.sh gb <rom> zelda-la 1500`, `... gb <rom> pokemon-red 700`,
`... gbc <rom> smb-deluxe 500`, `... gbc <rom> zelda-dx 1500`, `... gbc <rom> dkc 700`.

**Core:** o PC não tem o Gambatte (`~/.config/retroarch/cores` só tem o `mgba_libretro.so`), então
as capturas saíram do mGBA, que o `es_systems.cfg` também lista para `gb` e `gbc`. O script fixa
o modelo (`Game Boy` ou `Game Boy Color`), sem borda de SGB, paleta `Grayscale` e sem correção
de cor, o mesmo papel do `gb.opt`/`gbc.opt` da feature 55 no Gambatte. Os valores exatos dos
cinzas e da conversão RGB555 -> RGB888 podem diferir entre os cores (o mGBA entrega 0/82/173/255):
a réplica mede os 4 tons com 0/85/170/255 (a spec) e com os cinzas do mGBA, e o shader trabalha
sobre a luma, então diferenças pequenas caem no mesmo tom.
Se o Gambatte for instalado em `~/.config/retroarch/cores`, o script passa a usá-lo.

Não commite capturas de jogos nem ROMs: ficam fora do git.

## O que a réplica mede

- GB: os 4 níveis (0/85/170/255 e os do mGBA) com `LCD_GRID` 0 (Delta Luma >= 0.20 entre vizinhos,
  L3 > 0.82, L0 < 0.14, G > R > B), a grade em 533x480 sobre blocos de T0 e T3, a nitidez em
  320x288 (2x) e o PSNR fp16 em 533x480 de cada captura.
- GBC: a cartela de 24 cores (matiz <= 2 graus, saturação >= -0.05, `LCD_GRID` 0), e em cada
  captura a nitidez em 2x, o estouro e o PSNR fp16 em 533x480.
- **Nitidez:** gradiente médio do verde (horizontal + vertical) com o shader e `LCD_GRID` 0, contra
  o do vizinho mais próximo **com a mesma transformação de cor** (`cor_gb`/`cor_gbc` aplicada ao
  vizinho), para medir só a amostragem.
- **Estouro:** pixel cuja cor lida pelo shader (já amostrada) tem canal máximo abaixo de 245 e que
  sai em 255. Comparar com o vizinho mais próximo contaria como estouro a borda de um branco.

## Calibração (o que mudou em relação ao design inicial)

- `SOFTNESS` 0.05 nos dois (o design trazia 0.12 no GB; o GBA usa 0.15): os jogos de GB/GBC usam
  muito pontilhado de 1 pixel, e com 0.10 ou mais a nitidez em 2x fica abaixo de 97% (Pokemon
  94,5%, Zelda DX 95,1% e DKC 95,2% com 0.12). Em 3,33x a transição continua com ~1 pixel de saída.
- **Nitidez em 3,33x não é afirmada.** A réplica a imprime (informativa) e a spec mede só 2x: em 3,33x
  o vizinho mais próximo tem bordas duras de 3 e 4 pixels de saída e o sharp-bilinear uma transição de
  ~1 pixel, então o *Pokémon Red* dá 94,6% (95,2% mesmo com `SOFTNESS` 0, 97,6% no *Zelda* e 99,0% no
  *Mario Land 2*). O `SOFTNESS` não resolve; os outros cenários da spec passam com 0.05.
- Teto do `gbc-modern-remaster` em `mx + 0.035` (0.05 no GBA): com 0.05, cores com canal máximo
  243-244 chegavam a 255 (104 pixels no *Super Mario Bros. Deluxe*).
- T0 da paleta `rgb(20, 36, 12)` (o design trazia `rgb(14, 34, 20)`, com azul maior que o vermelho,
  fora do G > R > B da spec).
- Lacuna da grade do GB puxa para `T3 * 0.55` (o design trazia `T3 * 0.88`, que dá só ~2,6% de
  sombra no fundo e não cumpre o cenário de 82% a 96% do pico).

## O que NÃO se consegue medir no PC

- **Precisão `mediump` real do Mali-400 e tempo de quadro:** só no aparelho. A réplica emula fp16
  com arredondamento nos pontos críticos (`fp16=True`).
- **Compilação em GLSL ES 1.00:** os dois shaders compilam e ligam no RetroArch do PC (GL desktop,
  `Loaded 1 program(s)` com preset automático apontando para eles; um erro de sintaxe proposital
  dá `Failed to compile fragment shader`), mas o compilador da Mali-400 só se confere no aparelho.
- **Busca do preset por pasta de conteúdo com ROM em `.zip`:** veja `design.md`, Riscos.
