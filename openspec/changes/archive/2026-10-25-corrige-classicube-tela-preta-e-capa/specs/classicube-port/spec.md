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
A imagem SHALL disponibilizar o script inicializador `ClassiCube.sh`, o `gamelist.xml` e as imagens de capa tanto na partição `roms` (`/storage/roms/ports_scripts/`) quanto na partição `system` (`/usr/bin/ports/` e `/usr/share/classicube/`), com sincronização automática no boot (`r36-classicube-sync.service`), garantindo que a imagem do jogo apareça no menu "Ports" e que o jogo atualize e carregue mesmo quando o cartão SD for gravado com `--keep-roms` ou em cima do overlayFS de `mount_romfs.sh`.

#### Scenario: Inicialização pelo menu
- **WHEN** o usuário seleciona o ClassiCube no menu de Ports do EmulationStation
- **THEN** o script define as variáveis de ambiente necessárias (`SDL_VIDEO_GL_DRIVER`, `SDL_VIDEO_EGL_DRIVER`, `SDL_GAMECONTROLLERCONFIG`), garante que os ativos offline existam em `/storage/roms/ports/classicube`, muda o diretório de trabalho para `/storage/roms/ports/classicube` e dispara o executável no modo local com `--singleplayer` sem repassar argumentos externos do EmulationStation

#### Scenario: Exibição da capa na lista mesmo após atualização com --keep-roms
- **WHEN** o usuário navega pelo menu "Ports" do EmulationStation (tanto em gravação completa quanto após `./flash.sh --keep-roms`)
- **THEN** a lista exibe o nome "Classic Craft (ClassiCube)" e a imagem da capa correspondente (`img/ClassiCube.png` / `images/ClassiCube-image.png`), disponível tanto no overlay `/usr/bin/ports` / `/storage/roms/ports_scripts` quanto em `/storage/.config/emulationstation/gamelists/ports/gamelist.xml`

#### Scenario: Retorno limpo ao EmulationStation
- **WHEN** o jogador seleciona "Quit game" no menu de pausa ou pressiona simultaneamente `Select + Start` no controle
- **THEN** o processo encerra sem travar o framebuffer e retorna o foco à interface do EmulationStation

### Requirement: Mapeamento de controles do portátil
A configuração e o binário do ClassiCube SHALL carregar o banco de mapeamentos SDL2 (`SDL_GameControllerAddMappingsFromFile` e `SDL_GAMECONTROLLERCONFIG`) compatível com a `libSDL2-2.0.so.0.9.0` da base, mapeando os botões físicos (incluindo `SDL_CONTROLLER_BUTTON_BACK` como `Select`) e o direcional/analógico do R36S clone (`micro_gamepad`) para as ações principais do jogo.

#### Scenario: Jogabilidade via gamepad no SDL 2.0.9
- **WHEN** o jogador opera o direcional, analógicos e os botões ABXY/L/R/Start/Select no portátil
- **THEN** o controle `micro_gamepad` é reconhecido por `SDL_IsGameController` e responde imediatamente às ações de movimentação, câmera, interação com blocos, abertura do menu (`Start`), inventário (`Select`) e saída rápida (`Select + Start`)
