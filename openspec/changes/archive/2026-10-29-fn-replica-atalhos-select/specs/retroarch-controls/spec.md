# Spec Delta

## MODIFIED Requirements

### Requirement: Hotkey no Select com atalhos de fábrica
O hotkey SHALL ser o FN quando o FN está remapeado (botão 10 do `micro_gamepad`), e o Select SHALL ser só o botão Select do jogo. Quando o FN não está remapeado (chave `r36-fn-original`, `fn_key` ausente ou código recusado), o hotkey SHALL ser o Select. Os atalhos SHALL ser os de fábrica: X = menu, Y = screenshot, L e R = carregar e salvar estado, L2 = câmera lenta, R2 = avanço rápido, Start = sair. Pausa e FPS SHALL ficar nos mesmos botões físicos de fábrica: baixo = pausa, direita = FPS.

#### Scenario: Abrir o menu
- **WHEN** o usuário aperta FN + X durante o jogo
- **THEN** o menu do RetroArch abre

#### Scenario: Salvar estado
- **WHEN** o usuário aperta FN + R durante o jogo
- **THEN** o RetroArch salva o estado no slot atual

#### Scenario: Pausa no botão de baixo
- **WHEN** o usuário aperta FN + o botão de baixo durante o jogo
- **THEN** o jogo pausa

#### Scenario: Select livre para o jogo
- **WHEN** o usuário aperta Select + X durante o jogo, com o FN remapeado
- **THEN** o menu do RetroArch não abre e o jogo recebe o Select e o X

#### Scenario: Select volta a ser o hotkey sem o FN remapeado
- **WHEN** o `fn_key` não aparece ou a chave `r36-fn-original` existe, e o usuário aperta Select + X durante o jogo
- **THEN** o menu do RetroArch abre

#### Scenario: Atalhos que não são de fábrica
- **WHEN** o autoconfig da imagem gerada é inspecionado
- **THEN** não há atalhos de volume, troca de slot, reset nem rewind ligados a botões do controle
