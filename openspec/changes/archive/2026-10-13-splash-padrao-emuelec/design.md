# Design

## Context

- **Boot:** o `show-version.service` (em `basic.target`) roda `/usr/bin/lsb_release`. O fabricante transformou esse script num player: ele faz `ffplay -f rawvideo -video_size 640x480 -pixel_format rgb24 /usr/config/splash/splash-1080.raw`. O `.raw` tem 921600 bytes (640 × 480 × 3) e mostra a arte do God of War.
- **Jogo:** o `emuelec-utils` chama `show_splash.sh gameloading`. Quando não há tela em `/storage/roms/splash/...`, o script usa `/storage/.config/splash/loading-game-std.png`. A resolução do aparelho contém "x", então ele escolhe as variantes `-std`. Nos modos `intro` e `exit`, ele usa `splash-std.png`. O `mpv` roda com `-fs`.
- Em `/usr/config/splash` e em `/storage/.config/splash` há cinco PNGs de 103443 bytes com o mesmo conteúdo (a arte): `splash-std.png`, `splash-1080.png`, `loading-game-std.png`, `loading-game.png` e `retroarch.png`.
- **Fontes escolhidas pelo usuário** (prévias aprovadas em `work/splash-final/`):
  - boot: `distributions/EmuELEC/splash/Amlogic-ng/splash-1080.png` do repositório EmuELEC, commit `c5e7cbac2a9e661d9a19e8d56f69bf8f846cbaaf` (1920x1080, logo + "EMUELEC", sem "LOADING");
  - jogo: ícone `gamepad-2` do `lucide-static@0.460.0` (licença ISC), opção 3 dos exemplos.
- O mecanismo de features substitui arquivos inteiros e herda dono e modo do original. Arquivos soltos na raiz da feature são ignorados pelo carregador.

## Goals / Non-Goals

**Goals:**
- Telas nativas em 640x480: o `mpv` e o `ffplay` não reescalam, e não há barras.
- Geração reproduzível e origem auditável, sem dependência nova no build.

**Non-Goals:**
- Trocar o `bootlogo.bmp` da p2, as telas de bateria ou o vídeo de introdução.
- Remover ou consertar o `lsb_release` modificado: ele continua tocando o `.raw` no boot.
- Animar a tela de carregamento.

## Decisions

1. **Mapeamento de arquivos (iguais nas duas camadas):**

   | Arquivo da base | Conteúdo novo |
   |---|---|
   | `splash-std.png` | boot (`boot-640x480`) |
   | `splash-1080.png` | boot |
   | `retroarch.png` | boot (não é usado nos scripts, mas era cópia da arte) |
   | `splash-1080.raw` | boot em RGB24 cru |
   | `loading-game-std.png` | jogo (`jogo-640x480`) |
   | `loading-game.png` | jogo |

2. **Boot: recorte central 4:3 e redução, sem barras.** O original 16:9 (1920x1080) é recortado no centro para 1440x1080 e reduzido para 640x480. O logo e a palavra EMUELEC cabem inteiros no recorte; perdem-se só as laterais do fundo de raios. Alternativa descartada: reduzir inteiro com barras pretas em cima e embaixo (letterbox). O logo ficaria menor e a tela não seria cheia.

3. **Jogo: ícone em traço sobre gradiente escuro.** O SVG do Lucide é colorido em `#d8dce6`, rasterizado a 190x190 e centralizado num gradiente radial de `#2b2f36` para `#0b0c0f`, em 640x480.

4. **PNG RGB de 8 bits, sem alfa e sem metadados (`-strip`).** É o formato mais simples para o `mpv` do aparelho e torna o sha256 estável. O `.raw` é gerado do PNG de boot final (`rgb:` do ImageMagick), então os pixels são idênticos.

5. **Imagens geradas uma vez e versionadas, com script na feature.** O build continua só com a biblioteca padrão do Python. A raiz da feature leva:
   - `fonte-splash-distribuicao-1080.png` (o PNG oficial, conferido por sha256) e `fonte-gamepad-2.svg` (do `lucide-static@0.460.0`), como arquivos soltos: o carregador rejeita subdiretórios que não sejam camadas, então não há `fontes/`;
   - `gerar.sh`, que produz as 12 imagens das duas camadas a partir das fontes;
   - `LEIA-ME.txt`, com URLs, commit e versão, o aviso de licença ISC do Lucide, a licença GPL do EmuELEC para o PNG e os sha256 das fontes e dos arquivos gerados.

   Um teste rápido confere os sha256 contra o `LEIA-ME.txt` e lê o cabeçalho IHDR dos PNGs (largura, altura, profundidade e tipo de cor), sem depender do ImageMagick.
   - Alternativa descartada: gerar no build, o que adicionaria ImageMagick ou Pillow como dependência.

6. **Feature única `30-splash-padrao-emuelec` com as camadas `system` e `storage`.** A cópia em `/usr/config/splash` é a que o boot lê e a que o EmuELEC usa para recriar o STORAGE (reset de fábrica). A cópia em `/storage/.config/splash` é a que o `show_splash.sh` lê.

## Risks / Trade-offs

- [O usuário grava com `--keep-storage` e continua vendo a arte ao abrir jogos] → O README avisa: o boot muda com qualquer gravação do SYSTEM, mas a tela de jogo só muda com `--wipe-storage`. Alternativa: copiar os dois `loading-game*.png` para `/storage/.config/splash` pelo PC (ext4).
- [O `ffplay` do boot espera exatamente 921600 bytes] → O teste confere o tamanho e a correspondência com o PNG.
- [A versão do ImageMagick muda os bytes gerados] → Os sha256 registrados são os dos arquivos versionados. O `gerar.sh` só é usado para mudar as telas, e quem regerar atualiza o `LEIA-ME.txt`. A conferência da regeneração (requisito de reprodutibilidade) usa a versão registrada no `LEIA-ME.txt`.
- [Outro script do fabricante usa algum desses arquivos com outro formato] → Os únicos usos encontrados no SYSTEM são o `show_splash.sh`, o `lsb_release` e o `emustation-config`. A validação no aparelho cobre o boot, a abertura de um jogo e a saída de um jogo.

## Migration Plan

1. Build e conferência do `changes.txt`: 6 caminhos substituídos em `system` e 6 em `storage`.
2. Gravação com `--wipe-storage` (ou só `--part system` para ver a tela de boot).
3. Rollback: `enabled = false` na feature e novo build, ou gravar o build anterior.
