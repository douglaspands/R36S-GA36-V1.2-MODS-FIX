# Proposal

## Why

O percentual de bateria que o EmulationStation mostra é impreciso: começa errado depois de ligar e cai rápido demais. O número vem do driver `axp22` do kernel (mistura de curva OCV e contador de coulomb, com parâmetros do `sys_config` na bootarea), e o aparelho não tem rede nem SSH. Hoje o registro térmico grava só `bat_status`, `bat_pct` e `bat_voltage`, o que não separa um driver mal calibrado de uma célula fraca. Sem esse dado, qualquer correção seria um chute.

## What Changes

- O registro térmico (feature 43) passa a gravar no CSV mais quatro colunas de bateria: `bat_current` (mA, com sinal), `bat_charge_now` e `bat_charge_full` (mAh) e `bat_pct_est`.
- `bat_pct_est` é uma estimativa "sombra" calculada pelo próprio script a partir da tensão (curva genérica de Li-ion, com filtro). Ela **não** aparece no ES nem no RetroArch e não altera o `capacity` do kernel: serve só para comparar com o `bat_pct` do kernel numa descarga completa.
- O retrato do boot (`r36-sysinfo.txt`) passa a trazer o `uevent` completo de cada `power_supply` (inclui `charge_full_design`, `capacity_level`, `technology`) e as linhas `axp` do `dmesg`, para ver o que o driver acredita sobre a célula e o ponto de partida do boot.
- Um script de análise no PC (`tools/`) lê o `r36-thermal.csv` e resume o início da sessão (tensão × % do kernel × % estimado) e a descarga (% × tempo, tensão × %).
- O README documenta as colunas novas e o roteiro da descarga completa para coletar o log.
- Fora do escopo: mostrar o valor corrigido no ES, mexer no `capacity` por `mount --bind`, alterar o `sys_config` ou o `udt_battery.sh`. Isso fica para uma change seguinte, com o log real em mãos.

## Capabilities

### New Capabilities
- `battery-diagnostics`: o que o aparelho registra para avaliar a precisão da bateria (colunas do CSV, estimativa sombra, retrato do boot) e a análise no PC.

### Modified Capabilities

Nenhuma. As colunas novas entram no CSV como requisitos próprios da capability nova; os requisitos de `thermal-control` continuam valendo (cabeçalho novo força a rotação do CSV antigo, comportamento já especificado).

## Impact

- `features/43-registro-termico/system/usr/lib/r36/thermal-log`: leitura das grandezas novas, estimativa sombra e seção de bateria do retrato.
- `tests/test_registro_termico.py`: casos das colunas novas, da estimativa e do retrato. Teste novo para o script de análise.
- `tools/`: script de análise do CSV (Python via `uv`).
- `README.md`: seção da feature 43.
- Efeito no aparelho: só leitura de `/sys` e do `dmesg` a cada 5 s e uma vez por boot, sem mudar clock, governor, DRAM nem o que o ES exibe.
- Quem gravar o cartão com `--keep-roms` tem o `r36-thermal.csv` antigo movido para `.1` (o `.1` anterior é substituído), porque o cabeçalho muda: copie os CSVs de interesse antes de gravar.
