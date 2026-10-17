# cpu-frequency-scaling Specification

## Purpose

Definir como o governor ondemand da CPU é afinado na imagem, para que o clock suba cedo e não caia no meio do jogo, evitando travadas, queda de FPS e som picotado sem ligar o máximo desempenho.

## Requirements

### Requirement: Ondemand sobe cedo e desce devagar
Com o governor `ondemand` ativo, o sistema SHALL usar `up_threshold` 30 e `sampling_down_factor` 10 nos tunables do ondemand, também depois que o boot do EmulationStation termina e o governor volta para `ondemand`.

#### Scenario: Após o boot
- **WHEN** o aparelho termina de ligar com o governor `ondemand`
- **THEN** `up_threshold` vale 30 e `sampling_down_factor` vale 10 nos tunables do ondemand

#### Scenario: Governor trocado durante o boot
- **WHEN** o script de autostart passa o governor por `performance` e depois o devolve a `ondemand`
- **THEN** o afinamento é reaplicado depois dessa troca, e o retrato do sistema do boot mostra `up_threshold` 30 e `sampling_down_factor` 10

### Requirement: Piso de frequência da CPU
A frequência mínima da CPU SHALL ser 600 MHz enquanto o governor for `ondemand`, tanto no menu quanto em jogo, desde o fim do boot.

#### Scenario: Jogo em modo normal
- **WHEN** um jogo roda com o máximo desempenho desligado
- **THEN** nenhuma linha do registro térmico desse jogo traz `cpu_mhz` abaixo de 600

#### Scenario: Menu parado
- **WHEN** o aparelho fica parado no menu do EmulationStation
- **THEN** o `scaling_min_freq` da CPU vale 600000 kHz, o governor continua `ondemand`, e as linhas do registro térmico no menu não trazem `cpu_mhz` abaixo de 600

### Requirement: Afinamento sobrevive à troca de modo
Depois que um jogo é aberto e fechado, com o máximo desempenho ligado ou desligado, o sistema SHALL manter o governor `ondemand` e os mesmos valores de `up_threshold`, `sampling_down_factor` e frequência mínima do boot.

#### Scenario: Jogo com máximo desempenho
- **WHEN** o usuário abre e fecha um jogo com o máximo desempenho ligado
- **THEN** de volta ao menu o governor é `ondemand`, `up_threshold` vale 30, `sampling_down_factor` vale 10 e a frequência mínima vale 600 MHz

#### Scenario: Jogo sem máximo desempenho
- **WHEN** o usuário abre e fecha um jogo com o máximo desempenho desligado
- **THEN** os valores de `up_threshold`, `sampling_down_factor` e frequência mínima continuam os do boot

### Requirement: Máximo desempenho não é afetado
O afinamento do ondemand SHALL NOT alterar o modo de máximo desempenho: com a chave ligada, o governor em jogo continua `performance`, a cena da DRAM `0` e o clock em 1200 MHz.

#### Scenario: Sistema com a opção ligada
- **WHEN** o usuário liga o máximo desempenho para um sistema e abre um jogo dele
- **THEN** o registro térmico mostra `performance`, `cpu_mhz` 1200 e `dram_scene` 0 nas linhas desse jogo

### Requirement: Afinamento desligável
O afinamento do ondemand SHALL fazer parte de uma feature própria, que pode ser desligada sem afetar as demais, incluindo o serviço que o reaplica depois do boot.

#### Scenario: Feature desligada
- **WHEN** a imagem é gerada com a feature do afinamento desligada
- **THEN** o ondemand roda com os tunables da imagem base, não existe o serviço de reaplicação, e a abertura de jogos não falha por causa da ausência do afinamento

#### Scenario: DRAM com a feature desligada
- **WHEN** a imagem é gerada com a feature do afinamento desligada e um jogo roda com o máximo desempenho desligado
- **THEN** a DRAM fica na cena `1`, como na imagem base

### Requirement: DRAM na cena 0 com jogo aberto
Com o máximo desempenho desligado, o sistema SHALL pôr a DRAM na cena `0` enquanto um jogo estiver aberto, mantendo o governor `ondemand` e o afinamento, e SHALL devolvê-la à cena `1` ao voltar ao menu.

#### Scenario: Jogo em modo normal
- **WHEN** um jogo roda com o máximo desempenho desligado
- **THEN** as linhas do registro térmico desse jogo trazem governor `ondemand` e `dram_scene` 0

#### Scenario: Volta ao menu
- **WHEN** o usuário fecha o jogo e volta ao EmulationStation
- **THEN** as linhas seguintes do registro térmico trazem governor `ondemand` e `dram_scene` 1

#### Scenario: Boot
- **WHEN** o aparelho termina de ligar, antes de qualquer jogo
- **THEN** a cena da DRAM é a da imagem base, e o afinamento do boot não a altera
