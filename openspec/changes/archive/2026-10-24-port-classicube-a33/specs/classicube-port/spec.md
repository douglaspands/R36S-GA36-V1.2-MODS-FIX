# classicube-port Specification

## Purpose

Definir os requisitos de compilação, validação de ABI, estrutura de arquivos offline e inicialização do ClassiCube (cliente otimizado compatível com Minecraft Classic) como um port nativo no EmuELEC para o hardware do R36S clone (Allwinner A33).

## ADDED Requirements

### Requirement: Binário compilado para o A33 com SDL2 e OpenGL ES 2.0
O binário do ClassiCube SHALL ser compilado para arquitetura ARMv7-A hard-float (`-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -O2`), ativando os backends nativos de vídeo OpenGL ES 2.0 (`CC_BUILD_GLES`) e janela/input SDL2 (`CC_BUILD_SDL2`).

#### Scenario: Atributos do binário compilado
- **WHEN** o binário `ClassiCube` é inspecionado com `readelf` e `file`
- **THEN** ele é um executável ELF 32-bit ARM, hard-float, ARMv7-A com suporte a VFPv4 e NEON, sem símbolos de depuração

#### Scenario: Renderização via GLES 2.0 nativo
- **WHEN** o ClassiCube é inicializado no console
- **THEN** ele conecta-se diretamente aos drivers EGL e GLESv2 da Mali-400 (`libEGL.so.1`, `libGLESv2.so.2`) sem emuladores de OpenGL desktop (sem GL4ES)

### Requirement: Conformidade estrita de ABI com a imagem base
O binário do ClassiCube SHALL depender exclusivamente das bibliotecas dinâmicas presentes na partição SYSTEM da imagem base, sem símbolos de glibc superiores a `GLIBC_2.36`.

#### Scenario: Verificação de símbolos de glibc
- **WHEN** as tabelas de símbolos do binário são conferidas contra a ABI da base
- **THEN** não há nenhuma dependência de versão de símbolo `GLIBC_` superior a 2.36

#### Scenario: Bibliotecas dinâmicas compartilhadas
- **WHEN** as tags `DT_NEEDED` do executável são inspecionadas
- **THEN** todas as bibliotecas necessárias (`libSDL2-2.0.so.0`, `libGLESv2.so.2`, `libEGL.so.1`, `libm.so.6`, `libc.so.6`, `libpthread.so.0`, `libdl.so.2`) correspondem aos nomes exportados por `/usr/lib/` no SYSTEM

### Requirement: Pacote de ativos offline para execução sem internet
Como o aparelho não dispõe de interface de rede (sem Wi-Fi), a instalação do ClassiCube SHALL conter previamente todos os arquivos de recursos necessários para a partida local, incluindo texturas clássicas (`texpacks/default.zip`) e sons básicos (`audio/`).

#### Scenario: Primeiro boot sem rede
- **WHEN** o usuário inicia o ClassiCube pela primeira vez no console offline
- **THEN** o jogo carrega o mapa local com blocos texturizados e sons de passos/interação sem emitir erros de download ou falhas de conexão

### Requirement: Lançador integrado aos Ports do EmulationStation
A imagem SHALL disponibilizar um script inicializador em `/storage/roms/ports_scripts/ClassiCube.sh` (visível na lista "Ports" da interface), responsável por configurar o ambiente de execução e iniciar o binário.

#### Scenario: Inicialização pelo menu
- **WHEN** o usuário seleciona o ClassiCube no menu de Ports do EmulationStation
- **THEN** o script define as variáveis de ambiente necessárias (`SDL_VIDEO_GL_DRIVER`, `SDL_VIDEO_EGL_DRIVER`), muda o diretório de trabalho para `/storage/roms/ports/classicube` e dispara o executável

#### Scenario: Retorno limpo ao EmulationStation
- **WHEN** o jogador pressiona o botão de sair do jogo (ou combinação de atalho)
- **THEN** o processo encerra sem travar o framebuffer e retorna o foco à interface do EmulationStation

### Requirement: Mapeamento de controles do portátil
A configuração do ClassiCube SHALL mapear os botões físicos e o direcional/analógico do R36S clone para as ações principais do jogo (mover, olhar, pular, quebrar bloco, colocar bloco, trocar bloco e pausar).

#### Scenario: Jogabilidade via gamepad
- **WHEN** o jogador opera o direcional e os botões ABXY/L/R
- **THEN** a resposta às ações ocorre de forma imediata e sem conflitos de teclas
