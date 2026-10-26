#!/bin/bash
# Captura um quadro do mGBA (RetroArch Flatpak) sem shader, a 2x, para alimentar replica.py.
# uso: capturar-sem-shader.sh <rom.zip> <frame> <nome> sem   (o modo "com" aplica o shader pelo
# caminho de auto-shader, mas a captura sai distorcida; veja LEIA-ME.md)
set -u
ROM="$1"; FR="$2"; OUT="$3"; MODE="$4"
W=~/.cache/shader-gba-test/$OUT
rm -rf "$W"; mkdir -p "$W/cfg/mGBA" "$W/shots"
SH="$(cd "$(dirname "$0")/../../../.." && pwd)/features/54-shaders-gba/system/usr/share/common-shaders/gba"
if [ "$MODE" = com ]; then
  cp "$SH/gba-modern-remaster.glsl" "$SH/gba-modern-remaster.glslp" "$W/cfg/mGBA/"
  cp "$W/cfg/mGBA/gba-modern-remaster.glslp" "$W/cfg/mGBA/mGBA.glslp"
fi
cat > "$W/app.cfg" <<EOC
rgui_config_directory = "$W/cfg"
auto_shaders_enable = "true"
video_shader_enable = "true"
video_gpu_screenshot = "true"
screenshot_directory = "$W/shots"
video_fullscreen = "false"
video_windowed_fullscreen = "false"
video_scale = "2.0"
video_scale_integer = "true"
video_window_save_positions = "false"
audio_enable = "false"
EOC
timeout 180 flatpak run org.libretro.RetroArch -L ~/.var/app/org.libretro.RetroArch/config/retroarch/cores/mgba_libretro.so --appendconfig "$W/app.cfg" --max-frames="$FR" --max-frames-ss "$ROM" > "$W/log.txt" 2>&1
echo "exit $?"; ls -la "$W/shots"; tail -5 "$W/log.txt"
