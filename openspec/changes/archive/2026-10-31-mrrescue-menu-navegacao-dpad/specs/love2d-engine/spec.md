# love2d-engine Specification (Delta)

## MODIFIED Requirements

### Requirement: Jogo de validação Mr. Rescue pré-instalado e compatibilizado
A imagem SHALL fornecer o jogo *Mr. Rescue* (`mrrescue.love`) pré-instalado em `/storage/roms/love/`, configurado para rodar nativamente com a resolução e os botões adequados ao console. A navegação pelas telas de menu (tela inicial, opções, seleção de fases, tutoriais e recordes) SHALL responder aos eventos digitais do D-pad (`love.gamepadpressed` e `love.joystickpressed`), SHALL NOT depender de repetição contínua dos eixos analógicos brutos (`axis1`/`axis2` com temporizador em `updateKeys()`), e SHALL permanecer utilizável sem disparos involuntários mesmo na presença de calibração nula ou drift na alavanca analógica.

#### Scenario: Partida inicial de Mr. Rescue
- **WHEN** o jogador abre Mr. Rescue no primeiro boot
- **THEN** o jogo exibe imagem sem cortes, reproduz som e responde aos botões do gamepad

#### Scenario: Navegação na tela inicial sem interferência analógica
- **WHEN** o jogo é iniciado na tela inicial (`mainmenu`) e o direcional analógico reporta deflexão residual permanente (ex: $\text{ABS\_Y} = 18$ por calibração de boot)
- **THEN** o cursor de seleção de opções permanece estável no item atual sem rolar ou "metralhar" para baixo
- **AND** o usuário consegue navegar entre os itens do menu de forma pontual utilizando os botões direcionais físicos do D-pad (Cima e Baixo)
