# Proposal

## Why

O R36S não tem como ajustar o brilho da tela: a base só lê `brightness.level` do `emuelec.conf` (80 na feature 10) ao acordar da suspensão e ao abrir um jogo, e nenhum botão o muda. Agora que o FN chega como botão próprio (`BTN_MODE`, 316, feature 20), dá para usar **FN + D-pad ↑/↓** como atalho de brilho sem conflitar com o RetroArch (nenhum hotkey usa o D-pad) nem com o ES (o FN fica reservado nele).

## What Changes

- **Feature nova `62-brilho-fn`**: um serviço leitor de eventos de entrada (`evtest`, no estilo do `udt_events.sh`) que, com o FN apertado, sobe o brilho no D-pad ↑ e desce no D-pad ↓, em passo fixo, repetindo enquanto a seta fica apertada. O D-pad pode chegar como botão ou como eixo (`ABS_HAT0Y`): o leitor trata os dois.
- **Nível persistente** em arquivo próprio da p8, `r36-brilho.level` (0 a 100), com piso para a tela nunca apagar. O `emuelec.conf` não serve de fonte, porque o ES o regrava. O nível é aplicado no `lcdbl` (`/sys/devices/virtual/disp/disp/attr/lcdbl`, 0 a 255, escala `(nível*255+50)/100`) no boot e a cada ajuste.
- **Reset ao padrão (80)** de duas formas: o clique do analógico esquerdo (L3) com o FN apertado (FN + L3; ↑ e ↓ juntos não serve, o usuário não consegue apertá-los ao mesmo tempo), e o arquivo vazio `r36-brilho-original` na raiz da p1, aplicado no boot (apaga o nível salvo e deixa o brilho no padrão).
- **Acordar da suspensão**: o `udt_pwr_events.sh` (feature 46) passa a chamar o `brilho-aplica` logo depois de restaurar o `lcdbl`, para o brilho salvo valer depois do sono. É a única mudança fora da feature nova, e é uma só linha.
- **Log** `r36-brilho.log` na p1, gravado só com a chave `r36-diagnostico`.
- O FN **continua sem função** no EmulationStation (o `tests/test_fn.py` segue valendo). O `emuelecRunEmu.sh` **não é alterado**.

## Capabilities

### New Capabilities
- `screen-brightness`: ajuste do brilho da tela por FN + D-pad ↑/↓, nível persistente com piso, reset ao padrão (FN + L3 e chave `r36-brilho-original`) e reaplicação no boot e ao acordar.

### Modified Capabilities
- `diagnostic-logs`: a lista de logs sob a chave `r36-diagnostico` passa a incluir o `r36-brilho.log`.

## Impact

- Novo: `features/62-brilho-fn/**` (script `brilho-aplica`, leitor de eventos, units do systemd), `tests/test_brilho_fn.py`.
- Alterado: `features/46-audio/system/usr/bin/udt_pwr_events.sh` (uma chamada, no ramo de acordar). Nenhum outro arquivo existente.
- Dependências: o `fn-remapeia` da feature 20 (o FN como 316) e o `evtest` da base. Sem o remapeamento (chave `r36-fn-original`, `fn_key` ausente), o FN não chega como 316 e o atalho não funciona; o brilho salvo ainda vale no boot.
- Roda em paralelo com as changes A, B e C dentro de `integra-limite-idioma-shaders-gb`, sem arquivo em comum com elas.
- Que o D-pad chegue com o FN apertado, e se vem como botão ou eixo, só se confirma no aparelho.
- Fora do escopo: ajuste de brilho dentro do RetroArch (`screen_brightness` no `retroarch.cfg`), o brilho no menu do ES e o modo automático.
