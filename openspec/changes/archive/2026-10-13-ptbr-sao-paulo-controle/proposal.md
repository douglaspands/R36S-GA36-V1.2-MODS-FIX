# Proposal

## Why

A imagem de fábrica vem com o EmuELEC em espanhol do México (`es_MX`, fuso `America/Mexico_City`), o menu do RetroArch em inglês e o tema XMB, que é pesado para o A33. No RetroArch, o controle do R36S tem A e B trocados em relação à posição física. Uma reconfiguração feita no aparelho deixou o hotkey no direcional para baixo, o que abaixa o volume, bloqueia a entrada do jogo e permite reset, saída ou sobrescrita de save sem querer. Este change leva para a imagem o idioma, o fuso, o menu e o mapeamento posicional corretos.

## What Changes

- EmuELEC em português do Brasil (`system.language=pt_BR`) e fuso `America/Sao_Paulo`, no `emuelec.conf` da p8.
- EmulationStation com `Language` = `pt_BR` no `es_settings.cfg`.
- Menu do RetroArch em português do Brasil (`user_language = "7"`) e com o driver RGUI. O `setsettings.sh` reescreve o `menu_driver` a cada jogo a partir de `global.retroarch.menu_driver` do `emuelec.conf`; sem esse valor, ele força o XMB no A33. Por isso o RGUI é declarado no `emuelec.conf` e também no `retroarch.cfg`.
- Autoconfig do `micro_gamepad` no RetroArch com mapeamento posicional do RetroPad: baixo = B (btn 1), direita = A (btn 0), cima = X (btn 2), esquerda = Y (btn 3). Os números foram validados no aparelho.
- Atalhos do RetroArch iguais aos de fábrica, com o hotkey no Select (btn 8) e nenhum atalho no direcional. Pausa e FPS seguem o mesmo botão físico de antes da troca A↔B.
- Os remaps por core de fábrica (N64, Flycast etc.) não mudam. Os emuladores standalone ficam fora do escopo.
- Duas features novas, aplicadas só na camada `storage`: `10-ptbr-sao-paulo` e `20-controle-posicional`.
- **BREAKING (no cartão):** as mudanças só chegam ao aparelho com uma gravação que use `--wipe-storage`, que apaga saves e configurações. O usuário já aceitou isso.

## Capabilities

### New Capabilities
- `system-locale`: idioma e fuso horário do sistema, do EmulationStation e do menu do RetroArch na imagem gerada.
- `retroarch-menu`: driver de menu do RetroArch usado na imagem e como ele se mantém entre os jogos.
- `retroarch-controls`: mapeamento do controle embutido no RetroArch (RetroPad posicional) e os atalhos de hotkey.

### Modified Capabilities
(nenhuma: as features usam o mecanismo de camadas existente sem mudar seus requisitos)

## Impact

- Novos diretórios `features/10-ptbr-sao-paulo/` e `features/20-controle-posicional/`, só com a camada `storage/`.
- Arquivos da p8 substituídos inteiros, com base nos originais de fábrica: `.config/emuelec/configs/emuelec.conf`, `.config/emulationstation/es_settings.cfg`, `.config/retroarch/retroarch.cfg` e `joypads/micro_gamepad.cfg`.
- Nenhuma mudança em `tools/r36img/`, no SYSTEM, no boot ou nas ROMs.
- Na primeira inicialização, o EmuELEC compila o locale `pt_BR.UTF-8` com `localedef`, o que pode deixar esse boot alguns segundos mais lento.
- Se o controle for reconfigurado pelo menu do EmulationStation, o `micro_gamepad.cfg` é regravado no aparelho.
