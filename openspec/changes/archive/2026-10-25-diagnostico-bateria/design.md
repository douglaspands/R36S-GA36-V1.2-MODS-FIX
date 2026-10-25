# Design

## Context

O percentual de bateria vem do kernel (driver `axp22`, `/sys/class/power_supply/battery/capacity`) e é lido por três consumidores: o ES, o RetroArch e o `udt_battery.sh` (desligamento por bateria fraca). Os parâmetros do driver ficam no `sys_config` da bootarea, que o projeto não altera. Ver `proposal.md` para a motivação.

O `thermal-log` (feature 43) já escolhe a primeira `power_supply` do tipo `Battery` e grava `bat_status`, `bat_pct` e `bat_voltage`. Ele é `sh` com busybox, lê tudo de `$SYS`/`$PROC` configuráveis (os testes montam uma árvore falsa) e usa `awk` para a ocupação dos núcleos. O retrato do boot usa o helper `si`, que imprime `caminho: valor` com a primeira linha de cada arquivo.

Não há como medir no aparelho agora: o kernel pode não expor `current_now`, `charge_now` ou `charge_full`, e o sinal de `current_now` é desconhecido. O desenho precisa funcionar com qualquer subconjunto disso.

## Goals / Non-Goals

**Goals:**
- Ao fim de uma descarga completa, o CSV e o retrato permitem decidir entre "parâmetros do driver errados" e "célula fraca", e medir o erro do ponto de partida no boot.
- Registrar sem mudar nada do que o usuário vê nem do desempenho.

**Non-Goals:**
- Corrigir o percentual exibido, mexer no `capacity` ou no `udt_battery.sh`.
- Interpretar o sinal de `current_now`: registra-se o valor como o kernel informa.
- Compensar a queda de tensão sob carga na estimativa sombra.

## Decisions

**1. Colunas novas logo depois de `bat_voltage`.** O cabeçalho vira `...,bat_status,bat_pct,bat_voltage,bat_current,bat_charge_now,bat_charge_full,bat_pct_est,system,...`. A rotação forçada por cabeçalho diferente já está no script e na spec (`thermal-control`), então o CSV antigo vira `.1` sozinho. Alternativa: acrescentar no fim da linha; descartada porque quebra o agrupamento das colunas de bateria e não evita a rotação.

**2. Unidades.** `current_now` em µA vira mA, `charge_*` em µAh vira mAh, como `voltage_now` já vira mV. O helper `num` descarta o sinal, então entra um irmão `snum` (aceita `-` inicial). Alternativa: gravar µA cru; descartada para manter a leitura no PC igual à da tensão.

**3. Estimativa sombra com tabela e interpolação no `awk`.** Pontos (mV → %): 3300→0, 3500→4, 3600→12, 3700→30, 3800→50, 3900→65, 4000→78, 4100→90, 4200→100. Antes da curva, a tensão passa por um filtro exponencial inteiro (`f = f + (v - f) / 4`), com o estado numa variável do laço. O estado zera quando o status é `Charging`/`Full` (a coluna fica vazia) e no `--once`, que usa a tensão crua. Fora de 3300–4200 a saída é cortada em 0 e 100.
- Por que tensão pura: é o único dado que existe em qualquer kernel. A corrente, se vier, fica no CSV para a análise corrigir depois no PC.
- Por que a curva fica no script e não num arquivo: é uma hipótese para comparar, não configuração do usuário. Os testes fixam os pontos.
- Alternativa: filtro de mediana. Descartada: exige guardar uma janela em `sh`.

**4. A estimativa só vai para o CSV.** Nada publica `bat_pct_est` em `/sys`, `/run` ou arquivo lido pelo ES. Isso mantém a spec "exibição inalterada" verdadeira por construção e evita testar `mount --bind` sobre o sysfs sem o aparelho.

**5. Retrato: `uevent` completo e `axp` do `dmesg`.** Na seção `== bateria ==`, cada linha do `uevent` de cada `power_supply` sai como `caminho/uevent: CHAVE=valor`. Depois vêm as últimas 80 linhas de `dmesg | grep -i axp`, cada uma prefixada por `dmesg:`. Ausência vira `(ausente)`, como o resto do retrato. O retrato já é gravado uma vez por boot no primeiro ciclo, então ele também registra o ponto de partida do boot (percentual e tensão do primeiro instante). Alternativa: uma linha separada no CSV no boot; descartada porque o primeiro registro do CSV e o retrato já dão o mesmo dado.

**6. Análise no PC.** `tools/analisa_bateria.py`, só biblioteca padrão, rodado com `uv run python -I tools/analisa_bateria.py <csv...>`. Agrupa por `boot`, ignora linhas em carga para a taxa de queda, e imprime por boot: tensão e percentuais (kernel e estimado) nas primeiras amostras, e queda do kernel e do estimado por hora. Colunas ausentes são avisadas, não são erro. Fica em `tools/` e não no pacote `r36img`, porque não toca no cartão.

## Risks / Trade-offs

- [O driver não imprime os números `OCV_percentage`/`Coulumb_percentage` no `dmesg`] → O `uevent` e `charge_full_design` ainda mostram a capacidade que o driver assume; a tensão e a corrente do CSV bastam para ajustar uma curva no PC.
- [O kernel não expõe `current_now`/`charge_*`] → Campos vazios; a decisão H1 × H2 cai na comparação tensão × tempo do CSV, que já existe.
- [A curva genérica não casa com a célula] → É esperado e o objetivo é medir o desvio. Por isso o `bat_pct` do kernel e o `bat_pct_est` vão lado a lado e nada exibido muda.
- [Queda de tensão sob carga deixa a estimativa baixa em jogo] → A análise compara também linhas de menu (carga leve); o filtro de 4 amostras suaviza picos curtos, não o nível sustentado.
- [Cabeçalho novo move o CSV antigo para `.1` e apaga o `.1` anterior] → Aviso no README e na proposal: copiar os CSVs antes de gravar.
- [Mais ~25 bytes por linha] → A rotação em 1 MB mantém o teto de 2 MB; uma descarga de várias horas continua cabendo nos dois arquivos.
- [`dmesg` custa pouco, mas roda no boot] → Só uma vez por boot, dentro do retrato, que já tem de passar pelo `can_write`.
