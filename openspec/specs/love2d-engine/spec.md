# love2d-engine Specification

## Purpose

Define os requisitos de compatibilidade, execução standalone, viewport físico 640x480, integração de áudio ALSA/OpenAL, encerramento via FN+Start, telas de splash e controles para jogos LÖVE 2D no R36S clone (Allwinner A33).

## Requirements

### Requirement: Executável LÖVE standalone com viewport ajustado para 640x480
O sistema SHALL fornecer o binário executável `love` compilado para ARMv7-A hard-float (Cortex-A7, NEON, glibc <= 2.36) com backend OpenGL ES 2.0 (`libGLESv2.so.2`) e contexto EGL no framebuffer `mali-fbdev` (`/dev/fb0`). O runtime SHALL ajustar o viewport e a escala de renderização para a resolução física de 640x480 do display LCD do portátil, preservando a proporção de aspecto (aspect ratio) de jogos projetados para diferentes resoluções.

#### Scenario: Renderização no framebuffer Mali-400 sem servidor X11
- **WHEN** o executável `love` é chamado com um pacote de jogo `.love` em `/dev/fb0`
- **THEN** o processo inicializa a superfície EGL e renderiza diretamente no framebuffer nativo de 640x480 sem deslocamento de tela

#### Scenario: Jogo com resolução de janela arbitrária
- **WHEN** um jogo define dimensões em janela diferentes de 640x480 (por exemplo 768x600 no `conf.lua`)
- **THEN** o runtime dimensiona a imagem proporcionalmente dentro da área visível de 640x480 mantendo o aspecto correto com barras pretas quando necessário, sem cortar elementos de interface

### Requirement: Lançador com telas de splash neutras na inicialização e saída
O lançador `/usr/bin/love.sh` SHALL exibir a tela neutra de carregamento do sistema (`/usr/config/splash/loading-game.png`) através do reprodutor `mpv` em segundo plano com `blank_buffer` logo antes de inicializar o motor LÖVE, e reaplicar a exibição da tela neutra ao término do processo antes de devolver o controle ao EmulationStation.

#### Scenario: Abertura de jogo exibe splash de transição
- **WHEN** o jogador seleciona um título no menu LÖVE do EmulationStation
- **THEN** a tela de carregamento com o ícone de controle é apresentada de forma contínua até o jogo abrir sua janela, sem cintilação de console de texto

#### Scenario: Encerramento de jogo exibe splash de retorno
- **WHEN** o jogo LÖVE é encerrado pelo usuário
- **THEN** a tela neutra de saída é exibida cobrindo o framebuffer antes do EmulationStation reaparecer

### Requirement: Atalho universal de encerramento via FN + Start
O sistema SHALL permitir o encerramento imediato de qualquer jogo LÖVE através do pressionamento simultâneo dos botões `FN` e `Start`. O lançador `/usr/bin/love.sh` SHALL declarar o botão 10 (`BTN_MODE`, emitido pelo `FN` remapeado do `micro_gamepad`) como `guide:b10` na variável `SDL_GAMECONTROLLERCONFIG`, e o perfil `love.gptk` SHALL definir `hotkey = guide` e `start = enter` para que o daemon `gptokeyb` envie o sinal `SIGTERM` ao processo do jogo.

#### Scenario: Pressionamento simultâneo de FN e Start
- **WHEN** o jogador segura o botão físico FN e aperta Start durante a partida
- **THEN** o daemon `gptokeyb` intercepta a combinação e envia sinal de término ao processo `love`, fechando o jogo e retornando ao menu

#### Scenario: Select livre de atalhos do sistema
- **WHEN** o jogador pressiona Select sozinho ou combinado com outros botões no jogo
- **THEN** a ação de Select chega normalmente à lógica interna do jogo sem acionar encerramento involuntário

### Requirement: Integração do subsistema de som via ALSA e diagnóstico sob chave
O lançador `/usr/bin/love.sh` SHALL exportar `SDL_AUDIODRIVER=alsa`, ajustar `Speaker Function` de acordo com `/sys/class/switch/h2w/state` e chamar `/usr/lib/r36/audio-ganho aplica` antes e após a execução. Sob a chave `r36-diagnostico` na partição `R36-ROMS`, o lançador SHALL ativar log verboso do OpenAL Soft (`ALSOFT_LOGLEVEL=3`) gravando em `/storage/roms/love/r36-love-alsoft.log`.

#### Scenario: Inicialização do som no hardware de áudio
- **WHEN** um jogo LÖVE toca efeitos sonoros ou música
- **THEN** o backend ALSA do OpenAL Soft conecta-se ao dispositivo PCM padrão do sistema e o áudio é reproduzido no alto-falante ou fone no volume configurado

#### Scenario: Diagnóstico com a chave ativa na p1
- **WHEN** a chave `r36-diagnostico` existe em `/storage/roms` e o jogo é iniciado
- **THEN** o arquivo `r36-love-alsoft.log` é criado na pasta `love` registrando os dispositivos ALSA e a inicialização dos drivers de áudio

#### Scenario: Execução comum sem chave de diagnóstico
- **WHEN** a chave `r36-diagnostico` não existe em `/storage/roms`
- **THEN** nenhum log adicional do OpenAL é gravado na partição de ROMs, preservando o ciclo de escrita do cartão SD

### Requirement: Mapeamento posicional dos botões do portátil
O ambiente do LÖVE SHALL mapear os botões de ação física do portátil na disposição de consoles portáteis (botão da direita = A, botão inferior = B, botão superior = X, botão da esquerda = Y). O `SDL_GAMECONTROLLERCONFIG` e o tratamento de botões crus de joystick no executável `love` SHALL entregar os eventos de controle de modo que os índices de botões correspondam à geometria física do R36S.

#### Scenario: Acionamento dos botões de face
- **WHEN** o jogador aperta o botão físico da direita ou de baixo do portátil
- **THEN** os eventos reportados ao jogo correspondem às ações atribuídas respectivamente aos botões físicos da direita e de baixo, sem inversão tipo Xbox

#### Scenario: D-pad e analógicos no jogo
- **WHEN** o jogador utiliza o direcional digital (D-pad) ou os direcionais analógicos
- **THEN** os eixos e botões direcionais respondem nas orientações convencionais de movimento e navegação

### Requirement: Perfil gptokeyb limpo sem conflitos de teclas
O arquivo de configuração `love.gptk` SHALL vincular apenas os botões de atalho do sistema (`guide`/`hotkey`, `start`, `back`) e os direcionais mínimos para controle de menu, abstendo-se de injetar teclas de ação arbitrárias do teclado (`space`, `c`, `x`, `v`, `a`, `s`, `d`, `f`, `mouse_left`) sobre os botões de ação do joystick.

#### Scenario: Jogo com suporte a joystick nativo
- **WHEN** o jogador aperta um botão de face durante a partida
- **THEN** o jogo recebe exclusivamente o evento do botão de joystick sem receber simultaneamente eventos falsos de teclado do gptokeyb

### Requirement: Propagação de localização e idioma do console
O lançador `/usr/bin/love.sh` SHALL resolver o idioma ativo do sistema a partir de `/storage/.config/emuelec/configs/emuelec.conf` (`system.language`) com fallback para `/storage/.emulationstation/es_settings.cfg` (`Language`) e padrão `en_US`. O script SHALL exportar as variáveis `CONSOLE_LANG`, `CONSOLE_LANG_SHORT`, `LANG` (`<código>.UTF-8`), `LANGUAGE` e gravar `/tmp/console_lang`.

#### Scenario: Detecção de idioma em script Lua
- **WHEN** o script Lua do jogo consulta `os.getenv("CONSOLE_LANG")` e identifica `pt_BR`
- **THEN** o jogo aplica a localização correspondente sem falha de execução

### Requirement: Registro de log de execução rotativo e configurável
O lançador `/usr/bin/love.sh` SHALL manter registro rotativo em `/storage/roms/love/love.log` controlado por `ENABLE_LOG=1`, arquivando em `love.log.1` quando o arquivo atingir 100 KB, com possibilidade de desativação definindo `ENABLE_LOG=0`.

#### Scenario: Rotação automática de log
- **WHEN** o arquivo `love.log` ultrapassa 100 KB no início da execução
- **THEN** o arquivo existente é rotacionado para `love.log.1` e um novo `love.log` é iniciado

### Requirement: Console LÖVE integrado ao EmulationStation
O `es_systems.cfg` SHALL manter a declaração do sistema `love` mapeando a pasta `/storage/roms/love`, aceitando extensões `.love` e `.zip`, e apontando o comando para `/usr/bin/love.sh "%ROM%"`.

#### Scenario: Inicialização de jogo a partir do menu
- **WHEN** o usuário seleciona um jogo `.love` na interface do EmulationStation
- **THEN** o EmulationStation invoca `/usr/bin/love.sh` passando o caminho da ROM como primeiro argumento

### Requirement: Jogo de validação Mr. Rescue pré-instalado e compatibilizado
A imagem SHALL fornecer o jogo *Mr. Rescue* (`mrrescue.love`) pré-instalado em `/storage/roms/love/`, configurado para rodar nativamente com a resolução e os botões adequados ao console.

#### Scenario: Partida inicial de Mr. Rescue
- **WHEN** o jogador abre Mr. Rescue no primeiro boot
- **THEN** o jogo exibe imagem sem cortes, reproduz som e responde aos botões do gamepad
