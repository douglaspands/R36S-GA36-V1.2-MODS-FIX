# Proposal

## Why

A change anterior (`maxperf-desligado-por-padrao`) gravou `global.maxperf=0` na imagem, mas o log do aparelho (`r36-thermal.csv`) mostra `governor=performance` em todas as 296 linhas de jogo (GBA, SNES, CPS2, N64), com a chave `0` no cartão. O motivo está no código da imagem base: o `emuelecRunEmu.sh` chama `maxperf` na linha 8, antes de ler qualquer configuração, e o bloco que consultaria a chave (linhas 475 a 484) está comentado. Assim a opção "Enable max performance" do menu do ES não faz nada, e o README da feature 10 descreve um comportamento que não existe. O mesmo log também mostrou dois defeitos do registro térmico que impedem medir o efeito: a ocupação por núcleo sai vazia e a cena da DRAM também.

## What Changes

- Nova camada `system/` na feature `10-ptbr-sao-paulo` com uma cópia do `emuelecRunEmu.sh` da imagem base, alterada em dois pontos: a chamada incondicional `maxperf` da linha 8 é removida e, depois de `PLATFORM` e `ROMNAME` estarem definidos, o script lê `maxperf` (jogo, sistema e global, na ordem do `get_ee_setting`) e chama `maxperf` quando o valor é `1` e `normperf` nos demais casos. O `normperf` do fim do script continua como está.
- O `thermal-log` (feature `43-registro-termico`) passa a gravar a ocupação de `cpu0` a `cpu3`, e a achar a cena da DRAM também em `devfreq/sunxi-ddrfreq/dsm/scene`, que é onde o `maxperf` escreve.
- Testes novos: o `emuelecRunEmu.sh` da imagem respeita a chave e só difere da base nos pontos esperados; o `thermal-log` grava 18 campos por linha e acha a DRAM no caminho com `devfreq`.
- O README da feature 10 passa a ser verdadeiro e a descrever o mecanismo; o da feature 43 deixa de dizer que não mexe no governor, porque a feature 10 passa a mexer.
- Fora do escopo: tetos de clock por sistema, o `emuelec_autostart.sh`, e qualquer ajuste de cartão já gravado (só imagem nova ou regravada recebe o script).

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `thermal-control`: ganha dois requisitos novos (o início de cada jogo respeita a chave de máximo desempenho; o log traz de fato a ocupação por núcleo e a cena da DRAM). Os requisitos existentes não mudam: o código é que não os cumpre hoje.

## Impact

- `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh` (novo, derivado do script da imagem base, GPL-2.0-or-later).
- `features/43-registro-termico/system/usr/lib/r36/thermal-log`.
- `tests/test_ptbr_controle.py`, `tests/test_registro_termico.py`, `README.md`.
- Pela primeira vez uma feature sobrescreve um script do sistema; a cópia precisa ser conferida contra a base a cada troca de imagem base.
- Efeito no aparelho: com `maxperf=0`, os jogos passam a rodar em `ondemand`, esquentam menos e rendem menos nos sistemas pesados até o usuário ligar a opção neles.
