# Design

## Context

Ver proposal.md (Why). Fatos levantados na base que definem a abordagem:

**Vídeo e telas**
- A tela é 640x480. O GB e o GBC rodam no core `gambatte` (padrão nas duas pastas), no RetroArch 1.17.0 com driver `gl` (GLES2, Mali-400 MP2).
- O `setsettings.sh` desta base só aplica `netplay`, `snapshot` e `shaderset` do `emuelec.conf`. O loop de `ratio`, `smooth` e `integerscale` está comentado. O `shaderset` também está quebrado: só emite `--set-shader /tmp/shaders/<valor>` quando o valor é `1` ou `true`.
- O `bezels.sh` roda a cada jogo e reescreve `aspect_ratio_index`, `video_scale_integer`, `custom_viewport_*` e `input_overlay*` no `retroarch.cfg` global sempre que `/storage/.config/bezels_enabled` existe. O `global.bezel=0` está desligado.
- `/tmp/shaders` é um overlayfs de `/usr/share/common-shaders` (embaixo) com `/storage/shaders` (em cima), e `/tmp/overlays` é um overlayfs de `/usr/share/retroarch-overlays` com `/storage/overlays`. O `video_shader_dir` e o `overlay_directory` apontam para `~/shaders` e `~/overlays`.
- Shaders de fábrica úteis em `common-shaders/rpi`:
  - `gameboy.glslp`: 5 passadas. O pass0 (`dot.glsl`) é `viewport`, e os 4 do `gb-pass` são `source x1` sobre ele, ou seja, também em resolução de tela.
  - `gameboy-screen-grid.glslp` (2 passadas), `zfast_lcd_standard.glslp` (1 passada), `hq2x_lcd3x`, e as paletas em `resources/` (`dmg-palette-*`, `gbp-palette` e outras).
- Opções do gambatte nesta build: `gambatte_gb_colorization`, `gambatte_gb_internal_palette` (com `GB - DMG`), `gambatte_gbc_color_correction` e `gambatte_gbc_color_correction_mode`.

**Telas de boot**
- O `/usr/bin/lsb_release` de fábrica, chamado no boot pelo `show-version.service`, carrega `disp.ko`, `lcd.ko` e `mali.ko` e desenha `/usr/config/splash/splash-1080.raw` direto no framebuffer com `ffplay`. Esse conteúdo fica no `fb0`.
- Ao abrir um jogo, o `emuelecRunEmu.sh` roda `mpv /storage/.config/splash/loading-game.png &`. No intervalo entre o mpv sair e o RetroArch desenhar, aparece o que ficou no `fb0`, que é a tela de boot.
- O EmulationStation carrega `:/logo.png` como fundo da tela de carregamento, com o texto de progresso por cima. As cópias em `/usr/config/emulationstation/resources/logo.png` e `/storage/.config/emulationstation/resources/logo.png` têm o sha256 `f7e623e6…` da arte de fábrica, que é o God of War.
- O binário do ES procura um `:/splash.xml` (e `/splash.xml` no tema) com elementos de `progressbar`. É o layout da tela de carregamento do ES do Batocera.

**Projeto**
- O carregador de features rejeita subdiretórios que não sejam camadas. Por isso fontes e scripts ficam soltos na raiz da feature, como na feature 30.
- A feature 30 gera as telas com ImageMagick 7 (`gerar.sh`), versiona os PNGs nas camadas e registra os sha256 no LEIA-ME. O `tests/test_splash.py` confere os arquivos contra o LEIA-ME.

## Goals / Non-Goals

**Goals:**
- Configurar GB e GBC sem tocar no `retroarch.cfg` global nem em scripts de fábrica.
- Artes 100% reproduzíveis pelo script da feature.
- Uma única imagem do boot até o jogo, sem depender do que sobra no framebuffer.

**Non-Goals:**
- Moldura para GBA, Game Gear e outros portáteis.
- Corrigir o `shaderset` ou o `setsettings.sh` de fábrica.
- Mexer no logo do U-Boot, na tela de bateria e no vídeo de introdução.
- Atualizar o `/storage` de cartões gravados com `--keep-storage`.
- Moldura alternativa em 3x ou troca de cor do GBC pelo menu.

## Decisions

1. **Configuração por override de diretório de conteúdo do RetroArch.** Os arquivos ficam na camada `storage`:
   - `/storage/.config/retroarch/config/Gambatte/gb.cfg` e `gbc.cfg` (overrides de vídeo e overlay);
   - `gb.opt` e `gbc.opt` (opções do core);
   - `/storage/shaders/presets/Gambatte/gb.glslp` e `gbc.glslp` (preset automático de shader por diretório).

   O RetroArch escolhe esses arquivos pelo nome da pasta da ROM (`gb` ou `gbc`), então nenhum outro core nem sistema é afetado. Os overrides têm prioridade sobre o `retroarch.cfg`, então o `bezels.sh` pode reescrever o global sem desfazer nada.
   - Descartado: as chaves `gb.*` do `emuelec.conf`, porque o `setsettings.sh` desta base ignora `ratio` e `integerscale`, e o `shaderset` está quebrado.
   - Descartado: o `bezels.sh` com `/storage/roms/bezels/gb/default.cfg`, porque ele mexe no `retroarch.cfg` global e depende de `gb.bezel=1`.

2. **Viewport customizado de 534x480 na altura total.** A proporção 10:9 em 480 px de altura dá 533,33 px de largura. Arredondado para 534, sobram 53 px iguais de cada lado. Cada override declara:
   - `aspect_ratio_index` = o índice "Custom" do RetroArch 1.17 (23, a confirmar na tarefa);
   - `custom_viewport_width = 534`, `custom_viewport_height = 480`, `custom_viewport_x = 53` e `custom_viewport_y = 0`;
   - `video_scale_integer = "false"`, `input_overlay_enable = "true"`, `input_overlay` com o caminho absoluto do `.cfg` da moldura, `input_overlay_opacity = "1.0"` e `input_overlay_hide_in_menu = "false"`.

   O viewport é fixado explicitamente, em vez de usar a proporção "core provided", para o recorte da moldura bater pixel a pixel sem depender do arredondamento do RetroArch. A escala (3,33x) não é inteira: cada pixel do jogo vira 3 ou 4 pixels da tela, alternando. A grade do shader (decisão 4), calculada na resolução da tela, disfarça essa irregularidade. Com `video_smooth = "false"`, as bordas continuam nítidas.
   - Descartado: escala inteira 3x (480x432). Perde 48 px de altura e cria faixas em cima e embaixo; o usuário escolheu a altura total.

3. **Molduras geradas por script, com geometria fixa.** Um `gerar.sh` com ImageMagick 7, no padrão da feature 30, compõe as duas molduras de 640x480 RGBA.

   Nas duas, o recorte do jogo é x=53 a 586, y=0 a 479 (534x480), transparente. As molduras são só as faixas laterais (x=0 a 52 e x=587 a 639), opacas, de cima a baixo.

   **DMG.**
   - As duas faixas na cor da lente, cinza-azulado escuro (por volta de `#5d6070`, tirada de fotos de referência), com uma sombra interna fina junto ao jogo.
   - Esquerda: LED vermelho com brilho e o texto "BATTERY" abaixo, centrados na faixa, na altura do LED real.
   - Direita: lisa, sem texto nem linhas.

   **GBC Atomic Purple.**
   - As duas faixas em roxo translúcido (por volta de `#4b3b8f`), com textura e brilho leves que sugerem plástico translúcido.
   - Esquerda: LED e o texto "POWER".
   - Direita: lisa, sem texto.

   A geometria exata é registrada no LEIA-ME e usada pelos overrides. As fontes ficam soltas na raiz da feature com origem, licença e sha256:
   - uma fonte tipográfica livre (OFL) parecida com a do console, para "BATTERY" e "POWER".
   - Descartado: os pacotes prontos (drkhrse, mugwomp93, Jeltr0n). O drkhrse tem o mesmo estilo de faixas laterais, mas nenhum deles tem licença, e as faixas dele não batem com o recorte de 534 px.

4. **Cor e textura do LCD.** O shader é escolhido medindo no aparelho:

   **GB, opção preferida:** gambatte com `gambatte_gb_colorization = "disabled"` (saída em cinza) e o preset com o `gameboy.glslp` de fábrica, usando a paleta `dmg-palette` em `resources/`. Esse shader aplica os 4 verdes do DMG, a grade e a sombra e o "fantasma" dos pixels. É o mais fiel.

   **GB, alternativa (se ficar abaixo de 60 fps):** `gambatte_gb_colorization = "internal"` com `gambatte_gb_internal_palette = "GB - DMG"`, mais um preset de 1 passada com grade (`zfast_lcd_standard`).

   **GBC:** `gambatte_gbc_color_correction = "GBC only"` mais o preset de grade leve.

   Os presets na camada `storage` apontam para os `.glsl` de fábrica por caminho absoluto em `/usr/share/common-shaders/…`. Um caminho relativo, a partir de `/storage/shaders/presets`, não acharia os arquivos de baixo do overlayfs.

5. **Molduras na camada `system`, overrides na `storage`.** Os PNGs e `.cfg` de overlay vão para `/usr/share/retroarch-overlays/r36-gameboy/`, que fica visível em `/tmp/overlays/r36-gameboy/`, e os overrides apontam para lá. Assim, uma atualização só do SYSTEM já leva artes novas. Os overrides precisam do storage de qualquer forma, porque o diretório de config do RetroArch é só o `/storage`.

6. **Uma imagem só do boot ao jogo: o ícone vira também a tela de boot.** O `gerar.sh` da feature 30 passa a escrever o PNG do ícone em `splash-std.png`, `splash-1080.png`, `retroarch.png`, `splash-1080.raw` (RGB24), `loading-game*.png` e também nos dois `emulationstation/resources/logo.png` (SYSTEM e STORAGE).
   - Como o `fb0` passa a guardar o ícone desde o boot, o intervalo entre o mpv sair e o RetroArch desenhar mostra o próprio ícone, sem precisar mexer no `emuelecRunEmu.sh`.
   - Descartado: manter o mpv aberto até o RetroArch assumir. Exigiria editar o script de fábrica e matar o processo, e não cobriria a volta do jogo.

7. **Esconder o texto de progresso do ES.** Um `splash.xml` em `resources/` (SYSTEM e STORAGE) define a tela de carregamento só com a imagem de fundo, sem texto e sem barra. A sintaxe é conferida no código do batocera-emulationstation (`Splash.cpp`). Se este fork não aceitar `visible = false`, há duas saídas, nesta ordem:
   1. texto com tamanho mínimo e mesma cor do fundo;
   2. remover o elemento do layout.

   A validação no aparelho decide.

8. **Feature 30 renomeada para `30-telas-icone-controle`.** A feature deixa de usar o EmuELEC. Saem `fonte-splash-distribuicao-1080.png`, o crédito e o aviso de branding, e o Lucide (ISC) continua. O `tests/test_splash.py` e o README seguem o novo nome. A verificação da arte de fábrica passa a varrer todos os arquivos do SYSTEM e do STORAGE gerados, não só os diretórios de splash.

9. **Nova feature `51-gameboy-fiel`** (`order = 51`), com:
   - camadas `system` (molduras e `.cfg` de overlay) e `storage` (overrides, `.opt` e presets);
   - na raiz: `gerar.sh`, `LEIA-ME.txt` e as fontes.

   Um teste novo, `tests/test_gameboy.py`, confere:
   - os sha256 contra o LEIA-ME;
   - 640x480 RGBA;
   - alfa zero em todo o retângulo do jogo (534x480 em x=53) e alfa total nas faixas laterais;
   - que os `custom_viewport_*` dos overrides batem com o recorte registrado.

## Risks / Trade-offs

- [O `gameboy.glslp` de 5 passadas em resolução de tela não segura 60 fps na Mali-400] → a área de 534x480 tem 78% mais pixels que um layout em 2.5x, então o risco é real. Usar a alternativa da decisão 4 (paleta no core e grade de 1 passada), medida no aparelho antes de fechar.
- [A grade em escala não inteira (3,33x) fica irregular] → o shader é calculado na resolução da tela. Se ainda incomodar, testar o `gameboy-screen-grid`. Não muda a geometria.
- [O índice "Custom" de `aspect_ratio_index` difere nesta build] → conferir pelo menu (Vídeo, Escala, Proporção) e no `retroarch.cfg` salvo, e ajustar o número.
- [O override por pasta não é aplicado (nome da pasta ou do core diferente de `Gambatte`)] → conferir o nome do core no `gambatte_libretro.info` e testar com o RetroArch mostrando "Override de diretório carregado".
- [Este fork do ES não aceita esconder o texto pelo `splash.xml`] → as saídas da decisão 7.
- [`--keep-storage` mantém o God of War no ES e o GB sem moldura] → documentado no README, com cópia manual pelo PC (`R36-STORAGE`) como alternativa.
- [Fidelidade das cores sem acesso ao console] → as cores são calibradas por fotos de referência citadas no LEIA-ME e aprovadas pelo usuário numa prévia antes de gravar o cartão.

## Migration Plan

- Gravar com `--wipe-storage` para receber tudo. Com `--keep-storage`, só a tela de boot muda.
- Rollback: desabilitar `51-gameboy-fiel` no `feature.toml` e reverter o commit da feature 30.

## Open Questions

- Cores exatas da carcaça e da lente: definidas na prévia aprovada pelo usuário, sem mudar geometria nem specs.
