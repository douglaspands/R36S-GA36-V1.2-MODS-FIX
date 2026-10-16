# Tasks

## 1. Build: opção `--test`

- [x] 1.1 Em `tools/r36img/build.py`, adicionar `--test` a `parse_args` (com texto de ajuda e um exemplo no epílogo) e o parâmetro `test` a `build()`. Verificar com `./build.sh --help`, que lista a opção.
- [x] 1.2 Em `build()`, derivar o identificador de saída (`ts` ou `ts-test`) e usá-lo no diretório `out/`, no nome da imagem `.img.xz` e no diretório de trabalho `work/`, mantendo `ts` puro no manifest e no `volume_id`. Verificar com um teste em `tests/test_image.py` que um build com `test=True` cria `<ts>-test/` com a imagem `..._build_<ts>-test.img.xz` e que um build normal não muda de nome.
- [x] 1.3 Em `build_info_text` e no manifest, acrescentar `teste: sim` e `"test": true` só em builds de teste. Verificar em `tests/test_image.py` que o build de teste tem o campo e a linha, que o normal não tem nenhum dos dois, e que o `timestamp` do manifest continua `AAAAMMDD-HHMMSS`.
- [x] 1.4 Atualizar a regex de nome em `tests/test_image.py` para aceitar o sufixo opcional e rodar `uv run pytest tests/test_image.py`, que deve passar.

## 2. Flash: reconhecer builds de teste

- [x] 2.1 Em `tools/r36img/flash.py`, mudar `TS_RE` para `^\d{8}-\d{6}(-test)?$`, ajustar a mensagem de erro de `--build` ao novo formato e atualizar a ajuda (`HELP`/`EPILOG`). Verificar em `tests/test_flash.py` que `--build <ts>-test` é aceito, que `--build <ts>-teste` é recusado com o formato esperado e que um build normal continua funcionando.
- [x] 2.2 Em `build_line`, acrescentar o marcador `test` quando o manifest tiver `"test": true`. Verificar em `tests/test_flash.py` que `--list-builds`, o menu e o plano mostram a linha do build de teste com o marcador e a de um build normal sem ele.
- [x] 2.3 Cobrir em `tests/test_flash.py` que um build `<ts>-test` entra na ordenação e na escolha do "mais recente" sem tratamento especial. Rodar `uv run pytest tests/test_flash.py`, que deve passar.

## 3. Documentação e integração

- [x] 3.1 Documentar `./build.sh --test` no `README.md` (seção de build e seção "Onde ver qual build está no cartão") e verificar que o exemplo documentado roda como escrito.
- [x] 3.2 Rodar a suíte completa com `uv run pytest` e conferir que nada regrediu.
- [x] 3.3 Gerar um build real com `./build.sh --test --no-features --fast` e verificar que `out/` mostra a pasta e a imagem com `-test`, que `./flash.sh --list-builds` mostra o marcador e que o `R36-BUILD.txt` do build tem `teste: sim`.
