# Proposal: mrrescue-menu-navegacao-dpad

## Why

No clone do R36S (GA36-MB V1.2, Allwinner A33), em momentos esporádicos ao iniciar o jogo *Mr. Rescue* (`mrrescue.love`), o cursor de seleção de opções na tela inicial (`mainmenu`) fica travado movendo-se continuamente para baixo ("metralhando" a cada 0,2s). Reiniciar o jogo não resolve o problema, que só é sanado reiniciando o aparelho por completo.

A causa de hardware e driver reside na leitura analógica:
1. No hardware, os potenciômetros dos direcionais analógicos não são lidos por GPIOs diretos do SoC A33, mas por um microcontrolador auxiliar (MCU) via ADC, cujos pacotes chegam ao kernel pela porta serial interna `/dev/ttyS1` (`sw_uart`).
2. Se o console for inicializado ou reiniciado enquanto a alavanca analógica estiver levemente esbarrada, inclinada ou pressionada em um estojo, o firmware do MCU registra essa posição deslocada como "ponto neutro/zero". Quando o analógico retorna ao centro físico real, a leitura de tensão em relação ao falso zero cai para a faixa de piso ($\le 50$ em escala 0..255).
3. O driver de kernel `udt_joystick.ko` calcula o eixo vertical como $\text{ABS\_Y} = 18 - \text{adc\_val\_to\_axis}(\text{buff\_rcv}[4])$. Com a leitura de piso, o valor emitido é $\text{ABS\_Y} = 18$ (+1.0 no SDL2, deflexão máxima para baixo), sem zona morta de hardware (`flat = 0`).
4. Essa calibração reside na memória volátil do MCU e do kernel, permanecendo inalterada até o próximo ciclo de energia (reboot do console).

No software do jogo (`mrrescue.love`), a função `updateKeys()` herdou código legado de PC de 2012 que faz polling contínuo dos eixos analógicos (`axis2 > 0.90`) chamando repetidamente `gamestates[state].action("down")` a cada 0,2s (`yacccool = AXIS_COOLDOWN`). Isso sequestra a navegação dos menus, enquanto o D-pad digital (`micro_gamepad b13..b16`) permanece 100% íntegro e imune a desvios analógicos.

Esta change soluciona a falha restringindo a navegação de todos os menus exclusivamente ao D-pad digital e botões físicos, eliminando a repetição analógica do `updateKeys()` e mantendo o uso do analógico restrito à movimentação do bombeiro durante a partida.

## What Changes

- **Isolamento da navegação de menus no D-pad digital**: Remove em `main.lua` do *Mr. Rescue* o laço de repetição analógica com temporizador (`yacccool`/`xacccool`) que chamava `gamestates[state].action("up"|"down"|"left"|"right")` em `updateKeys()`.
- **Navegação de menus via eventos discretos de controle**: Assegura que todas as telas de menu (`mainmenu`, `options`, `howto`, `levelselection`, `highscore_list`, `highscore_entry`, `ingame_menu`, `summary`, `splash`) respondam de forma rápida e estável apenas aos eventos de pressionamento digital (`love.gamepadpressed` com `dpup`/`dpdown`/`dpleft`/`dpright` e `love.joystickpressed` com botões 14 a 17), sem repetição indevida ou dependência de eixos flutuantes.
- **Preservação do analógico na movimentação da partida**: Mantém o preenchimento de `keystate.up`, `keystate.down`, `keystate.left` e `keystate.right` a partir dos eixos analógicos dentro de `updateKeys()`, garantindo que o jogador possa usar a alavanca analógica para andar e subir escadas normalmente durante a fase.
- **Testes automatizados e documentação**: Atualiza `tests/test_love2d.py` para verificar a ausência do laço analógico de menu e documenta o comportamento do D-pad nas três línguas do projeto (`docs/DESENVOLVIMENTO.md`, `docs/DEVELOPMENT.md`, `docs/DESARROLLO.md`).

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova é introduzida. -->

### Modified Capabilities
- `love2d-engine`: Atualiza o requisito do jogo de validação *Mr. Rescue* para garantir que a navegação em menus seja imune a calibrações fantasmas ou drift de eixos analógicos, operando de forma confiável via D-pad digital.

## Impact

- `features/64-love2d/roms/love/mrrescue.love`: Atualização do script `main.lua` dentro do arquivo comprimido do jogo.
- `tests/test_love2d.py`: Novos testes unitários verificando a remoção do laço de repetição analógica de menus e a integridade da navegação digital.
- `docs/DESENVOLVIMENTO.md`, `docs/DEVELOPMENT.md`, `docs/DESARROLLO.md`: Registro da estabilização de entrada nos menus do LÖVE 2D.
