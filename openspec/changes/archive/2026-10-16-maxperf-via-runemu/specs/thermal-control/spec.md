# Spec Delta

## ADDED Requirements

### Requirement: Início do jogo respeita a chave de máximo desempenho
Ao abrir um jogo, o sistema SHALL ligar o modo de máximo desempenho (governor `performance` e cena da DRAM `0`) apenas quando a chave de máximo desempenho do jogo, do sistema ou global, nessa ordem de precedência, tiver o valor `1`; nos demais casos SHALL usar o modo normal (`ondemand` e cena `1`).

#### Scenario: Imagem recém-gravada
- **WHEN** um jogo de qualquer sistema é aberto numa imagem recém-gravada
- **THEN** o governor registrado nas linhas desse jogo é `ondemand`

#### Scenario: Sistema com a opção ligada
- **WHEN** o usuário liga o máximo desempenho para um sistema no menu e abre um jogo dele
- **THEN** o governor registrado nas linhas desse jogo é `performance`, e o de um jogo de outro sistema continua `ondemand`

#### Scenario: Jogo com a opção desligada num sistema ligado
- **WHEN** o máximo desempenho está ligado para o sistema e desligado para um jogo dele
- **THEN** o governor registrado nas linhas desse jogo é `ondemand`

### Requirement: Ocupação por núcleo e cena da DRAM registradas
Cada linha do registro SHALL trazer a ocupação de `cpu0` a `cpu3` e a cena da DRAM lida do mesmo caminho em que o modo de máximo desempenho a escreve.

#### Scenario: Linha com ocupação
- **WHEN** uma linha é gravada com o aparelho ligado e os núcleos acessíveis
- **THEN** os quatro campos de ocupação trazem um número de 0 a 100, e a linha tem tantos campos quanto o cabeçalho

#### Scenario: Cena da DRAM
- **WHEN** o sistema tem a cena da DRAM em `sunxi-ddrfreq/devfreq/sunxi-ddrfreq/dsm/scene`
- **THEN** a coluna `dram_scene` traz o valor desse arquivo
