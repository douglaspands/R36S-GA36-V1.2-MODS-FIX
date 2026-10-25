# Tasks

## 1. Colunas de bateria no registro

- [x] 1.1 Em `features/43-registro-termico/system/usr/lib/r36/thermal-log`, adicionar o helper `snum` (aceita `-` inicial) e ler `current_now`, `charge_now` e `charge_full` da bateria, convertendo µA/µAh para mA/mAh. Incluir `bat_current,bat_charge_now,bat_charge_full,bat_pct_est` no `HEADER` logo depois de `bat_voltage` e na linha do `printf`. Verificar com `sh -n` e `bash -n` no script.
- [x] 1.2 Estender `tests/test_registro_termico.py` (árvore falsa com `current_now` de `-450000`, `charge_now` de `1200000` e `charge_full` de `2000000`): o cabeçalho traz as quatro colunas depois de `bat_voltage`, a linha tem o mesmo número de campos, os valores saem `-450`, `1200` e `2000`, e com os três arquivos removidos os campos ficam vazios sem quebrar a linha. Ajustar o teste do cabeçalho existente. Verificar com `uv run python -I -m unittest tests.test_registro_termico`.

## 2. Estimativa sombra

- [x] 2.1 No `thermal-log`, calcular `bat_pct_est`: filtro exponencial inteiro (`f = f + (v - f) / 4`) sobre a tensão em mV, com o estado numa variável do laço, e interpolação linear pela tabela 3300→0, 3500→4, 3600→12, 3700→30, 3800→50, 3900→65, 4000→78, 4100→90, 4200→100, cortada em 0 e 100. Com status `Charging`/`Full` ou sem tensão o campo fica vazio e o filtro zera; no `--once` usa a tensão crua. Nada é publicado fora do CSV. Verificar com `sh -n`.
- [x] 2.2 Testes em `tests/test_registro_termico.py`: 4200 mV → 100; 3300 mV → 0; 3750 mV → 40; abaixo de 3300 → 0 e acima de 4200 → 100; `Charging` e `Full` → campo vazio; sem `voltage_now` → vazio; duas amostras seguidas com a segunda 200 mV menor (laço, com `R36_INTERVAL` curto ou chamadas em sequência) → a queda da estimativa é menor que a da tensão crua. Verificar que nenhum arquivo além do CSV e do retrato é criado em `$R36_ROMS`/`$R36_SYS`. Rodar `uv run python -I -m unittest tests.test_registro_termico`.

## 3. Retrato da bateria no boot

- [x] 3.1 No `sysinfo_body` do `thermal-log`, substituir a seção `== bateria ==` por: `uevent` de cada `power_supply` (uma linha `caminho/uevent: CHAVE=valor` por entrada), os campos `status`, `capacity`, `voltage_now`, `current_now`, `charge_now`, `charge_full`, `charge_full_design` e `capacity_level` da bateria via `si`, e as últimas 80 linhas de `dmesg | grep -i axp`, cada uma prefixada por `dmesg:`. Ausências viram `(ausente)` e não travam. Verificar com `sh -n`.
- [x] 3.2 Estender os testes do retrato: com `uevent` falso na bateria e no carregador e um stub de `dmesg` no `PATH` com linhas `axp` e outras, o retrato traz as linhas do `uevent` com o caminho, só as linhas `axp` do `dmesg` (no máximo 80), e os campos pelo `si`; sem `power_supply` do tipo bateria e sem linhas `axp` o retrato marca `(ausente)` e o script termina com sucesso. Rodar `uv run python -I -m unittest tests.test_registro_termico`.

## 4. Análise no PC

- [x] 4.1 Criar `tools/analisa_bateria.py` (só biblioteca padrão): lê um ou mais `r36-thermal.csv`, agrupa por `boot`, e por boot imprime a tensão, o `bat_pct` e o `bat_pct_est` das primeiras amostras (com a diferença entre os dois percentuais) e a queda por hora do `bat_pct` e do `bat_pct_est` nas linhas em `Discharging`. Colunas ausentes são avisadas e o script termina com sucesso. Verificar rodando `uv run python -I tools/analisa_bateria.py <csv de teste>`.
- [x] 4.2 Criar `tests/test_analisa_bateria.py` com um CSV sintético de dois boots (um em descarga com os dois percentuais, outro sem as colunas novas): o resumo traz a diferença inicial e as taxas por hora esperadas, ignora linhas em `Charging`, e para o CSV antigo avisa as colunas faltantes sem erro. Rodar `uv run python -I -m unittest tests.test_analisa_bateria`.

## 5. Documentação

- [x] 5.1 Atualizar a seção da feature 43 no `README.md`: as quatro colunas novas e suas unidades, que `bat_pct_est` é só comparação e não aparece no ES, a seção de bateria do `r36-sysinfo.txt`, o aviso de copiar os CSVs antigos antes de gravar (o cabeçalho novo move o `r36-thermal.csv` para `.1` e apaga o `.1` anterior), o roteiro da descarga completa (carregar a 100%, ligar, menu e jogos até desligar sozinho, copiar `r36-thermal.csv`, `r36-thermal.1.csv` e `r36-sysinfo.txt`) e o comando de `tools/analisa_bateria.py`. Verificar que os nomes de colunas e de arquivos citados batem com o script e com `tools/analisa_bateria.py`.
- [x] 5.2 Atualizar a descrição da feature em `features/43-registro-termico/feature.toml` para citar corrente, carga e a estimativa. Verificar com `uv run python -I -m unittest tests.test_registro_termico` (o teste da feature lê o `feature.toml`).

## 6. Integração

- [x] 6.1 Rodar `./build.sh` e verificar no `changes.txt` que o `thermal-log` aparece alterado, sem remoções nem conflitos com as demais features. Inspecionar o SYSTEM gerado somente leitura (`unsquashfs -lls`): o script continua executável.
- [x] 6.2 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms` e verificar que termina com "verificado". Rodar a suíte completa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`) e verificar que ela passa.

## Workflow follow-up

- O usuário grava o cartão (`--part system` basta, com `--keep-roms`) depois de copiar os CSVs antigos, carrega a bateria a 100% e faz uma descarga completa, com um trecho de menu e um de jogo.
- No PC, rodar `uv run python -I tools/analisa_bateria.py` sobre o CSV e abrir o `r36-sysinfo.txt`: decidir entre parâmetros do driver errados (H1) e célula fraca (H2), e se `current_now`/`charge_*` existem.
- Com o log em mãos, abrir a change seguinte (percentual corrigido no ES, ou aviso de célula fraca).
- Branch própria criada a partir da `main` no início do `/opsx:apply`; commit, merge e push só a pedido. Arquivar com `/opsx:archive`.
