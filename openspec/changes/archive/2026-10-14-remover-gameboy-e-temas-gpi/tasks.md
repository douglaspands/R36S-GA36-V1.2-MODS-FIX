# Tasks

## 1. Remover a feature 51-gameboy-fiel

- [x] 1.1 Na branch `feat/remover-gameboy-e-temas-gpi`, apagar `features/51-gameboy-fiel/` e `tests/test_gameboy.py`. Verificar com `grep -rn "51-gameboy\|r36-gameboy\|Gambatte" tools tests features` que nada mais cita a feature.
- [x] 1.2 No README, tirar a seção `51-gameboy-fiel`. Na parte de `--keep-storage`, listar o que apagar pelo PC na `R36-STORAGE` (`.config/retroarch/config/Gambatte/gb.cfg`, `gb.opt`, `gbc.cfg`, `gbc.opt` e `shaders/presets/Gambatte/gb.glslp`, `gbc.glslp`). Verificar com `grep -n "gameboy-fiel\|Barlow\|BATTERY" README.md` que não sobra nenhuma referência à feature.

## 2. Tirar os temas GPi da feature 50-temas-extras

- [x] 2.1 Em `features/50-temas-extras/feature.toml`, apagar os três `[[external]]` de Mario, Sonic e Crash (GPi). Atualizar a `description` para os quatro temas que ficam e, no comentário do topo, tirar a nota sobre PokemonUno, KirbyUno e YoshiUno. Verificar com `grep -c "^\[\[external\]\]"` que restam 4 e com `grep -n "GPi"` que não sobra nenhuma referência.
- [x] 2.2 No README, atualizar a seção `50-temas-extras`: quatro temas, cerca de 348 MiB, sem o parágrafo dos temas 16:9. Explicar que, com `--keep-storage`, é preciso trocar de tema se um GPi estiver ativo e depois apagar os três diretórios `* (GPi)` de `.config/emulationstation/themes/`. Verificar com `grep -n "GPi" README.md` que só sobra essa instrução de limpeza.

## 3. R36-BUILD.txt sem a linha de timestamp

- [x] 3.1 Em `build_info_text` (`tools/r36img/build.py`), tirar a linha `timestamp:`. O cabeçalho, `imagem:`, `tamanho_cartao_mib:` e `features:` continuam, e o `manifest.json` mantém a chave `timestamp`. Verificar que o texto gerado começa com o cabeçalho seguido de `imagem: ..._build_<ts>.img.xz`.
- [x] 3.2 Em `tests/test_image.py`, trocar a asserção `timestamp: {ts}` por uma sobre `imagem: r36s_ga36-mb_v1.2-20260416_build_{ts}.img.xz` e acrescentar `assertNotIn("timestamp:", txt)`. Verificar com `R36_SLOW=1 uv run python -I -m unittest tests.test_image`.
- [x] 3.3 No README ("Onde ver qual build está no cartão"), dizer que a versão é o timestamp no fim do nome da imagem, registrado na linha `imagem:`. Verificar que o texto confere com a saída do 3.1.

## 4. Integração

- [x] 4.1 Rodar `./build.sh` com todas as features e verificar:
  - o relatório de conteúdo externo lista só os quatro temas, abaixo de 400 MiB;
  - o `changes.txt` não tem nenhuma linha com `feature=51-gameboy-fiel`;
  - o `R36-BUILD.txt` da p7 (`mtype -i out/<ts>/parts/system.img ::R36-BUILD.txt`) não tem `timestamp:` e lista oito features;
  - a suíte completa passa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`).
- [x] 4.2 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage` e verificar que termina com "verificado".
- [x] 4.3 Rodar `openspec validate remover-gameboy-e-temas-gpi --strict` e verificar que passa.

## Workflow follow-up

- O usuário grava o cartão com `--wipe-storage` e confere no aparelho:
  - GB e GBC sem moldura e na velocidade de fábrica;
  - a lista de temas com NES-BOX, Minimal EmuELEC, Switch, Graphite OGA e Crystal;
  - o `R36-BUILD.txt` na R36-SYSTEM.
- Commit na branch `feat/remover-gameboy-e-temas-gpi` quando o usuário pedir. Arquivar com `/opsx:archive`, o que também retira a spec `gameboy-display`.
