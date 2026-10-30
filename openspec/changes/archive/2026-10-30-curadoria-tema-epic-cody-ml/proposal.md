# Proposal

## Why

O tema padrão **Epic Cody ML** no R36S (tela compacta de 3.5", 640x480) apresenta problemas críticos de design, usabilidade e tipografia no aparelho real:
1. **Nomes de consoles truncados com reticências**: A caixa de texto de `sys_line2` com largura fixa de `0.45` e tamanho de fonte `0.18` estrangula títulos de consoles com mais de 7 caracteres, exibindo abreviações desfiguradas como `"GAME..."` (GameBoy Color), `"NINT..."` (Nintendo 64) e `"PLAY..."` (PlayStation) em mais de 50 sistemas.
2. **Rodapé desproporcional e colidindo com o console**: A ausência de estilização explícita de `<helpsystem>` na visualização de sistema faz o EmulationStation injetar o rodapé padrão da base em fonte gigante e esticada de ponta a ponta, colidindo visualmente com a imagem do console (`controller`), cuja posição inferior sobrepõe diretamente as legendas de navegação.
3. **Desalinhamento e margens coladas no aro do display**: Elementos de texto ancorados em `pos: 0.003` (menos de 2 pixels do aro plástico do R36S) transmitem aspecto amador e desconfortável.
4. **Termos em inglês remanescentes**: O botão principal exibe o badge fixo `(A) ENTER` em inglês desenhado em SVG, e diversos metadados e categorias em `_languages/pt-br.xml` mantêm expressões em inglês (como `retroarch.nameLabel` = *"Options"*, `gameandwatch.sys_line1` = *"LCD SCREEN"*, `coco.sys_line1` = *"Color COMPUTER"* e `ports.sys_line1` = *"Game"*).

Esta change realiza uma curadoria completa de UX e Design no tema Epic Cody ML, restaurando o alinhamento elegante do original upstream de CodyV59, eliminando truncamentos e entregando uma interface refinada, equilibrada e 100% localizada.

## What Changes

- **Hierarquia Tipográfica e Fim dos Truncamentos**:
  - Reestruturação da divisão de títulos: Linha 1 (`sys_line1`) como marca/família (ex: `Nintendo Game Boy`, `Nintendo`, `Sony`, `Coleção`) e Linha 2 (`sys_line2`) como identidade principal (ex: `Color`, `64`, `DS`, `PlayStation`, `Todos os Jogos`).
  - Inclusão da tag `<text name="sys_line1">` nos 59 consoles que não a possuíam em seus `theme.xml`.
  - Calibragem de `sys_line2` no `theme.xml` raiz com `fontSize: 0.130` e expansão da largura da caixa para a largura total da tela (`size: 0.975`), garantindo que nomes de consoles (como Super Nintendo, Game Boy Advance, etc.) caibam inteiramente sem gerar reticências (`...`), abreviando apenas se o texto ultrapassar a tela.
- **Rodapé Elegante e Eliminação de Sobreposição de Imagem**:
  - Estilização explícita de `<helpsystem name="help">` em `<view name="system">` e `<view name="basic, detailed, video">` com a fonte `./_art/Acre.otf`, escala discreta `fontSize: 0.022`, ícones na cor de destaque âmbar (`#FFAE00`) e textos em cinza suave (`#A0A0A0`).
  - Redimensionamento e reposicionamento do gráfico do console (`controller`): de `maxSize: 0.33 0.33` em `pos: 0.35 0.65` para `maxSize: 0.28 0.28` em `pos: 0.35 0.62`, criando um respiro livre de mais de 24 pixels entre a imagem e as legendas de navegação inferiores.
- **Grid de Alinhamento e Margem Segura (Safe Margins)**:
  - Alinhamento de todos os elementos da coluna de informações esquerda (`shortdescription`, `sys_line1`, `sys_line2`, `buttonA`, `systemInfo`, `longdescription`) em uma linha-guia visual consistente a `x = 0.025` (~16 pixels da borda), evitando proximidade excessiva com o aro plástico da carcaça.
- **Curadoria Completa de Tradução e Localização**:
  - Badge do botão principal dinâmico por idioma via SVG: criação de `button-pt.svg` com `(A) ENTRAR` e `button-es.svg` com `(A) ENTRAR`, mantendo `button.svg` original para inglês (`(A) ENTER`).
  - Tradução e limpeza de todos os termos remanescentes em inglês nos catálogos `_languages/pt-br.xml` e `_languages/es-latam.xml` (`Options` -> `RetroArch`, `Pixel Games` -> `Console Fantasia`, `LCD SCREEN` -> `Portátil LCD`, `Game` -> `Jogos Nativos`, etc.), além da padronização de maiúsculas/minúsculas.
- **Atualização do utilitário gerador**:
  - Atualização de `tools/refatora_epic_cody_ml.py` para refletir as novas regras de curadoria, layout e catálogos de tradução.

## Capabilities

### New Capabilities
Nenhuma.

### Modified Capabilities
- `es-themes`: atualiza os requisitos visuais do tema Epic Cody ML para proibir truncamento por reticências em títulos de consoles na tela de 640x480, exigir margem segura à esquerda, espaçamento sem colisão entre a imagem do console e o rodapé de navegação, e localização integral do botão de ação e metadados.

## Impact

- **Temas do EmulationStation**: alterações restritas aos arquivos de layout e idiomas em `features/50-temas-extras/storage/.config/emulationstation/themes/Epic Cody ML/` (`theme.xml`, consoles `*/theme.xml`, `_languages/*.xml`, `_art/var/`).
- **Scripts de ferramenta**: `tools/refatora_epic_cody_ml.py`.
- **Compatibilidade**: total aderência à especificação de temas do EmulationStation e suporte multi-idioma nativo (pt-br, es-latam, en).
