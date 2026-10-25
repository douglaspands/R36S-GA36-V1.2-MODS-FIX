# classicube-port Specification

## Purpose

Definir os requisitos de compilação, validação de ABI, estrutura de arquivos offline e inicialização do ClassiCube (cliente otimizado compatível com Minecraft Classic) como um port nativo no EmuELEC para o hardware do R36S clone (Allwinner A33).

## Requirements

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

### Requirement: Conformidade estrita de ABI com a imagem base
O binário do ClassiCube SHALL depender exclusivamente das bibliotecas dinâmicas presentes na partição SYSTEM da imagem base, sem símbolos de glibc superiores a `GLIBC_2.36`.

#### Scenario: Verificação de símbolos de glibc
- **WHEN** as tabelas de símbolos do binário são conferidas contra a ABI da base
- **THEN** não há nenhuma dependência de versão de símbolo `GLIBC_` superior a 2.36

#### Scenario: Bibliotecas dinâmicas compartilhadas
- **WHEN** as tags `DT_NEEDED` do executável são inspecionadas
- **THEN** todas as bibliotecas necessárias (`libSDL2-2.0.so.0`, `libGLESv2.so.2`, `libEGL.so.1`, `libm.so.6`, `libc.so.6`, `libpthread.so.0`, `libdl.so.2`) correspondem aos nomes exportados por `/usr/lib/` no SYSTEM

### Requirement: Binário do ClassiCube na p1 como port normal
O binário `ClassiCube` SHALL ser entregue pela imagem em `/storage/roms/ports/classicube/ClassiCube`, na p1, como o executável de qualquer port, e SHALL NOT existir cópia dele na partição SYSTEM. A p1 (FAT32) não guarda permissão de execução, então ele SHALL executar de uma cópia fora da p1 preparada pelo serviço da capability `ports-executables`. O binário que está na p1 SHALL ser sempre o que vale: o jogador pode substituí-lo pelo PC, e uma gravação com `--keep-roms` SHALL NOT sobrescrevê-lo. Na p1 ficam também os arquivos que o jogador ou o PC alteram (opções, mapas, texturas e sons em `/storage/roms/ports/classicube/`).

#### Scenario: Atualização com --keep-roms
- **WHEN** o cartão é gravado com `--keep-roms` a partir de um build com binário novo
- **THEN** a p1 não é regravada e o jogo continua abrindo com o binário que já estava nela, e o jogador atualiza copiando o binário novo pelo PC

#### Scenario: Gravação completa
- **WHEN** o cartão é gravado por completo a partir do build
- **THEN** a p1 traz `ports/classicube/ClassiCube` e o jogo abre sem o jogador copiar nada

#### Scenario: Boot sem regravar a FAT32
- **WHEN** o aparelho dá boot com o lançador, a capa e os ativos já presentes e iguais aos do SYSTEM
- **THEN** o `r36-classicube-sync.service` não grava nenhum arquivo na p1 e não mexe no binário

#### Scenario: Imagem não entrega binário no SYSTEM
- **WHEN** uma imagem é gerada com a feature `60-port-classicube`
- **THEN** o SYSTEM não contém `usr/share/classicube/ClassiCube` e a p1 contém `ports/classicube/ClassiCube`

#### Scenario: Binário do jogador na p1
- **WHEN** o jogador copia pelo PC um `ClassiCube` novo para `ports/classicube/` e liga o aparelho
- **THEN** o jogo abre com esse binário, sem regravar o SYSTEM

### Requirement: Pacote de ativos offline para execução sem internet
Como o aparelho não dispõe de interface de rede (sem Wi-Fi), a instalação do ClassiCube SHALL conter previamente todos os arquivos de recursos necessários para a partida local, incluindo texturas clássicas (`texpacks/default.zip`) e sons básicos (`audio/`).

#### Scenario: Primeiro boot sem rede
- **WHEN** o usuário inicia o ClassiCube pela primeira vez no console offline
- **THEN** o jogo carrega o mapa local com blocos texturizados e sons de passos/interação sem emitir erros de download ou falhas de conexão

### Requirement: Lançador integrado aos Ports do EmulationStation
A imagem SHALL manter o lançador `ClassiCube.sh`, a entrada no `gamelist.xml` e as capas em `/storage/roms/ports_scripts/` (p1), com cópia mestre em `/usr/share/classicube/ports_scripts/` que o `r36-classicube-sync.service` restaura no boot quando falta ou difere, inclusive após `--keep-roms`. O serviço SHALL rodar antes do `emustation.service` e esperar até 20 s o `/storage/roms` ser montado, sem `After=emuelec-autostart.service`; se a montagem não vier, ele sai sem gravar e o ES abre normalmente. A imagem SHALL NOT criar `/usr/bin/ports`, para que o overlay do `mount_romfs.sh` continue falhando como na base e a pasta da p1 siga visível e editável pelo PC. O lançador SHALL executar só `/storage/roms/ports/classicube/ClassiCube`; se esse arquivo faltar ou o sistema o recusar (código de saída 126 ou 127), o lançador SHALL mostrar um aviso e encerrar, devolvendo o foco ao EmulationStation.

#### Scenario: Inicialização pelo menu
- **WHEN** o usuário seleciona o ClassiCube no menu de Ports do EmulationStation
- **THEN** o script define as variáveis de ambiente necessárias (`SDL_VIDEO_GL_DRIVER`, `SDL_VIDEO_EGL_DRIVER`, `SDL_GAMECONTROLLERCONFIG`), garante que os ativos offline existam em `/storage/roms/ports/classicube`, muda o diretório de trabalho para `/storage/roms/ports/classicube` e executa `/storage/roms/ports/classicube/ClassiCube` no modo local com `--singleplayer`, sem repassar argumentos externos do EmulationStation

#### Scenario: Binário ausente ou recusado
- **WHEN** o usuário abre o ClassiCube e `ports/classicube/ClassiCube` não existe, ou o sistema o recusa com código de saída 126 ou 127
- **THEN** o lançador mostra um aviso e volta ao EmulationStation, sem reabrir o jogo

#### Scenario: Saída normal do jogo não repete a execução
- **WHEN** o jogador sai do jogo pelo menu de pausa ou por `Select + Start`
- **THEN** o lançador encerra e volta ao EmulationStation, sem abrir o jogo uma segunda vez

#### Scenario: Exibição da capa na lista mesmo após atualização com --keep-roms
- **WHEN** o cartão é gravado por completo ou com `./flash.sh --keep-roms` e o aparelho termina o boot
- **THEN** `/storage/roms/ports_scripts/` contém `ClassiCube.sh`, as capas e uma entrada `<path>./ClassiCube.sh</path>` no `gamelist.xml`, e o menu "Ports" exibe "Classic Craft (ClassiCube)" com a capa

#### Scenario: Boot até o EmulationStation
- **WHEN** o aparelho liga com a feature `60-port-classicube` na imagem
- **THEN** o boot passa do splash e o EmulationStation abre, sem esperar pelo fim do `emuelec-autostart.service`

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

### Requirement: Sentido dos analógicos
O analógico esquerdo SHALL mover o personagem e o direito SHALL girar a câmera, ambos no sentido físico do movimento: empurrar para cima anda para frente (esquerdo) ou olha para cima (direito), e empurrar para baixo faz o oposto. Nos menus e no inventário, empurrar para cima SHALL mover a seleção para cima.

#### Scenario: Andar para frente
- **WHEN** o jogador empurra o analógico esquerdo para cima, estando no mundo
- **THEN** o personagem anda para frente, e para baixo ele anda para trás

#### Scenario: Olhar para cima
- **WHEN** o jogador empurra o analógico direito para cima
- **THEN** a câmera sobe, e para baixo ela desce

#### Scenario: Seleção em menu
- **WHEN** o jogador empurra o analógico esquerdo ou o direito para cima num menu ou no inventário
- **THEN** a seleção sobe, e para baixo ela desce

### Requirement: Zona morta dos analógicos
Os dois analógicos SHALL ignorar deslocamentos de até cerca de 20% do curso, e o restante do curso SHALL ser reescalado de 0 a 1, para a deriva do ADC não mover o personagem nem a câmera.

#### Scenario: Analógico solto com deriva
- **WHEN** o jogador solta os analógicos e eles leem até 20% do curso em qualquer eixo
- **THEN** o personagem fica parado e a câmera não gira

#### Scenario: Saída da zona morta
- **WHEN** o jogador empurra o analógico direito logo além dos 20% do curso
- **THEN** a câmera começa a girar de forma lenta e contínua, sem salto de velocidade

### Requirement: Velocidade da câmera e dos menus pelo analógico
Com o analógico direito no fundo, a câmera SHALL girar cerca de 110°/s, e a seleção de menus e inventário pelos analógicos SHALL andar um passo em menos de 0,5 s com o analógico no fundo. Esses valores SHALL independer da taxa de quadros.

#### Scenario: Volta completa
- **WHEN** o jogador mantém o analógico direito no fundo para um lado
- **THEN** a câmera completa uma volta em cerca de 3 a 4 segundos

#### Scenario: Navegação em menu
- **WHEN** o jogador mantém o analógico para baixo num menu com vários botões
- **THEN** a seleção desce um item em menos de 0,5 s

### Requirement: Binds padrão do gamepad
O ClassiCube SHALL usar estes binds padrão no `micro_gamepad`, com o layout dos botões da Nintendo: A (direita) pula, X (cima) abre o inventário, Y (esquerda) pega o bloco, L quebra e R coloca bloco, L2 e R2 trocam o item da barra, e clicar L3 e R3 juntos (os dois analógicos apertados) faz respawn. O Select continua sendo o botão de voltar e fechar menus. O chat e a definição do ponto de spawn SHALL NOT ter botão padrão no gamepad.

#### Scenario: Pausar sem mexer no spawn
- **WHEN** o jogador aperta Start no mundo para abrir o menu de pausa
- **THEN** o menu abre e o ponto de respawn não muda

#### Scenario: Y não abre o chat
- **WHEN** o jogador aperta Y no mundo
- **THEN** o bloco sob a mira é copiado para a barra e o chat e o teclado virtual não abrem

#### Scenario: Respawn
- **WHEN** o jogador segura L3 (analógico esquerdo apertado) e aperta R3 (analógico direito apertado) no mundo
- **THEN** o personagem volta ao ponto de respawn

#### Scenario: Combinações de modificador sem efeito duplo
- **WHEN** o jogador aperta B+L ou B+R
- **THEN** só a velocidade ou o voo é acionado, sem quebrar nem colocar bloco

#### Scenario: Binds salvos pelo jogador valem
- **WHEN** o jogador remapeia um bind do gamepad pelo menu do jogo
- **THEN** o bind salvo no `options.txt` prevalece sobre o padrão

### Requirement: Sensibilidade da câmera em cartões já usados
O lançador SHALL passar a sensibilidade da câmera do preset novo (`mousesensitivity = 120`) também ao `options.txt` de um cartão que já o tem, mas somente quando o valor gravado ainda for o do preset antigo (30). Um valor diferente de 30 SHALL ser preservado.

#### Scenario: Cartão gravado com --keep-roms e preset antigo
- **WHEN** o `options.txt` do cartão tem `mousesensitivity = 30` e o jogo é aberto pelo menu Ports
- **THEN** o valor passa a 120 e as demais linhas do arquivo ficam iguais

#### Scenario: Valor ajustado pelo jogador
- **WHEN** o `options.txt` do cartão tem `mousesensitivity` diferente de 30
- **THEN** o lançador não altera o valor
