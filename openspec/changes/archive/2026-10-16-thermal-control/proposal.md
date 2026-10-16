# Proposal

## Why

O R36S esquenta demais durante o jogo. O `emuelecRunEmu.sh` chama `maxperf` em todo jogo: governor `performance` com os 4 núcleos a 1,2 GHz e 1,32 V, e DRAM fixa em 552 MHz, até em NES ou Game Boy. O kernel só reduz o clock aos 90 °C. A saída óbvia, o governor `ondemand`, já foi testada e descartada: o Mario Kart do GBA (mGBA) mudava de desempenho a cada curva, porque o governor seguia a carga sempre atrasado. A alternativa, um teto de clock fixo por sistema e core, depende de números que não temos: quanto cada sistema esquenta e quanto clock cada core realmente usa. Este change só mede. Os tetos ficam para uma spec futura, baseada no log.

## What Changes

- Feature nova `43-registro-termico`: um serviço systemd que, a cada 5 s, grava uma linha num CSV com temperatura, clock, governor, ocupação de cada núcleo da CPU, cena da DRAM, estado da bateria e o sistema, emulador, core e jogo em execução. Não usa cron, que continua desligado pela feature 41.
- O log fica em `/storage/roms/r36-thermal.csv`, na partição FAT32, para ser lido direto no PC. É um arquivo só, para preservar a linha do tempo (o calor de um jogo pesado continua no jogo seguinte).
- O log nunca estoura o cartão: rotação para `r36-thermal.1.csv` ao passar de 1 MB (no máximo 2 MB no total), e nada é gravado com menos de 64 MB livres na partição de ROMs.
- Nada muda no clock, no governor ou no `maxperf`. O aparelho continua se comportando como hoje, só que medido.
- A feature pode ser desligada (`enabled = false`) quando a medição acabar.

## Capabilities

### New Capabilities
- `thermal-control`: comportamento térmico do aparelho. Neste change, o registro de temperatura, clock e carga durante o uso. Mais tarde, os tetos de clock definidos a partir desse registro.

### Modified Capabilities
(nenhuma)

## Impact

- Novo diretório `features/43-registro-termico/`: script em `system/usr/lib/r36/`, unit `r36-thermal-log.service` e o link de ativação.
- ROMs (p1): os arquivos `r36-thermal.csv` e `r36-thermal.1.csv` aparecem no uso, com 2 MB no máximo.
- Nenhuma mudança em `tools/r36img/`, no `emuelecRunEmu.sh`, no `script.bin` (bootarea), no kernel ou no initramfs.
- README: como ler o log e como desligar a feature.
- Fora do escopo: tetos de clock por `sistema:core`, vigia térmico, troca de core padrão (gpSP no GBA, snes9x2005_plus no SNES, picodrive no Mega Drive) e qualquer mudança no `script.bin`.
