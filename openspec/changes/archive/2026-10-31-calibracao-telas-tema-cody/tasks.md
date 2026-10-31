# Tasks: Calibração de Telas, Alinhamento de Atalhos e Design System do Tema Epic Cody ML

## 1. Proteção e Higienização de Imagens de Fundo
- [x] 1.1 Adicionar `"_art/ingame-global-bg.*"` na diretiva `exclude` do `features/50-temas-extras/feature.toml` para blindar imagens curadas contra sobrescrita no build.
- [x] 1.2 Higienizar o cabeçalho (`x = 0..206, y = 0..52`) das imagens `ingame-global-bg.png` e `ingame-global-bg.jpg` preenchendo a região com preto puro (`#000000`), eliminando o texto "SELECT GAME" e os blocos estilo Tetris.

## 2. Refatoração e Unificação do `theme.xml`
- [x] 2.1 Unificar as declarações de gamelist em uma única visualização canônica `<view name="basic, detailed, video, grid">`, eliminando blocos fragmentados ou variações concorrentes.
- [x] 2.2 Calibrar o elemento `<textlist name="gamelist">` para `pos: 0 0.12` e `size: 0.319 0.824` (largura 32%, finalizando em `y = 453px`, 13 títulos visíveis com respiro de 2px antes do rodapé).
- [x] 2.3 Declarar o elemento `<text name="md_name">` como legenda inferior fixa em `pos: 0.339 0.835` (`size: 0.64 0.08`, `BebasNeue`, `#FFAE00`, `alignment: left`), presente em todas as visualizações de jogos.
- [x] 2.4 Alinhar a barra de atalhos `<helpsystem name="help">` rigorosamente à esquerda (`pos: 0.025 0.985`, `origin: 0 1`), iniciando na margem de 16px.

## 3. Calibração do Diálogo de Save State (`GuiSaveState`)
- [x] 3.1 Calibrar as dimensões do modal de Save State para 608px de largura (`x = 16..624`, 95% da tela) e 432px de altura (`y = 24..456`), alinhando atalhos e cabeçalho à esquerda em `x = 32px`.
- [x] 3.2 Ajustar a escala tipográfica dos rótulos de data e hora para formato compacto (`fontSize = 0.028`), garantindo margem segura dentro de cada card de slot sem corte ou truncamento.

## 4. Atualização de Ferramentas e Testes Automatizados
- [x] 4.1 Sincronizar o script `tools/refatora_epic_cody_ml.py` com a unificação de visualizações e réguas do Design System.
- [x] 4.2 Expandir a suíte de testes em `tests/test_temas_extras.py` para validar a presença da regra de exclusão no `feature.toml`, o alinhamento à esquerda do `helpsystem`, a dimensão vertical da lista de jogos e a ausência de blocos rasterizados no cabeçalho.
- [x] 4.3 Executar a suíte de testes completa (`python3 -I -m unittest discover -s tests`) e atestar 100% de sucesso.

## 5. Refinamentos de Régua e Alinhamento Solicitados (Iteração 2)
- [x] 5.1 Alinhamento milimétrico régua de "GAMES" (`top_label`) e nomes da gamelist: ajustar `<horizontalMargin>` para `0.025` no `<textlist name="gamelist">`, igualando o início do texto em `x = 16.0px`.
- [x] 5.2 Alterar a cor do nome do jogo (`md_name`) para branco puro (`#FFFFFF`) e ativar rolagem automática horizontal em loop (`<singleLineScroll>true</singleLineScroll>`) quando o título ultrapassar a largura da tela.
- [x] 5.3 Calibração de preview adaptável (`md_image` / `md_video`): reposicionar centro para `pos: 0.66 0.485` e expandir `<maxSize>0.62 0.70</maxSize>`, rebaixando `md_name` para `pos: 0.339 0.865` (`size: 0.64 0.06`), garantindo adaptação máxima sem sobreposição.
- [x] 5.4 Sincronização da barra de atalhos (`helpsystem`): alinhar gamelist na mesma posição do carrossel (`pos: 0.025 0.965`, `origin: 0 1`) e reduzir altura da gamelist para `size: 0.319 0.805` (término em `y = 444px`, 4px antes dos atalhos).
- [x] 5.5 Limpeza da linha divisória vertical: terminar linha em `y = 444px` e desobstruir pixels `x = 206..208` para `y = 445..479` em `_art/ingame-global-bg.png` e `.jpg` antes dos atalhos.
- [x] 5.6 Calibração tipográfica do modal de Save State: refatorar tokens de menu (`menutitle: 0.038`, `menutext: 0.030`) e documentar no design o funcionamento do `GuiSaveState` no binário do EmulationStation.
- [x] 5.7 Atualização de ferramentas (`refatora_epic_cody_ml.py`, `gera_prints_interface.py`) e testes automatizados (`test_temas_extras.py`).
