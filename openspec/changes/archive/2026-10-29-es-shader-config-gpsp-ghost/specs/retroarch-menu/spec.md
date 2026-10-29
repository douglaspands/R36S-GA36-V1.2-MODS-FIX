## ADDED Requirements

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
