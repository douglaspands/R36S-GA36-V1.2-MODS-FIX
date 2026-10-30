# Spec Delta

## MODIFIED Requirements

### Requirement: Volume guardado em arquivo próprio
O volume SHALL ser guardado também num arquivo próprio da feature (`r36-audio.volume`, na p8), que vale mais que o `audio.volume` do `emuelec.conf` na leitura. O sistema SHALL manter `audio.volume` no `emuelec.conf` sincronizado em tempo real pelos botões de volume e SHALL reaplicar o valor de `r36-audio.volume` no `emuelec.conf` durante o encerramento do sistema (shutdown/reboot), impedindo que a sobrescrita de memória do EmulationStation reverta o volume salvo. Sem nenhum dos dois, vale o padrão 29.

#### Scenario: Reiniciar pelo menu do EmulationStation
- **WHEN** o usuário baixa o volume pelos botões e reinicia o aparelho pelo menu do EmulationStation
- **THEN** no boot seguinte e no encerramento, o `emuelec.conf` e o `speaker volume control` preservam e refletem o volume real deixado pelo usuário

#### Scenario: Ajuste em tempo real pelos botões
- **WHEN** o usuário aperta os botões de volume
- **THEN** `r36-audio.volume` e `audio.volume` em `emuelec.conf` são atualizados imediatamente com o novo valor
