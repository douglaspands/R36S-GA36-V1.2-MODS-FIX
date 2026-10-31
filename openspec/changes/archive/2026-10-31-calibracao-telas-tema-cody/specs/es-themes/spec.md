# es-themes Specification Delta

## Purpose
Especificar os requisitos e cenários de aceitação para a calibração de layout, alinhamento universal de atalhos à esquerda, unificação da lista de jogos e especificação do Design System do tema Epic Cody ML na resolução de 640x480 (display 3.5" do R36S).

## Requirements

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
