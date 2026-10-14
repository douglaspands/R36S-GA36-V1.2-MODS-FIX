# es-themes Specification

## Purpose
Definir quais temas do EmulationStation a imagem gerada traz, onde eles ficam e qual é o padrão, para o usuário escolher entre vários temas sem precisar de rede no aparelho.

## Requirements

### Requirement: Temas extras disponíveis no menu
A imagem gerada SHALL trazer, além do NES-BOX, os temas extras declarados pela feature de temas. Todos SHALL aparecer na lista de temas das configurações de interface do EmulationStation.

#### Scenario: Escolher um tema
- **WHEN** o cartão é gravado com `--wipe-storage` e o usuário abre a lista de temas do EmulationStation
- **THEN** a lista mostra o NES-BOX e cada tema extra, e escolher um deles aplica o tema depois do reinício do EmulationStation

### Requirement: Temas legíveis na tela do aparelho
Cada tema extra SHALL mostrar a lista de sistemas e a lista de jogos na tela de 640x480 sem texto cortado a ponto de impedir a navegação. Um tema que falhar nessa validação SHALL sair do conjunto.

#### Scenario: Navegação com um tema extra
- **WHEN** o usuário seleciona um tema extra e navega até a lista de jogos de um sistema
- **THEN** os nomes dos sistemas e dos jogos são legíveis e a seleção atual é visível

### Requirement: NES-BOX continua padrão
O tema ativo no primeiro boot SHALL continuar sendo o NES-BOX.

#### Scenario: Primeiro boot
- **WHEN** o aparelho inicia pela primeira vez com o storage gravado pela imagem
- **THEN** o EmulationStation abre com o tema NES-BOX

### Requirement: Espaço dos temas limitado
Os temas extras juntos SHALL ocupar no máximo 400 MiB na p8, e o build SHALL falhar se o limite for ultrapassado.

#### Scenario: Orçamento respeitado
- **WHEN** o build aplica a feature de temas
- **THEN** o relatório do build mostra o tamanho total dos temas extras, e ele é de no máximo 400 MiB

#### Scenario: Orçamento estourado
- **WHEN** a lista de temas extraídos soma mais de 400 MiB
- **THEN** o build falha antes de gerar a imagem, mostrando o tamanho de cada tema
