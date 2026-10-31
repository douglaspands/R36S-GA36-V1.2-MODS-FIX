# Proposal: Localização do Top Label da Lista de Jogos no Tema Epic Cody ML

## Problem
Na tela de lista de jogos (`basic`, `detailed`, `video`) do tema padrão **Epic Cody ML**, o texto `"SELECT GAME"` aparece fixo em inglês no topo esquerdo da tela (acima da lista de títulos).

Investigando a estrutura do tema, constatou-se que:
1. O texto `"SELECT GAME"` está gravado diretamente como bitmap rasterizado no topo do arquivo de imagem de fundo da coluna de jogos: `_art/ingame-global-bg.png` (e `.jpg`), na região `x=0..204, y=20..50`.
2. O `theme.xml` raiz do tema já possui o elemento `<text name="top_label" extra="true">` posicionado exatamente naquela coordenada (`pos: 0.01 0.01`, `size: 0.20 0.08`, fonte `BebasNeue.otf`, cor `F8F8F8`, tamanho `0.039`), porém seu conteúdo está vazio (`<text></text>`).
3. Como o texto é desenhado diretamente nos pixels da imagem, ele não acompanha as trocas de idioma do tema feitas pelo seletor `<subset name="language">` (ficando sempre em inglês, inclusive para usuários em `pt-BR` ou `es-Latam`).

## Proposed Solution
Adotar a abordagem dinâmica orientada a componentes do EmulationStation:
1. **Limpeza da imagem de fundo**: Tratar a imagem `_art/ingame-global-bg.png` (e `.jpg`), removendo o texto estático "SELECT GAME" da região superior esquerda e preenchendo-a com a cor de fundo padrão sólida (`#000000` / `#0a0a0a`), mantendo as linhas decorativas e a separação da coluna intactas.
2. **Ativação da variável dinâmica `${top_label}`**:
   - No `theme.xml` raiz do Epic Cody ML, definir no bloco `<view name="basic, detailed, video">`:
     ```xml
     <text name="top_label" extra="true">
         <text>${top_label}</text>
         ...
     </text>
     ```
   - Adicionar a variável `top_label` nos catálogos de idiomas (`_languages/`):
     - `pt-br.xml`: `<top_label>GAMES</top_label>` (conforme solicitado pelo usuário)
     - `es-latam.xml`: `<top_label>JUEGOS</top_label>` (conforme alinhado)
     - `en.xml`: `<top_label>GAMES</top_label>`
3. **Sincronização do gerador e dos testes**:
   - Atualizar `tools/refatora_epic_cody_ml.py` para incluir `top_label` nos catálogos e na refatoração do `theme.xml` raiz.
   - Atualizar `tests/test_tema_epic_cody_ml.py` para garantir a presença, simetria e valores corretos de `top_label`.

## Scope
- **In scope**:
  - Limpeza de `SELECT GAME` em `_art/ingame-global-bg.png` e `_art/ingame-global-bg.jpg`.
  - Configuração de `<text>${top_label}</text>` em `theme.xml`.
  - Inserção de `top_label` em `pt-br.xml` ("GAMES"), `es-latam.xml` ("JUEGOS") e `en.xml` ("GAMES").
  - Atualização do script `tools/refatora_epic_cody_ml.py`.
  - Atualização dos testes automatizados em `tests/test_tema_epic_cody_ml.py`.
- **Out of scope**:
  - Alterações em outros temas (NES-BOX, Minimal, Graphite).
  - Alterações nas traduções de menus do EmulationStation (`.po`/`.mo`).
