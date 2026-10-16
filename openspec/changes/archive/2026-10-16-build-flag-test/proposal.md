# Proposal

## Why

Hoje todo build em `out/` tem só um timestamp, e nada distingue uma imagem intermediária, gerada para testar uma ideia (por exemplo, ajustes de governor), de uma imagem que o usuário considera boa. Quem olha a pasta `out/` ou o cartão não sabe qual é qual. Uma flag no build que marque a imagem como de teste resolve isso, e só isso.

## What Changes

- `./build.sh --test` gera um build marcado como de teste. O diretório passa a ser `out/<timestamp>-test/` e a imagem completa passa a ser `<prefixo>_build_<timestamp>-test.img.xz`. O sufixo é em inglês (`-test`).
- O campo `timestamp` do manifest continua com o timestamp puro. O manifest ganha `"test": true` em builds de teste. Em builds normais o campo `test` não existe, para não mudar o manifest existente.
- O `R36-BUILD.txt` de um build de teste ganha a linha `teste: sim`, para o marcador aparecer também no cartão (`/flash/R36-BUILD.txt`). O de um build normal não muda.
- O `flash.sh` passa a reconhecer diretórios `<timestamp>-test`: eles aparecem no menu e no `--list-builds`, podem ser indicados em `--build <timestamp>-test` e entram na escolha do "mais recente" como qualquer outro. Não há tratamento especial nem proteção extra para builds de teste.
- A linha de cada build (menu, `--list-builds` e plano) mostra o marcador `test` quando o manifest indica build de teste.
- Sem `--test`, nada muda no build normal: mesmo nome, mesmo manifest, mesmo `R36-BUILD.txt`.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `image-build`: o requisito "Artefatos de saída versionados" ganha o sufixo opcional `-test` no nome do diretório e da imagem, o campo `test` no manifest e a linha no `R36-BUILD.txt`.
- `sd-flashing`: os requisitos "Modos de gravação" e "Informações de cada build" passam a aceitar o identificador com o sufixo `-test` em `--build` e a mostrar o marcador na linha do build.

## Impact

- `tools/r36img/build.py`: nova opção `--test`, nomes de saída, `build_info_text` e manifest.
- `tools/r36img/flash.py`: `TS_RE` (hoje só `^\d{8}-\d{6}$`, o que faria o `flash.sh` ignorar as pastas com sufixo), `available_builds`, `build_line` e a validação de `--build`.
- Testes: `tests/test_image.py` (regex do nome), `tests/test_flash.py` e um teste novo para o build de teste.
- `README.md`: documentar `--test`.
- Fora de escopo: ajustes de governor, melhorias do registro térmico e o core padrão do CPS2. Cada um será uma change própria.
