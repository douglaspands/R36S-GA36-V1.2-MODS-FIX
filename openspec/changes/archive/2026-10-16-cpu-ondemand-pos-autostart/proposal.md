# Proposal

## Why

No teste da imagem `20261016-193758-test`, o `r36-sysinfo.txt` gravado aos 52 s de boot mostrou `up_threshold` 95, `sampling_down_factor` 1 e `scaling_min_freq` 120000: o afinamento do ondemand não vale no menu. A causa está no SYSTEM da imagem. O `cpufreq.service` (`WantedBy=basic.target`) roda cedo e só afina se o governor já for `ondemand`. Depois, o `emuelec_autostart.sh` chama `maxperf` (linha 80) e, mais adiante, `normperf` (linha 247), que volta o governor para `ondemand` e zera os tunables. Nada reaplica o afinamento depois disso. Em jogo ele vale, porque o `emuelecRunEmu.sh` o reaplica após cada `normperf`; o menu fica com clocks de 240 MHz e subida tardia. A spec `cpu-frequency-scaling` já exige 30 / 10 / 600 MHz "após o boot" e no menu, então hoje a imagem não cumpre a própria spec.

## What Changes

- A feature `44-cpu-ondemand` ganha o serviço `r36-cpu-ondemand.service`, um oneshot com `After=emuelec-autostart.service` que roda `/usr/lib/r36/cpu-ondemand-tune` (sem argumento, então sem mexer na DRAM). Entra em `emuelec.target.wants`, no mesmo molde do `r36-thermal-log`.
- Nenhum arquivo da base é substituído por isso. Desligar a feature remove o serviço.
- O `r36-thermal-log` já roda depois do `emuelec-autostart.service`; passa a ser ordenado também depois do novo serviço, para o retrato do boot mostrar os valores afinados.
- A imagem é gerada com `./build.sh --test`. A validação no aparelho é o `r36-sysinfo.txt` e o CSV do próximo teste.

## Capabilities

### New Capabilities

### Modified Capabilities
- `cpu-frequency-scaling`: o afinamento passa a ser reaplicado depois do boot completo do EmulationStation, de modo que vale no menu parado e não só em jogo.

## Impact

- `features/44-cpu-ondemand`: unidade systemd nova e link em `emuelec.target.wants`; descrição do `feature.toml`.
- `features/43-registro-termico`: `After=` do `r36-thermal-log.service` inclui o serviço novo.
- Testes: `tests/test_cpu_ondemand.py` e `tests/test_registro_termico.py`. README.
- Só SYSTEM: vale com qualquer gravação dele, inclusive `--keep-storage`.
- Depende de a change `dram-jogo-snes9x2010-listas-es` estar na `main` (o `thermal-log` com o retrato e o script com o argumento `jogo`).
