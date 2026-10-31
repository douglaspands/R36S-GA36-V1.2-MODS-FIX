# Design: Calibração de Telas, Alinhamento de Atalhos e Design System do Tema Epic Cody ML

## Context

O tema **Epic Cody ML** é o tema visual padrão da distribuição EmuELEC no clone do R36S (GA36-MB V1.2, Allwinner A33). O console utiliza um display LCD IPS de 3.5 polegadas com resolução física de **640x480 pixels** (proporção 4:3).

Esta especificação estabelece o **Design System definitivo do tema**, registrando todas as métricas espaciais (em coordenadas normalizadas do EmulationStation e em pixels absolutos), paleta de cores corporativa, hierarquia tipográfica e réguas estruturais para todas as telas (Carrossel de Sistemas, Lista de Jogos unificada e Modal de Save State).

---

## 1. Design Tokens & Fundamentos Globais

### 1.1 Resolução e Conversão de Coordenadas
O EmulationStation utiliza um sistema de coordenadas flutuantes normalizadas onde `(0.0, 0.0)` representa o canto superior esquerdo e `(1.0, 1.0)` o canto inferior direito da tela:
$$\text{Pixel}_X = \text{round}(X_{\text{norm}} \times 640)$$
$$\text{Pixel}_Y = \text{round}(Y_{\text{norm}} \times 480)$$

$$X_{\text{norm}} = \frac{\text{Pixel}_X}{640}, \quad Y_{\text{norm}} = \frac{\text{Pixel}_Y}{480}$$

### 1.2 Margens de Segurança do Display
Para evitar corte visual por moldura física ou sombras de borda da tela IPS:
- **Margem Lateral Padrão**: 16 pixels (`pos X = 0.025` à esquerda, margem direita em `x = 624px` / `0.975`).
- **Margem Superior do Cabeçalho**: 12 pixels (`pos Y = 0.025`).
- **Margem Inferior do Rodapé**: 7 a 16 pixels (`pos Y = 0.965..0.985`).

### 1.3 Paleta de Cores do Sistema

| Token | Código Hex | Opacidade | Uso Semântico |
| :--- | :--- | :--- | :--- |
| `color-bg-pure` | `#000000` | 100% | Fundo mestre da tela, coluna de jogos e canvas do cabeçalho |
| `color-bg-dark` | `#0A0A0A` | 100% | Fundo alternativo escuro e painéis secundários |
| `color-surface` | `#1C1C1C` | 100% | Barra seletora da lista de jogos e fundo de caixas modais |
| `color-surface-hover` | `#202020` | 100% | Fundo do menu e cards destacados |
| `color-border` | `#333333` | 100% | Bordas de separação sutis e contornos de cards inativos |
| `color-inactive` | `#585858` | 100% | Nomes de jogos não selecionados e ícones desativados |
| `color-muted` | `#888888` | 100% | Metadados secundários, desenvolvedora e rótulos de data |
| `color-legend` | `#A0A0A0` | 100% | Legendas de botões do helpsystem no rodapé |
| `color-text-pure` | `#FFFFFF` | 100% | Títulos de sistemas, nomes de cards e texto de alto contraste |
| `color-text-header` | `#F8F8F8` | 100% | Rótulo superior da lista de jogos (`top_label` = "GAMES") |
| `color-brand-amber` | `#FFAE00` | 100% | **Cor de destaque do tema**: linha divisória, jogo selecionado, títulos de consoles, `md_name` e ícones de botões |
| `color-transparent` | `#00000000` | 0% | Rótulos ocultos e caixas de bounding invisíveis |

### 1.4 Hierarquia Tipográfica

O tema utiliza duas famílias tipográficas embarcadas em `_art/`:

1. **`BebasNeue.otf` (Display Condensed Sans - Titulação e Identidade)**:
   - Utilizado em caixa alta (`forceUppercase = 1`), com condensação elegante e legibilidade limpa a longa distância.
   - **Hero Gigante (`sys_line2`)**: `fontSize = 0.130` (altura de glifo ~62.4px).
   - **Cabeçalho Primário (`top_label`, `nameLabel`)**: `fontSize = 0.050` (altura de glifo = 21.0px).
   - **Legenda de Título do Jogo (`md_name`)**: `fontSize = 0.045` (altura de glifo ~19.2px).
   - **Subtítulo de Console (`sys_line1`)**: `fontSize = 0.045` (altura de glifo ~19.2px).

2. **`Acre.otf` (Modern Geometric Sans - Leitura e Interface)**:
   - Utilizado para blocos de texto fluido, listas densas e atalhos de controle.
   - **Itens da Lista de Jogos (`gamelist`)**: `fontSize = 0.030` (~14.4px), `lineSpacing = 1.683`.
   - **Descrições e Sinopses (`shortdescription`, `longdescription`)**: `fontSize = 0.022` a `0.026` (~10.5 a 12.5px).
   - **Atalhos do Rodapé (`helpsystem`)**: `fontSize = 0.022` (~10.5px).
   - **Data/Hora em Cards (`GuiSaveState`)**: `fontSize = 0.028` (~9.0px) para caber sem truncamento.

---

## 2. Telas do Sistema: Réguas e Especificação Estrutural

### 2.1 Tela 1: Lista de Jogos (Gamelist) - Layout Unificado

A lista de jogos do tema Epic Cody ML adota um layout **único e universal** aplicado via `<view name="basic, detailed, video, grid">`, eliminando alternâncias ou quebras visuais ao navegar pelo sistema.

#### Diagrama de Régua da Gamelist (640x480):
```text
(0,0)                                                                        (639,0)
  +-----------------------------------------------------------------------------+ y=0
  |  GAMES (16px)                  NINTENDO ENTERTAINMENT SYSTEM        [BAT] [REL]  | y=12..40
  +=============================================================================+ y=53 (Linha Âmbar contínua)
  |                                |                                            |
  | > Super Mario Bros. 3 (16px)   |             +---------------+              |
  |   Mega Man 2                   |             |               |              |
  |   Castlevania                  |             |     ARTE      |              |
  |   Metroid                      |             |  CAPA / VÍDEO |              | y=65..401
  |   The Legend of Zelda          |             |  (396 x 336)  |              |
  |   Contra                       |             |  (maxSize     |              |
  |   DuckTales                    |             |   0.62 0.70)  |              |
  |   Ninja Gaiden                 |             +---------------+              |
  |   Kirby's Adventure            |                                            |
  |   Double Dragon                |   SUPER MARIO BROS. 3                      | y=415..444
  |   Battletoads                  |   (Título branco #FFFFFF fixo em y=0.865)  | (md_name)
  |   River City Ransom            |                                            |
  |   Gargoyle's Quest II          |                                            |
  | (13 títulos visíveis)          |                                            | y=444
  +--------------------------------+--------------------------------------------+ y=444 (Divisória termina aqui)
  | (A) ENTRAR  (B) VOLTAR  (X) FAVORITO  (SELECT) OPÇÕES                       | y=448..463
  +-----------------------------------------------------------------------------+ y=479
  x=0                              x=206-208                                  x=639
  |<------- 32% (206px) ---------->|<---------------- 68% (432px) ------------->|
```

#### Métricas do Cabeçalho:
- **Faixa de Cabeçalho**: `y = 0..52` (altura de 53px).
- **Linha Amarela Contínua**: `#FFAE00` na coordenada `y = 53`, correndo ininterrupta de `x = 0` a `x = 639`.
- **Rótulo Esquerdo (`top_label`)**:
  - `pos: 0.025 0.025` (`x = 16px, y = 12px`), `size: 0.28 0.08`.
  - Fonte: `BebasNeue.otf`, `fontSize = 0.050`, cor: `#F8F8F8`.
  - Fundo do cabeçalho: 100% preto sólido (`#000000`) nas imagens `_art/ingame-global-bg.*` na área `x = 0..206, y = 0..52`. Sem "SELECT GAME" e sem blocos estilo Tetris.
- **Título do Console (`nameLabel`)**:
  - `pos: 0.339 0.025` (`x = 217px, y = 12px`), `size: 0.64 0.08`.
  - Fonte: `BebasNeue.otf`, `fontSize = 0.050`, cor: `#FFAE00`, `alignment = left`.
  - Deixa livre a margem superior direita (`x > 0.85`) para a bateria e o relógio do sistema.

#### Métricas da Coluna Esquerda (Lista de Jogos):
- **Largura da Coluna**: 32% da largura total da tela (`x = 0..206px`).
- **Lista (`textlist name="gamelist"`)**:
  - `pos: 0 0.12` (`y = 58px`).
  - `size: 0.319 0.805` (largura: 204px, altura: 386.4px, finalizando exatamente em `y = 444.0px`).
  - Margem inferior livre de 4px antes da barra de rodapé (`y = 448px`).
  - **Alinhamento Régua Horizontal**: `<horizontalMargin>0.025</horizontalMargin>` define o recuo do texto para exatamente `0.025 * 640 = 16.0px`. Com `pos.x = 0`, o primeiro caractere de cada jogo inicia milimetricamente alinhado com o rótulo "GAMES" (`top_label` em `x = 16.0px`).
  - Capacidade: Exibe com perfeição **13 jogos** simultaneamente.
  - Cores: `primaryColor: 585858`, `secondaryColor: 888888`, `selectedColor: FFAE00`, `selectorColor: 1C1C1C`.
  - Tipografia: `Acre.otf`, `fontSize: 0.030`, `lineSpacing: 1.683`.

#### Métricas da Coluna Direita (Preview + Título):
- **Largura da Coluna**: 68% da largura total da tela (`x = 208..640px`).
- **Preview de Mídia Adaptável (`md_image`, `md_video`)**:
  - `pos: 0.66 0.485`, `origin: 0.5 0.5`.
  - `<maxSize>0.62 0.70</maxSize>` (área máxima: 396px de largura por 336px de altura, estendendo-se de `y = 65px` a `y = 401px`).
  - Adapta-se fluidamente à largura ou altura máxima mantendo a proporção de aspecto (1:1, 4:3, 16:9, arcade vertical) sem tocar no cabeçalho nem no título.
- **Título do Jogo (`md_name`) - Legenda Inferior**:
  - `pos: 0.339 0.865` (`x = 217px, y = 415.2px`).
  - `size: 0.64 0.06` (altura de 28.8px, ocupando `y = 415.2px .. 444.0px`).
  - Fonte: `BebasNeue.otf`, `fontSize = 0.045`, cor: branca pura (`#FFFFFF`), `alignment: left`.
  - Rolagem Dinâmica (`singleLineScroll = true`): Quando o título do jogo selecionado excede a largura disponível (409px), o EmulationStation executa a animação de rolagem contínua (marquee) horizontal em loop infinito, idêntica ao comportamento dos itens da lista de jogos.
  - Separação de 14.2px acima até o preview e 4.0px abaixo até a barra de atalhos.
- **Linha Divisória Vertical**:
  - Coluna `x = 207` termina em `y = 444px`. O trecho `y = 445..479` foi desobstruído com a cor de fundo nas imagens `ingame-global-bg.png` e `.jpg` para não cortar nem sobrepor a barra de atalhos.

#### Métricas do Rodapé de Atalhos (`helpsystem`):
- `pos: 0.025 0.965`, `origin: 0 1`.
- Alinhamento rigoroso **à esquerda** iniciando na coordenada segura `x = 16px`, posicionado na mesma altura e alinhamento do menu do carrossel (`view name="system"`).
- Tipografia: `Acre.otf`, `fontSize: 0.022`, `textColor: A0A0A0`, `iconColor: FFAE00`.
- Ocupação vertical: `y = 448..463` (altura de 15px).

---

### 2.2 Tela 2: Carrossel de Videogames (System View)

A tela principal de navegação de consoles apresenta o videogame selecionado com sua ficha histórica, controles e arte em cartaz.

#### Diagrama de Régua da System View (640x480):
```text
(0,0)                                                                        (639,0)
  +-----------------------------------------------------------------------------+ y=0
  |                                                                             |
  |  16-BIT / 1990 (shortdescription x=16, y=38)                                |
  |  SUPER NINTENDO (sys_line1 x=16, y=55)                                      |
  |  ENTERTAINMENT SYSTEM (sys_line2 x=16, y=77..150)                           |
  |                                                                             |
  |  [ (A) ENTRAR ] (buttonA x=16, y=221)                                       |
  |                                              +-------------------------+    |
  |  788 JOGOS DISPONÍVEIS                       |                         |    |
  |  (systemInfo x=16, y=274)                    |   CONTROLE DO CONSOLE   |    |
  |                                              |   (pos: 0.35 0.62)      |    |
  |  O SNES consolidou a era de ouro dos         |                         |    |
  |  jogos em 16-bit com gráficos Mode 7...      +-------------------------+    |
  |  (longdescription x=16, y=317..440)                                         |
  +-----------------------------------------------------------------------------+ y=455
  | (A) ENTRAR  (B) VOLTAR  (START) MENU                                        | y=463 (helpsystem)
  +-----------------------------------------------------------------------------+ y=479
```

#### Métricas dos Componentes:
- **Coluna de Informações**: Inicia na margem segura `x = 0.025` (16px).
- **`shortdescription`**: `pos: 0.025 0.080`, `size: 0.320 0.025`, `fontSize: 0.022`, `#FFFFFF`.
- **`sys_line1`**: `pos: 0.025 0.115`, `size: 0.975 0.045`, `fontSize: 0.045`, `#FFFFFF`.
- **`sys_line2`**: `pos: 0.025 0.160`, `size: 0.975 0.200`, `fontSize: 0.130`, `#FFFFFF`.
- **`buttonA`**: `pos: 0.025 0.460`, `size: 0 0.085`.
- **`systemInfo`**: `pos: 0.025 0.570`, `size: 0.400 0.042`, `fontSize: 0.050`, `#FFAE00`.
- **`longdescription`**: `pos: 0.025 0.660`, `size: 0.30 0.26`, `fontSize: 0.022`, `lineSpacing: 1.18`.
- **`controller`**: `pos: 0.35 0.62`, `maxSize: 0.28 0.28` (centralizado na metade inferior sem colidir com o rodapé).
- **`helpsystem`**: `pos: 0.025 0.965`, `origin: 0 1`, alinhado à esquerda.

---

### 2.3 Tela 3: Modal de Save State (`GuiSaveState`)

O diálogo de Save State permite visualizar e gerenciar os estados salvos de cada jogo através de uma janela modal sobreposta.

#### Diagrama de Régua do Modal de Save State (640x480):
```text
(0,0)                                                                        (639,0)
  +-----------------------------------------------------------------------------+
  |  Margem Superior da Tela (24px de respiro)                                  |
  |  +=======================================================================+  | y=24
  |  |  CARREGAR / SALVAR ESTADO                                             |  | y=24..68
  |  +-----------------------------------------------------------------------+  | y=68
  |  |                                                                       |  |
  |  |    +---------------+     +---------------+     +---------------+      |  |
  |  |    |    SLOT 1     |     |    SLOT 2     |     |    SLOT 3     |      |  | y=76
  |  |    | +-----------+ |     | +-----------+ |     | +-----------+ |      |  |
  |  |    | |           | |     | |           | |     | |           | |      |  |
  |  |    | | THUMBNAIL | |     | | THUMBNAIL | |     | | THUMBNAIL | |      |  | y=100..214
  |  |    | | (152x114) | |     | | (152x114) | |     | | (152x114) | |      |  |
  |  |    | +-----------+ |     | +-----------+ |     | +-----------+ |      |  |
  |  |    | 2026-10-31    |     | 2026-10-31    |     |    [VAZIO]    |      |  | y=225
  |  |    | 02:45         |     | 01:12         |     |               |      |  | y=238
  |  |    +---------------+     +---------------+     +---------------+      |  |
  |  |                                                                       |  |
  |  +-----------------------------------------------------------------------+  | y=416
  |  |  (A) CARREGAR  (X) NOVO SAVE  (Y) APAGAR  (B) CANCELAR                |  | y=416..456
  |  +=======================================================================+  | y=456
  |  Margem Inferior da Tela (24px de respiro)                                  |
  +-----------------------------------------------------------------------------+ y=479
  x=0   x=16                                                                x=624 x=639
        |<------------------- 608px de largura (95%) ---------------------->|
```

#### Métricas Estruturais do Modal:
- **Largura Útil do Modal**: **608 pixels** (`x = 16px` a `x = 624px`, ocupando 95% da tela). Alinhada perfeitamente com a margem de 16px do display.
- **Altura Útil do Modal**: **432 pixels** (`y = 24px` a `y = 456px`), com 24px de respiro simétrico superior e inferior.
- **Cabeçalho do Modal (`y = 24..68`)**:
  - Título alinhado à esquerda na coordenada `x = 32px` (16px de padding interno).
  - Fonte: `BebasNeue.otf`, cor `#FFAE00`, escala `0.045` (~21px).
- **Grid de Cards de Slots (`y = 76..408`)**:
  - 3 cards horizontais simétricos de ~170px de largura cada.
  - Thumbnail de captura: Proporção 4:3 com **152x114 pixels**, centralizada no card.
  - Título do Slot: Centralizado acima da thumbnail, em `#FFFFFF`.
  - Indicador de Seleção: Borda ativa `#FFAE00` (2px).
  - Rótulo de Data e Hora:
    - Posicionado abaixo da thumbnail com espaçamento seguro.
    - Tipografia compacta: `fontSize: 0.028` (~9.0px).
    - Evita corte de strings como `"2026-10-31 02:45"` mantendo mais de 20px de respiro lateral dentro do card.
- **Barra de Atalhos do Modal (`y = 416..456`)**:
  - Comandos alinhados estritamente **à esquerda** iniciando em `x = 32px`.
  - Tipografia: `Acre.otf`, `fontSize: 0.022`, ícones `#FFAE00` e textos `#A0A0A0`.

---

## 3. Decisões Técnicas de Engenharia

### Decisão 1: Proteção de Imagens no `feature.toml`
- **Problema**: O `./build.sh` sobrescrevia `_art/ingame-global-bg.png` ao descompactar o tarball upstream.
- **Solução**: Incluir `"_art/ingame-global-bg.*"` na diretiva `exclude` do `feature.toml`.
- **Efeito**: Garante que modificações locais de limpeza de imagem permaneçam perpétuas após qualquer rebuild.

### Decisão 2: Unificação de Views no `theme.xml`
- **Problema**: A fragmentação entre `<view name="basic">`, `<view name="detailed">` e `<view name="video">` causava omissão do `md_name` em algumas visualizações e permitia que o usuário ativasse modos que quebravam o layout pelo menu do EmuELEC.
- **Solução**: Fundir todas as declarações em `<view name="basic, detailed, video, grid">` com todos os elementos presentes (`top_label`, `nameLabel`, `gamelist`, `md_name`, `md_image`, `md_video`).

### Decisão 3: Alinhamento Universal dos Atalhos à Esquerda
- **Problema**: `helpsystem` com alinhamento à direita na gamelist colidia com o fluxo de leitura ocidental e contrastava com o alinhamento à esquerda da System View.
- **Solução**: Padronizar `pos: 0.025 ...` e `origin: 0 1` em todas as instâncias de `helpsystem`.

### Decisão 4: Calibração de Altura da Gamelist e Sincronização do Helpsystem
- **Problema**: `size y: 0.824` da lista de jogos avançava até `y = 453.1px`. Com os atalhos reposicionados na coordenada padrão do menu do carrossel (`pos: 0.025 0.965`, ocupando `y = 448..463px`), a lista de jogos colidia com os atalhos.
- **Solução**: Reduzir `size y` para `0.805`, finalizando a lista em `y = 444.0px`, garantindo respiro seguro de 4px antes dos botões de controle (`y = 448px`) e harmonizando a altura do rodapé entre o menu e a gamelist.

### Decisão 5: Alinhamento Milimétrico na Régua de "GAMES" e Itens da Lista
- **Problema**: O cabeçalho `top_label` ("GAMES") inicia em `x = 16.0px` (`pos: 0.025 0.025`). O componente `<textlist name="gamelist">` utilizava `<horizontalMargin>0.01</horizontalMargin>`, iniciando o texto dos jogos em `6.4px` (`0.01 * 640`), gerando desalinhamento visível de 9.6px à esquerda.
- **Solução**: Calibrar `<horizontalMargin>0.025</horizontalMargin>`.
- **Efeito**: O texto dos nomes dos jogos inicia rigorosamente na linha vertical `x = 16.0px`, alinhado à régua do cabeçalho.

### Decisão 6: Nome do Jogo em Branco Puro e Preview Adaptável sem Sobreposição
- **Problema**: `md_name` em cor âmbar (`#FFAE00`) competia visualmente com o jogo selecionado na lista e com o título do console. A caixa de preview de mídia (`0.60 0.60`) com o nome em `pos: 0.339 0.835` limitava o tamanho da imagem ou corria risco de sobreposição com títulos de jogos.
- **Solução**:
  - `md_name` alterado para branco puro (`#FFFFFF`).
  - `md_name` rebaixado para `pos: 0.339 0.865`, `size: 0.64 0.06` (`y = 415.2 .. 444.0px`).
  - Preview de mídia (`md_image`, `md_video`) reposicionado em `pos: 0.66 0.485` e ampliado para `<maxSize>0.62 0.70</maxSize>` (`y = 65 .. 401px`).
- **Efeito**: O preview adapta-se dinamicamente ao máximo da largura ou altura sem nunca tocar no título, preservando 14.2px de folga superior e 4.0px de folga inferior até os atalhos.

### Decisão 7: Término da Linha Divisória Vertical antes do Rodapé
- **Problema**: A linha divisória vertical em `x = 207` das imagens `_art/ingame-global-bg.png` e `.jpg` corria continuamente até `y = 479`, cortando a barra de atalhos e comprometendo a visibilidade dos ícones e textos do rodapé.
- **Solução**: Repintar os pixels `x = 206..208` no intervalo `y = 445..479` com a cor de fundo escuro nas duas imagens rasterizadas. A linha divisória finaliza em `y = 444px`.

### Decisão 8: Engenharia Reversa e Calibração Tipográfica do Modal de Save State
- **Análise do Binário EmulationStation**: A engenharia reversa de `GuiSaveState` (`/usr/bin/emulationstation`) revelou dois fatores concorrentes na tipografia do diálogo:
  1. O título do modal com o nome do jogo (`mTitle`) possui tamanho de fonte hardcoded em C++ via constante flutuante `0.085f` (offset `0x3138a4`), resultando em glifos gigantescos de `40.8px` (`0.085 * 480`) com a fonte interna `:/ubuntu_condensed.ttf`, extrapolando os limites em nomes longos.
  2. Os títulos de slots da grade multiplicam o tamanho da fonte do tema por `1.77f` (offset `0x313fe8`). Com `menutext` em `0.037` (17.8px), a fonte dos slots alcançava 31.4px.
- **Solução no Tema**:
  - No `<view name="menu">`, reduziu-se `<menuText name="menutitle">` para `fontSize: 0.038` (~18.2px) e `<menuText name="menutext">` para `fontSize: 0.030` (~14.4px).
  - Com essa calibração, a fonte multiplicada dos cards de slot cai para 25.5px, cabendo confortavelmente dentro do layout modal.
  - O tamanho de 40.8px do título do jogo é decorrente do binário upstream do EmuELEC; os offsets de patch binário (`0x3138a4`: `0.085f` -> `0.040f` e `0x313fe8`: `1.77f` -> `1.0f`) ficam documentados para eventual patch no pipeline de build.

---

## 4. Guia para Criação de Novas Telas ou Componentes

Qualquer nova tela ou elemento adicionado ao tema deve respeitar as seguintes regras fundamentais:

1. **Régua Horizontal**: Todo conteúdo alinhado à esquerda deve iniciar na coordenada de margem segura `x = 0.025` (16px) ou `x = 0.339` (217px para a coluna direita).
2. **Uso de Tipografia**:
   - Títulos, identificadores de sistema e rótulos curtos devem usar exclusivamente `BebasNeue.otf`.
   - Listas, sinopses, legendas e horários devem usar `Acre.otf`.
3. **Uso de Cores**:
   - Destaques, seleções e elementos de foco sempre utilizam âmbar `#FFAE00`.
   - Fundos são prioritariamente `#000000` ou `#1C1C1C`.
4. **Sem Elementos Flutuantes Soltos**: Nenhum elemento pode ultrapassar `y = 0.965` sem ser explicitamente uma barra de atalhos (`helpsystem`).
