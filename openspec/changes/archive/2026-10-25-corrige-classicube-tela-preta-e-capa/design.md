# Design

## Context

O console R36S clone (Allwinner A33, GPU Mali-400 MP2, EmuELEC 4.7) possui as seguintes características e restrições de hardware/sistema identificadas na imagem base:
1. **Driver OpenGL ES 2.0 (`usr/lib/libGLESv2.so.2.0`):**
   - Anuncia `"GL_EXT_texture_format_BGRA8888"` em `glGetString(GL_EXTENSIONS)`.
   - Valida estritamente a especificação Khronos `EXT_texture_format_BGRA8888`: em `glTexImage2D`, o 3º argumento (`internalformat`) **deve ser idêntico** ao 7º argumento (`format`). Caso contrário, emite `'format' does not match 'internalformat'` (`GL_INVALID_OPERATION`).
   - No código original do ClassiCube 1.3.9 (`src/_GLShared.h` e `src/Bitmap.h`), apenas `CC_BUILD_WEB` e `CC_BUILD_ANDROID` usam `PIXEL_FORMAT = GL_RGBA` (`0x1908`) com `BITMAPCOLOR_R_SHIFT = 0`. O build Linux usa `PIXEL_FORMAT = _GL_BGRA_EXT` (`0x80E1`), mas em `CallTexImage2D` (`src/_GLShared.h:137`) passa `GL_RGBA` como `internalformat` e `_GL_BGRA_EXT` como `format`. Isso faz com que 100% das texturas falhem e o shader amostre `(0, 0, 0, 1)` (tela preta).
2. **Backend SDL 2.0.9 (`usr/lib/libSDL2-2.0.so.0.9.0`) com `mali-fbdev`:**
   - Não possui gerenciador de janelas (X11/Wayland), logo `SDL_CreateWindow` não emite `SDL_WINDOWEVENT_FOCUS_GAINED`. Como `Window_Main.Focused` inicia em `false` (`0`), o ClassiCube bloqueia inputs (`Input.c:641`) e abre o menu de pausa escurecido (`Game.c:774`).
   - Por ser SDL **2.0.9**, ignora a variável de ambiente `SDL_GAMECONTROLLERCONFIG_FILE` (que só existe a partir do SDL 2.0.10). Ele lê apenas `SDL_GAMECONTROLLERCONFIG` ou chamadas explícitas a `SDL_GameControllerAddMappingsFromFile()`.
   - O controle interno do portátil (`190000006d6963726f5f67616d657000,micro_gamepad`) mapeia o botão Select como `back:b8` (`SDL_CONTROLLER_BUTTON_BACK`), enquanto `Window_SDL2.c` (`ProcessGamepadButtons`) checava apenas `SDL_CONTROLLER_BUTTON_GUIDE` para `CCPAD_SELECT`.
3. **Montagem de `/storage/roms/ports_scripts` e uso de `--keep-roms`:**
   - Em `/usr/bin/mount_romfs.sh` (linha 322 da imagem base), o EmuELEC executa:
     ```bash
     mount -t overlay ports -o lowerdir=/usr/bin/ports,upperdir=/emuelec/ports,workdir=/storage/.tmp/ports-workdir "${LINK}/ports_scripts"
     ```
     Isto **encobre** o diretório `/storage/roms/ports_scripts` da partição FAT32 (`p1`) com um `overlayfs` cujo `lowerdir` é `/usr/bin/ports` (partição `SYSTEM`, `p5`) e `upperdir` é `/emuelec/ports` (symlink para `/storage/.config/emuelec/ports` na partição `STORAGE`, `p8`)!
   - Além disso, quando o cartão SD é atualizado com `./flash.sh --keep-roms` (ou `--part system`), a partição `roms` (`p1`) não é sobrescrita.

Consulte `proposal.md` para motivação e `specs/classicube-port/spec.md` para os requisitos normativos.

## Goals / Non-Goals

**Goals:**
- Corrigir a renderização preta no ClassiCube fazendo o build GLES (`CC_BUILD_GLES`) usar formato `GL_RGBA` nativo em `Bitmap.h` e `_GLShared.h`.
- Garantir foco inicial ativo (`Window_Main.Focused = true`), carregamento de `gamecontrollerdb.txt` em `Window_SDL2.c`, suporte ao botão `BACK` como `Select` e atalho `Select + Start` para encerrar o jogo.
- Garantir que `ClassiCube.sh`, `gamelist.xml` e as imagens de capa (`img/ClassiCube.png` e `images/ClassiCube-*.png`) estejam presentes no overlay `/usr/bin/ports` (`system`), no `roms/ports_scripts` (`roms`) e sejam sincronizados no boot antes do EmulationStation iniciar, funcionando inclusive com `--keep-roms`.

**Non-Goals:**
- Não alterar nenhuma outra feature além de `60-port-classicube` e o script de build `ports/classicube/compilar.sh`.
- Não exigir conexão de rede (tudo roda 100% offline).

## Decisions

### 1. Patch no código-fonte C do ClassiCube durante `ports/classicube/compilar.sh`

Para manter a reprodutibilidade a partir do tarball oficial `classicube-1.3.9.tar.gz` (verificado por SHA256), `ports/classicube/compilar.sh` aplicará três modificações exatas via `python3` (ou `sed`) logo após extrair o tarball em `$src_dir`:

#### 1.1. Formato `RGBA` nativo para `CC_BUILD_GLES` em `src/Bitmap.h` e `src/_GLShared.h`
- **Em `src/Bitmap.h` (linha 11):**
  Substituir:
  ```c
  #if defined CC_BUILD_WEB || defined CC_BUILD_ANDROID || defined CC_BUILD_PSP || defined CC_BUILD_PSVITA || defined CC_BUILD_PS2 || defined CC_BUILD_PS4
  ```
  Por:
  ```c
  #if defined CC_BUILD_GLES || defined CC_BUILD_WEB || defined CC_BUILD_ANDROID || defined CC_BUILD_PSP || defined CC_BUILD_PSVITA || defined CC_BUILD_PS2 || defined CC_BUILD_PS4
  ```
- **Em `src/_GLShared.h` (linha 5):**
  Substituir:
  ```c
  #if defined CC_BUILD_WEB || defined CC_BUILD_ANDROID
  	#define PIXEL_FORMAT GL_RGBA
  #else
  	#define PIXEL_FORMAT _GL_BGRA_EXT
  #endif
  ```
  Por:
  ```c
  #if defined CC_BUILD_GLES || defined CC_BUILD_WEB || defined CC_BUILD_ANDROID
  	#define PIXEL_FORMAT GL_RGBA
  #else
  	#define PIXEL_FORMAT _GL_BGRA_EXT
  #endif
  ```
- **Racional:** Com `PIXEL_FORMAT = GL_RGBA` e os shifts de `BitmapCol` em ordem `R=0, G=8, B=16, A=24`, o decodificador PNG do ClassiCube já grava os pixels em memória como `RGBA`. Em `GLBackend_Init()`, `convert_rgba` permanece `false` (`PIXEL_FORMAT != GL_RGBA` é falso) e `CallTexImage2D` chama `_glTexImage2D(GL_TEXTURE_2D, lvl, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels)`. Tanto `internalformat` quanto `format` são `GL_RGBA` (`0x1908`), que é o formato nativo obrigatório de qualquer GPU OpenGL ES 2.0, sem nenhuma conversão extra de CPU!

#### 1.2. Foco inicial e Gamepad SDL 2.0.9 em `src/Window_SDL2.c`
- **Em `DoCreateWindow` (`src/Window_SDL2.c`, logo após `Window_Main.Exists = true;`):**
  Adicionar `Window_Main.Focused = true;`:
  ```c
  	Window_Main.Exists     = true;
  	Window_Main.Focused    = true;
  ```
- **Em `Gamepads_PreInit` (`src/Window_SDL2.c`, linha 476):**
  Carregar os mapeamentos do arquivo padrão do EmuELEC:
  ```c
  void Gamepads_PreInit(void) {
  	SDL_GameControllerAddMappingsFromFile("/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt");
  	SDL_GameControllerAddMappingsFromFile("/storage/.config/SDL-GameControllerDB/gamecontrollerdb.txt");
  }
  ```
- **Em `ProcessGamepadButtons` (`src/Window_SDL2.c`, linhas 497-498):**
  Mapear `SDL_CONTROLLER_BUTTON_BACK` junto com `SDL_CONTROLLER_BUTTON_GUIDE` para `CCPAD_SELECT`, e adicionar atalho `Select + Start` para fechar o jogo (`Window_RequestClose()`):
  ```c
  	int select_btn = SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_GUIDE) || SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_BACK);
  	int start_btn  = SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_START);
  	if (select_btn && start_btn) { Window_RequestClose(); return; }
  	Gamepad_SetButton(port, CCPAD_SELECT, select_btn);
  	Gamepad_SetButton(port, CCPAD_START,  start_btn);
  ```

### 2. Arquitetura de Empacotamento em `features/60-port-classicube` (Camadas `system` e `roms`)

```text
+-------------------------------------------------------------------------+
| Camada SYSTEM (p5 - sempre gravada mesmo com --keep-roms)               |
|                                                                         |
| 1. /usr/bin/ports/                                                      |
|    |-- ClassiCube.sh                                                    |
|    |-- gamelist.xml                                                     |
|    |-- img/ClassiCube.png                                               |
|    +-- images/ClassiCube-{image,thumb,marquee}.png                      |
|    (Usado diretamente como lowerdir do overlay em                       |
|     /storage/roms/ports_scripts montado pelo mount_romfs.sh!)           |
|                                                                         |
| 2. /usr/share/classicube/                                               |
|    |-- ClassiCube (binario ARMv7-A corrigido)                           |
|    |-- options.txt                                                      |
|    |-- texpacks/default.zip                                             |
|    +-- audio/default.zip                                                |
|                                                                         |
| 3. /usr/lib/r36/classicube-sync + r36-classicube-sync.service           |
|    (Roda Before=emustation.service e After=emuelec-autostart.service)   |
|    - Garante /emuelec/ports/gamelist.xml e img/ atualizados no overlay  |
|    - Garante /storage/.config/emulationstation/gamelists/ports/         |
|      gamelist.xml atualizado com <image>./img/ClassiCube.png</image>    |
|    - Garante ativos em /storage/roms/ports/classicube/                  |
+-------------------------------------------------------------------------+
```

- **Por que `/usr/bin/ports/` resolve a falta de imagem de capa imediatamente?**
  Porque o `/usr/bin/mount_romfs.sh` da imagem base monta um overlayFS em `/storage/roms/ports_scripts` usando `lowerdir=/usr/bin/ports,upperdir=/emuelec/ports`. Como `/usr/bin/ports` estava vazio na base, tudo o que era colocado apenas na FAT32 (`roms/ports_scripts/`) ficava **escondido por baixo do mount overlay** quando o `mount_romfs.sh` executava `finish_scan()`!
  Colocando `ClassiCube.sh`, `gamelist.xml`, `img/ClassiCube.png` e `images/ClassiCube-*.png` em `system/usr/bin/ports/` **e** sincronizando para `/emuelec/ports` e `/storage/roms/ports_scripts` via `/usr/lib/r36/classicube-sync` (que roda `After=emuelec-autostart.service` e `Before=emustation.service`), os arquivos ficam visíveis tanto se o overlay estiver montado quanto se não estiver, e mesmo quando gravado com `--keep-roms`!

- **Por que `/usr/share/classicube/` + execução direta do binário no `SYSTEM`?**
  O binário `ClassiCube` (~1,1 MiB), `options.txt`, `texpacks/default.zip` (~128 KiB) e `audio/default.zip` (~515 KiB) somam menos de 1,8 MiB (e ~700 KiB comprimidos em LZO no SquashFS `SYSTEM`).
  Ao instalar uma cópia mestre em `system/usr/share/classicube/`:
  - `ClassiCube.sh` pode executar diretamente `/usr/share/classicube/ClassiCube --singleplayer` (que já está num filesystem POSIX com permissão `0755`, sem precisar copiar para `/tmp` a cada execução!), mantendo o diretório de trabalho (`cd /storage/roms/ports/classicube`) para salvar mapas (`maps/`) e configurações do jogador.
  - Antes de iniciar o jogo, `ClassiCube.sh` garante que `/storage/roms/ports/classicube/{options.txt,texpacks/default.zip,audio/}` existam copiando de `/usr/share/classicube/` (e extraindo `audio/default.zip` se necessário). Assim, mesmo que a partição `p1` (`roms`) seja antiga (`--keep-roms`), o jogo carrega na versão nova com todos os ativos!

## Risks / Trade-offs

- **[Risco] Conflito de `gamelist.xml` salvo anteriormente pelo EmulationStation em `/storage/.config/emulationstation/gamelists/ports/gamelist.xml`:**
  - *Mitigação:* O script `/usr/lib/r36/classicube-sync` verifica se `/storage/.config/emulationstation/gamelists/ports/gamelist.xml` existe; se existir sem `ClassiCube.png`, atualiza/substitui pelo `gamelist.xml` com as tags de imagem e copia `img/ClassiCube.png` também para `/storage/.config/emulationstation/gamelists/ports/img/ClassiCube.png`.
- **[Risco] O usuário já tem um `options.txt` antigo no cartão sem `auto-pause = false`:**
  - *Mitigação:* Além de `Window_Main.Focused = true` no próprio binário C, o `ClassiCube.sh` garante que `auto-pause = false` esteja presente no `options.txt` em `/storage/roms/ports/classicube/options.txt`.
