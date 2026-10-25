# es-themes Specification Delta

## REMOVED Requirements

### Requirement: Tema NES-BOX-V2 disponível
A imagem gerada trazia o tema NES-BOX-V2 gerado localmente na p8. O requisito é removido; o tema padrão de fábrica NES-BOX permanece intacto.

### Requirement: NES-BOX-V2 cobre todos os sistemas da imagem
Requisito removido junto com o tema NES-BOX-V2.

### Requirement: Arte oficial primeiro, criada quando não existir
Requisito removido junto com o tema NES-BOX-V2.

### Requirement: Origem da arte registrada
Requisito removido junto com o tema NES-BOX-V2.

### Requirement: Formato da arte acrescentada
Requisito removido junto com o tema NES-BOX-V2.

## MODIFIED Requirements

### Requirement: Temas extras disponíveis no menu
A imagem gerada SHALL trazer, além do NES-BOX de fábrica, os temas extras declarados pela feature de temas: Minimal EmuELEC e Graphite OGA na partição `storage`, e Switch, Crystal e Epic Cody na partição `roms` (`themes/`). Todos SHALL aparecer na lista de temas das configurações de interface do EmulationStation.

#### Scenario: Escolher um tema extra na p8 ou no cartão
- **WHEN** o usuário abre a lista de temas do EmulationStation em "Configurações da interface → Tema"
- **THEN** a lista mostra o NES-BOX e cada tema extra (Minimal EmuELEC, Graphite OGA, Switch, Crystal e Epic Cody), e escolher qualquer um deles aplica o tema após reiniciar o EmulationStation.

### Requirement: Espaço dos temas limitado
Os temas extras leves mantidos na p8 SHALL ocupar no máximo 50 MiB no armazenamento do sistema. Os temas armazenados na partição `roms` SHALL respeitar o orçamento de download declarado no descritor da feature.

#### Scenario: Orçamento da partição storage respeitado
- **WHEN** o build aplica a feature de temas
- **THEN** o espaço consumido por temas na partição `storage` não excede 50 MiB.

#### Scenario: Temas no cartão disponíveis na partição de ROMs
- **WHEN** a imagem gerada é inspecionada
- **THEN** os temas Switch, Crystal e Epic Cody estão presentes no caminho `/themes/` da camada `roms` (FAT32) sem symlinks.
