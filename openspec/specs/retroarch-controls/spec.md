# retroarch-controls Specification

## Purpose

Definir como o controle embutido do R36S (`micro_gamepad`) é mapeado no RetroArch: botões do RetroPad pela posição física e atalhos que não interferem no jogo.

## Requirements

### Requirement: RetroPad pela posição física
No RetroArch, o controle embutido SHALL mapear os botões de face pela posição física: o de baixo é o B do RetroPad, o da direita é o A, o de cima é o X e o da esquerda é o Y, em todos os cores.

#### Scenario: Botões de face no SNES
- **WHEN** o usuário aperta o botão de baixo do aparelho num jogo de SNES
- **THEN** o jogo recebe o botão B, e o botão da direita gera o A, o de cima o X e o da esquerda o Y

#### Scenario: Botões de face no PlayStation
- **WHEN** o usuário aperta o botão de baixo do aparelho num jogo de PlayStation
- **THEN** o jogo recebe o botão ✕

#### Scenario: Números de botão no autoconfig
- **WHEN** o autoconfig do `micro_gamepad` da imagem gerada é inspecionado
- **THEN** ele declara B = botão 1, A = botão 0, X = botão 2 e Y = botão 3, com o driver `sdl2`

### Requirement: Direcional livre de atalhos
Nenhum botão do direcional SHALL ser o hotkey ou disparar uma ação do RetroArch. O direcional SHALL chegar ao jogo sempre, sozinho ou combinado com outros botões.

#### Scenario: Direcional para baixo durante o jogo
- **WHEN** o usuário aperta ou segura o direcional para baixo num core do RetroArch
- **THEN** o jogo recebe o comando para baixo, e o volume não muda

#### Scenario: Baixo combinado com outro botão
- **WHEN** o usuário aperta baixo junto com R, L, B ou Start durante o jogo
- **THEN** nenhum save state é salvo ou carregado, e o jogo não é reiniciado nem encerrado

### Requirement: Hotkey no Select com atalhos de fábrica
O hotkey SHALL ser o Select. Os atalhos SHALL ser os de fábrica: X = menu, Y = screenshot, L e R = carregar e salvar estado, L2 = câmera lenta, R2 = avanço rápido, Start = sair. Pausa e FPS SHALL ficar nos mesmos botões físicos de fábrica: baixo = pausa, direita = FPS.

#### Scenario: Abrir o menu
- **WHEN** o usuário aperta Select + X durante o jogo
- **THEN** o menu do RetroArch abre

#### Scenario: Salvar estado
- **WHEN** o usuário aperta Select + R durante o jogo
- **THEN** o RetroArch salva o estado no slot atual

#### Scenario: Pausa no botão de baixo
- **WHEN** o usuário aperta Select + o botão de baixo durante o jogo
- **THEN** o jogo pausa

#### Scenario: Atalhos que não são de fábrica
- **WHEN** o autoconfig da imagem gerada é inspecionado
- **THEN** não há atalhos de volume, troca de slot, reset nem rewind ligados a botões do controle

### Requirement: Remaps por core preservados
Os remaps por core que vêm de fábrica SHALL continuar na imagem sem alteração.

#### Scenario: Remap de N64
- **WHEN** a p8 da imagem gerada é comparada com a de fábrica
- **THEN** os arquivos de `.config/retroarch/config/remappings/` são idênticos aos de fábrica

### Requirement: OK e Cancel dos menus sem inversão
Nos menus do RetroArch, o RetroPad A (botão da direita) SHALL ser OK e o RetroPad B (botão de baixo) SHALL ser Cancel. A configuração NÃO SHALL inverter os dois.

#### Scenario: Configuração conferida no PC
- **WHEN** o `retroarch.cfg` da p8 da imagem gerada é inspecionado
- **THEN** ele declara `menu_swap_ok_cancel_buttons = "false"`

#### Scenario: Confirmar e voltar no menu
- **WHEN** o usuário abre o menu do RetroArch e aperta o botão da direita sobre um item, depois o de baixo
- **THEN** o botão da direita confirma o item e o de baixo volta um nível
