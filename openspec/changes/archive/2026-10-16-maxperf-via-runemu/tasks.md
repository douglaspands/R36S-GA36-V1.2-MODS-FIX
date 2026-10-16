# Tasks

## 1. Registro térmico (feature 43)

- [x] 1.1 Reproduzir o `cpu_busy` vazio: rodar a função do `thermal-log` com o `awk` que a imagem traz (extrair o binário do SYSTEM do cartão ou usar o do teste) sobre dois snapshots de `/proc/stat`. Registrar a causa no `design.md` e corrigir o `cpu_busy` para devolver `a,b,c,d`. Verificar que a saída tem 3 vírgulas mesmo com núcleos ausentes.
- [x] 1.2 Em `features/43-registro-termico/system/usr/lib/r36/thermal-log`, acrescentar `devfreq/sunxi-ddrfreq/dsm/scene` à busca da DRAM (em `platform/sunxi-ddrfreq/` e `devices/*/sunxi-ddrfreq/`), mantendo `R36_DRAM_SCENE` e os caminhos atuais.
- [x] 1.3 Em `tests/test_registro_termico.py`, afirmar que cada linha gravada tem tantos campos quanto o cabeçalho, que `cpu0` a `cpu3` trazem números, e que a DRAM é achada no caminho com `devfreq`. Verificar vendo os testes novos falharem no `thermal-log` antigo e passarem no novo.

## 2. Início do jogo respeita a chave (feature 10)

- [x] 2.1 Extrair o `emuelecRunEmu.sh` do SYSTEM da imagem base e gravá-lo em `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh` com o mesmo modo do original (executável). Remover o `maxperf` da linha 8 e inserir, logo após `ROMNAME` ser definido, a escolha por `get_ee_setting maxperf "${PLATFORM}" "${ROMNAME##*/}"` (`1` chama `maxperf`, o resto chama `normperf`). Verificar com `diff` contra a base: só essas alterações.
- [x] 2.2 Em `tests/test_ptbr_controle.py`, afirmar que o script existe e é executável, que não chama `maxperf` incondicionalmente antes da leitura da chave, e que o `diff` contra a base (quando ela está no cache de testes) tem só as linhas esperadas. Rodar o script com `get_ee_setting`/`maxperf`/`normperf` falsos para as três situações: global `0` (chama `normperf`), sistema `1` (chama `maxperf`), jogo `0` num sistema `1` (chama `normperf`).
- [x] 2.3 No `README.md`, na feature 10, descrever o mecanismo (script da base alterado, ordem jogo, sistema, global) e a necessidade de reconferir a cópia ao trocar a imagem base; na feature 43, dizer que ela só mede e que o governor é decidido pela feature 10. Verificar relendo as duas seções contra o script e a conf.
- [x] 2.4 Rodar `openspec validate maxperf-via-runemu --strict`.

## 3. Integração e verificação no aparelho

- [x] 3.1 Rodar `./build.sh` e verificar no `changes.txt` que `/usr/bin/emuelecRunEmu.sh` aparece como substituído pela feature 10 e que o `thermal-log` aparece alterado pela 43, sem conflito. Rodar a suíte completa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`) e verificar que passa.
- [x] 3.2 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage`, verificar que termina com "verificado", e conferir o script na p7 gravada.
- [x] 3.3 No aparelho (`--part system`, mantendo ROMs): jogar uns 10 minutos em GBA e em SNES e ler o `r36-thermal.csv`. Verificar que `governor` fica `ondemand`, `dram_scene` fica `1`, e que `cpu0` a `cpu3` trazem números. Ligar o máximo desempenho para o GBA no menu, jogar de novo e verificar `performance` e cena `0` só nele.

## Workflow follow-up

- Branch: `maxperf-via-runemu`. Arquivar a change depois da verificação no aparelho (3.3) e fazer o merge squash na main.
