# Proposal

## Why

A imagem de fábrica troca as telas do EmuELEC por uma arte do God of War com "R36S / Please Wait.....". Ela aparece em dois momentos: no boot, antes do EmulationStation, e ao abrir cada jogo. O usuário quer, no boot, a tela da distribuição EmuELEC e, ao abrir um jogo, um símbolo de controle sem texto.

## What Changes

- **Boot:** a tela de splash da distribuição EmuELEC (logo com o controle e a palavra EMUELEC) substitui a arte. A original tem 1920x1080 (16:9). Ela é recortada no centro para 4:3 e reduzida para 640x480, a resolução da tela do R36S. Vale para:
  - o `splash-1080.raw` que o boot toca;
  - `splash-std.png` e `splash-1080.png` (modos intro e exit do `show_splash.sh`);
  - `retroarch.png`, que não é usado pelos scripts, mas era cópia da arte.
- **Carregamento de jogo:** um ícone de controle cinza claro (Lucide `gamepad-2`) centralizado num fundo de gradiente escuro, sem texto, em 640x480. Substitui `loading-game-std.png` e `loading-game.png`.
- A troca é feita nos dois lugares onde as telas existem: `/usr/config/splash` (SYSTEM) e `/storage/.config/splash` (STORAGE).
- As imagens são geradas uma vez por um script versionado na feature e ficam no git (cerca de 1,3 MB no total). A origem (commit do EmuELEC e versão do Lucide) e os sha256 ficam registrados.
- Fora do escopo: o logo do U-Boot (`bootlogo.bmp` da p2, com a foto do R36S), as telas de bateria e o vídeo de introdução (`emuelec_intro_1080p.mp4`, idêntico ao oficial e desligado).
- Nova feature `30-splash-padrao-emuelec`, nas camadas `system` e `storage`.
- **No cartão:** a tela de boot muda com qualquer gravação do SYSTEM. A tela de carregamento de jogo, que o `show_splash.sh` lê do STORAGE, só muda com `--wipe-storage`.

## Capabilities

### New Capabilities
- `splash-screens`: quais imagens o aparelho mostra no boot e ao abrir um jogo, e de onde elas vêm.

### Modified Capabilities
(nenhuma)

## Impact

- Novo diretório `features/30-splash-padrao-emuelec/`, com:
  - as imagens nas camadas `system/` e `storage/`;
  - na raiz, fora das camadas, `gerar.sh` (gera as imagens), `LEIA-ME.txt` (origem, licenças e sha256) e as fontes (o PNG oficial e o SVG do ícone).
- Arquivos substituídos: 6 no SYSTEM (`usr/config/splash/`) e 6 no STORAGE (`.config/splash/`). Nenhum arquivo novo ou removido nas camadas.
- Nenhuma mudança em `tools/r36img/`. O ImageMagick só é preciso para regerar as imagens, não para o build.
