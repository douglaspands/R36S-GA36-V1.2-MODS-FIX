# Tasks

## 1. Uma imagem só: feature 30 com o ícone de controle

- [x] 1.1 Criar a branch `feat/gameboy-fiel-e-tela-icone` a partir da `main` e renomear `features/30-splash-padrao-emuelec/` para `features/30-telas-icone-controle/` com `git mv`. Atualizar o nome e a descrição no `feature.toml`. Verificar com `./build.sh --features 30-telas-icone-controle` que o carregador reconhece a feature sem erro de descritor.
- [x] 1.2 Reescrever o `gerar.sh` (decisão 6):
  - o PNG do ícone (o mesmo do `loading-game.png` atual) vai para `splash-std.png`, `splash-1080.png`, `retroarch.png`, `loading-game*.png` e para os `emulationstation/resources/logo.png` do SYSTEM (`system/usr/config/emulationstation/resources/`) e do STORAGE (`storage/.config/emulationstation/resources/`);
  - o `.raw` RGB24 é gerado do mesmo PNG;
  - remover `fonte-splash-distribuicao-1080.png`.

  Verificar que o `loading-game.png` regerado tem o mesmo sha256 de antes (`a4999143…`) e que `magick compare -metric AE -fuzz 1%` contra `work/splash-exemplos-simbolos/3-icone-controle.png` dá 0.
- [x] 1.3 Conferir no código do batocera-emulationstation (`Splash.cpp`, num commit fixo registrado no LEIA-ME) a sintaxe do `splash.xml`. Escrever um `splash.xml` que mostre só o `logo.png` em tela cheia, sem texto e sem barra de progresso, usando as saídas da decisão 7 se necessário. Colocá-lo em `resources/` no SYSTEM e no STORAGE. Verificar que o XML é válido (`xmllint --noout`) e que o `gerar.sh` ou o LEIA-ME o documentam.
- [x] 1.4 Refazer o `LEIA-ME.txt`:
  - origem só do Lucide (ISC);
  - lista dos arquivos por camada, incluindo `logo.png` e `splash.xml`;
  - sha256 regerados;
  - remover o crédito e o aviso de branding do EmuELEC.

  Verificar que rodar o `gerar.sh` duas vezes não muda nenhum sha256.
- [x] 1.5 Atualizar o `tests/test_splash.py`:
  - novo diretório da feature;
  - todos os PNGs de tela iguais ao do ícone;
  - `.raw` igual ao PNG;
  - `logo.png` nas duas camadas;
  - nenhum arquivo da feature com o sha256 `f7e623e6…` da arte de fábrica.

  Verificar com `uv run python -I -m unittest tests.test_splash`.
- [x] 1.6 Fazer o teste de integração (`R36_SLOW`) varrer todos os arquivos do SYSTEM (squashfs) e do STORAGE (ext4) da imagem gerada atrás do sha256 da arte de fábrica, e conferir que o vídeo de introdução, o logo do U-Boot e a tela de bateria continuam iguais aos da base. Verificar que o teste falha contra a imagem de `./build.sh --no-features` (o God of War está lá) e passa com as features.
- [x] 1.7 Atualizar o README (seção da feature 30): o ícone em todas as telas, o fim do logo do EmuELEC e a necessidade de `--wipe-storage` para o carregamento do ES. Verificar que os caminhos citados existem.

## 2. Fontes e geração das molduras

- [x] 2.1 Criar `features/51-gameboy-fiel/feature.toml` (`schema = 1`, `order = 51`, `enabled = true`). Baixar e colocar soltos na raiz:
  - uma fonte OFL parecida com a do console;
  - as fotos de referência só como URL no LEIA-ME, sem versionar.

  Registrar URL, licença e sha256 no `LEIA-ME.txt`. Verificar o sha256 de cada fonte contra um novo download.
- [x] 2.2 Escrever o `gerar.sh` (ImageMagick 7) que compõe `gb-dmg.png` e `gbc-atomic-purple.png` em 640x480 RGBA com a geometria da decisão 3, e os `.cfg` de overlay (`overlays = 1`, `overlay0_full_screen = true`, `overlay0_descs = 0`), em `system/usr/share/retroarch-overlays/r36-gameboy/`. Verificar que as duas execuções seguidas geram os mesmos sha256.
- [x] 2.3 Gerar uma prévia das duas molduras com uma captura de jogo no recorte (em `work/`, fora do git) e mostrar ao usuário para aprovar as cores e os elementos (spec `gameboy-display`, molduras do DMG e do GBC). Ajustar as cores até a aprovação, sem mudar a geometria. Verificar com a aprovação explícita do usuário.
- [x] 2.4 Escrever o `tests/test_gameboy.py`:
  - sha256 contra o LEIA-ME;
  - 640x480 RGBA;
  - alfa 0 em todo o retângulo do jogo (x=53 a 586, y=0 a 479) e alfa 255 nas faixas laterais (x=0 a 52 e x=587 a 639);
  - nas duas molduras, a faixa direita lisa, só com a cor de fundo (sem texto);
  - `.cfg` de overlay apontando para o PNG certo.

  Verificar com `uv run python -I -m unittest tests.test_gameboy`.

## 3. Configuração do RetroArch para GB e GBC

- [x] 3.1 Confirmar na base o nome do core (`corename` em `gambatte_libretro.info`) e o índice de `aspect_ratio_index` para "Custom" no RetroArch 1.17. Registrar no LEIA-ME. Verificar contra o `.info` e o código-fonte do RetroArch na tag `v1.17.0`.
- [x] 3.2 Criar os overrides `storage/.config/retroarch/config/<core>/gb.cfg` e `gbc.cfg` com:
  - viewport custom de 534x480 em x=53, y=0;
  - `video_scale_integer = "false"` e `video_smooth = "false"`;
  - overlay ligado com opacidade 1.0, apontando para `/tmp/overlays/r36-gameboy/<moldura>.cfg`.

  Estender o `tests/test_gameboy.py` para conferir que os `custom_viewport_*` batem com o recorte medido no PNG. Verificar com o teste.
- [x] 3.3 Criar `gb.opt` e `gbc.opt` com as opções do gambatte da decisão 4 (GB com `gambatte_gb_colorization = "disabled"` para o `gameboy.glslp`; GBC com `gambatte_gbc_color_correction = "GBC only"`), e os presets `storage/shaders/presets/<core>/gb.glslp` e `gbc.glslp` com caminhos absolutos em `/usr/share/common-shaders/`. Estender o teste para conferir que cada `.glsl` e cada textura citados no preset existem no squashfs da base. Verificar com o teste.
- [x] 3.4 Documentar a feature no README: o que muda em GB e GBC, que exige `--wipe-storage`, como desligar a moldura pelo menu do RetroArch e como regerar as artes. Documentar também a origem e a licença da fonte no `LEIA-ME.txt`. Verificar que os caminhos e comandos citados existem.

## 4. Integração e validação no aparelho

- [x] 4.1 Rodar `./build.sh` com todas as features e verificar:
  - nenhum conflito de caminho entre features;
  - o `changes.txt` lista os arquivos novos de 30 e 51;
  - `e2fsck -fn` na p8 passa;
  - a suíte completa passa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`).
- [x] 4.2 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage` e verificar que termina com "verificado".
- [x] 4.3 No aparelho, com o cartão gravado pelo usuário com `--wipe-storage`:
  - ligar e verificar que só o ícone aparece até o menu (sem God of War e sem texto de collections);
  - abrir e fechar um jogo de NES e verificar que só aparece o ícone no intervalo.

  Se o texto do ES aparecer, aplicar a próxima saída da decisão 7 e repetir.
- [x] 4.4 No aparelho, abrir um jogo de GB e um de GBC com o FPS do RetroArch ligado e verificar:
  - jogo na altura toda da tela, sem cortes, com as laterais preenchidas pela moldura (DMG: BATTERY à esquerda e direita lisa; GBC: POWER à esquerda e direita lisa);
  - verdes do DMG e grade visível;
  - 60 fps (59,7 no GB).

  Se o GB ficar abaixo, trocar para a alternativa da decisão 4 (paleta `GB - DMG` no core e grade de 1 passada), atualizar o teste e repetir. Abrir também um jogo de NES e verificar que ele continua sem moldura e sem shader.

## Workflow follow-up

- Commit na branch `feat/gameboy-fiel-e-tela-icone` quando o usuário pedir. Merge e arquivamento com `/opsx:archive` depois da validação no aparelho.
