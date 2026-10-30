# system-locale Specification

## Purpose

Definir o idioma e o fuso horário que a imagem gerada usa no sistema, no EmulationStation e no menu do RetroArch, para que o aparelho saia do cartão em português do Brasil e no horário de São Paulo.

## Requirements

### Requirement: Idioma do sistema em português do Brasil
A imagem gerada SHALL configurar o EmuELEC com o idioma `pt_BR`, de modo que o EmulationStation mostre seus menus em português do Brasil a partir do primeiro boot.

#### Scenario: Primeiro boot com storage gravado pela imagem
- **WHEN** o cartão é gravado com `--wipe-storage` e o aparelho inicia
- **THEN** os menus do EmulationStation aparecem em português do Brasil

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmuELEC declara o idioma `pt_BR`, e a configuração do EmulationStation declara `Language` = `pt_BR`

### Requirement: Fuso horário de São Paulo
A imagem gerada SHALL configurar o fuso horário do sistema como `America/Sao_Paulo`.

#### Scenario: Relógio no aparelho
- **WHEN** o aparelho inicia com o storage gravado pela imagem
- **THEN** o fuso horário ativo é `America/Sao_Paulo`

### Requirement: Demais configurações preservadas
As mudanças de idioma e fuso SHALL preservar todas as outras chaves dos arquivos de configuração de fábrica que alteram.

#### Scenario: Comparação com a fábrica
- **WHEN** cada arquivo de configuração alterado pela feature é comparado com o original de fábrica
- **THEN** as únicas diferenças são as chaves de idioma, fuso e menu definidas por este change

### Requirement: Menu do RetroArch em português do Brasil
A imagem gerada SHALL deixar o menu do RetroArch em português do Brasil, junto com o sistema e o EmulationStation, declarando `user_language = "7"` no `retroarch.cfg` de fábrica da p8.

#### Scenario: Menu aberto durante um jogo
- **WHEN** o usuário abre o menu do RetroArch durante um jogo, numa p8 gravada pela imagem
- **THEN** os textos do menu aparecem em português do Brasil

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do RetroArch declara `user_language = "7"` e a do EmulationStation declara `Language` = `pt_BR`

#### Scenario: Idioma trocado pelo usuário
- **WHEN** o usuário escolhe outro idioma em Settings > User Interface > Language e salva
- **THEN** o RetroArch mantém o idioma escolhido

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
