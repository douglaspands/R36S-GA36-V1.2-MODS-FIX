# es-themes Specification

## Purpose
Definir quais temas do EmulationStation a imagem gerada traz, onde eles ficam e qual é o padrão, para o usuário escolher entre vários temas sem precisar de rede no aparelho.

## Requirements

### Requirement: Temas extras disponíveis no menu
A imagem gerada SHALL trazer, além do NES-BOX de fábrica, os temas extras declarados pela feature de temas: Minimal EmuELEC e Graphite OGA na partição `storage`, e Switch, Crystal e Epic Cody na partição `roms` (`themes/`). Todos SHALL aparecer na lista de temas das configurações de interface do EmulationStation.

#### Scenario: Escolher um tema extra na p8 ou no cartão
- **WHEN** o usuário abre a lista de temas do EmulationStation em "Configurações da interface → Tema"
- **THEN** a lista mostra o NES-BOX e cada tema extra (Minimal EmuELEC, Graphite OGA, Switch, Crystal e Epic Cody), e escolher qualquer um deles aplica o tema após reiniciar o EmulationStation.

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
Os temas extras leves mantidos na p8 SHALL ocupar no máximo 50 MiB no armazenamento do sistema. Os temas armazenados na partição `roms` SHALL respeitar o orçamento de download declarado no descritor da feature.

#### Scenario: Orçamento da partição storage respeitado
- **WHEN** o build aplica a feature de temas
- **THEN** o espaço consumido por temas na partição `storage` não excede 50 MiB.

#### Scenario: Temas no cartão disponíveis na partição de ROMs
- **WHEN** a imagem gerada é inspecionada
- **THEN** os temas Switch, Crystal e Epic Cody estão presentes no caminho `/themes/` da camada `roms` (FAT32) sem symlinks.
