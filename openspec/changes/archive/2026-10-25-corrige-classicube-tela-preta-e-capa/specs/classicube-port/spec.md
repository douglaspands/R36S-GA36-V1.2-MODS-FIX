# Spec Delta: classicube-port

## MODIFIED Requirements

### Requirement: Binário compilado para o A33 com SDL2 e OpenGL ES 2.0
O binário do ClassiCube SHALL ser compilado para arquitetura ARMv7-A hard-float (`-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -O2`), ativando os backends nativos de vídeo OpenGL ES 2.0 (`CC_BUILD_GLES`) e janela/input SDL2 (`CC_BUILD_SDL2`), utilizando formato de textura `GL_RGBA` compatível com o driver Mali-400 (`libGLESv2.so.2.0`) e inicializando a janela com foco ativo (`Window_Main.Focused = true`) no framebuffer `mali-fbdev`.

#### Scenario: Atributos do binário compilado
- **WHEN** o binário `ClassiCube` é inspecionado com `readelf` e `file`
- **THEN** ele é um executável ELF 32-bit ARM, hard-float, ARMv7-A com suporte a VFPv4 e NEON, sem símbolos de depuração

#### Scenario: Renderização via GLES 2.0 nativo sem texturas pretas
- **WHEN** o ClassiCube é inicializado no console com GPU Mali-400
- **THEN** ele conecta-se diretamente aos drivers EGL e GLESv2 (`libEGL.so.1`, `libGLESv2.so.2`) e aloca todas as texturas (`white_square`, `terrain.png`, `gui.png` e fonte) com `internalformat = GL_RGBA` e `format = GL_RGBA`, renderizando o céu, blocos 3D e interface 2D com suas cores e texturas reais (sem tela preta por `GL_INVALID_OPERATION`)

#### Scenario: Foco inicial da janela em framebuffer sem window manager
- **WHEN** a janela SDL2 é criada no driver `mali-fbdev`
- **THEN** `Window_Main.Focused` inicia como `true` sem depender do evento `SDL_WINDOWEVENT_FOCUS_GAINED`, evitando que o jogo entre em auto-pause escuro ou bloqueie a entrada de comandos

### Requirement: Lançador integrado aos Ports do EmulationStation
A imagem SHALL manter o lançador `ClassiCube.sh`, a entrada no `gamelist.xml` e as capas em `/storage/roms/ports_scripts/` (p1), com cópia mestre em `/usr/share/classicube/ports_scripts/` que o `r36-classicube-sync.service` restaura no boot quando falta ou difere, inclusive após `--keep-roms`. A imagem SHALL NOT criar `/usr/bin/ports`, para que o overlay do `mount_romfs.sh` continue falhando como na base e a pasta da p1 siga visível e editável pelo PC.

#### Scenario: Inicialização pelo menu
- **WHEN** o usuário seleciona o ClassiCube no menu de Ports do EmulationStation
- **THEN** o script define as variáveis de ambiente necessárias (`SDL_VIDEO_GL_DRIVER`, `SDL_VIDEO_EGL_DRIVER`, `SDL_GAMECONTROLLERCONFIG`), garante que os ativos offline existam em `/storage/roms/ports/classicube`, muda o diretório de trabalho para `/storage/roms/ports/classicube` e executa `/usr/share/classicube/ClassiCube` no modo local com `--singleplayer`, sem repassar argumentos externos do EmulationStation

#### Scenario: Exibição da capa na lista mesmo após atualização com --keep-roms
- **WHEN** o cartão é gravado por completo ou com `./flash.sh --keep-roms` e o aparelho termina o boot
- **THEN** `/storage/roms/ports_scripts/` contém `ClassiCube.sh`, as capas e uma entrada `<path>./ClassiCube.sh</path>` no `gamelist.xml`, e o menu "Ports" exibe "Classic Craft (ClassiCube)" com a capa

#### Scenario: Ports do usuário preservados
- **WHEN** o usuário copia pelo PC outro script `.sh` para `R36-ROMS/ports_scripts/` e o `gamelist.xml` dessa pasta já tem entradas de outros jogos
- **THEN** o script aparece no menu "Ports", e o serviço de boot acrescenta a entrada do ClassiCube só quando ela falta, sem apagar nem substituir as outras entradas, e sem duplicá-la em boots seguintes

#### Scenario: Retorno limpo ao EmulationStation
- **WHEN** o jogador seleciona "Quit game" no menu de pausa ou pressiona simultaneamente `Select + Start` no controle
- **THEN** o processo encerra sem travar o framebuffer e retorna o foco à interface do EmulationStation

### Requirement: Mapeamento de controles do portátil
A configuração e o binário do ClassiCube SHALL carregar o banco de mapeamentos SDL2 (`SDL_GameControllerAddMappingsFromFile` e `SDL_GAMECONTROLLERCONFIG`) compatível com a `libSDL2-2.0.so.0.9.0` da base, mapeando os botões físicos (incluindo `SDL_CONTROLLER_BUTTON_BACK` como `Select`) e o direcional/analógico do R36S clone (`micro_gamepad`) para as ações principais do jogo.

#### Scenario: Jogabilidade via gamepad no SDL 2.0.9
- **WHEN** o jogador opera o direcional, analógicos e os botões ABXY/L/R/Start/Select no portátil
- **THEN** o controle `micro_gamepad` é reconhecido por `SDL_IsGameController` e responde imediatamente às ações de movimentação, câmera, interação com blocos, abertura do menu (`Start`), inventário (`Select`) e saída rápida (`Select + Start`)

## ADDED Requirements

### Requirement: Binário único na partição SYSTEM
O binário `ClassiCube` SHALL existir só em `/usr/share/classicube/ClassiCube`, na partição SYSTEM, com permissão `0755`, e o `ClassiCube.sh` SHALL executá-lo direto de lá. A partição `roms` SHALL NOT levar cópia do binário: a FAT32 não guarda permissão de execução e não é regravada com `--keep-roms`. Na p1 ficam só os arquivos que o jogador ou o PC alteram (opções, mapas, texturas e sons em `/storage/roms/ports/classicube/`).

#### Scenario: Atualização com --keep-roms
- **WHEN** o cartão é gravado com `--keep-roms` a partir de um build com binário novo
- **THEN** o jogo abre com o binário novo, porque ele vem do SYSTEM, sem depender de nada na p1

#### Scenario: Boot sem regravar a FAT32
- **WHEN** o aparelho dá boot com o lançador, a capa e os ativos já presentes e iguais aos do SYSTEM
- **THEN** o `r36-classicube-sync.service` não grava nenhum arquivo na p1 e não copia o binário para ela
