# Proposal: Calibração de Telas, Alinhamento de Atalhos e Design System do Tema Epic Cody ML

## Problem

Durante o uso diário do tema padrão **Epic Cody ML** na tela de 640x480 (3.5" IPS) do clone do R36S (GA36-MB V1.2), foram identificadas inconsistências visuais, sobreposições de layout e fragilidades no processo de montagem da imagem:

1. **Reaparecimento de "SELECT GAME" e blocos estilo Tetris após build**:
   - O arquivo `features/50-temas-extras/feature.toml` descompacta o tarball upstream original sem excluir `_art/ingame-global-bg.*`. Durante o `./build.sh`, os arquivos locais limpos eram sobrescritos pela versão original upstream, restaurando o texto rasterizado "SELECT GAME" e blocos decorativos estilo Tetris na região do cabeçalho (`x = 0..206, y = 0..52`).
2. **Ausência do título do jogo (`md_name`) nas visualizações `basic` e `detailed`**:
   - O elemento `<text name="md_name">` encontrava-se declarado exclusivamente dentro do bloco `<feature supported="video"><view name="video">`. Em sistemas sem suporte a vídeo ou nas visualizações básica e detalhada, o título do jogo selecionado não era exibido.
3. **Sobreposição da lista de jogos sobre a barra de botões do rodapé**:
   - O elemento `<textlist name="gamelist">` possuía dimensões `pos: 0 0.12` e `size: 0.319 0.91`, totalizando altura `1.03` (494px em uma tela de 480px). Os últimos itens da lista vazavam por cima dos botões de atalho do rodapé.
4. **Variações concorrentes e fragmentadas de gamelist**:
   - O `theme.xml` definia blocos divergentes para `<view name="basic">`, `<view name="detailed">`, `<view name="video">` e `<view name="grid">`, permitindo que o menu do EmuELEC exibisse opções de estilos alternativos que quebravam o layout ou ocultavam metadados.
5. **Inconsistência no alinhamento dos botões de atalho (`helpsystem`)**:
   - Na lista de jogos, o `helpsystem` estava alinhado à direita (`pos: 1 1`, `origin: 1 1`), enquanto no carrossel de sistemas estava alinhado à esquerda. O usuário determinou que todos os atalhos devem ficar rigorosamente alinhados à esquerda em todas as telas (gamelist e modal de save state).
6. **Modal de Save State desalinhado e com corte de data/hora**:
   - O diálogo de seleção de Save State (`GuiSaveState`) utilizava dimensões estreitas com margens assimétricas, e a tipografia das legendas de data e hora sofria compressão/corte nos cards de slots.
7. **Falta de documentação consolidada do Design System**:
   - Ausência de uma especificação canônica com todas as réguas, coordenadas absolutas, percentuais, cores e tipografia do tema, dificultando ajustes futuros ou a adição de novas telas sem reescritas integrais.

## Proposed Solution

1. **Proteção da Imagem Curada no `feature.toml`**:
   - Adicionar `"_art/ingame-global-bg.*"` à lista `exclude` do `features/50-temas-extras/feature.toml`, garantindo que os bitmaps limpos nunca sejam sobrescritos durante a extração do tarball upstream no build.
2. **Higienização Definitiva do Bitmap do Cabeçalho**:
   - Preencher toda a região retangular superior esquerda (`x = 0..206, y = 0..52`) das imagens `ingame-global-bg.png` e `ingame-global-bg.jpg` com preto sólido (`#000000`), eliminando completamente tanto o texto "SELECT GAME" quanto os blocos estilo Tetris.
3. **Unificação Integral das Visualizações de Gamelist**:
   - Consolidar todas as visualizações em um único layout universal padronizado: `<view name="basic, detailed, video, grid">`.
   - Eliminar blocos fragmentados ou variações concorrentes no menu do EmuELEC.
4. **Calibração Régua Milimétrica da Gamelist (640x480)**:
   - **Cabeçalho**: `y = 0..52` (53px de altura), linha amarela contínua (`#FFAE00`) em `y = 53`. `top_label` em `pos: 0.025 0.025` (`x = 16.0px`), `nameLabel` em `pos: 0.339 0.025` (`x = 217px`), ambos em Bebas Neue `0.050`.
   - **Coluna Esquerda (Lista de Jogos)**: Largura compacta de 32% (`x = 0..206px`), `pos: 0 0.12`, `size: 0.319 0.805`, terminando exatamente em `y = 444px` (exibindo 13 jogos com respiro seguro de 4px antes dos atalhos). Recuo interno com `<horizontalMargin>0.025</horizontalMargin>`, alinhando milimetricamente o texto dos jogos com a palavra "GAMES" na régua vertical de `x = 16.0px`.
   - **Coluna Direita (Preview Adaptável + Título Branco)**: Preview em `pos: 0.66 0.485` com `<maxSize>0.62 0.70</maxSize>` (área útil de até 396x336px, `y = 65..401`), adaptando-se à largura ou altura máxima sem tocar no título nem no cabeçalho. Título do jogo (`md_name`) posicionado em `pos: 0.339 0.865` (`size: 0.64 0.06`, `y = 415..444`, Bebas Neue, `#FFFFFF` branco puro, `alignment: left`).
   - **Linha Divisória**: Finaliza em `y = 444px`, sendo desobstruída (`x = 206..208`, `y = 445..479`) nas imagens rasterizadas para não cortar os botões do rodapé.
   - **Rodapé de Atalhos**: `helpsystem` com `pos: 0.025 0.965`, `origin: 0 1`, rigorosamente alinhado à esquerda a partir de `x = 16px` na mesma posição do menu do carrossel (`system`).
5. **Calibração do Modal de Save State (`GuiSaveState`) e Menus**:
   - Reduzir `fontSize` do menu (`menutitle: 0.038`, `menutext: 0.030`), compactando as legendas dos cards de slot para 25.5px.
   - Expandir a largura do modal para ocupar 608px (95% da tela, `x = 16..624`), alinhando as bordas externas diretamente na régua de 16px da tela.
   - Ajustar altura para 432px (`y = 24..456`).
   - Reduzir o tamanho da fonte de data e hora para escala compacta (~9px / `0.028`), garantindo que o timestamp caiba confortavelmente dentro do card de 160px.
   - Alinhar os atalhos de ação do modal rigorosamente à esquerda em `x = 32px`.
   - Documentar a engenharia reversa do binário `emulationstation` quanto aos multiplicadores hardcoded em C++.
6. **Consolidação do Design System Canônico**:
   - Registrar no documento de design todas as métricas em pixels e coordenadas normalizadas, paleta de cores, hierarquia tipográfica e réguas de layout para todas as telas do tema.

## Scope

- **In scope**:
  - Atualização de `features/50-temas-extras/feature.toml` com regra de exclusão para `_art/ingame-global-bg.*`.
  - Limpeza do cabeçalho em `_art/ingame-global-bg.png` e `_art/ingame-global-bg.jpg`.
  - Refatoração de `theme.xml` do tema Epic Cody ML (unificação de views, dimensões da gamelist, posição do `md_name`, alinhamento à esquerda do `helpsystem`).
  - Calibração de métricas e estilos do diálogo de Save State em conformidade com o EmulationStation.
  - Atualização dos scripts de suporte e ferramentas (`tools/refatora_epic_cody_ml.py`).
  - Criação e atualização de testes automatizados (`tests/test_temas_extras.py`).
  - Documentação completa do Design System do tema em `design.md`.
- **Out of scope**:
  - Modificação do código-fonte em C++ do EmulationStation (alterações são puramente por CSS/XML de tema e configurações de layout suportadas pelo ES).
  - Alterações em outros temas (NES-BOX, Minimal, Graphite).
  - Alterações em traduções de menu do RetroArch ou catalogo de PO/MO do ES.
