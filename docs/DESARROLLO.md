Disponible en: [English](DEVELOPMENT.md) | [Português](DESENVOLVIMENTO.md) | Español

# Fábrica de imágenes del clon R36S (GA36-MB V1.2)

Este repositorio genera imágenes de tarjeta SD para un **clon del R36S** con placa
**GA36-MB V1.2**. Cada cambio solicitado se convierte en una *feature* versionada, y cada build
genera una imagen nueva, identificada por el momento exacto en que fue generada.

## Para quién es

El dispositivo está pensado para que **juegue un niño de 6 años** (el hijo del mantenedor
de este repositorio). Esto orienta las decisiones de cada feature: todo en pantalla en su
idioma nativo (español o portugués en el sistema, en EmulationStation y en el menú de RetroArch
con `./build.sh --lang es_ES`), facilitando enormemente la lectura de quien está aprendiendo;
menos avisos y animaciones entre encender y jugar; imagen y sonido agradables (shaders para GBA,
Game Boy y Game Boy Color, sin ghosting en la pantalla LCD, audio limpio y sin zumbidos); y menús sencillos. Al
proponer una modificación, pregúntate siempre: ¿ayuda a un niño pequeño a encontrar y abrir un juego por sí solo?

## El dispositivo y por qué sólo esta base funciona

- El SoC es un **Allwinner A33**, remarcado comercialmente como RK3326. Las imágenes genéricas
  de R36S (ArkOS, AmberELEC, ROCKNIX...) están compiladas para Rockchip y **no arrancan**.
- Sólo funciona con la imagen **EmuELEC 4.7 "Nexus" de fábrica** (kernel sunxi 3.4.39, `script.bin`).
  El código fuente de este fork no es público, por lo que el sistema no puede recompilarse por completo.
- Por ello, el build **parte siempre de la imagen de fábrica** (`base/`), que jamás se
  modifica directamente, sustituyendo de forma segura sólo las particiones objetivo: archivos de SYSTEM (squashfs),
  STORAGE (ext4), ROMs (FAT32) y la partición de arranque (FAT16).
- **Sin red, SSH ni Wi-Fi: todo mediante la tarjeta SD.** El dispositivo carece de conectividad.
  Para transferir archivos (cores, logs, perfiles), retira la tarjeta y léela o grábala en tu PC:
  `R36-ROMS` (FAT32) se abre sin root; `R36-STORAGE` (ext4) contiene archivos del sistema del usuario root.

Estructura de la tarjeta SD (sectores de 512 bytes):

| Partición | Inicio  | Contenido                                        | Etiqueta en PC |
|-----------|---------|--------------------------------------------------|----------------|
| bootarea  | 0       | MBR, EBRs, boot0, U-Boot, tabla softw411         | —              |
| p2        | 73728   | FAT16 leída por U-Boot (sólo 16 MiB asignados)   | `R36-BOOT`     |
| p5        | 139264  | variables de entorno de U-Boot                   | —              |
| p6        | 172032  | kernel + initramfs                               | —              |
| p7        | 237568  | FAT16 con `SYSTEM` (squashfs) y `R36-BUILD.txt`  | `R36-SYSTEM`   |
| p8        | 1810432 | ext4 `/storage`: partidas guardadas, ajustes     | `R36-STORAGE`  |
| p1        | 4956160 | FAT32 `/storage/roms`, hasta el final de tarjeta | `R36-ROMS`     |

## Requisitos previos

Linux (probado en Fedora) con Python 3.11 o más reciente:

```bash
sudo dnf install squashfs-tools mtools dosfstools e2fsprogs util-linux xz coreutils
```

`squashfs-tools` debe ser versión 4.6 o posterior con soporte para LZO. El build comprueba
estas herramientas e indica si falta alguna.

La imagen de fábrica proviene de esta publicación en r/R36S:
<https://www.reddit.com/r/R36S/comments/1w2i8em/r36s_ga36mb_v1220260416_emuelec_no_roms/>

Colócala dentro de `base/`, con el nombre exacto:

```
base/R36S GA36-MB V1.2-20260416 - Emuelec - No ROMS.img
```

La suma sha256 esperada está configurada en `config/base.toml`. Si no coincide, el build la rechazará.
El directorio `base/` y todas las imágenes generadas se mantienen fuera de git.

## Generar una imagen

**Idioma: el valor por defecto es inglés.** Un `./build.sh` sin argumentos genera la imagen en
inglés (`en_US`) en EmuELEC, EmulationStation y RetroArch. Para español, pasa `--lang es_ES`. Para
portugués de Brasil, pasa `--lang pt_BR`. Así la imagen se genera directamente en el idioma del usuario,
sin necesidad de editar archivos.

```bash
./build.sh                    # tarjeta de 16 GB (15000 MiB), features activadas, en inglés
./build.sh --lang es_ES       # lo mismo, en español
./build.sh --lang pt_BR       # lo mismo, en portugués de Brasil
./build.sh --no-features      # imagen equivalente a fábrica (referencia de prueba)
./build.sh --offline          # utiliza sólo el caché local de descargas (sin red)
./build.sh --test             # marca el build como imagen de prueba (sufijo -test)
./build.sh --help             # muestra todas las opciones
```

El build se ejecuta como usuario estándar (sin sudo) y tarda aproximadamente 2 minutos. La salida
se deposita en `out/<AAAAMMDD-HHMMSS>/`:

- `r36s_ga36-mb_v1.2-20260416_<idioma>_build_<timestamp>.img.xz`: imagen completa comprimida para grabar con Etcher o dd. `<idioma>` es el código en minúsculas con guión (`en-us`, `es-es`, `pt-br`);
- `parts/*.img`: imágenes de cada partición individual utilizadas por `./flash.sh`;
- `manifest.json`: timestamp, idioma (`"language"`), tamaño de tarjeta, offsets, hashes sha256 y features;
- `changes.txt`: informe detallado de archivos agregados, modificados o eliminados.

Con `--test`, el build se marca como imagen de prueba: el directorio pasa a ser `out/<timestamp>-test/` y la imagen `..._<idioma>_build_<timestamp>-test.img.xz`. El contenido de las particiones no cambia. `manifest.json` añade `"test": true` y `R36-BUILD.txt` incluye la línea `teste: sim`.

### Idioma

`--lang <código>` (o `--idioma <código>`, mantenido como alias compatible) define el idioma inicial de fábrica. Códigos aceptados: `es_ES`, `pt_BR`, `pt_PT`, `en_US` (por defecto), `en_GB`, `fr_FR`, `de_DE` e `it_IT`. El build ajusta tres claves en copias en `work/`: `system.language` en `emuelec.conf`, `Language` en `es_settings.cfg` y `user_language` en `retroarch.cfg`. Los archivos de origen en `features/10-ptbr-sao-paulo` permanecen intactos.

- Código no reconocido: el build se detiene antes de crear archivos y lista los códigos válidos.
- `--no-features --lang ...`: error (los archivos de configuración proceden de las features).
- El idioma se aplica en particiones limpias (`--wipe-storage`). Al flashear con `--keep-storage`, EmuELEC y EmulationStation conservan los ajustes existentes, y RetroArch se sincroniza automáticamente al abrir el primer juego (`idioma-aplica` en feature `56-retroarch-ajustes`).

| Idioma deseado            | Comando                       | Nombre de la imagen     |
|---------------------------|-------------------------------|-------------------------|
| inglés (por defecto)      | `./build.sh`                  | `..._en-us_build_...`   |
| español                   | `./build.sh --lang es_ES`     | `..._es-es_build_...`   |
| portugués de Brasil       | `./build.sh --lang pt_BR`     | `..._pt-br_build_...`   |

### Tamaño de la tarjeta

La partición de ROMs se extiende hasta el final de la tarjeta, por lo que la imagen debe ajustarse a la capacidad física real. Mide tu tarjeta con el lector conectado:

```bash
lsblk -b -d -o NAME,SIZE,RM,MODEL
```

Divide el valor `SIZE` entre 1048576 para obtener MiB y utiliza un valor **igual o ligeramente inferior**:

| Tamaño comercial    | Tamaño real típico  | Comando                         |
|---------------------|---------------------|---------------------------------|
| 8 GB                | 7300 a 7800 MiB     | `./build.sh --size-mib 7400`    |
| 16 GB (tarjeta base)| 15000 MiB           | `./build.sh`                    |
| 32 GB               | ~29800 MiB          | `./build.sh --size-mib 29800`   |

El mínimo admisible es 7000 MiB, alineado hacia abajo a múltiplos de 4 MiB.

## Grabar la tarjeta

Ejecuta `./flash.sh` **en una terminal normal** (solicita contraseña de sudo para escribir en el dispositivo). Empieza siempre con `--dry-run` para comprobar el plan sin modificar nada:

```bash
./flash.sh --device /dev/sdc --all --wipe-roms --wipe-storage --dry-run
```

### Elegir el build

Para consultar los builds generados en `out/` con sus características (no requiere sudo):

```bash
./flash.sh --list-builds
```

Si ejecutas sin `--build` en una terminal con varios builds disponibles, se muestra un menú interactivo. La opción 1 es el build más reciente (Enter para aceptar). Para especificar un build concreto: `--build 20261013-153045`.

### Grabación completa

Escribe bootarea, p2 (16 MiB), p5, p6, p7, p8 y p1 (escribiendo únicamente los sectores con datos):

```bash
./flash.sh --device /dev/sdc --all --wipe-roms --wipe-storage     # tarjeta nueva: borra todo
./flash.sh --device /dev/sdc --all --keep-roms --keep-storage     # actualiza sistema, conserva juegos y saves
./flash.sh --device /dev/sdc --all --keep-roms --wipe-storage     # conserva juegos, reinicia ajustes
```

- Requiere obligatoriamente `--keep-storage` o `--wipe-storage` para proteger partidas guardadas.
- Si la partición p1 contiene ROMs adicionales a las de fábrica, el script exige `--keep-roms` o `--wipe-roms`.

### Grabación parcial

Escribe exclusivamente las particiones seleccionadas en una tarjeta previamente particionada por este proyecto:

```bash
./flash.sh --device /dev/sdc --part system                  # sólo SYSTEM (p7)
./flash.sh --device /dev/sdc --part boot                    # sólo partición boot p2 (16 MiB)
./flash.sh --device /dev/sdc --part storage --wipe-storage  # p8: reinicia configuraciones
./flash.sh --device /dev/sdc --part roms --wipe-roms        # p1: reinicia juegos
```

### Protecciones y diagnóstico de salud de `flash.sh`

- Acepta únicamente **unidades completas extraíbles** (`RM=1`) o lectores integrados (`mmcblk`), bloqueando discos del sistema y particiones individuales.
- **Diagnóstico físico previo**:
  - Examina mensajes de kernel (`dmesg`) para detectar caídas de bus o fallos I/O (`buffer I/O error`).
  - Realiza una prueba atómica de bloqueo de solo lectura por hardware (*read-only lock test*) en el último sector antes de escribir.
  - Verifica la integridad FAT32 no destructiva (`fsck.fat -n`) al usar `--keep-roms`.
- **Reconstrucción analítica y canónica del MBR**:
  - Con `--keep-roms`, reconstruye matemáticamente la partición `p1` con el sector canónico `4956160`, tipo `0x0C` (FAT32 LBA) y alineación de 4 MiB.
- Solicita confirmación explícita escribiendo el nombre del dispositivo (ej.: `sdc`).
- Desmontaje automático, comprobación sha256 previa y verificación de lectura posterior.
- **Sincronización estricta y expulsión segura de hardware**:
  - Aplica `sync`, `blockdev --flushbufs` y `udevadm settle`.
  - Apaga la alimentación del lector de forma automática con `udisksctl power-off -b /dev/sdX` al terminar con éxito para permitir la extracción física inmediata de la tarjeta microSD (usa `--no-eject` si deseas inspeccionarla en el PC).

Para realizar pruebas sin tarjeta física, puedes grabar en un archivo de imagen disperso:

```bash
mkdir -p work
truncate -s 15000M work/cartao-teste.img
./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage
```

## Features habilitadas

- **`10-ptbr-sao-paulo`**: localización del sistema, EmulationStation y RetroArch RGUI; zona horaria `America/Sao_Paulo`. Catálogos de traducción completos para EmulationStation en `pt_BR` y `es_MX` (`.po` y `.mo`), preservando términos técnicos de videojuegos (*Save State*, *Core*, *Shader*, *Bezel*, *BIOS*, *ROMs*, *RetroAchievements*) y adaptando los diálogos a la pantalla de 3.5" (640x480). Ajusta valores por defecto idóneos:
  - Proporción de aspecto nativa del core (`global.ratio=core`);
  - Disposición estándar de confirmación/cancelación (`menu_swap_ok_cancel_buttons = "false"`);
  - gpSP como emulador predeterminado de GBA (`gba.core=gpsp`);
  - snes9x2005_plus_a33 reoptimizado como core de SNES (`53-cores-a33`);
  - fceumm como core de NES (`nes.core=fceumm`);
  - fbalpha2012 como core de CPS2 (`cps2.core=fbalpha2012`);
  - Rendimiento máximo desactivado por defecto (`global.maxperf=0`) para preservar temperaturas térmicas estables;
  - Desactivación de servicios innecesarios (red, Bluetooth, actualizaciones online, rewind);
  - Capturas de pantalla asociadas a save states en `savestates/<sistema>/` en `R36-ROMS` para visualización en EmulationStation;
  - Controladores ausentes fijados en `"null"` (`wifi_driver`, `bluetooth_driver`, `microphone_driver`, `midi_driver`).

- **`20-controle-posicional`**: asignación posicional física de botones en RetroArch (abajo = B, derecha = A, arriba = X, izquierda = Y) y botón FN como tecla de acceso rápido (hotkey):

| Atajo en juego    | Acción                 |
|-------------------|------------------------|
| FN + X            | Menú de RetroArch      |
| FN + Y            | Captura de pantalla    |
| FN + L / R        | Cargar / Guardar estado|
| FN + L2           | Cámara lenta           |
| FN + R2           | Avance rápido          |
| FN + Abajo        | Pausa                  |
| FN + Derecha      | Contador de FPS        |
| FN + Start        | Salir del juego        |

  - **Botón FN:** reasigna en el arranque `fn_key` de 464 a 316 (`BTN_MODE`) y configura `input_enable_hotkey_btn = "10"` en `micro_gamepad.cfg`. Select queda totalmente libre para su función en los juegos. Crea el archivo vacío `r36-fn-original` en la raíz de `R36-ROMS` para restablecer el valor original.

- **`30-telas-icone-controle`**: pantalla de carga neutra con icono de mando minimalista desde el encendido hasta el lanzamiento del juego, eliminando pantallas estridentes de fábrica ("Please Wait...").

- **`40-zram-swap`**: memoria de intercambio zram comprimida en RAM con prioridad máxima (32767), eliminando el archivo swapfile de disco de 300 MB.

- **`41-servicos-enxutos`**: deshabilita servicios innecesarios en el arranque: control remoto IR (`lircd`), `cron`, sincronización horaria por red (`systemd-timesyncd`) y `pulseaudio` (ALSA gestiona el audio de forma nativa).

- **`42-roms-noatime`**: remonta `/storage/roms` con la opción `noatime`, reduciendo escrituras innecesarias en la tarjeta SD al abrir juegos.

- **`43-registro-termico`**: registro pasivo de telemetría cada 5 segundos en `R36-ROMS/r36-thermal.csv` (temperaturas, frecuencias de CPU, voltaje y corriente de batería, brillo LCD, emulador activo). Genera `r36-sysinfo.txt` con el estado completo del hardware. Herramientas de análisis en `tools/analisa_bateria.py` y calibración en `tools/ajusta_curva_bateria.py`.

- **`44-cpu-ondemand`**: calibración del gobernador `ondemand` (`up_threshold` 30, `sampling_down_factor` 10, `scaling_min_freq` 600000) y escena de DRAM 0 durante juegos para evitar caídas de fotogramas sin forzar sobrecalentamiento.

- **`46-audio`**: silencio real a volumen 0 (`speaker volume control = 0`), restauración del volumen guardado en el arranque (`r36-audio.volume`), aumento de latencia de audio a 96 ms y calidad de remuestreo a 1 en RetroArch para eliminar chasquidos. Revertir mediante `r36-audio-original` en `R36-ROMS`.

- **`48-bateria-percentual`**: cálculo analítico del porcentaje de batería mediante curvas de tensión y corriente en lugar del defectuoso driver de fábrica, montado mediante bind sobre `/sys/class/power_supply/battery/capacity`. Revertir mediante `r36-bateria-original`.

- **`50-temas-extras`**: temas adicionales para EmulationStation:
  - Partición de sistema (p8 ext4): **Minimal EmuELEC**, **Graphite OGA**, **Epic Cody ML** (tema predeterminado 4:3 multilingüe con soporte en `_languages/` para español latino, portugués de Brasil e inglés);
  - Partición de ROMs (p1 FAT32): temas enriquecidos **Switch** y **Crystal** ubicados en `themes/`.

- **`52-psp-desempenho`**: perfil optimizado de PPSSPP para Allwinner A33 (resolución interna nativa 1x 480x272, 4 hilos de CPU, filtrado de texturas nearest, omisión de lecturas de GPU).

- **`53-cores-a33`**: emuladores recompilados con optimizaciones Cortex-A7 y LTO (`snes9x2005_plus_a33`).

- **`54-shaders-gba`**: shader de una pasada `gba-modern-remaster` con curva de color viva, escalado bilinear nítido y sutil rejilla LCD. Activo por defecto en GBA. Desactivar mediante `r36-gba-sem-shader` en `R36-ROMS`.

- **`55-shaders-gb-gbc`**: shaders optimizados para Game Boy (`gb-modern-dmg`, paleta verde oliva DMG) y Game Boy Color (`gbc-modern-remaster`), configurados por carpeta de contenido (`<Core>/gb.glslp`, `<Core>/gbc.glslp`). Desactivar con `r36-gb-sem-shader` o `r36-gbc-sem-shader`.

- **`56-retroarch-ajustes`**: aplicación de "SHADER SET" de EmulationStation mediante `shaderset-aplica` (`--set-shader`), sincronización de idioma con EmuELEC mediante `idioma-aplica`, corrección de rutas para guardar configuraciones (`rgui_config_directory`), y fusión de fotogramas en gpSP (`gpsp_frame_mixing = "enabled"`, desactivar con `r36-gpsp-sem-ghost`).

- **`58-ports-exec`**: gestión automática de permisos de ejecución para ports independientes en FAT32 mediante montajes bind desde p8. También cubre las carpetas `*-recomp` de juegos recompilados (por patrón de nombre, con el mismo caché y registro).

- **`60-port-classicube`**: port nativo de ClassiCube 1.3.9 (recreación de Minecraft Classic en C) con aceleración GLES2, zonas muertas calibradas para sticks analógicos y controles adaptados.

- **`62-brilho-fn`**: control de brillo de pantalla directo mediante `FN + D-pad Arriba/Abajo` (rango 10 a 100, pasos de 5), persistido entre reinicios en `r36-brilho.level`. Restablecer a 80 mediante `FN + clic L3` o creando `r36-brilho-original`.

- **`64-love2d`**: motor oficial standalone **LÖVE 11.5** para Allwinner A33 (ARMv7-A / NEON / GLES 2.0). Integra videojuegos indie desarrollados en Lua en EmulationStation (`roms/love/` para archivos `.love` y `.zip`). Renderizado directo en framebuffer GLES2 (`/dev/fb0`), mapeo de controles SDL2, demonio en segundo plano para salida con `FN + Start`, audio cristalino con OpenAL Soft (48000 Hz, int16, bsinc12), y variables de entorno de localización (`CONSOLE_LANG`, `CONSOLE_LANG_SHORT`, `LANG`, `LANGUAGE`). Incluye el juego de demostración *Mr. Rescue* con navegación de menús aislada en la cruceta digital D-pad (inmune a derivas de calibración analógica) y movimiento analógico durante la partida.

- **`66-recomp`**: consolas de juegos recompilados, es decir, una ROM convertida en un ejecutable nativo armhf, sin core ni RetroArch. Hoy solo existe `gba-recomp`; el recompilador en sí es un cambio futuro.
  - **Sistema en EmulationStation:** `gba-recomp` lee `/storage/roms/gba-recomp/` (partición `R36-ROMS`) y lista el `.sh` (o `.SH`) de la raíz de la carpeta (un juego es `Juego.sh` más una carpeta `Juego/` al lado con `launch.sh` y el `.elf`). Un sistema `*-recomp` sin juegos no aparece en el menú. La carpeta trae un `LEIAME.txt` en tres idiomas.
  - **Formato del juego:** el `.sh` ejecuta (con `bash` explícito) un ELF armhf (ARMv7-A, hard-float) que solo usa bibliotecas de la imagen (glibc hasta 2.36, libstdc++ hasta `GLIBCXX_3.4.29`; un C++ más nuevo necesita `-static-libstdc++`). Abre la ventana y el sonido con las bibliotecas del sistema (SDL2, GLES2, ALSA).
  - **Ejecución:** `r36-ports-exec` (feature `58-ports-exec`) guarda una copia `0755` en la p8 y la monta sobre el archivo de la p1. `/usr/bin/recomp.sh "%ROM%" "%SYSTEM%"`, el mismo para todas las consolas, comprueba la firma ELF y ejecuta el juego directamente, sin `emuelecRunEmu.sh` ni `--core`, mediante un symlink `/tmp/r36-recomp-game` (15 caracteres: el nombre de proceso que busca `gptokeyb`, aunque el ELF tenga un nombre largo o arbitrario).
  - **Salir del juego:** `FN + Start` termina el juego con `SIGTERM` mediante `gptokeyb` (perfil `/usr/config/gptokeyb/recomp.gptk`: solo `hotkey`, `start` y `back`, ninguna tecla de acción del teclado sobre los botones del juego). `Select` llega al juego y FN solo no hace nada. No hay `es_input.cfg` nuevo: FN sigue sin función en ES.
  - **Audio, idioma y registro:** como en LÖVE (ruta `Speaker Function`, `audio-ganho aplica` antes y después; `CONSOLE_LANG`, `CONSOLE_LANG_SHORT`, `LANG` y `LANGUAGE`). El registro queda en `R36-ROMS/<consola>-recomp/recomp.log` (rota a `recomp.log.1` al pasar de 100 KB) con el juego, el sistema, el `ldd` (una biblioteca faltante aparece como `not found`) y el código de salida; los registros extra solo salen con la clave `r36-diagnostico`.
  - **Tema:** `gba-recomp/` en el tema Epic Cody ML (`theme.xml`, `logo.png`, `poster.png`, `system.png` y el arte en `_art/posters` y `_art/controllers`), derivado del arte del GBA con un sello RECOMP por `tools/gera_arte_gba_recomp.py`, con las variables `gba-recomp.*` en los tres idiomas.
  - **Añadir una consola:** declara el sistema `<consola>-recomp` (las dos copias de `es_systems.cfg`, comando `/usr/bin/recomp.sh "%ROM%" "%SYSTEM%"`, extensión `.sh`), la carpeta en `roms/` y la carpeta del tema. Ni el lanzador ni `r36-ports-exec` cambian. El ELF de prueba (`tools/recomp_teste/`) sirve para validar en el aparato.

### Diagnóstico

Los registros de diagnóstico se encuentran inactivos por defecto para evitar escrituras en la tarjeta SD. Para habilitarlos, crea un archivo vacío llamado `r36-diagnostico` en la raíz de `R36-ROMS`:

```sh
touch /run/media/douglas/R36-ROMS/r36-diagnostico
```

Con la clave presente, se graban `r36-audio.log`, `r36-bateria.log`, `r36-shader-gba.log`, `r36-shader-gb-gbc.log`, `r36-idioma.log` y `r36-brilho.log`. El registro térmico (`r36-thermal.csv`, `r36-sysinfo.txt`) funciona de manera independiente sin requerir la clave.

## Crear una feature

Una feature es un directorio dentro de `features/`. Consulta el ejemplo documentado en `features/00-exemplo/`.

1. Copia la plantilla:

   ```bash
   cp -r features/00-exemplo features/10-mi-feature
   ```

2. Edita `features/10-mi-feature/feature.toml`: define `name`, `description`, `order` y pon `enabled = true`.
3. Distribuye tus archivos en las capas correspondientes:
   - `system/`: se integra en la raíz `/` del sistema (squashfs de solo lectura);
   - `storage/`: se integra en `/storage` (configuraciones, ej. `storage/.config/emuelec/configs/emuelec.conf`);
   - `roms/`: se integra en `/storage/roms`;
   - `boot/`: partición de arranque p2 (`bootlogo.bmp`, etc.; límite de 16 MiB).
4. Para eliminar archivos de fábrica, utiliza la directiva `[[remove]]`.
5. Para recursos de gran tamaño, utiliza `[[external]]` indicando URL y suma sha256.
6. Genera y verifica:

   ```bash
   ./build.sh --features 10-mi-feature       # genera sólo esta feature
   ./build.sh                                # genera con todas las features activadas
   cat out/<timestamp>/changes.txt
   ```

Reglas importantes:
- Archivos en `system/` y `storage/` pertenecen a `0:0`, permisos `0755` para ejecutables, `0644` para el resto.
- Dos features no pueden modificar la misma ruta a menos que la posterior declare `[[override]]`.
- Cada nueva feature dispone de su propio change OpenSpec y rama git dedicada.

## Dónde ver qué build está en la tarjeta

El archivo `R36-BUILD.txt` detalla el nombre de imagen, tamaño, idioma (`idioma: en_US`) y features:
- En PC: partición **R36-SYSTEM**;
- En la consola: accesible en `/flash/R36-BUILD.txt`.

Las imágenes de prueba indican `teste: sim`.

## Rollback

- Graba un build anterior: `./flash.sh --device /dev/sdc --all --keep-roms --keep-storage --build <timestamp>`.
- O restaura la imagen original de fábrica, preservada intacta en `base/`:

  ```bash
  sudo dd if="base/R36S GA36-MB V1.2-20260416 - Emuelec - No ROMS.img" of=/dev/sdc bs=4M conv=fsync status=progress
  ```

## Qué no hacer jamás

- **No permitas que Windows "repare" ni formatee la tarjeta.** Puede corromper las tablas de partición MBR.
- **No escribas más de 16 MiB en la partición p2.** Aunque el MBR indique 128 MiB, los sectores superiores se solapan con el kernel y SYSTEM.
- **No crees `.please_resize_me`** en ninguna partición: provocará un formateo destructivo de p1 y p8 al arrancar.
- **No instales imágenes genéricas de R36S** (ArkOS, AmberELEC, etc.): están compiladas para Rockchip y no arrancan en este clon Allwinner A33.
- No modifiques jamás la imagen almacenada en `base/`.

## Para desarrolladores

```bash
uv run python -I -m unittest discover -s tests              # pruebas rápidas (~30 s)
R36_SLOW=1 uv run python -I -m unittest discover -s tests   # generación completa de imágenes (~5 min)
```

El entorno Python se gestiona con [uv](https://docs.astral.sh/uv/) (`uv sync`). El código fuente reside en `tools/r36img/`.

### Compilar un core

`./cores.sh` compila emuladores libretro para el SoC Allwinner A33 mediante contenedores sin root:

```bash
./cores.sh compilar snes9x2005_plus o3                              # compila, valida ABI y copia a la feature
./cores.sh verificar                                                # verifica ABI y hashes sha256
./cores.sh perfil snes9x2005_plus <R36-ROMS>/pgo/snes9x2005_plus   # importa datos de perfilado PGO
./cores.sh resumo <R36-ROMS>/r36-thermal.csv --roms <R36-ROMS>      # genera resumen de rendimiento
```
