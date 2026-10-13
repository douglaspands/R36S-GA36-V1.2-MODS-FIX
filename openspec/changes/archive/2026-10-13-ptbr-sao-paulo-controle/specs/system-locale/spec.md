# Spec Delta

## Purpose

Definir o idioma e o fuso horário que a imagem gerada usa no sistema, no EmulationStation e no menu do RetroArch, para que o aparelho saia do cartão em português do Brasil e no horário de São Paulo.

## ADDED Requirements

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

### Requirement: Menu do RetroArch em português do Brasil
A imagem gerada SHALL configurar o RetroArch para mostrar seu menu em português do Brasil.

#### Scenario: Menu aberto durante um jogo
- **WHEN** o usuário abre o menu do RetroArch durante um jogo
- **THEN** os textos do menu aparecem em português do Brasil

### Requirement: Demais configurações preservadas
As mudanças de idioma e fuso SHALL preservar todas as outras chaves dos arquivos de configuração de fábrica que alteram.

#### Scenario: Comparação com a fábrica
- **WHEN** cada arquivo de configuração alterado pela feature é comparado com o original de fábrica
- **THEN** as únicas diferenças são as chaves de idioma, fuso e menu definidas por este change
