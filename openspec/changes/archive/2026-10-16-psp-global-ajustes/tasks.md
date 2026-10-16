# Tasks

## 1. Feature 52-psp-desempenho

- [x] 1.1 Criar a branch `feat/psp-global-ajustes` a partir da `main`. Verificar com `git branch --show-current`.
- [x] 1.2 Trocar as 4 chaves da decisão 2 (`TextureFiltering = 2`, `ReplaceTextures = False`, `AchievementsEnable = False`, `EnableCheats = False`) nas duas cópias do `ppsspp.ini` da feature 52 (`system/usr/config/ppsspp/PSP/SYSTEM/` e `storage/.config/ppsspp/PSP/SYSTEM/`), preservando as outras linhas, a ordem e os finais de linha. Verificar com `cmp` que as duas cópias são idênticas e com `diff` contra a base que só as 10 linhas mudam.
- [x] 1.3 Atualizar o comentário e a `description` do `features/52-psp-desempenho/feature.toml` para citar a textura nearest e os extras desligados. Verificar com `./build.sh --features 52-psp-desempenho` que o carregador aceita o descritor.
- [x] 1.4 Somar as 4 chaves, com os valores de fábrica e os novos, ao `NOVOS` de `tests/test_psp.py` e trocar "seis" por "dez" no nome do teste contra a base. Verificar com `uv run python -I -m unittest tests.test_psp`, incluindo a classe `PspContraBase`.
- [x] 1.5 Atualizar a seção `52-psp-desempenho` do README: as 4 chaves novas na lista, "Seis chaves" vira "Dez chaves", e como religar os cheats e a filtragem linear pelo menu do PPSSPP. Verificar que a lista do README bate com o `NOVOS` do teste.

## 2. Integração

- [x] 2.1 Rodar `./build.sh` com todas as features e verificar:
  - nenhum conflito de caminho;
  - o `changes.txt` mostra os dois `ppsspp.ini` como substituídos pela feature 52;
  - a suíte completa passa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`).
- [x] 2.2 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage` e verificar que termina com "verificado".

## Workflow follow-up

- O usuário grava o cartão com `--wipe-storage`, abre um jogo de PSP sem ini próprio e confere no menu do PPSSPP: filtragem de textura nearest e cheats desligados.
- O usuário testa o GTA Liberty City Stories (`ULUS10041`) para a próxima change, que vai criar o ini por jogo com `SkipBufferEffects` e mais pulo de quadros.
- Commit na branch `feat/psp-global-ajustes` quando o usuário pedir. Arquivar com `/opsx:archive`.
