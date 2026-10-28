# Design

## Context

O percentual vem do `capacity` do driver `axp22`, lido por três consumidores: o ES (sysfs, genérico), o RetroArch (sysfs) e o `udt_battery.sh` (SYSTEM, `bash`, a cada 10 s). Esse último decide o LED (`capacity ≤ 20` acende o vermelho) e o desligamento (`V ≤ 3400000` e `capacity ≤ 0`, ou `V ≤ 3350000` sozinho, numa leitura instantânea). O fonte do kernel e o `sys_config` da bootarea não são alteráveis (CLAUDE.md), então o `capacity` só muda por sobreposição em userspace. Ver `proposal.md` (Why) para os números do ciclo de 26/10.

Fatos do aparelho que moldam o desenho:
- O kernel 3.4.39 não tem overlayfs, mas o projeto já usa `mount -o bind` (shaders). Bind de **arquivo** sobre um atributo do sysfs nunca foi testado aqui.
- `/sys/class/power_supply/battery` é um link simbólico; o bind precisa do caminho resolvido (`readlink -f`), que é o que aparece em `/proc/mounts`.
- O `uevent` do driver é gerado pelo kernel e não sofre a sobreposição: continua devolvendo o `POWER_SUPPLY_CAPACITY` de verdade.
- `current_now` vem positivo em descarga (+470 mA em repouso no menu). Não há RTC: só `uptime_s` ordena as amostras.
- Um serviço com `After=emuelec-autostart.service` e `Before=emustation.service` trava o boot. Os serviços `r36-audio` e `r36-shader-gba-prepara` já resolvem isso com `Before=emustation.service` sem o `After`.

## Goals / Non-Goals

**Goals:**
- O `capacity` lido por qualquer processo passa a vir de uma curva de tensão com compensação de queda, com erro médio na casa de poucos pontos e sem os patamares de 100% e 5%.
- Falha ou chave na p1 devolvem o comportamento de fábrica, sem afetar o boot nem o desligamento de segurança.
- Ajustar a curva só com o cartão: um arquivo na p1 sobrepõe a curva do SYSTEM, e uma ferramenta no PC gera esse arquivo a partir do CSV.

**Non-Goals:**
- Persistir estado entre boots (contador de coulomb, último valor): o primeiro valor de cada boot vem da curva.
- Mudar o `udt_battery.sh`, o corte de 3,40/3,35 V ou o debounce do desligamento.
- Tratar o percentual durante a carga além de seguir o kernel.

## Decisions

**1. Uma feature nova, `48-bateria-percentual`, e o registro (43) só lê.** A feature traz `/usr/lib/r36/bateria-percentual` (script `sh`), `/usr/lib/r36/bateria-curva.conf` (parâmetros) e `r36-bateria.service`. O `thermal-log` não depende dela: lê `capacity` (publicado) e o `uevent` (kernel). Alternativa: dentro da 43; descartada porque a 43 só mede e é desligável sem efeito no aparelho.

**2. Publicar por bind de arquivo em `/run/r36-bateria/capacity` sobre o `capacity` resolvido.** O script escreve o valor (`printf '%s\n'`) **no mesmo arquivo, sem `mv`** (o bind prende o inode), e consome o `mount -o bind` uma vez. Depois do bind lê `capacity` e confere que devolve o valor escrito; se não, desmonta e registra o motivo. Como o aparelho só se alcança pelo cartão, o registro vai para `r36-bateria.log` na raiz da p1 (sobrescrito a cada boot, gravado quando `/storage/roms` monta, como o `r36-shader-gba.log`): resultado do bind, curva usada (SYSTEM ou cartão) e, se houve, o motivo da falha ou da curva recusada. Alternativas: `LD_PRELOAD`/wrapper do `cat` (frágil, não vale para o ES e o RetroArch, que são binários), regravar o `udt_battery.sh` (não cobriria ES e RetroArch), módulo de kernel (sem fonte). O bind é a única via que cobre os três.

**3. Ordem: publicar antes do ES, sem `After=emuelec-autostart`.** `Type=simple`, `Before=emustation.service`, `WantedBy=emuelec.target`. O primeiro valor e o bind saem num `ExecStartPre` (que termina antes de o serviço contar como iniciado, logo antes do ES), e o laço fica no `ExecStart`. `ExecStopPost` desmonta o bind, o que devolve o `capacity` do kernel quando o serviço para ou falha. `Restart=always` religa; o `ExecStartPre` desmonta qualquer bind anterior antes de montar, para não empilhar.

**4. A chave `r36-bateria-original` na p1 é lida pelo laço, não pelo `ExecStartPre`.** A p1 só monta depois do `mount_romfs.sh`, que roda dentro do autostart (que a ordem acima não pode esperar). O serviço publica já no início e, na primeira vez que `/storage/roms` é ponto de montagem, procura a chave e o arquivo de curva do cartão: com a chave, desmonta o bind e encerra (`exit 0`, sem `Restart`); com um `r36-bateria-curva.conf`, recarrega a curva dele. O custo é o ES poder ler o valor publicado com a curva do SYSTEM nos primeiros segundos. Alternativa: esperar a p1 antes de publicar (como o `audio-prepara`); descartada porque o ES leria o valor do kernel nesse intervalo, justamente o valor ruim.

**5. Cálculo em `awk`, a cada 5 s.** Entradas: `voltage_now` (µV), `current_now` (µA) e `status`, lidos do `uevent` (que também dá o `POWER_SUPPLY_CAPACITY` do kernel). Passos:
1. `vc = mV + R * mA / 1000` (R em mΩ, `150` de partida; corrente ausente vale 0).
2. Filtro `f = f + (vc - f) / 4`, reiniciado quando o status é `Charging`/`Full` ou na primeira amostra do boot.
3. Interpolação linear na tabela monotônica de `bateria-curva.conf` (`ponto=mV,pct`, ordenada por mV; fora da faixa corta em 0 e 100).
4. Piso de segurança sobre a tensão **lida**: `V ≤ 3450` força 0, e `V ≥ 3500` força pelo menos 1.
5. Em descarga, `pub = min(pub_anterior, calculado)`; na primeira amostra, `pub = calculado`.
6. Em `Charging`/`Full`, `pub` = `POWER_SUPPLY_CAPACITY` do kernel e `pub_anterior` é descartado.

Os pontos do `bateria-curva.conf` saem do ajuste isotônico (PAV) do ciclo de 26/10 com R = 150 mΩ (MAE 0,5, máx 5,9 dentro da amostra), reduzido a ~12 pontos. O piso do passo 4 existe porque o corte do `udt_battery.sh` exige `capacity = 0` junto com `V ≤ 3400`: sem ele, o valor sobre a curva a 3400 mV/850 mA seria ~2% e o aparelho só desligaria pelo corte forçado de 3350 mV. Alternativa à compensação `V + R·I`: tabela bidimensional (tensão × corrente); descartada por exigir mais ciclos para calibrar.

**6. Parâmetros num arquivo `key=value` + `ponto=mV,pct`, com sobreposição pelo cartão.** Chaves: `r_mohm`, `filtro`, `v_zero`, `v_um`. A curva do SYSTEM é a padrão; `r36-bateria-curva.conf` na raiz da p1, se existir e passar numa checagem (pontos crescentes em mV e em pct, ao menos 2), a sobrepõe; senão o serviço registra e usa a do SYSTEM. Por quê: o aparelho só se alcança pelo cartão, e testar uma curva nova não deve exigir regravar o `system`.

**7. `tools/ajusta_curva_bateria.py` gera a curva a partir do CSV.** Reaproveita o cálculo de ciclo e a integração em mAh de `analisa_bateria.py`, ajusta a curva isotônica sobre `V + R·I` para uma grade de R, escolhe o R de menor erro, reduz a ~12 pontos e escreve o `.conf`. É o instrumento do segundo ciclo (que reduz a dependência de uma amostra só). Só biblioteca padrão, sem `numpy`.

**8. `analisa_bateria.py` por ciclo.** Junta os boots; integra `bat_current` em mAh por `Δuptime_s` dentro de cada boot (descarta `Δ` > 60 s, que é lacuna, e amostras fora de `Discharging`); a carga restante de referência é `100 × (1 − mAh / total)`, válida quando o ciclo termina em desligamento (aviso se o último boot não chega a ≤ 3450 mV). Mede o erro de `bat_pct` e `bat_pct_pub` e os patamares do kernel (primeiro e último instante em que o valor é igual a 100 ou a 5, em minutos, mAh e mV). Separa ciclos por `Charging`/`Full` ou por boot que começa mais de 150 mV acima do fim do anterior; `--desde <boot>` escolhe um ciclo. Substitui o resumo por boot.

**9. Colunas do CSV.** `…,bat_status,bat_pct,bat_voltage,bat_current,bat_pct_pub,lcdbl,system,…`. `bat_pct` vem de `POWER_SUPPLY_CAPACITY` do `uevent`; `bat_pct_pub` de `capacity`; `lcdbl` de `/sys/devices/virtual/disp/disp/attr/lcdbl` (a escrita já é usada pelo `udt_pwr_events.sh`; se não for legível, a coluna fica vazia, que já é o comportamento de campo ilegível). Saem `bat_charge_now`, `bat_charge_full` e `bat_pct_est` (e a função `pct_est` e o filtro `BATF` do script). O cabeçalho novo rotaciona o CSV antigo para `.1` pelo mecanismo existente (spec `thermal-control`).

**10. Retrato: `/sys/class/axppower`.** A seção `== bateria ==` ganha `si` para cada arquivo regular legível do diretório (inclusive `axpdebug`), com `(ausente)` se o diretório não existe. Só leitura, uma vez por boot.

## Risks / Trade-offs

- [O bind sobre o sysfs pode não pegar no 3.4.39] → A conferência pós-bind (ler de volta) detecta; falhando, o serviço desmonta e o aparelho fica com o valor do kernel. A tarefa de validação no aparelho é obrigatória antes de considerar a change pronta.
- [A curva sai de um ciclo só] → O erro de 0,5 é dentro da amostra. A sobreposição pela p1 e o `ajusta_curva_bateria.py` permitem reajustar com o segundo ciclo sem regravar o `system`; o README fixa o erro do `bat_pct_pub` como critério.
- [`min(pub_anterior, calculado)` trava num valor baixo após um afundamento de tensão] → A compensação por corrente e o filtro de 4 amostras reduzem os picos; o erro típico de subestimar no topo (até ~16 pontos na genérica) é o que a validação mede. Aceita-se não subir, como pedido na spec.
- [Reboot em meio à descarga reinicia a referência pela curva] → O valor pode subir alguns pontos entre boots; sem persistência (Non-Goal).
- [Percentual durante a carga segue o kernel, que marcou 0% a 3654 mV] → Visível, mas já era assim; o CSV agora registra carga e tensão para tratar numa change própria se incomodar.
- [Reader pode ler o valor do kernel nos primeiros segundos, antes do bind] → O `ExecStartPre` publica antes de o ES iniciar; o `udt_battery.sh` já tem `Before=emuelec.target` e pode ler o valor do kernel por até alguns segundos, o que não afeta o desligamento (exige `V ≤ 3400000` também).
- [Leitura de atributos do `axppower` pode ser lenta ou ter efeito colateral] → Só os arquivos regulares legíveis, uma vez por boot, dentro de `can_write`; qualquer falha vira `(ausente)`.
- [Mais um serviço consumindo CPU] → Um `awk` e algumas leituras de `/sys` a cada 5 s, `Nice=19`.

## Migration Plan

1. Implementar e testar no PC com árvore falsa (`R36_SYS`, `R36_ROOT`), incluindo o piso, a descida monotônica e a chave.
2. Gravar o `system` novo e, no aparelho, confirmar que `cat /sys/class/power_supply/battery/capacity` bate com o `bat_pct_pub` do CSV e que o `bat_pct` do CSV continua o do kernel.
3. Fazer um segundo ciclo completo com a correção ligada; rodar `analisa_bateria.py`; reajustar a curva pelo cartão se o erro médio passar de ~5 pontos.
4. Reversão: `r36-bateria-original` na raiz da p1 (sem regravar) ou `enabled = false` em `features/48-bateria-percentual/feature.toml` e gerar de novo.

## Open Questions

- O carregador reporta `Full`? Só há uma amostra em `Charging` no log. O desenho trata `Charging` e `Full` do mesmo jeito, então a resposta não muda spec nem tarefas.
