# Tasks

## 1. Fontes, geração e arquivos da feature

- [x] 1.1 Criar `features/30-splash-padrao-emuelec/feature.toml` (`schema = 1`, nome, descrição, `order = 30`, `enabled = true`). Verificar que `./build.sh --features 30-splash-padrao-emuelec` carrega a feature sem erro de descritor.
- [x] 1.2 Colocar na raiz de `features/30-splash-padrao-emuelec/` (arquivos soltos; o carregador rejeita subdiretórios que não sejam camadas) o `splash-1080.png` da distribuição (EmuELEC, `distributions/EmuELEC/splash/Amlogic-ng/`, commit `c5e7cbac2a9e661d9a19e8d56f69bf8f846cbaaf`) como `fonte-splash-distribuicao-1080.png` e o `gamepad-2.svg` do `lucide-static@0.460.0` como `fonte-gamepad-2.svg`. Verificar o sha256 de cada fonte contra o download direto das URLs fixadas.
- [x] 1.3 Escrever `features/30-splash-padrao-emuelec/gerar.sh`, seguindo as decisões 2 a 4 do design:
  - boot: recorte central 1440x1080, 640x480, PNG24 sem alfa e `-strip`;
  - `.raw` RGB24 gerado do PNG de boot;
  - jogo: ícone `#d8dce6` 190x190 sobre gradiente `#2b2f36`→`#0b0c0f`, PNG24;
  - as 6 cópias em `system/usr/config/splash/` e `storage/.config/splash/`, conforme o mapeamento da decisão 1.

  Verificar que os PNGs gerados são visualmente iguais às prévias aprovadas em `work/splash-final/` (`magick compare -metric AE` igual a 0) e que as duas camadas são idênticas (`diff -r`).
- [x] 1.4 Escrever `features/30-splash-padrao-emuelec/LEIA-ME.txt` com as URLs, o commit, a versão do Lucide e a do ImageMagick usada, o aviso da licença ISC do Lucide, a nota de licença GPL do EmuELEC e os sha256 das fontes e dos arquivos gerados. Verificar que o build não copia nada da raiz da feature para as camadas (`changes.txt`).
- [x] 1.5 Adicionar em `tests/` um teste rápido que confere:
  - os sha256 da feature contra o `LEIA-ME.txt`;
  - o IHDR de cada PNG (640x480, 8 bits, RGB, lido com a biblioteca padrão);
  - o `.raw` com 921600 bytes;
  - a ausência do sha256 da arte de fábrica em qualquer arquivo da feature.

  Verificar com `uv run python -I -m unittest discover -s tests`.

## 2. Documentação

- [x] 2.1 Adicionar a feature à seção "Features habilitadas" do README: tela da distribuição EmuELEC no boot, ícone de controle ao abrir jogos, que o boot muda com qualquer gravação do SYSTEM e a tela de jogo só com `--wipe-storage`, e como regerar com `gerar.sh`. Verificar que os comandos citados existem.

## 3. Integração (build e inspeção pelo PC)

- [x] 3.1 Rodar `./build.sh` e verificar que o `changes.txt` lista exatamente 6 substituições em `system` (`usr/config/splash/`) e 6 em `storage` (`.config/splash/`) para a feature 30, e nenhuma adição ou remoção.
- [x] 3.2 Extrair do build, somente leitura (`unsquashfs` e `debugfs`), os dois diretórios de telas e verificar:
  - nenhum arquivo tem o sha256 da arte de fábrica;
  - `blank.png`, `emuelec_intro_1080p.mp4`, `twitch-1080.png` e `youtube-1080.png` continuam iguais aos da base;
  - o `bootlogo.bmp` da p2 não mudou.
- [x] 3.3 Rodar a suíte completa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`) e verificar que ela passa.

## Workflow follow-up

- O usuário grava o cartão com `--wipe-storage` e valida no aparelho:
  - logo da distribuição EmuELEC em tela cheia no boot;
  - ícone de controle ao abrir um jogo;
  - nenhuma arte do God of War na saída do jogo.
- Commit na branch `feat/splash-padrao-emuelec` quando o usuário pedir. Arquivar com `/opsx:archive`.
