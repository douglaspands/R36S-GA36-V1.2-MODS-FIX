# Tasks

## 1. Preparação

- [x] 1.1 Criar a branch `dram-jogo-snes9x2010-listas-es` a partir da `main` depois do merge de `cps2-fbalpha2012-ondemand-afinado`, e verificar com `git branch --show-current` e `./build.sh --help`, que deve listar `--test`

## 2. DRAM na cena 0 com jogo aberto

- [x] 2.1 No `features/44-cpu-ondemand/system/usr/lib/r36/cpu-ondemand-tune`, gravar `0` na cena da DRAM (caminho do `maxperf`, configurável por `R36_DRAM_SCENE`) só quando receber o argumento `jogo` e o governor for `ondemand`, e atualizar o comentário do cabeçalho; verificar em `tests/test_cpu_ondemand.py`, com a árvore sysfs falsa, os casos `jogo` com `ondemand` (cena vira `0`), sem argumento (cena intacta), `jogo` com `performance` (cena intacta) e arquivo da cena ausente (sai com 0)
- [x] 2.2 No `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`, passar `jogo` só na chamada após o `normperf` da abertura, deixando a da saída sem argumento; verificar em `tests/test_cpu_ondemand.py` que só a chamada da abertura passa `jogo`, e com `uv run pytest tests/test_ptbr_controle.py` que a contagem de linhas que diferem da base continua em 1 removida e 12 adicionadas
- [x] 2.3 Atualizar a `description` de `features/44-cpu-ondemand/feature.toml` e a seção da `44-cpu-ondemand` no `README.md` (DRAM na cena `0` em jogo, cena `1` no menu, desligar a feature devolve a cena `1`, como conferir pela coluna `dram_scene`); verificar que o README cita `dram_scene` e a cena `0` em jogo

## 3. SNES com snes9x2005_plus

- [x] 3.1 Adicionar `snes.emulator=libretro` e `snes.core=snes9x2005_plus` ao `emuelec.conf` da `10-ptbr-sao-paulo`, junto das linhas de GBA e CPS2; verificar em `tests/test_ptbr_controle.py` os dois valores e a ausência de `snesh.core` e `snesmsu1.core`, com `uv run pytest tests/test_ptbr_controle.py`
- [x] 3.2 Documentar o SNES no `README.md`, junto das notas do gpSP e do fbalpha2012; verificar que o texto cita o `snes9x2005_plus`, os outros cores e a escolha pelo menu

## 4. Listas do EmulationStation

- [x] 4.1 No `es_settings.cfg` da `10-ptbr-sao-paulo`, trocar `FolderViewMode` para `never` e incluir `<bool name="FavoritesFirst" value="true" />` na ordem dos `bool`; verificar em `tests/test_ptbr_controle.py` (`test_es_settings`) as duas chaves, e com `diff` contra o `es_settings.cfg` do `storage.img` do build `20261016-172250-test` que só essas duas linhas mudaram
- [x] 4.2 Documentar no `README.md`, na lista de padrões da `10-ptbr-sao-paulo`, as pastas ocultas e os favoritos no topo, com o caminho no menu do ES para voltar e a nota de que só chega com `--wipe-storage`; verificar que o texto cita `FolderViewMode` e `FavoritesFirst`

## 5. RetroArch em inglês

- [x] 5.1 No `retroarch.cfg` da `10-ptbr-sao-paulo`, trocar `user_language` de `7` para `0`; verificar em `tests/test_ptbr_controle.py` (`test_retroarch_cfg`) o valor `0` e que `system.language` e o `Language` do ES continuam `pt_BR`, com `uv run pytest tests/test_ptbr_controle.py`
- [x] 5.2 Atualizar a `description` de `features/10-ptbr-sao-paulo/feature.toml` e a seção da `10-ptbr-sao-paulo` no `README.md`: RetroArch em inglês por padrão e como trocar para o português no próprio menu; verificar que o README não diz mais que o RetroArch vem em `pt_BR`

## 6. Diagnóstico no cartão

- [x] 6.1 No `features/43-registro-termico/system/usr/lib/r36/thermal-log`, incluir `cpu_max_mhz` depois de `cpu_mhz`, `dram_mhz` depois de `dram_scene` e `bat_voltage` (mV) depois de `bat_pct`, com a conversão de unidade da DRAM do design; verificar em `tests/test_registro_termico.py` o cabeçalho novo, os valores convertidos a partir de uma árvore falsa (Hz e kHz para a DRAM, µV para a bateria), campos vazios quando o arquivo falta e a rotação de um log com o cabeçalho antigo
- [x] 6.2 No mesmo script, gravar `r36-sysinfo.txt` uma vez por boot, no primeiro ciclo em que `can_write` passa, via arquivo temporário e `mv`, com as seções e os itens do design e `(ausente)` para o que não existe; verificar em `tests/test_registro_termico.py` que o arquivo sai com valores e caminhos da árvore falsa, marca um item ausente, não é gravado com as ROMs desmontadas ou sem espaço, não é regravado no segundo ciclo e que a linha do CSV é gravada normalmente
- [x] 6.3 Atualizar a `description` de `features/43-registro-termico/feature.toml` e a seção da `43-registro-termico` no `README.md` (colunas novas e o `r36-sysinfo.txt`); verificar que o README lista `cpu_max_mhz`, `dram_mhz`, `bat_voltage` e `r36-sysinfo.txt`

## 7. Imagem de teste

- [x] 7.1 Rodar a suíte inteira com `uv run pytest` e verificar que tudo passa
- [x] 7.2 Gerar a imagem com `./build.sh --test` e verificar que o diretório e a imagem terminam em `-test`, e que o `R36-BUILD.txt` traz `teste: sim` e as features `43-registro-termico` e `44-cpu-ondemand`
- [x] 7.3 Conferir na imagem gerada, sem sudo: no SYSTEM, o `cpu-ondemand-tune` com o caso `jogo` e o `emuelecRunEmu.sh` passando `jogo` só na abertura; na p8, `snes.core=snes9x2005_plus` no `emuelec.conf`, `FolderViewMode`/`FavoritesFirst` no `es_settings.cfg` e `user_language = "0"` no `retroarch.cfg`
- [ ] 7.4 No aparelho (gravado com `--keep-roms --wipe-storage`, bateria carregada): ficar 5 min no menu e 10 min em cada um de CPS2 (mvsc), PSX, SNES e N64; abrir e fechar um jogo com o máximo desempenho ligado. No PC, verificar no `r36-sysinfo.txt` os governors e frequências disponíveis, o `sampling_rate` e as cenas e frequências da DRAM (herda a tarefa 1.2 da change arquivada); no CSV, `dram_scene` 0 em jogo e 1 no menu, `cpu_mhz` sem valores abaixo de 600, `core` `snes9x2005_plus` no SNES e `fbalpha2012` no CPS2, `cpu_max_mhz` e `bat_voltage` preenchidos; e, com o usuário, o menu do RetroArch em inglês e o do ES em português, som e quadros nos quatro sistemas comparados ao teste anterior (herda a tarefa 4.4)

## Workflow follow-up

- Se o teste no aparelho mostrar `cpu_max_mhz` abaixo de 1200 com a bateria cheia, tratar o teto de frequência em change à parte, com base no `r36-sysinfo.txt`.
- Ao arquivar, ajustar à mão o `## Purpose` de `openspec/specs/system-locale/spec.md`, que ainda cita o menu do RetroArch em português do Brasil.
- Arquivar a change depois da validação no aparelho e fazer o merge da branch na `main`.
