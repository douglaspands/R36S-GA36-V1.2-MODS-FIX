# es-themes Specification

## Purpose
Definir quais temas do EmulationStation a imagem gerada traz, onde eles ficam e qual é o padrão, para o usuário escolher entre vários temas sem precisar de rede no aparelho.

## Requirements

### Requirement: Temas extras disponíveis no menu
A imagem gerada SHALL disponibilizar uma coleção de temas para o EmulationStation: Minimal EmuELEC, Graphite OGA e Epic Cody ML instalados na partição `storage`, e Switch, Crystal e NES-BOX na partição de ROMs do cartão (`themes/`). O tema original Epic Cody SHALL ser removido da partição `storage`. Todos os temas ativos SHALL aparecer na lista de temas das configurações de interface do EmulationStation.

#### Scenario: Escolher um tema extra na p8 ou no cartão
- **WHEN** o usuário abre a lista de temas do EmulationStation em "Configurações da interface → Tema"
- **THEN** a lista mostra cada tema disponível (Minimal EmuELEC, Graphite OGA, Epic Cody ML, Switch, Crystal e NES-BOX) sem exibir o tema original Epic Cody, e escolher qualquer um deles aplica o tema após reiniciar o EmulationStation

### Requirement: Temas legíveis na tela do aparelho
Cada tema extra SHALL mostrar a lista de sistemas e a lista de jogos na tela de 640x480 sem texto cortado a ponto de impedir a navegação. Um tema que falhar nessa validação SHALL sair do conjunto.

#### Scenario: Navegação com um tema extra
- **WHEN** o usuário seleciona um tema extra e navega até a lista de jogos de um sistema
- **THEN** os nomes dos sistemas e dos jogos são legíveis e a seleção atual é visível

### Requirement: NES-BOX continua padrão
O tema ativo no primeiro boot SHALL ser o Epic Cody ML, configurado nativamente na partição default do sistema (`storage`).

#### Scenario: Primeiro boot
- **WHEN** o aparelho inicia pela primeira vez com o storage gravado pela imagem
- **THEN** o EmulationStation abre com o tema Epic Cody ML como padrão

### Requirement: Espaço dos temas limitado
Os temas mantidos na partição `storage` (p8) SHALL respeitar o limite de espaço livre e não exceder 300 MiB no total. Os temas armazenados na partição `roms` (FAT32) SHALL respeitar o orçamento de download e não conter links simbólicos.

#### Scenario: Orçamento da partição storage respeitado
- **WHEN** o build aplica a feature de temas
- **THEN** o espaço consumido por temas na partição `storage` (Minimal, Graphite e Epic Cody) não excede 300 MiB e deixa espaço livre para saves e RetroArch

#### Scenario: Temas no cartão disponíveis na partição de ROMs
- **WHEN** a imagem gerada é inspecionada
- **THEN** os temas Switch, Crystal e NES-BOX estão presentes no caminho `/themes/` da camada `roms` (FAT32) sem links simbólicos

### Requirement: Suporte a múltiplos idiomas no tema Epic Cody ML
O tema Epic Cody ML SHALL disponibilizar um seletor de idiomas via `<subset name="language">` acessível no menu de configurações do tema, com suporte a `pt-br` (Português do Brasil), `es-latam` (Español Latino) e `en` (English). O idioma `pt-br` SHALL ser o padrão ativo no primeiro boot.

#### Scenario: Alternância de idioma no tema
- **WHEN** o usuário seleciona um idioma no menu de opções do tema Epic Cody ML
- **THEN** as descrições de consoles, categorias e títulos de coleções são atualizados instantaneamente para o idioma escolhido

### Requirement: Calibração visual e terminologia no tema
As descrições, títulos e elementos de interface no tema Epic Cody ML SHALL respeitar os limites espaciais da resolução 640x480, alinhando a coluna de informações em margem segura à esquerda (mínimo 2% de deslocamento horizontal) sem corte próximo à moldura física do aparelho, e SHALL manter nomenclaturas técnicas e de gêneros clássicos (*16-bit*, *Arcade*, *RPGs*, *Shmups*) inalteradas no catálogo em português.

#### Scenario: Leitura de descrição de console
- **WHEN** o usuário visualiza qualquer sistema no carrossel do tema Epic Cody ML em português
- **THEN** os textos de `shortdescription` e `longdescription` cabem confortavelmente dentro dos limites visuais da tela de 3.5 polegadas respeitando a margem esquerda de segurança

### Requirement: Hierarquia visual e ausência de truncamento nos títulos de consoles
O tema Epic Cody ML SHALL distribuir a titulação dos sistemas em duas linhas estruturadas (`sys_line1` para fabricante/família e `sys_line2` para modelo/identificador) com dimensionamento de caixa e tipografia calibrados para a resolução de 640x480, de modo que nenhum nome de console ou coleção gere truncamento com reticências (`...`) na tela do aparelho.

#### Scenario: Visualização de consoles com nomes longos no carrossel
- **WHEN** o usuário navega por consoles de nomes extensos como GameBoy Color, PlayStation, Nintendo 64, Nintendo DS ou coleções como Todos os Jogos
- **THEN** a linha hero (`sys_line2`) e o subtítulo (`sys_line1`) são exibidos inteiramente sem reticências ou cortes

### Requirement: Estilização harmônica do rodapé e proteção contra sobreposição
A visualização de sistemas (`system`) do tema Epic Cody ML SHALL estilizar explicitamente o elemento `<helpsystem name="help">` com tipografia discreta, proporções compactas e cores harmônicas com a paleta do tema, e a arte do console (`controller`) SHALL ser dimensionada e posicionada de modo a garantir espaçamento livre de sobreposição em relação à barra de navegação inferior.

#### Scenario: Navegação na tela inicial sem colisão visual
- **WHEN** o usuário visualiza a tela principal de um sistema
- **THEN** a imagem representativa do videogame não sobrepõe os textos e ícones da barra de comandos inferior, e as legendas de botões utilizam fonte proporcional sem ocupar agressivamente a tela

### Requirement: Localização integral de elementos visuais e badges de ação
O tema Epic Cody ML SHALL exibir o badge do botão de ação principal (botão A) e todos os metadados de sistema e categorias traduzidos de acordo com o idioma ativo do tema (`pt-br`, `es-latam` ou `en`), sem manter termos em inglês na interface configurada em português ou espanhol.

#### Scenario: Botão de ação e metadados em português
- **WHEN** o tema Epic Cody ML está ativo no idioma Português (Brasil)
- **THEN** o badge do botão principal indica `(A) ENTRAR` e rótulos de configurações, emuladores e categorias especiais não exibem termos em inglês órfãos

### Requirement: Proteção e limpeza de arte curada do tema
O descritor da feature `50-temas-extras` (`feature.toml`) SHALL excluir explicitamente arquivos de imagem de fundo curados (`_art/ingame-global-bg.*`) durante a extração do tarball upstream. As imagens `ingame-global-bg.png` e `ingame-global-bg.jpg` sob a partição `storage` SHALL possuir a área retangular de cabeçalho (`x = 0..206, y = 0..52`) preenchida exclusivamente com a cor de fundo sólida preta (`#000000`), sem resquícios do texto rasterizado "SELECT GAME" nem de blocos decorativos estilo Tetris.

#### Scenario: Build preserva arte curada
- **WHEN** o comando de build `./build.sh` descompacta o tema upstream a partir do cache externo
- **THEN** as imagens `_art/ingame-global-bg.png` e `.jpg` locais da feature não são sobrescritas pela versão do repositório externo, mantendo o cabeçalho limpo sem texto estático nem blocos rasterizados

### Requirement: Layout unificado e singular da lista de jogos
O tema Epic Cody ML SHALL definir uma única especificação estrutural consolidada para a lista de jogos através da declaração `<view name="basic, detailed, video, grid">` em `theme.xml`, eliminando variações divergentes ou fragmentadas de layout. O tema não SHALL expor estilos concorrentes de gamelist que alterem a composição de colunas ou ocultem os metadados principais.

#### Scenario: Visualização consistente em qualquer modo de lista
- **WHEN** o usuário seleciona ou alterna o estilo de exibição da lista de jogos no EmulationStation
- **THEN** a disposição espacial de colunas, proporções de imagem e elementos visuais permanece rigorosamente idêntica e unificada

### Requirement: Calibração espacial da coluna de jogos e legenda do título
Na visualização de lista de jogos, o tema Epic Cody ML SHALL calibrar as dimensões e posicionamento dos elementos conforme a régua de 640x480:
1. O elemento `<textlist name="gamelist">` SHALL ocupar no máximo 32% da largura da tela (`pos: 0 0.12`, `size: 0.319 0.805`), finalizando a exibição em `y <= 444px` com margem de segurança de no mínimo 4px antes da barra de comandos inferior (`y = 448px`), e SHALL possuir `<horizontalMargin>0.025</horizontalMargin>`, garantindo que o início do texto dos jogos coincida milimetricamente na coordenada `x = 16.0px` com o rótulo de cabeçalho `top_label` ("GAMES").
2. O elemento `<text name="md_name">` SHALL estar presente em todas as visualizações de jogos como legenda inferior na coluna direita em `pos: 0.339 0.865` (`size: 0.64 0.06`), com tipografia Bebas Neue em cor branca pura (`#FFFFFF`), alinhamento à esquerda (`alignment = left`) e propriedade `<singleLineScroll>true</singleLineScroll>`, garantindo que títulos longos que excedam a largura da coluna executem rolagem suave (marquee) contínua da esquerda para a direita, sem quebra de linha nem truncamento por reticências.
3. Os elementos de mídia `<image name="md_image">` e `<video name="md_video">` SHALL estar centralizados em `pos: 0.66 0.485` com limite de proporção `<maxSize>0.62 0.70</maxSize>`, adaptando-se à largura máxima (396px) ou altura máxima (336px) e finalizando a área de exibição em `y <= 401px`, garantindo separação livre de no mínimo 14px acima do título `md_name` sem nenhuma sobreposição.
4. A linha divisória vertical em `_art/ingame-global-bg.png` e `.jpg` SHALL finalizar na coordenada `y = 444px`, sendo desprovida de pigmento âmbar (`x = 206..208`, `y = 445..479`) para não cortar nem sobrepor a barra de atalhos do rodapé.

#### Scenario: Navegação na lista sem colisão no rodapé e alinhamento régua
- **WHEN** o usuário navega pela lista de jogos de qualquer sistema
- **THEN** o texto dos títulos dos jogos inicia exatamente em `x = 16px` alinhado à palavra "GAMES", a arte visual adapta-se sem tocar no título, o nome do jogo é renderizado em branco puro em `y = 415px`, a linha divisória termina antes dos atalhos e a lista finaliza em `y = 444px` sem tocar na barra inferior

### Requirement: Alinhamento universal à esquerda dos botões de atalho
Os elementos de atalho e comandos de controle (`<helpsystem name="help">`) do tema Epic Cody ML SHALL estar rigorosamente alinhados à esquerda da tela com mesma altura e posição (`pos: 0.025 0.965`, `origin: 0 1`), iniciando na coordenada horizontal `x = 16px` (margem segura do display), tanto na visualização de sistemas (`system`), quanto na visualização unificada de jogos (`basic, detailed, video, grid`) e na tela modal de gerenciamento de Save State (`GuiSaveState`).

#### Scenario: Alinhamento de atalhos na lista de jogos
- **WHEN** o usuário visualiza a lista de jogos de qualquer console
- **THEN** a barra de botões de atalho no rodapé inicia na margem esquerda da tela (`x = 16px`) com alinhamento à esquerda, em vez de alinhamento à direita

#### Scenario: Alinhamento de atalhos no diálogo de Save State
- **WHEN** o usuário abre o diálogo de seleção de Save State no EmulationStation
- **THEN** os botões de atalho de confirmação e cancelamento no rodapé do diálogo iniciam alinhados à esquerda

### Requirement: Calibração espacial e tipográfica do modal de Save State
O diálogo de gerenciamento de Save State (`GuiSaveState`) e os menus do tema Epic Cody ML SHALL respeitar as margens simétricas da tela de 640x480:
1. A largura do modal SHALL ser expandida para 608 pixels (`x = 16px` até `x = 624px`, correspondendo a 95% da tela), alinhando suas bordas laterais com a margem segura de 16px do display.
2. A altura do modal SHALL ocupar 432 pixels (`y = 24px` até `y = 456px`), mantendo 24px de respiro simétrico superior e inferior.
3. Os 3 cards de slots exibidos lado a lado SHALL possuir área útil de ~160px cada com thumbnails em proporção 4:3 (152x114px).
4. O bloco `<view name="menu">` SHALL definir `<menuText name="menutitle">` com `fontSize: 0.038` e `<menuText name="menutext">` com `fontSize: 0.030`, calibrando a tipografia dos cards e do modal de forma compacta para conter os nomes e horários sem truncamento visual na resolução de 640x480.
5. O rótulo de data e hora posicionado abaixo de cada thumbnail SHALL utilizar escala tipográfica reduzida (~9px / `0.028`), garantindo que o timestamp completo ("YYYY-MM-DD HH:MM") caiba com folga lateral dentro da largura do card sem truncamento ou colisão com as bordas do cartão.

#### Scenario: Exibição do modal de Save State com cards calibrados
- **WHEN** o usuário abre a interface de Save State com múltiplos slots ocupados
- **THEN** o diálogo ocupa a largura útil de 608px respeitando as margens de 16px da tela, e as datas e horas dos estados salvos são perfeitamente legíveis dentro dos limites dos cards

### Requirement: Tema do sistema gba-recomp
O tema Epic Cody ML SHALL trazer uma pasta `gba-recomp/` com `theme.xml`, `logo.png`, `poster.png` e `system.png`, de modo que o sistema `gba-recomp` não caia no visual genérico. A arte SHALL ser derivada da do GBA com um selo "RECOMP" visível, para distinguir a lista dos jogos do core GBA.

#### Scenario: Sistema com arte própria
- **WHEN** o EmulationStation mostra a lista de sistemas com `gba-recomp` presente
- **THEN** o sistema aparece com logo, poster e imagem de sistema próprios, e o selo RECOMP o distingue do sistema `gba`

#### Scenario: Arquivos do tema presentes
- **WHEN** a pasta do tema na p8 da imagem gerada é inspecionada
- **THEN** `gba-recomp/` contém `theme.xml`, `logo.png`, `poster.png` e `system.png`

### Requirement: Textos de gba-recomp nos três idiomas
Os arquivos `_languages/pt-br.xml`, `es-latam.xml` e `en.xml` SHALL declarar as variáveis `gba-recomp.nameLabel`, `sys_line1`, `sys_line2`, `shortdescription` e `longdescription`, e o `theme.xml` do sistema SHALL consumi-las. Os textos SHALL ser idênticos aos do sistema `gba`; a marca recomp SHALL ser um selo amarelo pequeno ("RECOMP") ao lado da primeira linha. Nenhum texto SHALL ficar em inglês em `pt-br` e `es-latam`.

#### Scenario: Idioma português
- **WHEN** o tema está em `pt-br` e o jogador vê a lista de sistemas
- **THEN** a descrição de `gba-recomp` está em português

#### Scenario: Primeira linha com a marca recomp
- **WHEN** o jogador vê a lista de sistemas com o tema em qualquer idioma
- **THEN** `gba-recomp` mostra "Nintendo" na primeira linha com um selo amarelo pequeno "RECOMP" ao lado, o resto do texto e o pôster e o controle iguais aos do `gba`, e nenhum selo no rodapé

#### Scenario: Variável ausente
- **WHEN** os três arquivos de idioma são conferidos
- **THEN** cada um declara as cinco variáveis `gba-recomp.*`, sem nenhuma faltando

### Requirement: gba-recomp legível em 640x480
Os textos de `gba-recomp` SHALL caber na tela de 640x480, com `sys_line1` e `sys_line2` sem truncamento por reticências, na lista de sistemas e no cabeçalho da lista de jogos, respeitando as margens e o layout unificado do tema.

#### Scenario: Título sem truncamento
- **WHEN** a lista de sistemas mostra `gba-recomp` em qualquer um dos três idiomas
- **THEN** `sys_line1` e `sys_line2` aparecem inteiros, sem reticências

#### Scenario: Lista de jogos com o layout do tema
- **WHEN** o jogador abre a lista de `gba-recomp`
- **THEN** a lista usa o mesmo layout unificado dos demais sistemas, sem elemento cortado nem sobreposto à barra de atalhos
