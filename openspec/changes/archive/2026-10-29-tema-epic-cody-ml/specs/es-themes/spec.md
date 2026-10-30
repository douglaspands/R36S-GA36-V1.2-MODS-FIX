# Spec Delta

## MODIFIED Requirements

### Requirement: Temas extras disponíveis no menu
A imagem gerada SHALL disponibilizar uma coleção de temas para o EmulationStation: Minimal EmuELEC, Graphite OGA e Epic Cody ML instalados na partição `storage`, e Switch, Crystal e NES-BOX na partição de ROMs do cartão (`themes/`). O tema original Epic Cody SHALL ser removido da partição `storage`. Todos os temas ativos SHALL aparecer na lista de temas das configurações de interface do EmulationStation.

#### Scenario: Escolher um tema extra na p8 ou no cartão
- **WHEN** o usuário abre a lista de temas do EmulationStation em "Configurações da interface → Tema"
- **THEN** a lista mostra cada tema disponível (Minimal EmuELEC, Graphite OGA, Epic Cody ML, Switch, Crystal e NES-BOX) sem exibir o tema original Epic Cody, e escolher qualquer um deles aplica o tema após reiniciar o EmulationStation

### Requirement: NES-BOX continua padrão
O tema ativo no primeiro boot SHALL ser o Epic Cody ML, configurado nativamente na partição default do sistema (`storage`).

#### Scenario: Primeiro boot
- **WHEN** o aparelho inicia pela primeira vez com o storage gravado pela imagem
- **THEN** o EmulationStation abre com o tema Epic Cody ML como padrão

## ADDED Requirements

### Requirement: Suporte a múltiplos idiomas no tema Epic Cody ML
O tema Epic Cody ML SHALL disponibilizar um seletor de idiomas via `<subset name="language">` acessível no menu de configurações do tema, com suporte a `pt-br` (Português do Brasil), `es-latam` (Español Latino) e `en` (English). O idioma `pt-br` SHALL ser o padrão ativo no primeiro boot.

#### Scenario: Alternância de idioma no tema
- **WHEN** o usuário seleciona um idioma no menu de opções do tema Epic Cody ML
- **THEN** as descrições de consoles, categorias e títulos de coleções são atualizados instantaneamente para o idioma escolhido

### Requirement: Calibração visual e terminologia no tema
As descrições e títulos no tema Epic Cody ML SHALL respeitar os limites de caracteres para a resolução de 640x480 (sem sobreposição com a barra de botões) e SHALL manter nomenclaturas técnicas e de gêneros clássicos (*16-bit*, *Arcade*, *RPGs*, *Shmups*) inalteradas no catálogo em português.

#### Scenario: Leitura de descrição de console
- **WHEN** o usuário visualiza qualquer sistema no carrossel do tema Epic Cody ML em português
- **THEN** os textos de `shortdescription` e `longdescription` cabem confortavelmente dentro dos limites visuais da tela de 3.5 polegadas
