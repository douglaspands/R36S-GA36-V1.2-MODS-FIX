# Proposal

## Why

O aparelho é para uma criança de 7 anos, e ler os menus na própria língua facilita muito. O idioma do EmuELEC (menu do ES e sistema) é uma escolha do usuário, mas o menu do RetroArch tem a sua, o `user_language` do `retroarch.cfg`, e as duas não se falam: quem troca o idioma no EmuELEC continua com o RetroArch no idioma antigo, e só se descobre dentro de um jogo. A change `es-shader-config-gpsp-ghost` põe o padrão de fábrica em português do Brasil (`user_language = "7"`), mas isso só vale para uma p8 nova e não acompanha uma troca posterior.

## What Changes

- **Idioma do EmuELEC vale no RetroArch:** um script novo, chamado pelo `emuelecRunEmu.sh` antes de cada jogo (como o `shaderset-aplica`), lê o idioma do EmuELEC e grava o `user_language` correspondente no `retroarch.cfg`. A tabela traduz o código do EmuELEC (`pt_BR`, `en_US`, `es_ES`, `fr_FR`...) para o número do RetroArch (`7`, `0`, `3`, `2`...). Um idioma fora da tabela deixa o `user_language` como está.
- **Fonte do idioma:** `system.language` do `emuelec.conf` (p8). Se a troca pelo menu do ES gravar só no `es_settings.cfg`, o script lê esse arquivo; a verificação no aparelho decide (ver `design.md`).
- **Idioma padrão escolhido no build:** `./build.sh --idioma <código>` (padrão **`en_US`**, decisão do usuário) define o idioma de fábrica do EmuELEC (`system.language`), do ES (`Language`) e do RetroArch (`user_language`) de uma vez, para gerar uma imagem pronta para quem vai usar o aparelho. **BREAKING:** um `./build.sh` sem argumento passa a gerar imagem em inglês; para português é preciso `./build.sh --idioma pt_BR`. O idioma só muda o conteúdo dessas três chaves, nas cópias do build em `work/`; os arquivos das features no repositório não mudam (continuam em `pt_BR`).
- **Idioma no nome da imagem:** **BREAKING** o nome da imagem passa a ser `<prefixo>_<idioma>_build_<timestamp>[-test].img.xz`, com o código em minúsculas e hífen (`en-us` no padrão, `pt-br` com `--idioma pt_BR`). O diretório de saída continua `<timestamp>`, então o `flash.sh --build` não muda. O idioma também entra no manifest e no `R36-BUILD.txt`.
- **Fora de escopo:** idioma do sistema operacional, do ES e dos temas (já tratados pela feature 10); mudar o padrão de fábrica do `user_language` (vem da change `es-shader-config-gpsp-ghost`); idiomas que o RetroArch 1.17 não traduz; fonte do RGUI e acentos.

## Capabilities

### New Capabilities
- `retroarch-language`: o menu do RetroArch usa o idioma escolhido no EmuELEC, a cada jogo, sem o usuário abrir o menu do RetroArch.
- `build-language`: o idioma padrão da imagem é uma opção do build e vale igual no EmuELEC, no ES e no RetroArch.

### Modified Capabilities
- `image-build`: o nome da imagem, o manifest e o `R36-BUILD.txt` passam a registrar o idioma do build.

## Impact

- `features/10-ptbr-sao-paulo`: `system/usr/bin/emuelecRunEmu.sh` (uma chamada nova, como a do `shaderset-aplica`); seus arquivos de idioma continuam em `pt_BR` no repositório, e o build reescreve as três chaves nas cópias em `work/` com o idioma de `--idioma` (`en_US` por padrão).
- `tools/r36img/build.py` (e o ajuste dos arquivos de configuração no plano de cada build), `./build.sh --help`, o manifest e o `R36-BUILD.txt`; `tests/test_image.py` (a regex do nome da imagem).
- `features/56-retroarch-ajustes` (criada pela change `es-shader-config-gpsp-ghost`): script novo `idioma-aplica` em `system/usr/lib/r36/`. Esta change **depende** dela: precisa dela mesclada na `main` (ou rebaseada) antes do `/opsx:apply`.
- Testes novos em `tests/`, mais `README.md` e `CLAUDE.md` (na integração `integra-limite-idioma-shaders-gb`, a partir de `docs-retroarch-idioma-do-emuelec.md` desta pasta).
- Vale em qualquer cartão, inclusive com `--keep-storage`, porque o script roda no SYSTEM a cada jogo.
- Não verificável no PC: onde o ES grava a troca de idioma e a aparência do RGUI nos outros idiomas dependem do aparelho.
