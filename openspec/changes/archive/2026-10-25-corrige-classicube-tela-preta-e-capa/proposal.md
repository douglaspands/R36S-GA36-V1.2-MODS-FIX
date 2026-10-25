# Proposal

## Why

Ao testar o port nativo do ClassiCube ("Classic Craft (ClassiCube)") no R36S clone (Allwinner A33 / Mali-400 MP2), foram constatados dois problemas críticos:

1. **O jogo abre com a tela inteiramente escura (preta) e sem responder adequadamente ao controle:**
   - **Falha de alocação de todas as texturas no OpenGL ES 2.0 (`GL_INVALID_OPERATION`):** Em `src/_GLShared.h` e `src/Bitmap.h`, o ClassiCube compila por padrão no Linux usando ordem de bytes `BGRA` (`PIXEL_FORMAT = _GL_BGRA_EXT = 0x80E1`). No `GLBackend_Init()` (`src/Graphics_GL2.c`), o driver proprietário da Mali-400 (`libGLESv2.so.2.0`) anuncia a extensão `GL_EXT_texture_format_BGRA8888`, fazendo o jogo definir `convert_rgba = false`. Porém, em `CallTexImage2D()` (`src/_GLShared.h:137`), o jogo invoca `_glTexImage2D(GL_TEXTURE_2D, lvl, GL_RGBA, width, height, 0, _GL_BGRA_EXT, GL_UNSIGNED_BYTE, pixels)` passando `internalformat = GL_RGBA` (`0x1908`) e `format = _GL_BGRA_EXT` (`0x80E1`). Pela especificação Khronos `EXT_texture_format_BGRA8888` no OpenGL ES 2.0 (confirmado na string de erro `'format' does not match 'internalformat'` dentro de `libGLESv2.so.2.0`), `internalformat` e `format` precisam ser idênticos. Como resultado, **todas** as chamadas `glTexImage2D` falham (incluindo a textura `white_square` 1x1 usada para cores sólidas, `terrain.png`, `gui.png` e a fonte `default.png`), e o fragment shader da Mali-400 amostra `(0, 0, 0, 1)` (preto) para todos os polígonos 2D e 3D.
   - **Janela sem foco inicial no backend `mali-fbdev` (`Window_Main.Focused == false`):** Em `src/Window_SDL2.c` (`DoCreateWindow`), `Window_Main.Focused` não é inicializado como `true` (aguardando evento `SDL_WINDOWEVENT_FOCUS_GAINED` de um window manager X11/Wayland inexistente no framebuffer `mali-fbdev`). Com isso, `Input.c` limpa os inputs quando `!Window_Main.Focused` e `Game.c` (`Game_RenderFrame`) força a abertura do menu de pausa escurecido se `autoPause` estiver ativo.
   - **Gamepad não reconhecido pelo SDL 2.0.9:** A `libSDL2-2.0.so.0.9.0` da imagem base é versão **2.0.9**, que lê apenas a variável `SDL_GAMECONTROLLERCONFIG` (string de mapeamento) e ignora `SDL_GAMECONTROLLERCONFIG_FILE` (adicionada apenas no SDL 2.0.10). Além disso, em `Window_SDL2.c` (`ProcessGamepadButtons`), o botão `CCPAD_SELECT` é lido apenas de `SDL_CONTROLLER_BUTTON_GUIDE` e não de `SDL_CONTROLLER_BUTTON_BACK` (que é o botão Select do `micro_gamepad` no R36S).

2. **O menu "Ports" do EmulationStation fica sem a imagem de capa do jogo (e o binário não atualiza com `--keep-roms`):**
   - **Arquivos presos exclusivamente na camada `roms` (`p1`) e ignorados por `--keep-roms`:** No `mount_romfs.sh` da imagem base (linha 322), o sistema monta um overlayFS em `/storage/roms/ports_scripts` com `lowerdir=/usr/bin/ports` (na partição `SYSTEM`) e `upperdir=/emuelec/ports` (isto é, `/storage/.config/emuelec/ports` na partição `storage`). Além disso, quando o usuário grava o cartão usando `./flash.sh --keep-roms` (ou `--part system --part storage`), a partição `p1` (`roms`) não é regravada.
   - **Falta de sincronização para `/usr/bin/ports` e `/storage/roms/ports/classicube`:** Como a feature `60-port-classicube` só colocava arquivos na camada `roms`, o overlay de `/storage/roms/ports_scripts` e as atualizações com `--keep-roms` faziam com que o `gamelist.xml`, a imagem `img/ClassiCube.png` e o binário atualizado não aparecessem no EmulationStation.

## What Changes

- **Correção da renderização GLES 2.0, foco SDL2 e controle no código do ClassiCube (`ports/classicube/compilar.sh`):**
  - Aplicar patch determinístico no código-fonte extraído em `ports/classicube/compilar.sh` antes do `make`:
    1. **`src/Bitmap.h` e `src/_GLShared.h`:** Incluir `defined CC_BUILD_GLES` na condição que usa ordem de bytes nativa `RGBA` (`BITMAPCOLOR_R_SHIFT 0`, `G_SHIFT 8`, `B_SHIFT 16`, `A_SHIFT 24`) e `#define PIXEL_FORMAT GL_RGBA`. Assim, todas as texturas (`white_square`, `terrain.png`, `gui.png`, fontes) usam `internalformat = GL_RGBA` e `format = GL_RGBA` nativamente no GLES 2.0, eliminando o erro `GL_INVALID_OPERATION` na GPU Mali-400 sem custo de conversão na CPU.
    2. **`src/Window_SDL2.c`:**
       - Em `DoCreateWindow()`, definir `Window_Main.Focused = true;` logo após criar a janela para que o jogo inicie focado no `mali-fbdev`.
       - Em `Gamepads_PreInit()`, carregar `/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt` via `SDL_GameControllerAddMappingsFromFile()` caso exista, garantindo suporte em SDL 2.0.9.
       - Em `ProcessGamepadButtons()`, aceitar `SDL_CONTROLLER_BUTTON_BACK` ou `SDL_CONTROLLER_BUTTON_GUIDE` para `CCPAD_SELECT`, e permitir sair rapidamente do jogo pressionando `Select + Start` simultaneamente (`Window_RequestClose()`).
  - Recompilar o binário `ClassiCube` com `./ports/classicube/compilar.sh`.
- **Empacotamento resiliente a `--keep-roms` e ao overlay de `ports_scripts` (`features/60-port-classicube`):**
  - Prover os scripts, `gamelist.xml` e imagens (`img/ClassiCube.png` e `images/ClassiCube-*.png`) também na camada `system` em `/usr/bin/ports/` (que é o `lowerdir` do overlay montado por `mount_romfs.sh` em `/storage/roms/ports_scripts`) e o pacote do jogo (`ClassiCube`, `options.txt`, `texpacks/default.zip`, `audio/default.zip`) em `/usr/share/classicube/`.
  - Criar um serviço/script de boot leve (`r36-classicube-sync.service` -> `/usr/lib/r36/classicube-sync`) que roda após `emuelec-autostart.service` (quando `/storage/roms` e o overlay `/storage/roms/ports_scripts` já estão montados) e sincroniza `/usr/share/classicube/` para `/storage/roms/ports/classicube/` e `/usr/bin/ports/` para `/storage/roms/ports_scripts/` e `/storage/.config/emulationstation/gamelists/ports/gamelist.xml`.
  - Atualizar `ClassiCube.sh` para exportar `SDL_GAMECONTROLLERCONFIG` (extraindo a linha `micro_gamepad` do `gamecontrollerdb.txt` para o SDL 2.0.9), sincronizar ativos ausentes de `/usr/share/classicube` caso necessário, e executar `/usr/share/classicube/ClassiCube` (ou `/tmp/classicube/ClassiCube`) com diretório de trabalho em `/storage/roms/ports/classicube`.
  - Atualizar `options.txt` com `auto-pause = false` e mapeamentos confortáveis para o portátil.

## Capabilities

### New Capabilities
Nenhuma.

### Modified Capabilities
- `classicube-port`: adiciona requisitos de compatibilidade de formato de textura `GL_RGBA` no OpenGL ES 2.0 (Mali-400), foco inicial da janela em `mali-fbdev`, suporte ao controle `micro_gamepad` em SDL 2.0.9 (incluindo botão Back/Select e atalho Select+Start para sair) e espelhamento em `system` (`/usr/bin/ports` e `/usr/share/classicube`) com sincronização automática no boot para garantir que a capa e o binário funcionem mesmo quando o cartão é atualizado com `--keep-roms`.

## Impact

- `ports/classicube/compilar.sh`: aplica os ajustes em `Bitmap.h`, `_GLShared.h` e `Window_SDL2.c` e regera o binário ARMv7-A.
- `features/60-port-classicube/`: inclui camada `system/` (`/usr/bin/ports/`, `/usr/share/classicube/`, `/usr/lib/r36/classicube-sync`, `/usr/lib/systemd/system/r36-classicube-sync.service`) além da camada `roms/`, e atualiza `ClassiCube.sh` e `options.txt`.
- `tests/test_port_classicube.py`: valida símbolos/strings do binário corrigido, estrutura nas camadas `system` e `roms`, `SDL_GAMECONTROLLERCONFIG` no launcher e serviço de sincronização.
