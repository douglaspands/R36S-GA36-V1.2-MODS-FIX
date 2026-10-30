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

### Requirement: Drivers de periféricos inexistentes desativados no RetroArch
A imagem gerada e o serviço de preparação do RetroArch no boot SHALL definir `wifi_enabled = "false"`, `wifi_driver = "null"`, `bluetooth_driver = "null"`, `microphone_driver = "null"` e `midi_driver = "null"` no `retroarch.cfg`.

#### Scenario: Configuração conferida na imagem
- **WHEN** o `retroarch.cfg` da p8 da imagem gerada é inspecionado
- **THEN** ele traz `wifi_enabled = "false"` e os quatro drivers em `"null"`

#### Scenario: Cartão atualizado com --keep-storage
- **WHEN** o `retroarch.cfg` da p8 traz os drivers de fábrica (`connmanctl`, `bluetoothctl`, `alsathread`, `alsa`) e o aparelho liga com o SYSTEM novo
- **THEN** o serviço de boot troca cada um para `"null"` e `wifi_enabled` para `"false"`

### Requirement: Itens de rede, streaming, gravação e rewind ocultos no menu do RetroArch
A imagem gerada e o serviço de preparação do RetroArch no boot SHALL definir `menu_show_rewind = "false"`, `menu_show_online_updater = "false"`, `quick_menu_show_download_thumbnails = "false"`, `quick_menu_show_start_recording = "false"`, `quick_menu_show_start_streaming = "false"`, `settings_show_network = "false"`, `settings_show_achievements = "false"` e `settings_show_ai_service = "false"` no `retroarch.cfg`.

#### Scenario: Configuração de visibilidade no retroarch.cfg
- **WHEN** o `retroarch.cfg` da p8 da imagem gerada ou após o boot é inspecionado
- **THEN** as oito chaves de visibilidade valem `"false"`
