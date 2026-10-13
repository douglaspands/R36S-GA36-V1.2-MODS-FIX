# Tasks

## 1. Feature 10-ptbr-sao-paulo (idioma, fuso e menu)

- [x] 1.1 Criar `features/10-ptbr-sao-paulo/feature.toml`: `schema = 1`, nome, descrição, `order = 10`, `enabled = true`. Verificar que `./build.sh --help` e o carregamento de features não acusam erro.
- [x] 1.2 Extrair da p8 da imagem base (com `debugfs`, somente leitura) o `emuelec.conf`, o `es_settings.cfg` e o `retroarch.cfg` originais para `features/10-ptbr-sao-paulo/storage/` (mesmos caminhos relativos). Verificar com `diff` que as cópias são idênticas às da base antes de editar.
- [x] 1.3 Editar o `emuelec.conf`: `system.language=pt_BR`, `system.timezone=America/Sao_Paulo` e `global.retroarch.menu_driver=rgui` (no lugar da linha comentada). Verificar que o `diff` contra a base mostra só essas 3 linhas.
- [x] 1.4 Editar o `es_settings.cfg` (`Language` = `pt_BR`) e o `retroarch.cfg` (`user_language = "7"`, `menu_driver = "rgui"`). Verificar que o `diff` contra a base mostra só essas linhas.
- [x] 1.5 Adicionar em `tests/` um teste rápido que lê os arquivos da feature e confere os valores de idioma, fuso e menu. Verificar com `uv run python -I -m unittest discover -s tests`.

## 2. Feature 20-controle-posicional (RetroArch)

- [x] 2.1 Criar `features/20-controle-posicional/feature.toml`: `schema = 1`, nome, descrição, `order = 20`, `enabled = true`.
- [x] 2.2 Criar `features/20-controle-posicional/storage/joypads/micro_gamepad.cfg` a partir do arquivo de fábrica, conforme o design (decisão 4):
  - cabeçalho `sdl2` com `vendor_id` `26989` e `product_id` `24431`;
  - A = 0, B = 1, X = 2, Y = 3;
  - hotkey 8, pausa 1, FPS 0 e os demais atalhos de fábrica;
  - sem atalhos de volume, slot, reset nem rewind.

  Verificar com `diff` contra o original de fábrica que só mudam o cabeçalho, `a_btn`/`b_btn` e `pause`/`fps`.
- [x] 2.3 Adicionar em `tests/` um teste rápido que faz o parse do `micro_gamepad.cfg` da feature e confere três coisas:
  - os botões de face valem A = 0, B = 1, X = 2, Y = 3;
  - `input_enable_hotkey_btn = 8`;
  - nenhuma chave diferente de `input_up/down/left/right_btn` usa os botões 13 a 16.

  Verificar com `uv run python -I -m unittest discover -s tests`.

## 3. Documentação

- [x] 3.1 Adicionar ao README uma seção curta com as features habilitadas (idioma e fuso, menu RGUI, controle posicional e tabela de atalhos com Select), avisando que exigem `--wipe-storage`. Verificar que os comandos citados existem no `--help` dos scripts.

## 4. Integração (build e inspeção pelo PC)

- [x] 4.1 Rodar `./build.sh` e verificar que o `changes.txt` lista exatamente os 4 caminhos substituídos na camada `storage`, com as features 10 e 20, e que o `R36-BUILD.txt` cita as duas features.
- [x] 4.2 Extrair a p8 do build (com `debugfs`, somente leitura) e verificar com `diff` contra a p8 da base que só mudaram as chaves deste change e que `.config/retroarch/config/remappings/` está idêntico.
- [x] 4.3 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage` (sem sudo) e verificar que a gravação termina com "verificado".
- [x] 4.4 Rodar a suíte completa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`) e verificar que ela passa.

## Workflow follow-up

- O usuário grava o cartão num terminal próprio, com `./flash.sh --device /dev/sdX --all --keep-roms --wipe-storage` (apaga saves e configurações, como autorizado).
- Validar no aparelho:
  - menus do ES e do RetroArch em pt-BR;
  - hora de São Paulo;
  - menu RGUI em dois jogos seguidos de sistemas diferentes;
  - baixo = B, direita = A, cima = X, esquerda = Y;
  - direcional para baixo sem mexer no volume;
  - Select + X/R/L/Start funcionando.
- Fazer commit na branch `feature/ptbr-sao-paulo-controle` e arquivar o change com `/opsx:archive`.
