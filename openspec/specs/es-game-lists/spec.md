# es-game-lists Specification

## Purpose
Definir como as listas de jogos do EmulationStation são apresentadas na imagem gerada, para o usuário achar os jogos sem navegar por pastas e com os favoritos à mão.

## Requirements

### Requirement: Listas sem pastas
A configuração do EmulationStation da imagem SHALL esconder as pastas nas listas de jogos, mostrando os jogos das subpastas direto na lista do sistema.

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmulationStation declara `FolderViewMode` com o valor `never`

#### Scenario: Sistema com jogos em subpastas
- **WHEN** o usuário abre a lista de um sistema cujos jogos estão em subpastas, como o FBNeo
- **THEN** a lista mostra os jogos, sem entradas de pasta

### Requirement: Favoritos no topo
A configuração do EmulationStation da imagem SHALL mostrar os jogos favoritos no início de cada lista.

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmulationStation declara `FavoritesFirst` com o valor `true`

#### Scenario: Lista com favoritos
- **WHEN** o usuário abre a lista de um sistema com jogos marcados como favoritos
- **THEN** os favoritos aparecem antes dos demais jogos

### Requirement: Demais opções do EmulationStation preservadas
A imagem SHALL manter iguais às da imagem gravada antes desta mudança as demais opções da configuração do EmulationStation, incluindo o idioma `pt_BR` e o tema NES-BOX.

#### Scenario: Comparação com a imagem anterior
- **WHEN** a configuração do EmulationStation da imagem nova é comparada com a da imagem anterior
- **THEN** só `FolderViewMode` e `FavoritesFirst` diferem
