# Tasks

## 1. Ajuste do Parser e CLI do Build

- [x] 1.1 Modificar `_build_parser` e `parse_args` em `tools/r36img/build.py` para definir `--lang` como argumento primário e `--idioma` como alias retrocompatível (`help=argparse.SUPPRESS`), atualizando mensagens de ajuda e validação de erro; verificar executando `tools/r36img/build.py --help`
- [x] 1.2 Atualizar a função `build` em `tools/r36img/build.py` para aceitar `lang=None` e `lang_opcional=False`, mantendo compatibilidade com keyword `idioma`
- [x] 1.3 Atualizar `tests/test_cli.py` para validar `--lang`, `--lang pt_BR`, erros com `--lang` e compatibilidade com `--idioma`; verificar com `uv run python -I -m unittest tests/test_cli.py`

## 2. Testes de Integração e Geração de Imagem

- [x] 2.1 Atualizar `tests/test_idioma_build.py` e `tests/test_image.py` para utilizar `lang` e validar que as imagens geradas continuam com nomenclatura e manifests corretos; verificar com `uv run python -I -m unittest tests/test_idioma_build.py tests/test_image.py`
- [x] 2.2 Rodar a suíte completa de testes do repositório para garantir ausência de regressões; verificar com `uv run python -I -m unittest discover -s tests`

## 3. Ilustração LÖVE e Documentação Multilíngue

- [x] 3.1 Gerar captura de tela `docs/img/tema-love.png` representando o console LÖVE no tema Epic Cody ML (via `tools/gera_prints_interface.py`) e verificar existência do arquivo
- [x] 3.2 Redigir nos três READMEs (`README.md`, `README.pt-BR.md`, `README.es.md`) a subseção de motivação do LÖVE (amor pela ideia do PICO-8 e jogos indie, mas com foco na portabilidade universal em todas as variantes do R36S, código aberto, 640x480 nativo e LuaJIT), acompanhada da imagem `docs/img/tema-love.png`
- [x] 3.3 Criar `docs/DEVELOPMENT.md` em inglês completo, com `--lang` em todas as instruções e links para os outros idiomas
- [x] 3.4 Criar `docs/DESARROLLO.md` em espanhol completo, com `--lang` em todas as instruções e links para os outros idiomas
- [x] 3.5 Atualizar `docs/DESENVOLVIMENTO.md` em português, com `--lang` e links para os outros idiomas
- [x] 3.6 Atualizar os links de referência aos manuais técnicos em cada README (`README.md` -> `docs/DEVELOPMENT.md`, `README.es.md` -> `docs/DESARROLLO.md`, `README.pt-BR.md` -> `docs/DESENVOLVIMENTO.md`)
- [x] 3.7 Atualizar referências em `CLAUDE.md` e `GEMINI.md` para orientar o uso de `./build.sh --lang pt_BR` nos builds do usuário e apontar os três manuais de desenvolvimento

## Workflow follow-up

- Validar change com `openspec validate build-cli-lang-arg --strict`.
- Arquivar a change com `/opsx-archive` após a aplicação e verificação.
