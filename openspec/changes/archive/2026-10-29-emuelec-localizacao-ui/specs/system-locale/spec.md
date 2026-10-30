# Spec Delta

## ADDED Requirements

### Requirement: Menus e caixas de diálogo do EmulationStation totalmente localizados
O EmulationStation SHALL possuir catálogos de mensagens completos para os idiomas `pt_BR` e `es_MX`, sem mensagens vazias que provoquem fallback para o inglês nos menus de ordenação, scrapers, diálogos de confirmação e opções de interface.

#### Scenario: Menus secundários em português
- **WHEN** o idioma ativo no EmulationStation é `pt_BR` e o usuário acessa as opções de ordenação da lista de jogos, diálogos de confirmação ou configurações de scraper
- **THEN** todas as opções e mensagens são exibidas em português do Brasil sem termos órfãos em inglês

#### Scenario: Menus secundários em espanhol latino
- **WHEN** o idioma ativo no EmulationStation é `es_MX` e o usuário acessa as opções e diálogos do sistema
- **THEN** as opções e mensagens são exibidas em espanhol latino-americano sem mensagens órfãs em inglês

### Requirement: Preservação de termos técnicos e limites de tela
As traduções para `pt_BR` e `es_MX` no EmulationStation SHALL manter termos técnicos consagrados da emulação em inglês (como Save State, Core, Shader, Scraper, Overlay, RetroAchievements e Hotkey) e SHALL restringir o comprimento das frases para evitar truncamento ou sobreposição na tela de 640x480.

#### Scenario: Visualização em tela de 3.5 polegadas (640x480)
- **WHEN** o usuário abre qualquer menu ou caixa de diálogo no EmulationStation em `pt_BR` ou `es_MX`
- **THEN** os textos não excedem a largura visível das caixas de diálogo e os termos técnicos consagrados permanecem em inglês no catálogo `pt_BR`
