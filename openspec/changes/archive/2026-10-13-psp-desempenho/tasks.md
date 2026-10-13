# Tasks

## 1. Feature 52-psp-desempenho

- [x] 1.1 Criar a branch `feat/psp-desempenho` a partir da `main` e o `features/52-psp-desempenho/feature.toml` (`schema = 1`, nome, descrição, `order = 52`, `enabled = true`). Verificar com `./build.sh --features 52-psp-desempenho` que o carregador aceita o descritor.
- [x] 1.2 Extrair o `ppsspp.ini` global da base e gravar cópias com as 6 chaves da decisão 2 trocadas, preservando todas as outras linhas, a ordem e os finais de linha, em `system/usr/config/ppsspp/PSP/SYSTEM/ppsspp.ini` e `storage/.config/ppsspp/PSP/SYSTEM/ppsspp.ini`. Verificar com `diff` contra a base que só 6 linhas mudam e que as duas cópias são idênticas.
- [x] 1.3 Escrever o teste (`tests/test_psp.py`): as únicas diferenças contra o ini da base são as 6 chaves, com os valores novos, e as duas camadas são iguais. Verificar com `uv run python -I -m unittest tests.test_psp`.
- [x] 1.4 Documentar a feature no README ("Features habilitadas"): as chaves alteradas, que exige `--wipe-storage`, como religar o contador de FPS pelo menu do PPSSPP e que os inis por jogo de fábrica continuam valendo. Verificar que os caminhos citados existem.

## 2. Integração

- [x] 2.1 Rodar `./build.sh` com todas as features e verificar:
  - nenhum conflito de caminho;
  - o `changes.txt` mostra os dois `ppsspp.ini` como substituídos pela feature 52;
  - os `*_ppsspp.ini` gerados são idênticos aos da base, comparando pelo `debugfs` e pelo `unsquashfs`;
  - a suíte completa passa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`).
- [x] 2.2 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage` e verificar que termina com "verificado".

## Workflow follow-up

- O usuário grava o cartão com `--wipe-storage`, abre um jogo de PSP sem ini próprio e confere no menu de gráficos do PPSSPP: resolução 1x, sem contador de FPS e pular quadros automático ligado. Também avalia a fluidez em GTA e PES.
- Uma change futura cria inis por jogo para GTA e PES quando as versões forem conhecidas.
- Commit na branch `feat/psp-desempenho` quando o usuário pedir. Arquivar com `/opsx:archive`.
