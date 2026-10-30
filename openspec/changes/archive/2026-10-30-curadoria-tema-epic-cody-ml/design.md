# Design

## Context

O tema Epic Cody ML é o tema padrão do sistema instalado na partição `storage` (p8) em `.config/emulationstation/themes/Epic Cody ML`. Ele utiliza variáveis carregadas de `_languages/` (`pt-br.xml`, `es-latam.xml`, `en.xml`) via `<subset name="language">`.

O display do R36S possui proporção 4:3 com resolução 640x480 e diagonal de 3.5 polegadas com moldura física de plástico. Mudanças anteriores introduziram `<size>0.45 0.20</size>` em `sys_line2` no `theme.xml` raiz na tentativa de evitar sobreposição com o poster de arte à direita, mas sem ajustar o tamanho da fonte (`0.18`) nem normalizar a hierarquia de nomes entre Linha 1 e Linha 2, gerando truncamento generalizado com reticências (`...`) em mais de 50 sistemas. Além disso, a ausência de configuração de `<helpsystem>` na visualização de sistema ativava o rodapé nativo desproporcional do EmulationStation que colidia com a arte dos controles.

## Goals / Non-Goals

**Goals:**
- Eliminar 100% dos truncamentos por reticências em nomes de sistemas e coleções no carrossel de 640x480.
- Reestruturar a titulação em duas linhas legíveis e equilibradas (Linha 1: Marca/Família; Linha 2: Modelo/Identificador).
- Estilizar o rodapé (`helpsystem`) de forma discreta e elegante com a paleta do tema (Acre 0.022, ícones âmbar `#FFAE00`, texto cinza neutro `#A0A0A0`).
- Redimensionar o gráfico do console (`controller`) para garantir respiro livre acima do rodapé, eliminando sobreposições.
- Aplicar margem segura à esquerda (`x = 0.025`, ~16px) em todos os elementos da coluna de texto.
- Localizar o badge visual do botão A para `(A) ENTRAR` em português e espanhol.
- Limpar e traduzir termos remanescentes em inglês em `pt-br.xml` e `es-latam.xml`.
- Manter o script `tools/refatora_epic_cody_ml.py` sincronizado com essas definições de layout e tradução.

**Non-Goals:**
- Não alterar a estrutura de diretórios dos temas nem mover arquivos para fora da partição `storage`.
- Não alterar as ilustrações de fundo (`_art/posters/`) nem a arte original dos consoles (`_art/controllers/`).

## Decisions

### 1. Hierarquia Tipográfica e Bounding Box de Títulos

- **Decisão**: 
  - `sys_line1`: BebasNeue, `fontSize: 0.045`, `pos: 0.025 0.115`, `size: 0.975 0.045`.
  - `sys_line2`: BebasNeue, `fontSize: 0.130`, `pos: 0.025 0.160`, `size: 0.975 0.200`.
  - Delimitação da largura da tela: A caixa de texto ocupa toda a largura disponível da tela (`x = 0.025` até `1.000`), evitando qualquer abreviação prematura com reticências (`...`) para consoles como "Super Nintendo", "Game Boy Advance", "Master System", etc. Apenas se o título ultrapassar a borda física da tela o EmulationStation aplicará o corte com reticências.
  - Inserção sistemática de `<text name="sys_line1">` nos 59 consoles que não possuíam essa linha em seus `theme.xml`.
- **Alternativa descartada**: Manter `<size>0.45 0.20</size>` ou `<size>0.52 0.20</size>`. Descartada porque causava truncamento prematuro com reticências ("Super Ninte...", "Game Boy Adva...", etc.) mesmo havendo espaço livre na tela.
- **Alternativa descartada**: Apenas encolher a fonte para `0.08`. Descartada porque enfraqueceria o impacto visual "Hero" característico do tema Epic Cody.

### 2. Estilização do HelpSystem e Reposicionamento do Gráfico do Console

- **Decisão**: 
  - Adicionar bloco `<helpsystem name="help">` em `<view name="system">` configurado com:
    - `<fontPath>./_art/Acre.otf</fontPath>`
    - `<fontSize>0.022</fontSize>`
    - `<textColor>A0A0A0</textColor>`
    - `<iconColor>FFAE00</iconColor>`
    - `<pos>0.025 0.965</pos>`
    - `<origin>0 1</origin>`
  - Reposicionar e redimensionar o gráfico do console:
    - `controller`: `pos: 0.35 0.62`, `maxSize: 0.28 0.28`. O limite inferior passa a ser `y = 0.90`, deixando 24 pixels de espaço livre até o rodapé em `y = 0.94 - 0.965`.
- **Alternativa descartada**: Ocultar o rodapé completamente (`<pos>2 2</pos>`). Descartada porque remove as instruções essenciais de navegação do usuário (Start = Menu, Y = Navegação rápida, Select = Aleatório).

### 3. Margem Segura da Coluna de Informações (Safe Margins)

- **Decisão**: Fixar a coordenada horizontal de todos os elementos alinhados à esquerda em `x = 0.025` (~16 pixels da borda):
  - `shortdescription`: `pos: 0.025 0.080`
  - `sys_line1`: `pos: 0.025 0.115`
  - `sys_line2`: `pos: 0.025 0.160`
  - `buttonA`: `pos: 0.025 0.460`
  - `systemInfo`: `pos: 0.025 0.570`
  - `longdescription`: `pos: 0.025 0.660`, `size: 0.30 0.26`
- **Alternativa descartada**: Manter `pos: 0.003`. Descartada porque textos colados no bisel plástico causam desconforto e parecem cortados no aparelho real.

### 4. Localização do Botão de Ação e Catálogos de Variáveis

- **Decisão**:
  - Criar `_art/var/button-pt.svg` e `_art/var/button-es.svg` vetorizados com o texto `ENTRAR` ao lado do círculo `(A)`, garantindo o traçado da letra 'A' em sentido horário (CW) e seu miolo em sentido anti-horário (CCW) para respeitar a *nonzero winding rule* do NanoSVG, impedindo que a letra A seja preenchida como massa sólida ("ENTR R").
  - Manter `_art/var/button.svg` original com `(A) ENTER` para inglês.
  - Definir a variável `<buttonImage>` em `_languages/*.xml`:
    - `pt-br.xml`: `./_art/var/button-pt.svg`
    - `es-latam.xml`: `./_art/var/button-es.svg`
    - `en.xml`: `./_art/var/button.svg`
  - No `theme.xml` raiz: `<image name="buttonA"><path>${buttonImage}</path></image>`.
  - Revisar e traduzir termos ingleses residuais em `pt-br.xml` e `es-latam.xml` (ex: `Options` -> `RetroArch`, `Pixel Games` -> `Console Fantasia`, `LCD SCREEN` -> `Portátil LCD`, `Game` -> `Jogos Nativos`, `Multiple Arcade Machine Emulator` -> `Emulador Arcade`).

## Risks / Trade-offs

- [Novos consoles adicionados no futuro sem a tag `sys_line1`] → O script `tools/refatora_epic_cody_ml.py` automatiza a geração incluindo sempre os nós necessários para novos sistemas.
- [Texto longo de descrição ultrapassar limite inferior] → O limite de caracteres em `longdescription` já é protegido no script (<= 190 caracteres), e o espaçamento ajustado em `y = 0.66` garante folga vertical.
