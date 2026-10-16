# Design

## Context

Veja `proposal.md` para a motivação. Estado atual, conferido no SYSTEM da imagem `20261016-150632`:

- `/usr/bin/cpufreq` (rodado no boot pelo `cpufreq.service`) só faz `up_threshold=50` no ondemand. Não mexe em `sampling_down_factor`, `sampling_rate` nem no piso de frequência.
- `maxperf()` e `normperf()` ficam em `/etc/profile.d/99-emuelec.conf`. No A33, `maxperf` escreve `performance` no governor e `0` na cena da DRAM; `normperf` escreve `ondemand` e `1`.
- O `emuelecRunEmu.sh` (feature `10-ptbr-sao-paulo`) chama `maxperf` ou `normperf` ao abrir o jogo, conforme a chave `maxperf`, e chama `normperf` de novo ao sair.
- O CPS2 vem de fábrica com `<core default="true">fbneo</core>` no `es_systems.cfg`. O padrão por sistema é sobrescrito no `emuelec.conf` da feature 10, como já é feito com `gba.core=gpsp`.

## Goals / Non-Goals

**Goals:**
- Tirar o clock de 240 a 408 MHz em jogo e subir rápido na rajada, sem ligar o máximo desempenho.
- Manter o afinamento depois de qualquer abertura e fechamento de jogo.
- Fixar o `fbalpha2012` como padrão do CPS2.

**Non-Goals:**
- Não trocar de governor nem criar um modo novo por sistema.
- Não mexer na cena da DRAM, no GPU nem em outros sistemas de arcade.
- Não ligar o máximo desempenho por padrão (decisão da change `maxperf-desligado-por-padrao` continua valendo).

## Decisions

**1. Feature nova `44-cpu-ondemand`, em vez de editar o `cpufreq` dentro da feature 10.**
A feature 10 é de localização e telas. Uma feature própria é desligável (requisito da spec) e fica no estilo de `40-zram-swap` e `43-registro-termico`. Alternativa descartada: pôr tudo na 10, o que mistura responsabilidades e impede desligar o afinamento sozinho. A ordem 44 só precisa ser única; não há dependência entre as features.

**2. Um script único `/usr/lib/r36/cpu-ondemand-tune`, chamado em dois pontos.**
Ele escreve `up_threshold`, `sampling_down_factor` e `scaling_min_freq`, e só age se o governor atual for `ondemand`. É chamado (a) pelo `/usr/bin/cpufreq` substituído, depois do `up_threshold=50` original, e (b) pelo `emuelecRunEmu.sh` logo após cada `normperf`, protegido por `[ -x ... ]` para não falhar com a feature desligada.
Motivo do (b): no kernel 4.9 do A33, trocar de `performance` para `ondemand` reinicializa o governor e os tunables voltam ao padrão do kernel (`up_threshold` 80, `sampling_down_factor` 1). Sem reaplicar, o afinamento sumiria na primeira vez que o usuário ligasse o máximo desempenho. Escrever `ondemand` com o ondemand já ativo não reinicializa nada, então o (b) é inofensivo no caminho comum.
Alternativas descartadas: um serviço systemd que reaplica periodicamente (consumo e latência sem necessidade) e editar o `profile.d/99-emuelec.conf` (arquivo da base grande, difícil de manter na substituição).

**3. Valores iniciais: `up_threshold` 30, `sampling_down_factor` 10, piso 600 MHz.**
Vêm do log: os degraus vistos são 240, 312, 408, 504, 600, 648, 1008, 1104 e 1200 MHz; um piso de 600 MHz corta os clocks de 240 a 504 MHz que apareceram em jogo, e o menu continua podendo variar de 600 a 1200 MHz. A spec fixa esses números porque é o que se testa no aparelho; ajuste fino é uma nova rodada da mesma change.
O piso de 600 MHz fica gravado em `scaling_min_freq` e persiste na troca de governor.
**4. CPS2 no `emuelec.conf` da feature 10.**
Duas linhas junto das de GBA (`cps2.emulator=libretro`, `cps2.core=fbalpha2012`). Alternativa descartada: alterar o `es_systems.cfg` da base, que obrigaria a substituir um arquivo grande e fora do padrão já usado.

**5. Imagem gerada com `--test`.**
O usuário pediu a imagem de teste. O conteúdo é o mesmo do build normal; muda só o sufixo `-test`. A ordem é: implementar, rodar os testes, gerar `./build.sh --test`.

## Risks / Trade-offs

- [O A/B do log mistura dois fatores: o modo performance muda o clock **e** a cena da DRAM (`0` contra `1`)] → O afinamento ataca só o clock. Se o resultado ainda for ruim, o próximo experimento é manter a cena `0` também no modo normal (change à parte), medida com o mesmo CSV.
- [Piso de 600 MHz e `sampling_down_factor` 10 aumentam consumo e temperatura] → A temperatura nunca passou de 55 °C no log. O consumo é medido na prática; a leitura da bateria no log estava travada em 5%, então não dá para medir por ali.
- [Os valores 30 / 10 / 600 podem não ser os ideais] → São chute fundamentado; o log novo mostra `%<1000MHz`, o desvio de clock e o piso observado, e o ajuste vira nova rodada.
- [O nome e o caminho dos tunables podem diferir do esperado (global em `cpufreq/ondemand` ou por `policy*`)] → O script segue o mesmo laço do `cpufreq` original, que cobre os dois, e ignora o que não existe.
- [A opção `--test` do build está só na branch `build-flag-test`, com mudanças ainda não commitadas nem mergeadas] → Antes de começar, resolver a base da nova branch (ver Open Questions).

## Migration Plan

Sem migração: a próxima imagem traz tudo. Reverter é desligar `44-cpu-ondemand` e remover as duas linhas do CPS2. Cartões já gravados não mudam até receberem a imagem nova.

## Open Questions

- A branch da change precisa sair da `main` (regra do projeto), mas o `--test` ainda está em `build-flag-test`. Mergear/commitar `build-flag-test` antes de começar, ou aplicar esta change em cima dela? Isso não muda as specs nem as tarefas, só o ponto de partida.
- `scaling_available_governors` e `sampling_rate` reais do aparelho: se existir `conservative` ou `schedutil`, reavaliar o governor numa change futura.
