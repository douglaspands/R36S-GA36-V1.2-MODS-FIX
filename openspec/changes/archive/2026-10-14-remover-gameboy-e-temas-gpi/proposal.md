# Proposal

## Why

No aparelho, a feature `51-gameboy-fiel` não ficou como esperado: a moldura e o shader do RetroArch deixam os jogos de GB e GBC lentos. Os três temas GPi (Mario, Sonic e Crash) da `50-temas-extras` também não agradaram. O resto da imagem está funcionando bem, então a mudança só remove essas peças e enxuga o registro do build.

## What Changes

- **BREAKING:** remove a feature `51-gameboy-fiel` inteira: molduras, overrides do Gambatte, presets de shader, script de geração, fonte e `tests/test_gameboy.py`. GB e GBC voltam à apresentação de fábrica, porque todos os arquivos da feature eram adicionados (nenhum substituía um da base).
- **BREAKING:** a `50-temas-extras` deixa de trazer **Mario (GPi)**, **Sonic (GPi)** e **Crash (GPi)**. Ficam Minimal EmuELEC, Switch, Graphite OGA e Crystal (cerca de 348 MiB, contra 381 MiB hoje). A descrição da feature e o README passam a listar só esses quatro.
- O `R36-BUILD.txt` (p7) perde a linha `timestamp:`. O timestamp continua no arquivo, no fim do nome da imagem (`imagem: ..._build_<timestamp>.img.xz`), que é a versão do build. O `manifest.json` não muda.
- **No cartão:** as duas remoções mexem na p8, então só valem com `--wipe-storage`. Com `--keep-storage`, os overrides do GB e os temas GPi continuam no cartão. Nesse caso, o README explica quais diretórios apagar pelo PC.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities
- `gameboy-display`: todos os requisitos saem. A capability deixa de existir, e GB e GBC ficam como na base.
- `es-themes`: sai o requisito "Temas com personagens de jogos infantis". Os outros continuam: temas no menu, legíveis em 640x480, NES-BOX padrão e limite de 400 MiB.
- `image-build`: o cenário "Nome da imagem" passa a dizer que o `R36-BUILD.txt` registra a versão pelo nome da imagem, sem uma linha própria de timestamp.

## Impact

- Remove o diretório `features/51-gameboy-fiel/` e o arquivo `tests/test_gameboy.py`.
- `features/50-temas-extras/feature.toml`: saem três `[[external]]`; mudam a `description` e o comentário do topo.
- `tools/r36img/build.py` (`build_info_text`) e `tests/test_image.py` (asserção sobre o `R36-BUILD.txt`).
- README: seções `50-temas-extras`, `51-gameboy-fiel` (sai) e "Onde ver qual build está no cartão".
- O código de conteúdo externo (`external.py`) continua, porque a feature 50 ainda o usa.
- Os tarballs dos temas GPi podem continuar em `work/cache/external/`. O build ignora arquivos que nenhum `[[external]]` cita.
