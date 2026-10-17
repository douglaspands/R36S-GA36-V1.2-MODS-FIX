# Spec Delta

## MODIFIED Requirements

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

### Requirement: Afinamento desligável
O afinamento do ondemand SHALL fazer parte de uma feature própria, que pode ser desligada sem afetar as demais, incluindo o serviço que o reaplica depois do boot.

#### Scenario: Feature desligada
- **WHEN** a imagem é gerada com a feature do afinamento desligada
- **THEN** o ondemand roda com os tunables da imagem base, não existe o serviço de reaplicação, e a abertura de jogos não falha por causa da ausência do afinamento
