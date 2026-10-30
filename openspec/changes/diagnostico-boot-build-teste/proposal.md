# Proposal

## Why

Quando um build trava o boot, o aparelho fica parado na imagem do controle e não mostra o motivo. O kernel 3.4.39 da base foi compilado sem console na tela (`# CONFIG_FRAMEBUFFER_CONSOLE is not set`), e as variáveis do U-Boot mandam o console para a porta serial interna (`console=ttyS2,115200 loglevel=0`). Por isso, mexer nos parâmetros de boot não faz o texto do Linux aparecer na tela. No caso do `r36-classicube-sync.service`, que travou o boot por esperar o `emuelec-autostart` e ao mesmo tempo segurar o EmulationStation, a causa só apareceu lendo o código. Um build de teste precisa mostrar e guardar o que o systemd está fazendo, sem SSH (o aparelho não tem rede) e sem mudar a imagem normal.

## What Changes

- O `feature.toml` ganha o campo opcional `test_only` (padrão `false`). Uma feature `test_only = true` entra só em builds com `./build.sh --test`, e o build normal a ignora.
- **BREAKING (spec):** `./build.sh --test` deixa de ser só uma marcação de nome. Ele passa a incluir as features `test_only` habilitadas e, por isso, muda o conteúdo da imagem. Sem `--test`, nada muda.
- Nova feature `90-boot-log-tela` (`test_only`): um serviço abre o `/usr/bin/fbterm` da base no começo do boot e mostra `journalctl -f` por cima da imagem do controle. O EmulationStation encerra esse terminal ao subir. Se o boot travar antes do ES, o log fica na tela.
- Nova feature `91-boot-log-cartao` (`test_only`): um serviço grava, a cada 5 s nos primeiros 3 min do boot, um retrato em texto (`systemctl list-jobs`, `systemctl --failed`, `journalctl -b` e `dmesg`). O retrato vai para `R36-ROMS/r36-boot-log/` quando a p1 está montada. Se ela não montar em 60 s, vai para `R36-SYSTEM/r36-boot-log/`, na p7. As duas são FAT e o PC as lê sem root.
- Nenhum dos dois serviços se ordena em relação ao `emuelec-autostart.service` ou ao `emustation.service`, para não travar o boot que querem diagnosticar.

## Capabilities

### New Capabilities

- `boot-diagnostics`: o que um build de teste mostra na tela e grava no cartão durante o boot para diagnosticar travamentos, e como isso convive com o boot normal.

### Modified Capabilities

- `feature-layers`: o descritor ganha `test_only`, e a seleção de features passa a considerar se o build é de teste.
- `image-build`: a opção `--test` passa a incluir as features `test_only` e deixa de ser neutra quanto ao conteúdo e ao conjunto de features.

## Impact

- **Código:** `tools/r36img/features.py` (campo `test_only` e seleção), `tools/r36img/build.py` (passa `test` para a seleção, ajuda do `--test`), testes em `tests/`.
- **Features novas:** `features/90-boot-log-tela/` e `features/91-boot-log-cartao/`, só na camada `system` (units systemd, scripts em `/usr/lib/r36/` e o drop-in do `emustation.service`).
- **Imagem:** build normal idêntico ao de hoje. Build de teste com alguns KiB a mais no SYSTEM e, no boot, a tela de log no lugar da imagem do controle até o ES abrir.
- **Cartão:** a p7 só é escrita no fallback, com `/flash` remontado em leitura e escrita pelo menor tempo possível. A p5 e a p6 (kernel e initramfs) não mudam.
- **Docs:** `docs/DESENVOLVIMENTO.md` (opção `--test`, as duas features e como ler o log) e `CLAUDE.md` (fato do aparelho: sem console do kernel na tela).
