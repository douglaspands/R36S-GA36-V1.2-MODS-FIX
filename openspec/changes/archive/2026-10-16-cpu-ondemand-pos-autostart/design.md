# Design

## Context

Veja `proposal.md` para a motivação. Estado conferido no SYSTEM do build `20261016-193758-test`:

- `cpufreq.service` (`WantedBy=basic.target`) roda `/usr/bin/cpufreq`, que chama `/usr/lib/r36/cpu-ondemand-tune` só se o governor já for `ondemand`.
- `emuelec-autostart.service` (`Type=oneshot`, `RemainAfterExit=yes`, `After=graphical.target`, `Before=emulationstation.service`, `WantedBy=emuelec.target`) roda o `emuelec_autostart.sh`. Nele, `maxperf` (linha 80) grava `performance`, e `normperf` (linha 247) grava `ondemand` e a cena `1` da DRAM. A troca `performance` para `ondemand` reinicializa os tunables no kernel 4.9 do A33.
- O `r36-thermal-log.service` (feature 43) já usa `After=emuelec-autostart.service` e `WantedBy=emuelec.target`, e roda sem problema na imagem real. Isso prova que o `emuelec-autostart.service` termina (o script não bloqueia) e que o `emuelec.target.wants` das features é lido.
- O `cpu-ondemand-tune` sem argumento não toca na DRAM, só nos tunables e no piso.

## Goals / Non-Goals

**Goals:**
- Reaplicar o afinamento depois do `normperf` do autostart, para o menu parado ter 30 / 10 / 600 MHz.

**Non-Goals:**
- Não mudar valores do afinamento, o `maxperf`/`normperf` da base nem a DRAM.
- Não substituir `emuelec_autostart.sh`.
- Não mexer nas outras chamadas do afinamento (`cpufreq` no boot e `emuelecRunEmu.sh`).

## Decisions

**1. Serviço oneshot na feature 44, ordenado depois do autostart.**
`r36-cpu-ondemand.service`: `After=emuelec-autostart.service`, `Type=oneshot`, `ExecStart=/usr/lib/r36/cpu-ondemand-tune`, `WantedBy=emuelec.target`, com o link em `usr/lib/systemd/system/emuelec.target.wants/`. É o molde do `r36-thermal-log`, já provado na imagem, e fica inteiro dentro da feature: desligar a 44 tira o serviço e o link.
Alternativas descartadas: substituir o `emuelec_autostart.sh` da base com uma linha a mais depois do `normperf`, o que exige cópia do arquivo e teste de diferença contra a base; usar um drop-in no `emuelec-autostart.service` com `ExecStartPost=`, que ficaria acoplado ao serviço da base e arriscaria atrasar o start do EmulationStation; mudar o `normperf` na base, que obriga a substituir o `profile.d`.
`ExecStart` sem `-`: o script sempre sai com 0. `Nice` não é preciso, o script é curto.

**2. O `thermal-log` espera o serviço novo.**
`After=emuelec-autostart.service r36-cpu-ondemand.service` no `r36-thermal-log.service`. `After=` para uma unidade que não existe (feature 44 desligada) é ignorado pelo systemd, então a 43 continua independente da 44. O retrato do boot sai depois do afinamento.

**3. Sem DRAM.**
O serviço roda sem o argumento `jogo`, então a cena da DRAM fica a do `normperf` (`1`) no menu.

## Risks / Trade-offs

- [O autostart termina depois de iniciar o EmulationStation, então há uma janela de segundos no menu sem afinamento] → Aceitável; o serviço roda assim que o oneshot do autostart termina. A validação é o retrato e o CSV no menu.
- [Algo muda o governor depois do serviço] → O `emuelecRunEmu.sh` já reaplica em cada jogo. O retrato e o CSV mostram o estado real.
- [A unidade não ser lida em `emuelec.target.wants`] → O mesmo mecanismo do `r36-thermal-log` já funciona na imagem; o teste confere o link e a imagem gerada é conferida.

## Migration Plan

Só imagem nova (SYSTEM). Gravar com `./flash.sh ... --part system`, ou `--all` com `--keep-roms --keep-storage`. Reverter: `enabled = false` na 44.

## Open Questions

- Nenhuma. O próximo teste dirá se `scaling_min_freq` 600000 e o `up_threshold` 30 aparecem no retrato do boot.
