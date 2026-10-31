#!/usr/bin/env bash
# Lançador standalone do LÖVE 11.5 para o R36S clone (Allwinner A33 / Mali-400 MP2)
# Mapeado no EmulationStation via /usr/bin/love.sh "%ROM%"
set -euo pipefail

R36_PREFIX="${R36_ROOT:-}"
ROM="${1:-}"

if [ -z "$ROM" ]; then
    echo "Uso: $0 <caminho_do_jogo.love>" >&2
    exit 1
fi

if ! command -v blank_buffer >/dev/null 2>&1 && [ -f /etc/profile ]; then
    set +eu
    . /etc/profile 2>/dev/null || true
    set -eu
fi

BIN="${R36_PREFIX}/usr/bin/love"
DB_FILE="${R36_PREFIX}/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt"
GPTK_CONF="${R36_PREFIX}/usr/config/gptokeyb/love.gptk"
[ ! -f "$GPTK_CONF" ] && GPTK_CONF="${R36_PREFIX}/usr/bin/love.gptk"

# Splash neutro do sistema na inicialização
SPLASH_IMG="${R36_PREFIX}/usr/config/splash/loading-game.png"
[ ! -f "$SPLASH_IMG" ] && SPLASH_IMG="${R36_PREFIX}/storage/.config/splash/loading-game.png"
[ ! -f "$SPLASH_IMG" ] && SPLASH_IMG="/usr/config/splash/loading-game.png"
[ ! -f "$SPLASH_IMG" ] && SPLASH_IMG="/storage/.config/splash/loading-game.png"

SPLASH_PID=""
if [ -f "$SPLASH_IMG" ] && command -v mpv >/dev/null 2>&1; then
    mpv "$SPLASH_IMG" >/dev/null 2>&1 &
    SPLASH_PID=$!
fi

if command -v blank_buffer >/dev/null 2>&1; then
    blank_buffer 2>/dev/null || true
fi

cleanup() {
    # Finaliza mpv do splash inicial se ainda estiver ativo
    [ -n "${SPLASH_PID:-}" ] && kill -9 "$SPLASH_PID" 2>/dev/null || true

    # Finaliza daemon do gptokeyb se ainda estiver ativo
    killall -9 gptokeyb 2>/dev/null || true

    # Restaura rota analógica e ganho do codec de áudio (sunxi-pcm-codec)
    local h2w_state
    h2w_state="$(cat "${R36_PREFIX}/sys/class/switch/h2w/state" 2>/dev/null || cat /sys/class/switch/h2w/state 2>/dev/null || echo 0)"
    case "$h2w_state" in
        "1"|"2")
            amixer cset name='Speaker Function' spk >/dev/null 2>&1 || true
            ;;
        *)
            amixer cset name='Speaker Function' headset >/dev/null 2>&1 || true
            ;;
    esac
    if [ -x "${R36_PREFIX}/usr/lib/r36/audio-ganho" ]; then
        "${R36_PREFIX}/usr/lib/r36/audio-ganho" aplica 2>/dev/null || true
    fi

    # Exibe splash neutro de encerramento antes de retornar ao EmulationStation
    if [ -f "$SPLASH_IMG" ] && command -v mpv >/dev/null 2>&1; then
        mpv "$SPLASH_IMG" >/dev/null 2>&1 || true
    fi

    if command -v blank_buffer >/dev/null 2>&1; then
        blank_buffer 2>/dev/null || true
    fi

    clear > /dev/tty0 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Rota analógica e ganho de áudio na entrada
export SDL_AUDIODRIVER=alsa
h2w_state="$(cat "${R36_PREFIX}/sys/class/switch/h2w/state" 2>/dev/null || cat /sys/class/switch/h2w/state 2>/dev/null || echo 0)"
case "$h2w_state" in
    "1"|"2")
        amixer cset name='Speaker Function' spk >/dev/null 2>&1 || true
        ;;
    *)
        amixer cset name='Speaker Function' headset >/dev/null 2>&1 || true
        ;;
esac
if [ -x "${R36_PREFIX}/usr/lib/r36/audio-ganho" ]; then
    "${R36_PREFIX}/usr/lib/r36/audio-ganho" aplica 2>/dev/null || true
fi

# Configuração otimizada do OpenAL Soft para o hardware de áudio do R36S (Allwinner A33)
ALSOFT_CONF_FILE="${R36_PREFIX}/etc/openal/alsoft.conf"
[ ! -f "$ALSOFT_CONF_FILE" ] && ALSOFT_CONF_FILE="${R36_PREFIX}/usr/config/openal/alsoft.conf"
[ ! -f "$ALSOFT_CONF_FILE" ] && ALSOFT_CONF_FILE="/etc/openal/alsoft.conf"
[ ! -f "$ALSOFT_CONF_FILE" ] && ALSOFT_CONF_FILE="/usr/config/openal/alsoft.conf"
if [ -f "$ALSOFT_CONF_FILE" ]; then
    export ALSOFT_CONF="$ALSOFT_CONF_FILE"
fi

# Diagnóstico OpenAL condicionado à chave r36-diagnostico na partição de ROMs
DIAG_CHAVE="${R36_PREFIX}/storage/roms/r36-diagnostico"
[ ! -f "$DIAG_CHAVE" ] && DIAG_CHAVE="/storage/roms/r36-diagnostico"
if [ -f "$DIAG_CHAVE" ]; then
    export ALSOFT_LOGLEVEL=3
    export ALSOFT_LOGFILE="${R36_PREFIX}/storage/roms/love/r36-love-alsoft.log"
    mkdir -p "$(dirname "$ALSOFT_LOGFILE")" 2>/dev/null || true
fi

# Detecção do idioma configurado no sistema (emuelec.conf -> es_settings.cfg -> fallback en_US)
EMUCONF="${R36_PREFIX}/storage/.config/emuelec/configs/emuelec.conf"
ESCFG="${R36_PREFIX}/storage/.config/emulationstation/es_settings.cfg"
[ ! -f "$ESCFG" ] && ESCFG="${R36_PREFIX}/storage/.emulationstation/es_settings.cfg"

limpa() {
    local v="$1"
    while :; do
        case "$v" in
            [[:space:]]*) v="${v#?}" ;;
            *) break ;;
        esac
    done
    LIMPO="${v%%[!A-Za-z_]*}"
}

DOCONF=""
DOES=""
if [ -f "$EMUCONF" ]; then
    while IFS= read -r linha || [ -n "$linha" ]; do
        case "$linha" in
            system.language=*) DOCONF="${linha#system.language=}"; break ;;
        esac
    done < "$EMUCONF"
fi
if [ -f "$ESCFG" ]; then
    while IFS= read -r linha || [ -n "$linha" ]; do
        case "$linha" in
            *'name="Language" value="'*)
                DOES="${linha#*name=\"Language\" value=\"}"
                DOES="${DOES%%\"*}"
                break ;;
        esac
    done < "$ESCFG"
fi
limpa "$DOCONF"; DOCONF="$LIMPO"
limpa "$DOES"; DOES="$LIMPO"

CONSOLE_LANG="${DOCONF:-$DOES}"
CONSOLE_LANG="${CONSOLE_LANG:-en_US}"
LANG_PRE="${CONSOLE_LANG:0:2}"
CONSOLE_LANG_SHORT="${LANG_PRE,,}"

export CONSOLE_LANG
export CONSOLE_LANG_SHORT
export LANG="${CONSOLE_LANG}.UTF-8"
export LANGUAGE="${CONSOLE_LANG}"

# Grava arquivo temporário com o idioma do console
echo "$CONSOLE_LANG" > /tmp/console_lang 2>/dev/null || true
if [ -n "$R36_PREFIX" ] && [ -d "${R36_PREFIX}/tmp" ]; then
    echo "$CONSOLE_LANG" > "${R36_PREFIX}/tmp/console_lang" 2>/dev/null || true
fi

export LD_LIBRARY_PATH="${R36_PREFIX}/usr/lib:${R36_PREFIX}/storage/roms/love/libs:${LD_LIBRARY_PATH:-}"
export LOVE_GRAPHICS_USE_OPENGLES=1
export SDL_VIDEO_GL_DRIVER="${R36_PREFIX}/usr/lib/libGLESv2.so.2"
export SDL_VIDEO_EGL_DRIVER="${R36_PREFIX}/usr/lib/libEGL.so.1"
export SDL_NOMOUSE=1
export HOME="/storage"

# Carrega mapeamento do micro_gamepad para o SDL2, garantindo o botão 10 (FN / BTN_MODE) como guide
DEFAULT_SDL_MAPPING="190000006d6963726f5f67616d657000,micro_gamepad,dpleft:b15,rightx:a2,dpright:b16,rightshoulder:b5,dpdown:b14,righty:a3,leftshoulder:b4,y:b3,x:b2,b:b1,a:b0,dpup:b13,back:b8,leftstick:b11,start:b9,lefty:a1,guide:b10,lefttrigger:b6,righttrigger:b7,rightstick:b12,leftx:a0,platform:Linux,"

if [ -f "$DB_FILE" ]; then
    SDL_CFG=""
    while IFS= read -r linha || [ -n "$linha" ]; do
        case "$linha" in
            *micro_gamepad*|*retrogame_joypad*)
                SDL_CFG="${SDL_CFG}${linha}"$'\n'
                ;;
        esac
    done < "$DB_FILE"
    if [ -n "$SDL_CFG" ]; then
        # Garante que guide aponte para b10 (FN / BTN_MODE) em micro_gamepad
        SDL_CFG="${SDL_CFG//guide:b8/guide:b10}"
        case "$SDL_CFG" in
            *guide:b10*) ;;
            *) SDL_CFG="${SDL_CFG%,},guide:b10," ;;
        esac
        export SDL_GAMECONTROLLERCONFIG="$SDL_CFG"
    else
        export SDL_GAMECONTROLLERCONFIG="$DEFAULT_SDL_MAPPING"
    fi
else
    export SDL_GAMECONTROLLERCONFIG="$DEFAULT_SDL_MAPPING"
fi

ENABLE_LOG="${ENABLE_LOG:-1}"
LOG_DIR="${R36_PREFIX}/storage/roms/love"
LOG_FILE="${LOG_DIR}/love.log"
LOG_ROT="${LOG_DIR}/love.log.1"

# Inicia gptokeyb em segundo plano para capturar FN + Start (guide + start) e finalizar o jogo com SIGTERM
if command -v gptokeyb >/dev/null 2>&1; then
    killall -9 gptokeyb 2>/dev/null || true
    if [ -f "$GPTK_CONF" ]; then
        gptokeyb 1 love -c "$GPTK_CONF" -killsignal 15 &
    else
        gptokeyb 1 love -killsignal 15 &
    fi
fi

if [ "$ENABLE_LOG" = "1" ]; then
    mkdir -p "$LOG_DIR" 2>/dev/null || true
    if [ -f "$LOG_FILE" ]; then
        TAM="$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)"
        TAM="${TAM//[[:space:]]/}"
        TAM="${TAM:-0}"
        if [ "$TAM" -ge 102400 ]; then
            mv -f "$LOG_FILE" "$LOG_ROT" 2>/dev/null || true
        fi
    fi

    {
        echo "=== LÖVE Inicialização: $(date) ==="
        echo "ROM: $ROM"
        echo "Argumentos: $*"
        echo "CONSOLE_LANG=$CONSOLE_LANG"
        echo "CONSOLE_LANG_SHORT=$CONSOLE_LANG_SHORT"
        echo "LANG=$LANG"
        echo "LANGUAGE=$LANGUAGE"
        echo "LOVE_GRAPHICS_USE_OPENGLES=$LOVE_GRAPHICS_USE_OPENGLES"
        echo "SDL_VIDEO_GL_DRIVER=$SDL_VIDEO_GL_DRIVER"
        echo "SDL_VIDEO_EGL_DRIVER=$SDL_VIDEO_EGL_DRIVER"
        echo "SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-}"
        echo "SDL_GAMECONTROLLERCONFIG=${SDL_GAMECONTROLLERCONFIG:-}"
        echo "--- Verificação ldd $BIN ---"
        ldd "$BIN" 2>&1 || true
        echo "--- Execução ---"
    } >> "$LOG_FILE" 2>&1

    if [ ! -x "$BIN" ]; then
        echo "Erro: Executável $BIN não encontrado ou sem permissão de execução." | tee -a "$LOG_FILE" >&2
        exit 127
    fi

    "$BIN" "$ROM" 2>&1 | tee -a "$LOG_FILE"
else
    if [ ! -x "$BIN" ]; then
        echo "Erro: Executável $BIN não encontrado ou sem permissão de execução." >&2
        exit 127
    fi

    "$BIN" "$ROM"
fi
