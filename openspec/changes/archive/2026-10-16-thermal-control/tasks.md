# Tasks

## 1. Script de registro

- [x] 1.1 Criar `features/43-registro-termico/system/usr/lib/r36/thermal-log` (executável, `#!/bin/sh`, só busybox). Ele deve montar o cabeçalho a partir das `thermal_zone*` encontradas e, a cada ciclo, gravar uma linha com as colunas do design (data, `uptime_s`, `boot`, temperaturas em °C, `cpu_mhz`, governor, `cpus_online`, ocupação de `cpu0` a `cpu3` pela diferença entre duas leituras de `/proc/stat`, `dram_scene`, bateria e `system`/`emulator`/`core`/`rom` extraídos do `emuelecRunEmu.sh` em `/proc/*/cmdline`). Os caminhos devem vir de variáveis de ambiente com os valores reais como padrão, e o script deve aceitar `--once`. Verificar com `bash -n` e `sh -n`.
- [x] 1.2 Implementar no script os limites de espaço: rotação para `r36-thermal.1.csv` acima de 1048576 bytes, pulo do ciclo com menos de 65536 KB livres em `df -k`, pulo do ciclo se `/storage/roms` não for ponto de montagem, e rotação forçada se o cabeçalho existente for diferente. Vírgulas e aspas no nome da ROM devem virar `;`.
- [x] 1.3 Criar `tests/test_registro_termico.py`. O teste roda o script com `sh` e `--once` sobre uma árvore falsa de `/proc` e `/sys` em diretório temporário (sem `/sys` real), com um stub de `df` no `PATH`. Ele deve conferir:
  - cabeçalho e linha com o mesmo número de colunas;
  - temperatura em milésimos convertida para °C;
  - ocupação calculada por núcleo, e campo vazio para um núcleo ausente;
  - jogo extraído de um `cmdline` falso do `emuelecRunEmu.sh` com vírgula no nome da ROM;
  - campos de jogo vazios sem esse processo;
  - rotação acima de 1 MB, com o `.1` anterior substituído;
  - nenhuma linha gravada com menos de 64 MB livres;
  - rotação quando o cabeçalho muda.

  Verificar com `uv run python -I -m unittest tests.test_registro_termico`.

## 2. Unit e feature

- [x] 2.1 Criar `features/43-registro-termico/feature.toml` (`order = 43`, `enabled = true`) e a unit `system/usr/lib/systemd/system/r36-thermal-log.service` (`Type=simple`, `Restart=always`, `RestartSec=30`, `Nice=19`, `After=emuelec-autostart.service`, `WantedBy=emuelec.target`), com o link em `emuelec.target.wants/`. Estender `tests/test_registro_termico.py` para conferir essas diretivas e que o link aponta para a unit. Verificar com `uv run python -I -m unittest tests.test_registro_termico`.
- [x] 2.2 Documentar no README a feature 43: o que ela grava, onde fica o CSV (`R36-ROMS/r36-thermal.csv`), as colunas, o limite de 2 MB e de 64 MB livres, que não muda clock nem governor, o roteiro da sessão de medição e como desligá-la. Verificar que os nomes de arquivo, de unit e de colunas citados batem com o script e a unit.

## 3. Integração (build e inspeção pelo PC)

- [x] 3.1 Rodar `./build.sh` com todas as features e verificar que o `changes.txt` lista o script, a unit e o link da feature 43, sem remoções e sem conflito com as features 10 a 52.
- [x] 3.2 Inspecionar o SYSTEM gerado somente leitura (`unsquashfs -lls`): o script é executável, a unit existe, e o link em `emuelec.target.wants/` aponta para ela.
- [x] 3.3 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms` e verificar que termina com "verificado". Rodar a suíte completa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`) e verificar que ela passa.

## Workflow follow-up

- O usuário grava o cartão (não precisa de `--wipe-storage`) e faz a sessão de medição:
  - 5 min no menu;
  - 10 min em cada um de NES, Mega Drive, SNES, GBA (Mario Kart), PSX, N64, PSP e CPS2.
- No PC, conferir `r36-thermal.csv` na partição `R36-ROMS`: as zonas térmicas, a unidade da temperatura e o `cpus_online`, que respondem às questões em aberto do design.
- Com o log em mãos, abrir a spec futura dos tetos de clock por `sistema:core`.
- Commit na branch `feat/registro-termico` quando o usuário pedir. Arquivar com `/opsx:archive`.
