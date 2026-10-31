# Design: Localização Dinâmica do Top Label da Lista de Jogos

## Context
O tema **Epic Cody ML** é o tema padrão do sistema EmuELEC no clone do R36S, com suporte dinâmico a múltiplos idiomas via `<subset name="language">`.

Na visualização de lista de jogos (`<view name="basic, detailed, video">`), a coluna da esquerda exibe a lista de ROMs. No topo dessa coluna, o tema upstream original trazia a imagem rasterizada `_art/ingame-global-bg.png` contendo o texto estático "SELECT GAME" impresso diretamente nos pixels em branco e âmbar. Ao mesmo tempo, o `theme.xml` já possuía o elemento `<text name="top_label" extra="true">`, mas vazio.

## Decisions

### 1. Limpeza do Bitmap vs Múltiplas Imagens de Fundo
- **Decisão**: Limpar a faixa superior esquerda (`x=0..204, y=10..52`) das imagens de fundo `ingame-global-bg.png` e `ingame-global-bg.jpg` substituindo os pixels de texto pela cor de fundo plana (`#000000` / `#0e0e0e`).
- **Justificativa**: Evita duplicar arquivos de imagem pesados por idioma (economiza ~150 KiB a cada imagem nova) e delega a renderização do texto ao motor nativo do EmulationStation, que utiliza a fonte vetorial BebasNeue com nitidez perfeita na tela de 640x480.
- **Alternativa descartada**: Criar `ingame-global-bg-pt.png` e `ingame-global-bg-es.png`. Descartada pelo aumento desnecessário de complexidade e consumo de espaço na partição `storage`.

### 2. Ativação do Elemento `<text name="top_label">` e Alinhamento Régua Milimétrica
- **Decisão**: Alterar os elementos de cabeçalho no `theme.xml`:
  ```xml
  <text name="top_label" extra="true">
      <fontPath>./_art/BebasNeue.otf</fontPath>
      <text>${top_label}</text>
      <alignment>left</alignment>
      <color>F8F8F8</color>
      <fontSize>0.050</fontSize>
      <origin>0 0</origin>
      <pos>0.025 0.025</pos>
      <size>0.28 0.08</size>
  </text>
  
  <text name="nameLabel" extra="true">
      <fontPath>./_art/BebasNeue.otf</fontPath>
      <alignment>left</alignment>
      <forceUppercase>1</forceUppercase>
      <color>FFAE00</color>
      <fontSize>0.050</fontSize>
      <origin>0 0</origin>
      <pos>0.339 0.025</pos>
      <size>0.64 0.08</size>
      <zIndex>50</zIndex>
  </text>
  ```
- **Justificativa e Métricas de Régua (Pixel-Perfect)**:
  - **Linha Amarela Contínua**: A linha horizontal âmbar original em `y = 53` corre reta e ininterrupta por toda a largura da tela (`x = 0..639`), sem degraus ou descontinuidades entre a coluna esquerda e o painel direito.
  - **Altura da Faixa**: A faixa superior possui exatamente 53 pixels de altura (`y = 0..52`).
  - **Harmonização Tipográfica**: Ambos os textos utilizam a mesma escala tipográfica (`fontSize: 0.050`, altura de glifo = 21px), garantindo baseline e linha de topo 100% coincidentes.
  - **Simetria Vertical Perfeita**:
    - Distância da borda superior da tela (`y = 0`) até o topo dos glifos: **16.0 pixels**.
    - Altura dos glifos: **21.0 pixels** (`y = 16..37`).
    - Distância da linha de base dos glifos (`y = 37`) até a linha amarela (`y = 53`): **16.0 pixels**.
    - Diferença vertical entre `GAMES` e o título do console: **0.0 pixels**.
  - **Alinhamento Horizontal por Colunas**:
    - `top_label`: Alinhado na margem padrão do sistema em `x = 0.025` (16 pixels da borda física da tela).
    - `nameLabel`: Alinhado na margem de conteúdo da coluna direita em `x = 0.339` (217 pixels), coincidindo rigorosamente com a margem do elemento `md_name` e da descrição.

### 3. Valores da Variável `top_label` por Idioma
- **Decisão**:
  - `pt-br`: `GAMES` (atendendo à preferência explícita do usuário).
  - `es-latam`: `JUEGOS` (termo natural e direto em espanhol).
  - `en`: `GAMES` (ou `SELECT GAME`, mantendo conciso como `GAMES`).

### 4. Alinhamento de `nameLabel` à Esquerda e Exibição de `md_name` (Design System Opção 1)
- **Decisão**:
  - O elemento `<text name="nameLabel">` em `<view name="basic, detailed, video">` do `theme.xml` deve manter `<alignment>left</alignment>` posicionado a partir de `pos: 0.339 0.025`.
  - O elemento `<text name="md_name">` deve ser posicionado rigorosamente como **legenda inferior** em `pos: 0.339 0.81` (Opção 1 adotada como especificação definitiva do Design System do tema), com `<alignment>left</alignment>` e cor âmbar `#FFAE00`.
- **Justificativa e Arquitetura do Design System**:
  - A Opção 1 (título abaixo da capa em `y = 0.81`) preserva integralmente a área de exibição da imagem da capa (`md_image`) e do vídeo de demonstração (`md_video`) entre `y = 75` e `y = 370`.
  - Posicionar o título abaixo da capa cria uma leitura natural de cima para baixo: o jogador visualiza a arte do jogo no centro e lê a identificação em destaque logo abaixo, com espaço seguro de 16 pixels antes da barra de comandos do rodapé (`helpsystem`).
  - A Opção 2 (título acima da capa) comprimiria o espaço vertical de exibição da arte, especialmente para capas verticais (Mega Drive, Master System) e capas quadradas (PlayStation, Dreamcast). A Opção 1 oferece compatibilidade estética universal com todas as proporções de capas.

### 5. Integração com a Ferramenta de Refatoração (`refatora_epic_cody_ml.py`)
- **Decisão**: Sincronizar `tools/refatora_epic_cody_ml.py` adicionando `top_label` nas variáveis base e nos dicionários de tradução, e garantindo que ao processar o tarball ou regenerar o tema, a limpeza da imagem e a injeção da tag `<text>${top_label}</text>` sejam reproduzíveis.

## Risks & Mitigations
- **Risco**: `top_label` não renderizar se a variável não estiver definida em algum idioma.
  - **Mitigação**: O teste de unidade `test_catalogos_pt_br_and_es_latam_exist_and_consistent` em `test_tema_epic_cody_ml.py` valida a simetria exata de chaves e proíbe variáveis vazias entre todos os catálogos.
