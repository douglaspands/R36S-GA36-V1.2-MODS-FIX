# Tasks

> **Instruções para execução (otimizado para execução direta passo a passo):**
> - No início do `/opsx-apply`, crie e mude para a branch `corrige-classicube-tela-preta-e-capa` a partir da `main` (`git checkout -b corrige-classicube-tela-preta-e-capa`).
> - Respeite as regras do `GEMINI.md`: comandos relativos à raiz do projeto, **um comando por chamada** (sem `cd`, sem `&&` ou `;`), **sem `sudo`**, e Python sempre via `uv run`.

## 1. Patch de código-fonte C e recompilação do ClassiCube (`ports/classicube/compilar.sh`)

- [x] 1.1 Editar `ports/classicube/compilar.sh` para, logo após o `tar -xzf "$tarball" -C "$src_dir" --strip-components=1`, aplicar um patch via `uv run python -I -c` nos arquivos `src/Bitmap.h`, `src/_GLShared.h` e `src/Window_SDL2.c`, e ao final copiar o binário compilado tanto para `features/60-port-classicube/roms/ports/classicube/ClassiCube` quanto para `features/60-port-classicube/system/usr/share/classicube/ClassiCube`:
  - **Em `$src_dir/src/Bitmap.h`:** substituir `#if defined CC_BUILD_WEB || defined CC_BUILD_ANDROID` por `#if defined CC_BUILD_GLES || defined CC_BUILD_WEB || defined CC_BUILD_ANDROID`.
  - **Em `$src_dir/src/_GLShared.h`:** substituir `#if defined CC_BUILD_WEB || defined CC_BUILD_ANDROID` por `#if defined CC_BUILD_GLES || defined CC_BUILD_WEB || defined CC_BUILD_ANDROID`.
  - **Em `$src_dir/src/Window_SDL2.c`:**
    1. Substituir `Window_Main.Exists     = true;` por `Window_Main.Exists     = true;\n\tWindow_Main.Focused    = true;`.
    2. Substituir `void Gamepads_PreInit(void) { }` por:
       ```c
       void Gamepads_PreInit(void) {
       	SDL_GameControllerAddMappingsFromFile("/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt");
       	SDL_GameControllerAddMappingsFromFile("/storage/.config/SDL-GameControllerDB/gamecontrollerdb.txt");
       }
       ```
    3. Substituir:
       ```c
       	Gamepad_SetButton(port, CCPAD_SELECT, SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_GUIDE));
       	Gamepad_SetButton(port, CCPAD_START,  SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_START));
       ```
       por:
       ```c
       	int select_btn = SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_GUIDE) || SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_BACK);
       	int start_btn  = SDL_GameControllerGetButton(gp, SDL_CONTROLLER_BUTTON_START);
       	if (select_btn && start_btn) { Window_RequestClose(); return; }
       	Gamepad_SetButton(port, CCPAD_SELECT, select_btn);
       	Gamepad_SetButton(port, CCPAD_START,  start_btn);
       ```
- [x] 1.2 Executar `./ports/classicube/compilar.sh` para recompilar o binário ARMv7-A hard-float no container `localhost/r36-cores-a33` e instalá-lo em `features/60-port-classicube/roms/ports/classicube/ClassiCube` e `features/60-port-classicube/system/usr/share/classicube/ClassiCube`.

## 2. Atualização do `options.txt` e do `ClassiCube.sh` (`features/60-port-classicube`)

- [x] 2.1 Atualizar `features/60-port-classicube/roms/ports/classicube/options.txt` adicionando `auto-pause = false` para garantir que o jogo nunca entre em menu de pausa escuro automaticamente:
  ```ini
  # Configuração prévia do ClassiCube para R36S clone (Allwinner A33 / Mali-400 MP2)
  # Tela: 640x480 nativa | 60 FPS | Texturas clássicas offline | Áudio 100%
  window-width = 640
  window-height = 480
  viewdist = 96
  fpslimit = Limit60FPS
  mousesensitivity = 30
  gfx-smoothlighting = false
  gfx-mipmaps = false
  soundsvolume = 100
  musicvolume = 100
  defaulttexpack = default.zip
  gui-blockinhand = true
  gui-showfps = true
  autocloselauncher = true
  singleplayerphysics = true
  viewbobbing = true
  auto-pause = false
  ```
- [x] 2.2 Atualizar `features/60-port-classicube/roms/ports_scripts/ClassiCube.sh` (com permissão `0755`) para:
  - Exportar `SDL_GAMECONTROLLERCONFIG` extraindo o mapeamento do `micro_gamepad` de `/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt` (necessário para SDL 2.0.9).
  - Sincronizar os arquivos offline de `/usr/share/classicube` para `/storage/roms/ports/classicube` caso o diretório na `p1` esteja incompleto (ex.: quando o cartão foi atualizado com `--keep-roms`).
  - Garantir `auto-pause = false` no `options.txt` do cartão.
  - Priorizar a execução direta de `/usr/share/classicube/ClassiCube` (ou `/tmp/classicube/ClassiCube` como fallback) com `cd /storage/roms/ports/classicube` e `--singleplayer`:
  ```bash
  #!/usr/bin/env bash
  # Inicializador do ClassiCube para EmuELEC no Allwinner A33 (R36S clone)
  # Mapeado no menu "Ports" do EmulationStation (/storage/roms/ports_scripts/ClassiCube.sh)
  set -euo pipefail

  PORT_DIR="/storage/roms/ports/classicube"
  SHARE_DIR="/usr/share/classicube"
  TMP_DIR="/tmp/classicube"
  DB_FILE="/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt"

  export LD_LIBRARY_PATH="/usr/lib:${LD_LIBRARY_PATH:-}"
  export SDL_VIDEO_GL_DRIVER="/usr/lib/libGLESv2.so.2"
  export SDL_VIDEO_EGL_DRIVER="/usr/lib/libEGL.so.1"

  if [ -f "$DB_FILE" ]; then
      export SDL_GAMECONTROLLERCONFIG_FILE="$DB_FILE"
      SDL_CFG="$(grep -E 'micro_gamepad|retrogame_joypad' "$DB_FILE" || true)"
      if [ -n "$SDL_CFG" ]; then
          export SDL_GAMECONTROLLERCONFIG="$SDL_CFG"
      fi
  fi

  mkdir -p "$PORT_DIR/texpacks" "$PORT_DIR/audio" "$PORT_DIR/maps"

  if [ -d "$SHARE_DIR" ]; then
      [ ! -f "$PORT_DIR/options.txt" ] && cp -f "$SHARE_DIR/options.txt" "$PORT_DIR/options.txt"
      [ ! -f "$PORT_DIR/texpacks/default.zip" ] && cp -f "$SHARE_DIR/texpacks/default.zip" "$PORT_DIR/texpacks/default.zip"
      if [ ! -f "$PORT_DIR/audio/default.zip" ] && [ -f "$SHARE_DIR/audio/default.zip" ]; then
          cp -f "$SHARE_DIR/audio/default.zip" "$PORT_DIR/audio/default.zip"
      fi
  fi

  if [ -f "$PORT_DIR/audio/default.zip" ] && ! compgen -G "$PORT_DIR/audio/*.wav" >/dev/null; then
      unzip -oq "$PORT_DIR/audio/default.zip" -d "$PORT_DIR/audio" 2>/dev/null || true
  fi

  if [ -f "$PORT_DIR/options.txt" ] && ! grep -q '^auto-pause' "$PORT_DIR/options.txt"; then
      echo "auto-pause = false" >> "$PORT_DIR/options.txt"
  fi

  cd "$PORT_DIR"

  if [ -x "$SHARE_DIR/ClassiCube" ]; then
      BIN="$SHARE_DIR/ClassiCube"
  elif [ -x "$PORT_DIR/ClassiCube" ]; then
      BIN="$PORT_DIR/ClassiCube"
  else
      mkdir -p "$TMP_DIR"
      cp -f "$PORT_DIR/ClassiCube" "$TMP_DIR/ClassiCube"
      chmod 0755 "$TMP_DIR/ClassiCube"
      BIN="$TMP_DIR/ClassiCube"
  fi

  "$BIN" --singleplayer
  exit 0
  ```

## 3. Espelhamento na camada `system` e serviço de boot (`features/60-port-classicube`)

- [x] 3.1 Copiar os arquivos de `features/60-port-classicube/roms/ports_scripts/` (`ClassiCube.sh`, `gamelist.xml`, `img/ClassiCube.png`, `images/ClassiCube-image.png`, `images/ClassiCube-thumb.png`, `images/ClassiCube-marquee.png`) para `features/60-port-classicube/system/usr/bin/ports/` (para que entrem diretamente no `lowerdir=/usr/bin/ports` do overlay montado pelo `mount_romfs.sh`).
- [x] 3.2 Copiar os arquivos de `features/60-port-classicube/roms/ports/classicube/` (`ClassiCube`, `options.txt`, `texpacks/default.zip`, `audio/default.zip`) para `features/60-port-classicube/system/usr/share/classicube/`.
- [x] 3.3 Criar o script `features/60-port-classicube/system/usr/lib/r36/classicube-sync` (com permissão `0755`) que sincroniza os metadados, capa e ativos no boot (após `emuelec-autostart.service` e antes de `emustation.service`):
  ```sh
  #!/bin/sh
  # Sincroniza o port ClassiCube e sua capa no menu Ports após mount_romfs.sh,
  # garantindo funcionamento mesmo em cartões atualizados com --keep-roms.

  PORTS_SRC="/usr/bin/ports"
  SHARE_SRC="/usr/share/classicube"
  PORTS_UPPER="/storage/.config/emuelec/ports"
  PORTS_ROMS="/storage/roms/ports_scripts"
  ES_GAMELIST_DIR="/storage/.config/emulationstation/gamelists/ports"
  PORT_DEST="/storage/roms/ports/classicube"

  if [ -d "$PORTS_SRC" ]; then
      for dst in "$PORTS_UPPER" "$PORTS_ROMS"; do
          mkdir -p "$dst/img" "$dst/images" 2>/dev/null || true
          cp -f "$PORTS_SRC/ClassiCube.sh" "$dst/ClassiCube.sh" 2>/dev/null || true
          chmod 0755 "$dst/ClassiCube.sh" 2>/dev/null || true
          cp -f "$PORTS_SRC/img/ClassiCube.png" "$dst/img/ClassiCube.png" 2>/dev/null || true
          cp -f "$PORTS_SRC/images/"*.png "$dst/images/" 2>/dev/null || true
          if [ ! -f "$dst/gamelist.xml" ] || ! grep -q "ClassiCube.png" "$dst/gamelist.xml" 2>/dev/null; then
              cp -f "$PORTS_SRC/gamelist.xml" "$dst/gamelist.xml" 2>/dev/null || true
          fi
      done

      mkdir -p "$ES_GAMELIST_DIR/img" "$ES_GAMELIST_DIR/images" 2>/dev/null || true
      cp -f "$PORTS_SRC/img/ClassiCube.png" "$ES_GAMELIST_DIR/img/ClassiCube.png" 2>/dev/null || true
      cp -f "$PORTS_SRC/images/"*.png "$ES_GAMELIST_DIR/images/" 2>/dev/null || true
      if [ ! -f "$ES_GAMELIST_DIR/gamelist.xml" ] || ! grep -q "ClassiCube.png" "$ES_GAMELIST_DIR/gamelist.xml" 2>/dev/null; then
          cp -f "$PORTS_SRC/gamelist.xml" "$ES_GAMELIST_DIR/gamelist.xml" 2>/dev/null || true
      fi
  fi

  if [ -d "$SHARE_SRC" ] && mountpoint -q /storage/roms 2>/dev/null; then
      mkdir -p "$PORT_DEST/texpacks" "$PORT_DEST/audio" "$PORT_DEST/maps" 2>/dev/null || true
      cp -f "$SHARE_SRC/ClassiCube" "$PORT_DEST/ClassiCube" 2>/dev/null || true
      [ ! -f "$PORT_DEST/options.txt" ] && cp -f "$SHARE_SRC/options.txt" "$PORT_DEST/options.txt" 2>/dev/null || true
      [ ! -f "$PORT_DEST/texpacks/default.zip" ] && cp -f "$SHARE_SRC/texpacks/default.zip" "$PORT_DEST/texpacks/default.zip" 2>/dev/null || true
      [ ! -f "$PORT_DEST/audio/default.zip" ] && cp -f "$SHARE_SRC/audio/default.zip" "$PORT_DEST/audio/default.zip" 2>/dev/null || true
  fi

  exit 0
  ```
- [x] 3.4 Criar a unit `features/60-port-classicube/system/usr/lib/systemd/system/r36-classicube-sync.service` e o symlink `features/60-port-classicube/system/usr/lib/systemd/system/emuelec.target.wants/r36-classicube-sync.service -> ../r36-classicube-sync.service`:
  ```ini
  [Unit]
  Description=Sincroniza ClassiCube e capa no menu Ports (R36S)
  After=emuelec-autostart.service
  Before=emustation.service

  [Service]
  Type=oneshot
  ExecStart=/usr/lib/r36/classicube-sync
  RemainAfterExit=yes

  [Install]
  WantedBy=emuelec.target
  ```

## 4. Testes automatizados e validação de build

- [x] 4.1 Atualizar `tests/test_port_classicube.py` para verificar:
  - Que o binário `ClassiCube` referencia `SDL_GameControllerAddMappingsFromFile` (garantindo que o patch de gamepad SDL 2.0.9 foi compilado no binário) e que `roms/ports/classicube/ClassiCube` e `system/usr/share/classicube/ClassiCube` são idênticos.
  - Que `system/usr/bin/ports/ClassiCube.sh`, `system/usr/bin/ports/gamelist.xml` e `system/usr/bin/ports/img/ClassiCube.png` existem e são idênticos aos de `roms/ports_scripts/`.
  - Que `system/usr/lib/r36/classicube-sync` tem sintaxe `sh -n` válida e `r36-classicube-sync.service` está habilitado em `emuelec.target.wants`.
  - Que `options.txt` contém `auto-pause = false` e `ClassiCube.sh` exporta `SDL_GAMECONTROLLERCONFIG`.
- [x] 4.2 Executar a suíte de testes completa com `uv run python -I -m unittest discover -s tests` e confirmar 100% de aprovação.
- [x] 4.3 Executar `./build.sh --test --fast` para validar a geração da imagem e verificar o `changes.txt`.
