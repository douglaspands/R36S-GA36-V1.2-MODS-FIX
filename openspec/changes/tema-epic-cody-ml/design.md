# Design

## Context

O tema Epic Cody (`es-theme-epic-cody-RG351V`) possui textos em inglês distribuídos em arquivos `theme.xml` em mais de 60 subdiretórios de consoles e coleções.
O EmulationStation no EmuELEC suporta o elemento `<subset>` no arquivo raiz `theme.xml`, permitindo carregar arquivos XML condicionais baseados na escolha do usuário no menu do tema.
Além disso, elementos `<text>` no EmulationStation suportam substituição de variáveis com a sintaxe `${nome_da_variavel}`.

## Goals / Non-Goals

**Goals:**
- Desacoplar todos os textos do tema em catálogos externos: `_languages/pt-br.xml`, `_languages/es-latam.xml` e `_languages/en.xml`.
- Configurar o seletor `<subset name="language">` com `pt-br` como primeira opção (padrão no boot).
- Preservar termos técnicos e clássicos (*16-bit*, *Arcade*, *RPGs*, *Shmups*, etc.) em português.
- Calibrar o comprimento dos textos para a janela de 640x480 (especialmente `shortdescription` e `longdescription`).
- Automatizar a extração e refatoração do tema via script para evitar erros manuais em 60+ pastas.

**Non-Goals:**
- Não alterar a arte gráfica original, logos, fontes ou layout dos elementos do tema.
- Não adicionar novos consoles que não existam no tema original upstream.

## Decisions

1. **Arquitetura de Variáveis e Subsets:**
   - *Decisão*: O `theme.xml` principal define o `<subset name="language">` que inclui `./_languages/<lang>.xml`. Cada arquivo de idioma define variáveis no bloco `<variables>` (ex: `<snes.short>`, `<snes.desc>`). Os `theme.xml` dos consoles apenas referenciam essas variáveis (`${snes.short}`).
   - *Alternativa*: Ter pastas de consoles separadas por idioma (ex: `snes-pt/`, `snes-en/`). Descartada por duplicar todo o peso do tema e quebrar a compatibilidade de nomes de sistemas do ES.

2. **Geração Automatizada com Script Python:**
   - *Decisão*: Criar um utilitário em `tools/` que descompacta o tema original, extrai os blocos `<text>` para gerar `_languages/en.xml` e os templates para `pt-br.xml` e `es-latam.xml`, e regrava os `theme.xml` com as tags de variáveis.
   - *Alternativa*: Edição manual de cada um dos mais de 60 arquivos `theme.xml`. Descartada por ser propensa a erros de sintaxe e inconsistências.

3. **Ordem dos Idiomas no Subset:**
   - *Decisão*: A ordem das tags `<include>` no `<subset name="language">` será `pt-br`, seguido de `es-latam` e `en`. No EmulationStation, quando não há seleção explícita salva em `es_settings.cfg`, o primeiro `<include>` do subset é ativado por padrão.

4. **Calibração de Texto para 640x480:**
   - *Decisão*: Limitar `shortdescription` a no máximo 30 caracteres (1 linha). Limitar `longdescription` a no máximo 180 caracteres distribuídos em 3-4 linhas curtas, evitando truncamento e garantindo legibilidade com a fonte *Acre* do tema.

5. **Substituição e Remoção do Tema Original da Imagem:**
   - *Decisão*: Remover o tema original `Epic Cody` da feature `50-temas-extras` (adicionando remoção se necessário ou substituindo o download) e definir `Epic Cody ML` como o único tema da família Epic presente na partição `storage`. O `es_settings.cfg` apontará para `Epic Cody ML`.
   - *Alternativa*: Manter ambos os temas instalados. Descartada pelo usuário para economizar espaço em disco na partição `storage` (evitando ocupar ~180 MiB extras).

## Risks / Trade-offs

- [Variáveis não definidas para algum sistema raro] → O script de extração garante cobertura de 100% dos nós `<text>` mapeados no tema upstream; caso falte em um idioma novo, haverá fallback do valor padrão.
- [Impacto de performance no carregamento do tema] → O parser XML do EmulationStation processa os arquivos de variáveis em milissegundos na memória durante o boot; sem impacto perceptível.
