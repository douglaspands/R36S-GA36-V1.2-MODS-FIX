# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Afinamento desligável
O afinamento do ondemand SHALL fazer parte de uma feature própria, que pode ser desligada sem afetar as demais.

#### Scenario: Feature desligada
- **WHEN** a imagem é gerada com a feature do afinamento desligada
- **THEN** o ondemand roda com os tunables da imagem base, e a abertura de jogos não falha por causa da ausência do afinamento

#### Scenario: DRAM com a feature desligada
- **WHEN** a imagem é gerada com a feature do afinamento desligada e um jogo roda com o máximo desempenho desligado
- **THEN** a DRAM fica na cena `1`, como na imagem base
