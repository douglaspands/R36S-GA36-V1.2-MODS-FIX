# Spec Delta: es-themes

## MODIFIED Requirements

### Requirement: Temas extras disponíveis no menu
A imagem gerada SHALL disponibilizar uma coleção de temas para o EmulationStation: Minimal EmuELEC, Graphite OGA e Epic Cody instalados na partição `storage`, e Switch, Crystal e NES-BOX na partição de ROMs do cartão (`themes/`). Todos SHALL aparecer na lista de temas das configurações de interface do EmulationStation.

#### Scenario: Escolher um tema extra na p8 ou no cartão
- **WHEN** o usuário abre a lista de temas do EmulationStation em "Configurações da interface → Tema"
- **THEN** a lista mostra cada tema disponível (Minimal EmuELEC, Graphite OGA, Epic Cody, Switch, Crystal e NES-BOX), e escolher qualquer um deles aplica o tema após reiniciar o EmulationStation

### Requirement: NES-BOX continua padrão
O tema ativo no primeiro boot SHALL ser o Epic Cody, configurado nativamente na partição default do sistema (`storage`).

#### Scenario: Primeiro boot
- **WHEN** o aparelho inicia pela primeira vez com o storage gravado pela imagem
- **THEN** o EmulationStation abre com o tema Epic Cody como padrão

### Requirement: Espaço dos temas limitado
Os temas mantidos na partição `storage` (p8) SHALL respeitar o limite de espaço livre e não exceder 300 MiB no total. Os temas armazenados na partição `roms` (FAT32) SHALL respeitar o orçamento de download e não conter links simbólicos.

#### Scenario: Orçamento da partição storage respeitado
- **WHEN** o build aplica a feature de temas
- **THEN** o espaço consumido por temas na partição `storage` (Minimal, Graphite e Epic Cody) não excede 300 MiB e deixa espaço livre para saves e RetroArch

#### Scenario: Temas no cartão disponíveis na partição de ROMs
- **WHEN** a imagem gerada é inspecionada
- **THEN** os temas Switch, Crystal e NES-BOX estão presentes no caminho `/themes/` da camada `roms` (FAT32) sem links simbólicos
