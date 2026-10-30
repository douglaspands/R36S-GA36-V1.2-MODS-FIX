# Spec Delta

## ADDED Requirements

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
