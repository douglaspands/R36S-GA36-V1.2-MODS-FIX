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
   - O controle interno do portátil (`190000006d6963726f5f67616d657000,micro_gamepad`) mapeia o botão físico Select (`b8`) **duas vezes**, como `back:b8` e `guide:b8`. O `CCPAD_SELECT` original, lido de `SDL_CONTROLLER_BUTTON_GUIDE`, já respondia a esse botão desde que o mapeamento fosse carregado; acrescentar `BACK` é redundância inofensiva, e o que faltava de fato era carregar o mapeamento no SDL 2.0.9.
3. **Montagem de `/storage/roms/ports_scripts` e uso de `--keep-roms`:**
   - No `finish_scan()` de `/usr/bin/mount_romfs.sh` (linha 319 da imagem base, chamado de forma síncrona por `emuelec_autostart.sh`), o EmuELEC tenta:
     ```bash
     mount -t overlay ports -o lowerdir=/usr/bin/ports,upperdir=/emuelec/ports,workdir=/storage/.tmp/ports-workdir "${LINK}/ports_scripts"
     ```
   - **Na imagem base `/usr/bin/ports` não existe** (conferido com `unsquashfs -l` no `SYSTEM`), então esse mount falha e `/storage/roms/ports_scripts` fica sendo a pasta FAT32 da p1, visível e editável no PC. O `es_systems.cfg` aponta o sistema `ports` para essa pasta. Criar `/usr/bin/ports` faz o overlay passar a montar e **esconde** tudo o que estiver na pasta da p1, inclusive ports que o usuário copiar pelo PC.
   - Quando o cartão SD é atualizado com `./flash.sh --keep-roms` (ou `--part system`), a partição `roms` (`p1`) não é regravada. Essa é a causa provável da capa ausente: os arquivos da feature nunca chegam à p1 de um cartão gravado assim.

Consulte `proposal.md` para motivação e `specs/classicube-port/spec.md` para os requisitos normativos.

## Goals / Non-Goals

**Goals:**
- Corrigir a renderização preta no ClassiCube fazendo o build GLES (`CC_BUILD_GLES`) usar formato `GL_RGBA` nativo em `Bitmap.h` e `_GLShared.h`.
- Garantir foco inicial ativo (`Window_Main.Focused = true`), carregamento de `gamecontrollerdb.txt` em `Window_SDL2.c`, suporte ao botão `BACK` como `Select` e atalho `Select + Start` para encerrar o jogo.
- Garantir que `ClassiCube.sh`, a entrada no `gamelist.xml` e as imagens de capa (`img/ClassiCube.png` e `images/ClassiCube-*.png`) estejam em `/storage/roms/ports_scripts` (p1) antes do EmulationStation iniciar, restaurados no boot a partir da cópia mestre no `system`, funcionando inclusive com `--keep-roms`.
- Manter `/storage/roms/ports_scripts` como a pasta FAT32 da p1 (sem overlay), para que o usuário continue podendo adicionar ports pelo PC.

**Non-Goals:**
- Não alterar nenhuma outra feature além de `60-port-classicube` e o script de build `ports/classicube/compilar.sh`.
- Não exigir conexão de rede (tudo roda 100% offline).

## Decisions

### 1. Patch no código-fonte C do ClassiCube durante `ports/classicube/compilar.sh`

Para manter a reprodutibilidade a partir do tarball oficial `classicube-1.3.9.tar.gz` (verificado por SHA256), `ports/classicube/compilar.sh` aplicará três modificações exatas via `uv run python -I -c` logo após extrair o tarball em `$src_dir`:

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

> **Revisão pós-arquivamento (2026-10-25).** A primeira versão desta decisão
> instalava os arquivos em `/usr/bin/ports/`, supondo que o overlay do
> `mount_romfs.sh` já encobria a p1 e que `/usr/bin/ports` estava vazio. Na base
> esse diretório não existe e o overlay falha; criá-lo ativaria o overlay e
> esconderia a pasta `ports_scripts` da p1. A versão abaixo substitui a anterior;
> as tarefas da seção 5 de `tasks.md` aplicam a troca.

```text
+-------------------------------------------------------------------------+
| Camada SYSTEM (p5 - sempre gravada, inclusive com --keep-roms)          |
|                                                                         |
| /usr/share/classicube/                                                  |
|   |-- ClassiCube            (único binário, executado direto daqui)     |
|   |-- options.txt                                                       |
|   |-- texpacks/default.zip                                              |
|   |-- audio/default.zip                                                 |
|   +-- ports_scripts/        (cópia mestre do que vai para a p1)         |
|         |-- ClassiCube.sh                                               |
|         |-- gamelist.xml    (só a entrada do ClassiCube)                |
|         |-- img/ClassiCube.png                                          |
|         +-- images/ClassiCube-{image,thumb,marquee}.png                 |
|                                                                         |
| /usr/lib/r36/classicube-sync + r36-classicube-sync.service              |
|   (After=emuelec-autostart.service, Before=emustation.service)          |
|   - só age se /storage/roms estiver montado                             |
|   - copia ClassiCube.sh e capas para /storage/roms/ports_scripts        |
|     quando faltam ou diferem (cmp -s)                                   |
|   - gamelist.xml: cria se não existe; se existe sem                     |
|     <path>./ClassiCube.sh</path>, insere o bloco <game> antes de        |
|     </gameList> (awk), sem tocar nas outras entradas                    |
|   - garante options.txt e texpacks/audio em /storage/roms/ports/        |
|     classicube só quando faltam (não copia o binário)                   |
|                                                                         |
| NÃO cria /usr/bin/ports: o overlay do mount_romfs.sh continua falhando  |
| como na base e ports_scripts segue sendo a pasta FAT32 da p1.           |
+-------------------------------------------------------------------------+
| Camada ROMS (p1 - só em gravação completa)                              |
|   ports_scripts/{ClassiCube.sh,gamelist.xml,img/,images/}               |
|   ports/classicube/{options.txt,texpacks/,audio/}  (sem o binário)      |
+-------------------------------------------------------------------------+
```

- **Por que não usar `/usr/bin/ports/`?**
  O `es_systems.cfg` aponta o sistema `ports` para `/storage/roms/ports_scripts`. Na base, sem `/usr/bin/ports`, o overlay do `finish_scan()` falha e essa pasta é a da p1. É o único lugar onde o usuário consegue pôr ports pelo PC (o aparelho não tem rede). Com `/usr/bin/ports` presente, o overlay monta com `lowerdir=/usr/bin/ports` e `upperdir=/storage/.config/emuelec/ports` (p8, ext4 de root) e a pasta da p1 some do ES.
  Sem o overlay, o `classicube-sync` escreve direto na p1 depois do `mount_romfs.sh` (que roda dentro do `emuelec-autostart.service`), antes de o ES subir. Assim a capa aparece mesmo num cartão gravado com `--keep-roms`.

- **Por que mesclar em vez de substituir o `gamelist.xml`?**
  O `gamelist.xml` de `ports_scripts` é compartilhado por todos os ports e é reescrito pelo ES (contagem de partidas, favoritos, ports do usuário). Substituí-lo inteiro quando falta a entrada do ClassiCube apagaria as outras. O sync só insere o bloco `<game>` que falta, e a busca por `<path>./ClassiCube.sh</path>` evita duplicar a entrada em boots seguintes.

- **Por que `/usr/share/classicube/` + execução direta do binário no `SYSTEM`?**
  O binário `ClassiCube` (~800 KiB), `options.txt`, `texpacks/default.zip` (~84 KiB) e `audio/default.zip` (~470 KiB) somam cerca de 1,4 MiB no SquashFS `SYSTEM`.
  - `ClassiCube.sh` executa diretamente `/usr/share/classicube/ClassiCube --singleplayer` (filesystem POSIX com `0755`, sem cópia para `/tmp`), com diretório de trabalho `/storage/roms/ports/classicube` para mapas (`maps/`) e opções do jogador.
  - Antes de iniciar o jogo, `ClassiCube.sh` garante que `/storage/roms/ports/classicube/{options.txt,texpacks/default.zip,audio/}` existam, copiando de `/usr/share/classicube/` (e extraindo `audio/default.zip` se necessário).
  - Com o binário só no `SYSTEM`, a cópia na p1 e a regravação de ~800 KiB na FAT32 a cada boot deixam de existir.

## Risks / Trade-offs

- **[Risco] Cartões que já deram boot com a primeira versão desta change:** têm `ClassiCube.sh`, capas e `gamelist.xml` em `/storage/.config/emuelec/ports` (upperdir do overlay) e em `/storage/.config/emulationstation/gamelists/ports/`.
  - *Mitigação:* sem `/usr/bin/ports` o overlay deixa de montar e o upperdir não é mais lido. A cópia em `gamelists/ports/` tem só a entrada do ClassiCube, com caminho relativo à pasta de ROMs, e continua coerente; o sync novo não escreve mais nesses dois lugares.
- **[Risco] O usuário apaga `ClassiCube.sh` da p1 de propósito:** o sync o recria no boot seguinte.
  - *Mitigação:* para tirar o jogo, desligar a feature (`enabled = false`) e gravar o `system` de novo.
- **[Risco] O usuário já tem um `options.txt` antigo no cartão sem `auto-pause = false`:**
  - *Mitigação:* Além de `Window_Main.Focused = true` no próprio binário C, o `ClassiCube.sh` garante que `auto-pause = false` esteja presente no `options.txt` em `/storage/roms/ports/classicube/options.txt`.
