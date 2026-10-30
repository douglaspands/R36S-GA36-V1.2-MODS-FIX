# Design

## Context

O EmulationStation no EmuELEC 4.7 carrega os arquivos de tradução gettext de `/usr/config/emuelec/configs/locale/<idioma>/LC_MESSAGES/emulationstation2.mo`.
Na imagem base, `pt_BR` possui 122 mensagens vazias e `es_MX` possui 148 mensagens vazias.
Os arquivos originais estão em formato texto `.po` e binário compilado `.mo`.

## Goals / Non-Goals

**Goals:**
- Completar 100% das mensagens vazias nos arquivos `.po` de `pt_BR` e `es_MX`.
- Manter as nomenclaturas técnicas consolidadas em inglês no catálogo `pt_BR` (*Save State*, *Core*, *Shader*, *Overlay*, *RetroAchievements*, *Scraper*, etc.).
- Adequar todas as frases para os limites físicos da tela de 3.5 polegadas (640x480).
- Compilar e entregar os arquivos `.mo` na partição `system` através de uma feature do build.

**Non-Goals:**
- Não alterar código C++ do binário do EmulationStation.
- Não alterar scripts de shell do sistema que não usem gettext.
- Não alterar outros idiomas além de `pt_BR` e `es_MX` (o `en_US` já é a fonte nativa).

## Decisions

1. **Camada de Entrega (SYSTEM via feature):**
   - *Decisão*: Criar a feature `features/12-localizacao-ui` (ou integrar em `features/10-ptbr-sao-paulo`) com os arquivos em `system/usr/config/emuelec/configs/locale/{pt_BR,es_MX}/LC_MESSAGES/`.
   - *Alternativa*: Gravar em `storage` (`/storage/.config/emuelec/configs/locale/`). Descartada porque o sistema lê primariamente do SYSTEM e o storage deve ser reservado para dados de usuário.

2. **Compilação de .po para .mo:**
   - *Decisão*: Compilar os arquivos `.mo` usando a ferramenta padrão `msgfmt` durante o desenvolvimento e commitar tanto o `.po` (legível e editável) quanto o `.mo` (binário consumido pelo ES).
   - *Alternativa*: Compilar dinamicamente no boot do aparelho. Descartada pois aumentaria o tempo de boot e adicionaria dependência de binários gettext desnecessários no console.

3. **Política de Nomenclatura Gamer:**
   - *Decisão*: Em `pt_BR`, manter termos como *Save State*, *Shader*, *Core*, *Scraper*, *Hotkey*, *Overlay* inalterados. Traduzir apenas ações (*Iniciar*, *Excluir*, *Ocultar*) e navegação (*Favoritos*, *Todos os Jogos*, *Recentes*).
   - *Alternativa*: Tradução literal completa. Descartada a pedido do usuário por prejudicar o entendimento técnico.

4. **Diretriz de Comprimento para 640x480:**
   - *Decisão*: Frases curtas e imperativas. Em opções de ordenação, utilizar formato padronizado como "Nome (A-Z)" em vez de "Ordenar por nome ascendente". Em confirmações, limitar a 2-4 palavras ("Iniciar mesmo assim?", "Tem certeza?").

## Risks / Trade-offs

- [Truncamento em diálogos estreitos] → Validação por contagem de caracteres (máximo ~35 caracteres por linha em caixas de aviso) e teste em emulador/aparelho.
- [Compatibilidade do charset UTF-8] → Garantir cabeçalho gettext explícito `Content-Type: text/plain; charset=UTF-8` e compilação sem warnings no `msgfmt`.
