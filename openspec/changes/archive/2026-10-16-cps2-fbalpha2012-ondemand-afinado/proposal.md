# Proposal

## Why

O registro térmico de 13/05 (231 amostras, GBA, PSX, CPS2, SNES e FBNeo, cada jogo em ondemand e depois em performance) mostra que, em jogo, o ondemand fica abaixo de 1000 MHz em 27 a 67% das amostras e chega a 240 MHz com o jogo rodando. A carga média por núcleo é baixa (35 a 46%), mas vem em rajadas de 60 a 100%. O clock baixo no quadro pesado explica o que o usuário sentiu em todos os emuladores: travadas, FPS abaixo do normal e som picotado. A temperatura nunca passou de 55 °C, então o ondemand atual economiza pouco e custa jogabilidade. Além disso, o CPS2 abre por padrão no `fbneo`, e o usuário prefere o `fbalpha2012`, que ele já escolheu à mão e rodou bem.

## What Changes

- O CPS2 passa a abrir por padrão no core `fbalpha2012` do RetroArch, declarado em `emuelec.conf` no mesmo molde do `gba.core=gpsp`. CPS1, Neo Geo e demais sistemas de arcade continuam como estão, e o `fbneo` segue selecionável no menu do CPS2.
- O ondemand passa a ser afinado para subir cedo e descer devagar: `up_threshold` menor, `sampling_down_factor` maior e um piso de frequência (`scaling_min_freq`) acima dos 240 a 408 MHz observados.
- O afinamento vale também depois de qualquer ida e volta pelo modo de máximo desempenho, porque o `normperf` regrava o governor e pode devolver os tunables aos valores de fábrica.
- O máximo desempenho continua desligado por padrão e ligável por sistema ou por jogo no menu. O que muda é o ondemand que roda quando ele está desligado.
- A imagem desta change é gerada com `./build.sh --test` (imagem de teste, sufixo `-test`), para o usuário validar no aparelho antes de uma imagem definitiva.

## Capabilities

### New Capabilities
- `cps2-emulation`: qual emulador e core o Capcom Play System 2 usa por padrão na imagem, sem remover as alternativas.
- `cpu-frequency-scaling`: como o governor ondemand da CPU é afinado na imagem, para o clock não cair no meio do jogo, e como esse ajuste sobrevive à troca de modo de desempenho.

### Modified Capabilities
<!-- Nenhuma. thermal-control continua válido: sem máximo desempenho, governor `ondemand` e cena `1`. -->

## Impact

- `features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf`: linhas `cps2.emulator` e `cps2.core`.
- Nova feature em `features/` (proposta: `44-cpu-ondemand`) com um script de afinamento em `system/usr/lib/r36/`, um `/usr/bin/cpufreq` que o chama no boot, e `feature.toml`. Desligável sem afetar as demais.
- `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`: chamar o script de afinamento logo após `normperf`, se o script existir.
- Testes em `tests/` no estilo dos de GBA e de registro térmico, e README.
- Sem mudança nas partições de ROMs, no boot ou no kernel. Depende de a opção `--test` do build estar disponível na branch de trabalho (ver design).
