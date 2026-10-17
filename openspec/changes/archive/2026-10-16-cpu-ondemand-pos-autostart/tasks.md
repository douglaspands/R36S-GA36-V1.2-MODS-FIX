# Tasks

## 1. Preparação

- [x] 1.1 Criar a branch `cpu-ondemand-pos-autostart` a partir da `main`, depois do merge de `dram-jogo-snes9x2010-listas-es`; verificar com `git branch --show-current` e conferindo que `features/43-registro-termico/system/usr/lib/r36/thermal-log` grava `r36-sysinfo.txt`

## 2. Serviço de reaplicação

- [x] 2.1 Criar `features/44-cpu-ondemand/system/usr/lib/systemd/system/r36-cpu-ondemand.service` (`After=emuelec-autostart.service`, `Type=oneshot`, `ExecStart=/usr/lib/r36/cpu-ondemand-tune`, `WantedBy=emuelec.target`) e o link relativo `emuelec.target.wants/r36-cpu-ondemand.service -> ../r36-cpu-ondemand.service`; verificar em `tests/test_cpu_ondemand.py`, com o `diretivas` e o `assert_link` de `test_otimizacoes`, essas diretivas, o link e que `ExecStart` aponta para um script executável da feature
- [x] 2.2 No `r36-thermal-log.service` da `43-registro-termico`, trocar para `After=emuelec-autostart.service r36-cpu-ondemand.service`; verificar em `tests/test_registro_termico.py` o `After` com os dois serviços e que a feature 43 continua sem `Requires`/`Wants` da 44
- [x] 2.3 Atualizar a `description` de `features/44-cpu-ondemand/feature.toml` e a seção da `44-cpu-ondemand` no `README.md` (o serviço roda depois do `emuelec-autostart`, porque o `normperf` do boot zera os tunables; como conferir pelo `r36-sysinfo.txt`); verificar que o README cita `r36-cpu-ondemand.service` e `r36-sysinfo.txt`

## 3. Validação

- [x] 3.1 Rodar a suíte inteira com `uv run pytest` e verificar que tudo passa
- [x] 3.2 Gerar a imagem com `./build.sh --test` e verificar que o diretório e a imagem terminam em `-test`; conferir no SYSTEM (`unsquashfs`, sem sudo) o serviço, o link em `emuelec.target.wants` e o `After` do `r36-thermal-log.service`
- [x] 3.3 No aparelho (gravado com `--part system`, bateria carregada): ligar, ficar 2 min no menu e abrir e fechar um jogo. No PC, verificar no `r36-sysinfo.txt` `up_threshold` 30, `sampling_down_factor` 10 e `scaling_min_freq` 600000, e no CSV `cpu_mhz` sem valores abaixo de 600 no menu e `dram_scene` 1 no menu
