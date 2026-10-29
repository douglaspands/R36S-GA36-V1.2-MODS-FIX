# retroarch-menu Specification

## Purpose

Definir qual driver de menu o RetroArch usa na imagem gerada e garantir que essa escolha se mantenha a cada jogo iniciado pelo EmuELEC.

## Requirements

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

### Requirement: Padrões de aparência e uso do RetroArch
A imagem gerada SHALL declarar no `retroarch.cfg` de fábrica da p8: `custom_viewport_width = "768"` e `custom_viewport_height = "672"`, `rgui_aspect_ratio = "11"`, `menu_show_load_content_animation = "false"` e `notification_show_autoconfig = "false"`. Cada valor SHALL poder ser mudado pelo menu do RetroArch, e o RetroArch SHALL gravar a mudança.

#### Scenario: Configuração conferida no PC
- **WHEN** o `retroarch.cfg` da p8 de uma imagem gerada é inspecionado
- **THEN** ele traz os cinco valores acima

#### Scenario: Sem animação nem aviso ao abrir um jogo
- **WHEN** o usuário abre um jogo com o controle já configurado
- **THEN** não aparecem a animação de carregamento de conteúdo nem o aviso de autoconfig do controle

#### Scenario: Valor mudado pelo usuário
- **WHEN** o usuário muda o viewport personalizado no menu e salva
- **THEN** o RetroArch mantém o valor novo nos jogos seguintes
