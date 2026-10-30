#!/bin/bash
# Captura quadros de GB/GBC SEM shader, na resolução nativa (160x144), com o RetroArch
# AppImage do PC, para alimentar replica.py.
# uso: capturar-sem-shader.sh <gb|gbc> <rom.zip> <nome> <quadro> [<quadro>...]
# Saída: ~/.cache/shader-gb-gbc-test/<nome>/<nome>-f<quadro>.png (160x144) e o log.
#
# O core é o que estiver em ~/.config/retroarch/cores: o Gambatte (padrão do gb e do gbc no
# aparelho) se existir, senão o mGBA, que também emula GB/GBC. Nos dois, as opções de cor
# ficam no que o aparelho entrega com a feature 55: GB em 4 cinzas puros (sem colorização) e
# GBC em RGB555 cru (sem a correção de cor). A config é própria (--config), sem tocar na do
# usuário, e video_gpu_screenshot = "false" grava o quadro do core sem escala nem filtro.
set -u
SIS="$1"; ROM="$2"; OUT="$3"; shift 3
APP=~/AppImages/retroarch.appimage
CORES=~/.config/retroarch/cores
W=~/.cache/shader-gb-gbc-test/$OUT
rm -rf "$W"; mkdir -p "$W/shots" "$W/cfg" "$W/sys"
if [ -f "$CORES/gambatte_libretro.so" ]; then
  CORE="$CORES/gambatte_libretro.so"
  cat > "$W/opts.cfg" <<EOC
gambatte_gb_colorization = "disabled"
gambatte_gbc_color_correction = "disabled"
gambatte_gb_internal_palette = "GB - Grayscale"
EOC
else
  CORE="$CORES/mgba_libretro.so"
  [ "$SIS" = gb ] && MODELO="Game Boy" || MODELO="Game Boy Color"
  cat > "$W/opts.cfg" <<EOC
mgba_gb_model = "$MODELO"
mgba_sgb_borders = "OFF"
mgba_gb_colors = "Grayscale"
mgba_gb_colors_preset = "0"
mgba_color_correction = "OFF"
mgba_skip_bios = "ON"
EOC
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
