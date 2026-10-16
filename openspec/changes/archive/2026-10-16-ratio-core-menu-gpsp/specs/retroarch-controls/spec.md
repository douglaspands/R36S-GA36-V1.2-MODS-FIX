# Spec Delta

## ADDED Requirements

### Requirement: OK e Cancel dos menus sem inversão
Nos menus do RetroArch, o RetroPad A (botão da direita) SHALL ser OK e o RetroPad B (botão de baixo) SHALL ser Cancel. A configuração NÃO SHALL inverter os dois.

#### Scenario: Configuração conferida no PC
- **WHEN** o `retroarch.cfg` da p8 da imagem gerada é inspecionado
- **THEN** ele declara `menu_swap_ok_cancel_buttons = "false"`

#### Scenario: Confirmar e voltar no menu
- **WHEN** o usuário abre o menu do RetroArch e aperta o botão da direita sobre um item, depois o de baixo
- **THEN** o botão da direita confirma o item e o de baixo volta um nível
