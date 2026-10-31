# Design: love2d-ajustes-r36s

## Context

O R36S clone (GA36-MB V1.2, Allwinner A33) executa o EmuELEC 4.7 Nexus em framebuffer nativo `/dev/fb0` (display LCD 640x480, 4:3) com GPU ARM Mali-400 MP2 via EGL e OpenGL ES 2.0. O console não possui servidor gráfico X11 nem Wayland. A entrada de controles é gerenciada pelo driver de kernel `udt_joystick` expondo o dispositivo `micro_gamepad`.

A integração prévia do LÖVE 11.5 como executável standalone (`/usr/bin/love.sh`) revelou discrepâncias na experiência do usuário em relação ao restante do sistema:
1. O atalho de encerramento do console (`FN + Start`) não funciona porque o FN emite `BTN_MODE` (código 316, botão 10 do `micro_gamepad`), que não estava associado à chave `guide` na configuração do SDL2 e do `gptokeyb`.
2. A transição visual entre o EmulationStation e o jogo exibe resíduos de console em vez do splash neutro com ícone de controle (`/usr/config/splash/loading-game.png`).
3. O subsistema de áudio não emite som devido à falta de inicialização explícita do driver ALSA no SDL/OpenAL e à ausência de sincronização de ganho do codec de áudio.
4. Jogos projetados para resoluções de desktop (como o *Mr. Rescue* em 768x600) abrem descentralizados ou com cortes de imagem no display fixo de 640x480.
5. Os botões de ação apresentam mapeamento divergente do layout físico do console (padrão Xbox vs. padrão físico Nintendo do R36S).

Veja a motivação detalhada no `proposal.md` e os requisitos funcionais no `specs/love2d-engine/spec.md`.

## Goals / Non-Goals

**Goals:**
- Mapear o botão FN (`BTN_MODE`, botão 10) como `guide` no SDL2 e configurar o `gptokeyb` para que o pressionamento simultâneo de `FN + Start` encerre qualquer jogo LÖVE com `SIGTERM`.
- Integrar telas de splash neutras na inicialização e saída no `/usr/bin/love.sh` com `mpv` e `blank_buffer`.
- Garantir a saída de som via ALSA no OpenAL Soft e disponibilizar diagnóstico verboso condicionado à chave `r36-diagnostico` na partição `R36-ROMS`.
- Implementar ajuste de escala/viewport proporcional no runtime LÖVE 11.5 para enquadrar qualquer resolução no display 640x480 com letterboxing automático.
- Ajustar os mapeamentos de controle no SDL e os índices de joystick no LÖVE para respeitar a geometria física dos botões de face do R36S.
- Eliminar injeções de teclado duplicadas no perfil `love.gptk`.

**Non-Goals:**
- Adicionar menus gráficos de configuração dentro do LÖVE durante o jogo.
- Recompilar o kernel ou alterar drivers do subsistema gráfico sunxi.
- Executar jogos através do RetroArch (o LÖVE permanece 100% standalone).

## Decisions

### Decisão 1: Atalho de encerramento universal com FN + Start via gptokeyb
**Decisão:** Injetar no `love.sh` a variável `SDL_GAMECONTROLLERCONFIG` contendo `guide:b10` para o dispositivo `micro_gamepad`, e reconfigurar `love.gptk` com:
```ini
hotkey = guide
start = enter
```
**Racional:** No boot do R36S, o serviço `r36-fn.service` remapeia o botão físico FN para `BTN_MODE` (código 316), que a `libSDL2` lê como botão 10 do gamepad. Ao mapeá-lo como `guide`, o `gptokeyb` monitora o botão 10 como hotkey do sistema. Quando o usuário pressiona `FN + Start`, o `gptokeyb` envia `SIGTERM` ao processo `love`, garantindo saída limpa para o EmulationStation sem prender o framebuffer.
**Alternativas consideradas:** Usar `Select + Start` (rejeitada por conflitar com ações de inventário/pausa em jogos e divergir da convenção do FN estabelecida no restante do console).

### Decisão 2: Ciclo de splash neutro no lançador love.sh
**Decisão:** Adicionar rotina de exibição do splash no `/usr/bin/love.sh` espelhando a lógica de `emuelecRunEmu.sh`:
- Antes de iniciar o binário:
  ```bash
  SPLASH_IMG="/usr/config/splash/loading-game.png"
  [ ! -f "$SPLASH_IMG" ] && SPLASH_IMG="/storage/.config/splash/loading-game.png"
  if [ -f "$SPLASH_IMG" ] && command -v mpv >/dev/null 2>&1; then
      mpv "$SPLASH_IMG" &
      SPLASH_PID=$!
  fi
  ```
- No `cleanup()` (ao sair do jogo):
  ```bash
  [ -n "${SPLASH_PID:-}" ] && kill -9 "$SPLASH_PID" 2>/dev/null || true
  if [ -f "$SPLASH_IMG" ] && command -v mpv >/dev/null 2>&1; then
      mpv "$SPLASH_IMG" >/dev/null 2>&1 || true
  fi
  ```
**Racional:** O `es_systems.cfg` chama `/usr/bin/love.sh` diretamente, sem passar por `emuelecRunEmu.sh`. Sem esse ciclo no lançador, a troca de tela exibe linhas de terminal e mensagens do `setterm`.

### Decisão 3: Cadeia de som ALSA, ganho analógico e diagnóstico
**Decisão:** No `/usr/bin/love.sh`:
1. Definir explicitamente `export SDL_AUDIODRIVER=alsa`.
2. Verificar fone de ouvido em `/sys/class/switch/h2w/state` e configurar `amixer cset name='Speaker Function' spk` (ou `headset`).
3. Chamar `/usr/lib/r36/audio-ganho aplica` antes de carregar o executável e no encerramento (`cleanup`).
4. Se o arquivo `/storage/roms/r36-diagnostico` existir, exportar:
   ```bash
   export ALSOFT_LOGLEVEL=3
   export ALSOFT_LOGFILE="/storage/roms/love/r36-love-alsoft.log"
   ```
**Racional:** A `libopenal.so.1.22.2` da base depende diretamente do ALSA (`libasound.so.2`). Sem a garantia de que o codec `sunxi-pcm-codec` está no canal analógico correto e com o ganho aplicado, o stream de áudio pode ser silenciado ou não encontrar o dispositivo padrão `pcm.!default`. O log sob `r36-diagnostico` fornece isolamento preciso sem onerar a escrita no cartão no dia a dia.

### Decisão 4: Viewport escalonado proporcionalmente para 640x480 no LÖVE
**Decisão:** No código fonte C++ do runtime LÖVE (`src/modules/window/sdl/Window.cpp` e `src/modules/graphics/opengl/Graphics.cpp`), interceptar as chamadas de criação de janela e renderização em modo GLES/fbdev:
- Consultar a resolução nativa do display via `SDL_GetDisplayBounds` ou fixar 640x480 no fbdev.
- Forçar a criação da janela em tela cheia na resolução física (640x480).
- Aplicar escala uniforme (`scale = min(640/w, 480/h)`) e translação centrada (`glViewport`), evitando que jogos com resoluções maiores ou arbitrárias tenham suas coordenadas deslocadas para fora do display.
**Alternativas consideradas:** Tentar configurar modo de vídeo via arquivo de configuração de cada jogo individualmente (rejeitada por ser inviável para novos jogos adicionados pelo usuário na pasta de ROMs).

### Decisão 5: Alinhamento posicional dos botões no hardware
**Decisão:**
1. No `SDL_GAMECONTROLLERCONFIG` gerado no `love.sh`:
   Mapear `a:b0,b:b1,x:b2,y:b3` (ou a permutação necessária conforme o padrão reportado pelos eixos de hardware) garantindo que o botão da direita gere A e o de baixo gere B.
2. No LÖVE (`src/modules/joystick/sdl/Joystick.cpp`):
   Assegurar que os botões físicos reportados para a API `love.joystick` (usada por jogos homebrew legados) respeitem a ordem dos botões de face (índices 1 a 4 correspondendo a Direita, Baixo, Cima, Esquerda), prevenindo inversões de pulo/ação.
**Alternativas consideradas:** Reconfigurar apenas no `options.lua` do *Mr. Rescue* (rejeitada por não solucionar o problema para futuros jogos LÖVE copiados para o SD).

### Decisão 6: Perfil gptokeyb limpo
**Decisão:** O arquivo `love.gptk` manterá apenas os mapeamentos de controle do sistema:
```ini
guide = esc
hotkey = guide
start = enter
back = esc
up = up
down = down
left = left
right = right
```
Removendo os binds de `space`, `c`, `x`, `v`, `mouse_left`, etc.
**Racional:** Esses mapeamentos tentavam simular um teclado sobre os botões de ação do gamepad, gerando eventos duplicados toda vez que o jogador pressionava um botão nativo do joystick.

## Risks / Trade-offs

- **[Custo de recompilação do LÖVE]** → *Risco:* A compilação do executável `love` no container Debian Bookworm requer ferramentas de compilação cruzada. *Mitigação:* O container `localhost/r36-love2d-builder` já está modelado em `ports/love2d/Containerfile` e `compilar.sh`.
- **[Desempenho de scaling em software/hardware]** → *Risco:* Escala de viewport pode consumir ciclos se feita de forma ineficiente. *Mitigação:* O ajuste de viewport é feito diretamente via `glViewport` e matriz de projeção OpenGL ES 2.0 na GPU Mali-400 MP2 com custo zero para a CPU.
