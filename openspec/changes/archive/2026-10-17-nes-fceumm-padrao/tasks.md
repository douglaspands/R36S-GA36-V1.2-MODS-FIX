# Tasks

## 1. Preparação

- [x] 1.1 Combinar com o usuário o destino das alterações não commitadas da change `tema-nes-box-completo`, criar a branch desta change a partir da `main` e verificar com `git branch --show-current` e `git status` que ela não carrega essas alterações
- [x] 1.2 Sem sudo, conferir na imagem base que `fceumm_libretro.so` existe e qual é o nome do core na entrada `nes` do `es_systems.cfg`; verificar anotando o resultado no commit ou na descrição da task, e parar se o core não existir

## 2. NES com fceumm

- [x] 2.1 Adicionar `nes.emulator=libretro` e `nes.core=fceumm` ao `emuelec.conf` da feature `10-ptbr-sao-paulo`, junto das linhas do SNES, e verificar que o arquivo não declara `fds.core`
- [x] 2.2 Cobrir os requisitos em `tests/test_ptbr_controle.py` (`nes.emulator`, `nes.core` e ausência de `fds.core`) e verificar com `uv run pytest tests/test_ptbr_controle.py`
- [x] 2.3 Atualizar a descrição em `features/10-ptbr-sao-paulo/feature.toml` e documentar o fceumm no `README.md`, junto da nota do SNES, citando como voltar ao nestopia pelo menu, que só imagem nova ou `--wipe-storage` recebe o padrão e o aviso sobre save states; verificar que o texto cita `fceumm` e `nestopia`

## 3. Imagem

- [x] 3.1 Rodar a suíte inteira com `uv run pytest` e verificar que tudo passa
- [x] 3.2 Gerar a imagem com `./build.sh --test` e verificar, sem sudo, que a p8 gerada traz `nes.core=fceumm` no `emuelec.conf`
- [x] 3.3 No aparelho, abrir um jogo de NES sem escolha prévia e verificar que roda no fceumm (registro térmico com `core` `fceumm`), e que escolher o nestopia pelo menu num jogo continua funcionando

## Workflow follow-up

- Arquivar a change depois da validação no aparelho.
