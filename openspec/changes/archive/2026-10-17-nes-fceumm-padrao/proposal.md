# Proposal

## Why

O NES da imagem base abre por padrão no `nestopia` (a lista de cores do RetroArch da base o associa ao sistema), que é mais pesado que o `fceumm`. O `fceumm` é o core de NES mais leve do RetroArch e o mais usado, e combina com a linha das últimas changes: SNES com `snes9x2005_plus`, GBA com `gpsp` e CPS2 com `fbalpha2012`, todos escolhidos por serem leves para o A33.

## What Changes

- O NES passa a abrir por padrão no core `fceumm` do RetroArch, declarado em `emuelec.conf` no mesmo molde do `snes.core=snes9x2005_plus` (`nes.emulator=libretro`, `nes.core=fceumm`).
- Os demais cores de NES (`nestopia`, `quicknes` e outros que a base traga) continuam instalados e selecionáveis pelo menu do EmulationStation, por sistema ou por jogo.
- Famicom Disk System (`fds`) e demais sistemas de Nintendo 8 bits não mudam.
- README e teste de configuração ganham a nova linha, no estilo das de GBA, SNES e CPS2.

Premissa: o `fceumm_libretro.so` já vem na imagem base. Isso não pôde ser conferido pelo repositório (o SYSTEM é um squashfs), então a primeira tarefa confirma antes de editar; se o core não existir, a change para e volta ao usuário.

## Capabilities

### New Capabilities
- `nes-emulation`: qual emulador e core o Nintendinho (NES) usa por padrão na imagem gerada, sem remover as alternativas; espelha `snes-emulation`.

### Modified Capabilities
<!-- Nenhuma. snes-emulation, gba-emulation e cps2-emulation não mudam. -->

## Impact

- `features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf`: linhas `nes.emulator` e `nes.core`.
- `features/10-ptbr-sao-paulo/feature.toml`: descrição passa a citar o fceumm.
- `tests/test_ptbr_controle.py`: asserções de `nes.core` e de ausência de `fds.core`.
- `README.md`: item sobre o fceumm na lista da feature `10-ptbr-sao-paulo`.
- Só imagem nova ou regravada com `--wipe-storage` recebe o padrão, como nos demais cores. Sem mudança em ROMs, boot, kernel ou temas.
- Hoje há alterações não commitadas de outra change (tema NES box v2) na branch `tema-nes-box-completo`; a branch desta change deve sair da `main`, sem levá-las.
