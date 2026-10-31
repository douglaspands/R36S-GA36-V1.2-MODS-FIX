# Design: mrrescue-menu-navegacao-dpad

## Context

O R36S clone (GA36-MB V1.2, Allwinner A33) executa jogos através do runtime standalone do LÖVE 11.5 (feature `64-love2d`). A interface de entrada combina duas tecnologias físicas distintas:
1. **D-pad e botões de face (GPIOs nativos)**: Os botões direcionais (Cima, Baixo, Esquerda, Direita) e botões de ação são conectados diretamente às portas GPIO do processador A33, gerando interrupções tratadas por `gpio_keys_gpio_work_func` no driver `udt_joystick.ko`. São entradas digitais perfeitas, estáveis e livres de ruído analógico.
2. **Direcionais Analógicos (ADC via MCU serial)**: Os dois joysticks analógicos são lidos por um microcontrolador auxiliar via conversor analógico-digital (ADC de 8 bits) e enviados em pacotes seriais pela UART interna `/dev/ttyS1` ao driver sunxi `sw_uart`. A cada 20 ms, a rotina `jk_keys_poll` do `udt_joystick.ko` lê o buffer de recepção `buff_rcv` e mapeia `ABS_Y = 18 - adc_val_to_axis(buff_rcv[4])`.

No hardware portátil, o MCU calibra a tensão neutra dos analógicos durante o ciclo de energização no boot do console. Caso o portátil seja ligado enquanto a alavanca analógica estiver sendo tocada ou pressionada em um estojo, o MCU registra a tensão fora de centro como ponto zero. Quando a alavanca volta ao centro mecânico, a leitura cai abaixo do limiar 50 ($\le 0{,}65\text{ V}$), fazendo `adc_val_to_axis` retornar 0 e o driver reportar $\text{ABS\_Y} = 18$ (+1.0 no SDL2, deflexão máxima para baixo). Esse estado persiste no hardware e no kernel até o próximo reboot do console.

No jogo *Mr. Rescue* (`mrrescue.love`), a função `updateKeys()` (chamada a cada quadro pelos menus através de `gamestates[state].update(dt)`) herdou código de PC que faz polling dos eixos analógicos:
```lua
if yacccool <= 0 then
    if axis2 < -0.90 then
        if state and gamestates[state] and gamestates[state].action then gamestates[state].action("up") end
        yacccool = AXIS_COOLDOWN
    elseif axis2 > 0.90 then
        if state and gamestates[state] and gamestates[state].action then gamestates[state].action("down") end
        yacccool = AXIS_COOLDOWN
    end
end
```
Com $\text{ABS\_Y} = 18$, `axis2 > 0.90` é sempre verdadeiro, disparando `mainmenu.action("down")` repetidamente a cada 0,2 s (`AXIS_COOLDOWN = 0.2`), fazendo o cursor do menu girar infinitamente para baixo.

## Goals / Non-Goals

**Goals:**
- Eliminar o travamento/rolagem contínua para baixo nos menus do *Mr. Rescue* sem exigir reinicialização do portátil.
- Isolar a navegação de todos os menus no D-pad digital e botões físicos, utilizando os eventos discretos nativos do LÖVE (`love.gamepadpressed` e `love.joystickpressed`).
- Manter o suporte aos analógicos durante a partida real (`keystate.up`, `keystate.down`, `keystate.left`, `keystate.right`), permitindo ao jogador andar e subir escadas com o analógico.
- Garantir que a alteração seja 100% contida no arquivo do jogo (`mrrescue.love`), sem alterar drivers, kernel ou lançadores do sistema.

**Non-Goals:**
- Modificar o driver de kernel `udt_joystick.ko` ou o firmware do MCU auxiliar.
- Alterar as configurações globais do SDL2 ou do lançador `/usr/bin/love.sh`.
- Desativar o direcional analógico durante a movimentação dentro das fases.

## Decisions

### Decisão 1: Remoção do laço de polling analógico para ações de menu em `updateKeys()`
**Decisão:** Em `main.lua` do *Mr. Rescue*, remover as chamadas a `gamestates[state].action(...)` acionadas por `axis1` e `axis2` com os temporizadores `xacccool` e `yacccool`.
**Racional:** A função `action(k)` dos estados de menu (`mainmenu`, `options`, `howto`, `levelselection`, `highscore_list`, `highscore_entry`, `ingame_menu`, `summary`, `splash`) foi concebida para navegação discreta. Em um portátil com D-pad físico de alta precisão, tentar simular pressionamentos repetitivos a partir de eixos brutos de joystick analógico (`joystick:getAxes()`) sem zona morta configurável expõe a interface a ruído de hardware, drift e calibrações de boot.
**Alternativas consideradas:**
- *Aumentar a zona morta do analógico no script*: Rejeitada porque se a calibração do boot ou falha de leitura jogar o valor para 18 (+1.0), qualquer zona morta abaixo de 1.0 continuará disparando o erro.
- *Filtrar apenas em `mainmenu.lua`*: Rejeitada porque o mesmo laço faria a seleção de fases (`levelselection`) ou menu de opções (`options`) girarem sem controle.

### Decisão 2: Centralização da navegação de menus no D-pad digital via eventos discretos
**Decisão:** Manter o roteamento dos direcionais de menu através dos callbacks de eventos `love.gamepadpressed` (com `dpup`, `dpdown`, `dpleft`, `dpright`) e `love.joystickpressed` (com botões 14 a 17 do `micro_gamepad`).
**Racional:** Callbacks de eventos do SDL2/LÖVE disparam apenas no instante físico do pressionamento (borda de subida). Quando o usuário solta o botão, nenhum evento adicional é emitido. Isso garante resposta imediata, precisa e imune a repetições em falso ou laços infinitos.

### Decisão 3: Preservação da movimentação contínua in-game pelo analógico
**Decisão:** Manter no `updateKeys()` a leitura de eixos para preenchimento de `keystate.left`, `keystate.right`, `keystate.up` e `keystate.down`:
```lua
if axis1 < -0.5 then keystate.left = true
elseif axis1 > 0.5 then keystate.right = true end
if axis2 < -0.5 then keystate.up = true
elseif axis2 > 0.5 then keystate.down = true end
```
**Racional:** Durante a partida (`ingame`), a tabela `keystate` dita a velocidade contínua do jogador no chão e a subida de escadas. Caso o jogador prefira usar o analógico para andar, ele continua operacional. Se porventura o analógico apresentar drift extremo de hardware, o jogador pode utilizar o D-pad sem ter o menu do jogo travado.

## Risks & Trade-offs

- **Navegação de menus apenas pelo D-pad**: O jogador não navegará menus de tela inicial pela alavanca analógica, usando exclusivamente as setas do D-pad digital. Em um console portátil retrô estilo Game Boy, isso coincide com a expectativa ergonômica natural e garante 100% de confiabilidade.
