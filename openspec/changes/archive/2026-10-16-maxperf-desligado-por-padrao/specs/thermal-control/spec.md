# Spec Delta

## ADDED Requirements

### Requirement: Máximo desempenho desligado por padrão
A imagem SHALL sair com a opção "Enable max performance" desligada para todos os sistemas e jogos, e SHALL manter a opção ligável por sistema ou por jogo no menu do EmulationStation.

#### Scenario: Imagem recém-gravada
- **WHEN** a imagem é gravada em um cartão novo e o aparelho liga
- **THEN** a configuração global do máximo desempenho está desligada, e nenhum sistema ou jogo tem a opção ligada

#### Scenario: Jogo sem ajuste próprio
- **WHEN** um jogo de um sistema sem ajuste de máximo desempenho é aberto
- **THEN** o aparelho esquenta menos do que com a opção ligada, e o governor e a cena da DRAM registrados no log seguem o modo normal (`ondemand` e cena `1`)

#### Scenario: Ligar onde for preciso
- **WHEN** o usuário liga o máximo desempenho para um sistema ou jogo pelo menu do EmulationStation
- **THEN** o ajuste vale só para esse sistema ou jogo, e os demais continuam com a opção desligada

### Requirement: Ajustes de teste fora da imagem
A imagem SHALL NOT trazer ajustes de máximo desempenho por sistema ou por jogo; só o ajuste global desligado.

#### Scenario: Conteúdo da configuração
- **WHEN** a configuração do EmuELEC da imagem é inspecionada
- **THEN** a única chave de máximo desempenho é a global, com o valor desligado
