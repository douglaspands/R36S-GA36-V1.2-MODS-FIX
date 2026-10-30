#!/bin/bash
# Captura quadros de consoles de mesa (Mega Drive, SNES) SEM shader, na resolução nativa,
# com o RetroArch AppImage do PC, para alimentar replica_tv.py.
# uso: capturar-sem-shader.sh <md|snes> <rom.zip> <nome> <quadro> [<quadro>...]
# Saída: ~/.cache/shader-tv-test/<nome>/<nome>-f<quadro>.png e o log.

set -u
SIS="$1"; ROM="$2"; OUT="$3"; shift 3
APP=~/AppImages/retroarch.appimage
CORES=~/.config/retroarch/cores
W=~/.cache/shader-tv-test/$OUT
rm -rf "$W"; mkdir -p "$W/shots" "$W/cfg" "$W/sys"

if [ "$SIS" = "md" ] || [ "$SIS" = "megadrive" ] || [ "$SIS" = "genesis" ]; then
  CORE="$CORES/genesis_plus_gx_libretro.so"
  cat > "$W/opts.cfg" <<EOC
genesis_plus_gx_render = "single field"
EOC
elif [ "$SIS" = "snes" ]; then
  CORE="$CORES/snes9x_libretro.so"
  cat > "$W/opts.cfg" <<EOC
snes9x_hires_blend = "disabled"
EOC
else
  echo "Sistema desconhecido: $SIS"
  exit 1
fi

cat > "$W/main.cfg" <<EOC
config_save_on_exit = "false"
core_options_path = "$W/opts.cfg"
global_core_options = "true"
rgui_config_directory = "$W/cfg"
system_directory = "$W/sys"
savefile_directory = "$W/sys"
savestate_directory = "$W/sys"
video_shader_enable = "false"
auto_shaders_enable = "false"
video_gpu_screenshot = "false"
screenshot_directory = "$W/shots"
screenshots_in_content_dir = "false"
auto_screenshot_filename = "false"
history_list_enable = "false"
content_runtime_log = "false"
video_fullscreen = "false"
video_scale = "2.0"
audio_enable = "false"
EOC

for FR in "$@"; do
  timeout 120 "$APP" --config "$W/main.cfg" -L "$CORE" --max-frames="$FR" --max-frames-ss "$ROM" > "$W/log-f$FR.txt" 2>&1
  echo "quadro $FR: saida $?"
  for png in "$W"/shots/*.png; do
    [ -f "$png" ] && mv "$png" "$W/$OUT-f$FR.png"
  done
done
echo "core: ${CORE##*/}"
ls -la "$W"
