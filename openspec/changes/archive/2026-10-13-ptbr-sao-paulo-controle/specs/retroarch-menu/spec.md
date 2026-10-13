# Spec Delta

## Purpose

Definir qual driver de menu o RetroArch usa na imagem gerada e garantir que essa escolha se mantenha a cada jogo iniciado pelo EmuELEC.

## ADDED Requirements

### Requirement: Menu RGUI no RetroArch
A imagem gerada SHALL fazer o RetroArch usar o driver de menu RGUI em todos os cores.

#### Scenario: Menu aberto durante um jogo
- **WHEN** o usuário abre o menu do RetroArch em qualquer core
- **THEN** o menu exibido é o RGUI

### Requirement: Menu mantido entre jogos
A escolha do RGUI SHALL ficar declarada na configuração global do EmuELEC, que o sistema reaplica ao RetroArch antes de cada jogo, para que o RGUI não seja trocado de volta para o XMB padrão do A33.

#### Scenario: Segundo jogo após o boot
- **WHEN** o usuário sai de um jogo e inicia outro, de outro sistema
- **THEN** o menu do RetroArch continua sendo o RGUI

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmuELEC declara `global.retroarch.menu_driver=rgui`, e a do RetroArch declara `menu_driver = "rgui"`
