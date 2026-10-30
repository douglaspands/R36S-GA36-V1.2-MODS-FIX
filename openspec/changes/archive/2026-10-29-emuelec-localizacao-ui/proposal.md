# Proposal

## Why

O EmulationStation de fábrica no EmuELEC 4.7 possui 122 strings sem tradução em português do Brasil (`pt_BR`) e 148 strings em espanhol latino (`es_MX`). Quando o usuário navega em menus secundários (como opções de ordenação, scrapers, diálogos de confirmação de ocultar jogos e menus de rede), a interface recorre ao texto original em inglês.

Além disso, como a tela do R36S clone (GA36-MB V1.2) possui dimensões compactas de 3.5 polegadas (640x480), traduções literais frequentemente excedem o tamanho dos botões e caixas de diálogo, gerando textos truncados ou quebras de linha indesejadas. 

Por fim, no ecossistema de retrogaming brasileiro, termos técnicos consagrados (como *Save State*, *Core*, *Shader*, *Scraper*, *Overlay*, *RetroAchievements*, *Hotkey*, *ROMs*) são universalmente compreendidos em inglês, e sua tradução literal causa estranheza e confusão. Uma localização de alta qualidade deve preservar esses termos técnicos em inglês enquanto traduz fluentemente a interface, ações e diálogos.

## What Changes

- **Tradução completa de `pt_BR`**: preenchimento das 122 strings vazias do arquivo `emulationstation2.po` para português do Brasil.
- **Tradução completa de `es_MX`**: preenchimento das 148 strings vazias do arquivo `emulationstation2.po` para espanhol latino-americano.
- **Preservação de nomenclaturas técnicas**: termos técnicos consagrados (*Save State*, *Core*, *Shader*, *Scraper*, *Overlay*, *Bezel*, *RetroAchievements*, *Netplay*, *Rewind*, *Hotkey*, *ROMs*, *BIOS*, *Boxart*, *Marquee*, *Snapshot*, *Wheel*) permanecem em inglês em `pt_BR`.
- **Sensibilidade visual para tela de 3.5" (640x480)**: calibração de textos de ações e mensagens para que sejam curtos e concisos (ex: "Nome (A-Z)" em vez de "Ordenar por nome ascendente", "Iniciar mesmo assim?" em vez de "Deseja iniciar o jogo assim mesmo?"), prevenindo estouro de layouts e caixas de diálogo.
- **Compilação e entrega no SYSTEM**: inclusão dos arquivos binários compilados `emulationstation2.mo` e fontes `.po` sob `usr/config/emuelec/configs/locale/{pt_BR,es_MX}/LC_MESSAGES/` através de uma feature do build.

## Capabilities

### New Capabilities
Nenhuma.

### Modified Capabilities
- `system-locale`: estende os requisitos de idioma para exigir cobertura completa (sem fallback em inglês) nos menus e caixas de diálogo do EmulationStation para `pt_BR` e `es_MX`, preservando nomenclaturas técnicas em inglês e restringindo comprimentos para a resolução 640x480.

## Impact

- **Sistema (SYSTEM / squashfs)**: sobrescrita dos arquivos `emulationstation2.po` e `emulationstation2.mo` em `usr/config/emuelec/configs/locale/pt_BR/LC_MESSAGES/` e `es_MX/LC_MESSAGES/`.
- **Experiência do Usuário**: eliminação de textos em inglês ao navegar pelo EmulationStation em português ou espanhol latino, com terminologia técnica gamer padronizada e adequada à tela de 3.5 polegadas.
- **Build**: compilação limpa via `msgfmt` ou inclusão direta dos `.mo` compilados na árvore de features.
