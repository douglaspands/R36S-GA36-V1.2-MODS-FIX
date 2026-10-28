# Proposal

## Why

A descarga completa de 26/10 (264 min, 2642 mAh integrados pela `bat_current`) mostrou que o `capacity` do kernel não serve de medidor: ficou em **100% por 71 min** (25% da carga já usada), caiu de 100 a 5% em 90 min (3× mais rápido que a carga real) e ficou em **5% por 86 min**, enquanto a carga real restante ia de 44% a 9%. O erro médio contra a carga real foi de 16,6 pontos (máximo 39). O `udt_battery.sh` lê esse mesmo `capacity`: o LED vermelho acende em `capacity ≤ 20`, que no log foi com ~50% de carga real, e depois não há mais aviso por ~100 min. O desligamento (tensão ≤ 3,40 V e `capacity = 0`, ou ≤ 3,35 V) é correto: todos os ciclos terminam em 3400 mV.

A estimativa sombra por tensão (`bat_pct_est`, curva genérica) já erra 4,9 pontos em média (máximo 16,5), e uma curva monotônica ajustada ao ciclo, com compensação de queda `V + R·I` (R ≈ 0,15 Ω), chega a 0,5 pontos (máximo 5,9), dentro da amostra de um ciclo só. A `diagnostico-bateria` deixou prevista esta change "com o log real em mãos".

## What Changes

- Um serviço de boot calcula o percentual a partir da tensão e da corrente (curva monotônica com compensação de queda, parâmetros num arquivo ajustável) e o publica por `mount --bind` sobre `/sys/class/power_supply/battery/capacity`. O ES, o RetroArch e o `udt_battery.sh` (LED e desligamento) passam a ler o mesmo valor, sem mexer no kernel nem no `udt_battery.sh`.
- Em descarga o valor publicado só cai (com histerese contra a subida quando a carga alivia); com o carregador ligado acompanha o `capacity` do kernel; o desligamento forçado a 3,35 V não depende do `capacity`.
- O valor chega a 0% perto do corte de 3,40 V sob carga, para o desligamento por `capacity ≤ 0` continuar acontecendo.
- Se o bind falhar, o serviço não publica nada e o aparelho segue com o valor do kernel. Uma chave na raiz da p1 (`r36-bateria-original`) desliga a correção.
- O registro térmico passa a gravar o `bat_pct` lido do `uevent` (o kernel de verdade, não o valor publicado), mais o percentual publicado, e ganha a coluna de brilho (`lcdbl`). As colunas `bat_charge_now` e `bat_charge_full` saem: o kernel não as expõe e estão vazias em todas as linhas.
- O retrato do boot lista `/sys/class/axppower` e o `axpdebug` do driver.
- O `tools/analisa_bateria.py` passa a juntar os boots num ciclo, integrar a corrente em mAh e medir o erro do kernel, da estimativa e do valor publicado contra a carga real, além dos patamares (tempo em 100%, tempo em 5%, tensão de entrada e saída de cada um).
- Um `tools/ajusta_curva_bateria.py` gera a curva (resistência de compensação e pontos) a partir de um ciclo do CSV, e um `r36-bateria-curva.conf` na raiz da p1 sobrepõe a curva do `system`, para reajustar com o segundo ciclo sem regravar.
- O README documenta a chave, as colunas e o roteiro de validação com um segundo ciclo.
- **BREAKING**: o cabeçalho do CSV muda (colunas removidas e adicionadas), então o `r36-thermal.csv` atual vira `.1` e o `.1` anterior é apagado: copie os CSVs antes de gravar. Os requisitos "estimativa só para avaliação" e "exibição inalterada" da `battery-diagnostics` deixam de valer.
- Fora do escopo: debounce do desligamento (leituras consecutivas abaixo de 3,40 V), o consumo do menu (23% de CPU ocupada) e contador de coulomb persistente.

## Capabilities

### New Capabilities
- `battery-level`: o percentual de bateria que o aparelho publica e que ES, RetroArch, LED e desligamento leem (cálculo, comportamento em descarga e carga, publicação, falha e chave para voltar ao valor do kernel).

### Modified Capabilities
- `battery-diagnostics`: colunas do CSV (saem as de carga, entra o brilho, `bat_pct` passa a ser o do kernel e entra o publicado), retrato com `axppower`, análise por ciclo com erro contra o coulomb, roteiro de validação; saem "estimativa só para avaliação" e "exibição inalterada".

## Impact

- `features/48-bateria-percentual/` (nova): serviço `r36-bateria`, script de cálculo e publicação, arquivo de parâmetros da curva.
- `features/43-registro-termico/system/usr/lib/r36/thermal-log`: leitura do `bat_pct` pelo `uevent`, colunas novas e removidas, brilho, seção `axppower` do retrato.
- `tools/analisa_bateria.py` e `tests/test_analisa_bateria.py`; `tests/test_registro_termico.py`; testes novos do cálculo e da publicação.
- `README.md`: seção das features 43 e 48.
- Efeito no aparelho: um laço leve (leitura de `/sys` a cada poucos segundos), e o `capacity` visível passa a ser o calculado. Só se confirma o bind sobre o sysfs do kernel 3.4.39 no aparelho; a validação exige um segundo ciclo completo antes de a curva ser considerada final.
