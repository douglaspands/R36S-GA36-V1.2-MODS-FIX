#!/usr/bin/env bash
# Lançador dos jogos recompilados (ELF armhf nativo, sem core nem RetroArch).
# Chamado pelo EmulationStation: /usr/bin/recomp.sh "%ROM%" "%SYSTEM%"
# Mesmo molde do love.sh: rota e ganho de áudio, idioma, splash neutro, gptokeyb (FN + Start
# encerra o jogo com SIGTERM) e log rotativo em /storage/roms/<sistema>/recomp.log.
# O ELF roda por um symlink de nome fixo (15 caracteres): o gptokeyb mata um processo pelo
# nome (comm, até 15 caracteres) e o jogo recompilado pode ter qualquer nome.
set -u

R36_PREFIX="${R36_ROOT:-}"
ROM="${1:-}"
SISTEMA="${2:-}"

if [ -z "$ROM" ]; then
    echo "Uso: $0 <jogo.recomp> [sistema]" >&2
    exit 1
fi

# Sem o segundo argumento, o sistema é o nome da pasta do jogo (gba-recomp, snes-recomp...)
if [ -z "$SISTEMA" ]; then
    SISTEMA="$(basename "$(dirname "$ROM")")"
fi

# O ES chama o script sem o ambiente de login: carrega o PATH do sistema (blank_buffer, mpv...)
if [ -z "$R36_PREFIX" ] && ! command -v blank_buffer >/dev/null 2>&1 && [ -f /etc/profile ]; then
    set +u
    . /etc/profile 2>/dev/null || true
    set -u
fi

NOME_PROCESSO="r36-recomp-game"
LINK="${R36_PREFIX}/tmp/${NOME_PROCESSO}"
LOG_DIR="${R36_PREFIX}/storage/roms/${SISTEMA}"
LOG_FILE="${LOG_DIR}/recomp.log"
LOG_ROT="${LOG_DIR}/recomp.log.1"
GPTK_CONF="${R36_PREFIX}/usr/config/gptokeyb/recomp.gptk"
DIAG_CHAVE="${R36_PREFIX}/storage/roms/r36-diagnostico"

# p1 somente leitura ou cheia não pode impedir o jogo: sem como gravar o log, ele vai para /dev/null.
mkdir -p "$LOG_DIR" 2>/dev/null || true
LOG_OUT="$LOG_FILE"
if ! { : >> "$LOG_FILE"; } 2>/dev/null; then
    LOG_OUT=/dev/null
fi

log() {
    { printf '%s\n' "$*" >> "$LOG_OUT"; } 2>/dev/null || true
}

if [ -f "$LOG_FILE" ]; then
    TAM="$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)"
    TAM="${TAM//[[:space:]]/}"
    if [ "${TAM:-0}" -gt 102400 ]; then
        mv -f "$LOG_FILE" "$LOG_ROT" 2>/dev/null || true
    fi
fi

log "=== recomp: $(date) ==="
log "jogo: $ROM"
log "sistema: $SISTEMA"

# Só um ELF roda: qualquer outra coisa vira erro no log e devolve o ES antes de mudar a tela.
if [ "$(head -c 4 "$ROM" 2>/dev/null)" != "$(printf '\177ELF')" ]; then
    log "ERRO: $ROM não é um ELF (assinatura 7f 45 4c 46 ausente ou arquivo ilegível)"
    exit 1
fi

# Splash neutro do sistema na inicialização
SPLASH_IMG="${R36_PREFIX}/usr/config/splash/loading-game.png"
[ ! -f "$SPLASH_IMG" ] && SPLASH_IMG="${R36_PREFIX}/storage/.config/splash/loading-game.png"
[ ! -f "$SPLASH_IMG" ] && SPLASH_IMG="/usr/config/splash/loading-game.png"
[ ! -f "$SPLASH_IMG" ] && SPLASH_IMG="/storage/.config/splash/loading-game.png"

SPLASH_PID=""
GPTK_PID=""

# Rota analógica conforme o fone (h2w/state 1 ou 2 = fone; os nomes do Speaker Function são trocados neste clone)
rota_audio() {
    local h2w_state
    h2w_state="$(cat "${R36_PREFIX}/sys/class/switch/h2w/state" 2>/dev/null || cat /sys/class/switch/h2w/state 2>/dev/null || echo 0)"
    case "$h2w_state" in
        "1"|"2") amixer cset name='Speaker Function' spk >/dev/null 2>&1 || true ;;
        *) amixer cset name='Speaker Function' headset >/dev/null 2>&1 || true ;;
    esac
    if [ -x "${R36_PREFIX}/usr/lib/r36/audio-ganho" ]; then
        "${R36_PREFIX}/usr/lib/r36/audio-ganho" aplica 2>/dev/null || true
    fi
}

cleanup() {
    trap - EXIT INT TERM
    [ -n "$SPLASH_PID" ] && kill -9 "$SPLASH_PID" 2>/dev/null
    [ -n "$GPTK_PID" ] && kill -9 "$GPTK_PID" 2>/dev/null
    [ -n "$GPTK_PID" ] && killall -9 gptokeyb 2>/dev/null
    rm -f "$LINK" 2>/dev/null

    rota_audio

    # Tela neutra de saída antes de devolver o ES
    if [ -f "$SPLASH_IMG" ] && command -v mpv >/dev/null 2>&1; then
        mpv "$SPLASH_IMG" >/dev/null 2>&1 || true
    fi
    command -v blank_buffer >/dev/null 2>&1 && { blank_buffer 2>/dev/null || true; }
    { clear > /dev/tty0; } 2>/dev/null || true
    return 0
}
trap cleanup EXIT INT TERM

if [ -f "$SPLASH_IMG" ] && command -v mpv >/dev/null 2>&1; then
    mpv "$SPLASH_IMG" >/dev/null 2>&1 &
    SPLASH_PID=$!
fi
command -v blank_buffer >/dev/null 2>&1 && { blank_buffer 2>/dev/null || true; }

export SDL_AUDIODRIVER=alsa
rota_audio

# Idioma do sistema (emuelec.conf -> es_settings.cfg -> en_US)
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

export CONSOLE_LANG CONSOLE_LANG_SHORT
export LANG="${CONSOLE_LANG}.UTF-8"
export LANGUAGE="${CONSOLE_LANG}"

export SDL_VIDEO_GL_DRIVER="${R36_PREFIX}/usr/lib/libGLESv2.so.2"
export SDL_VIDEO_EGL_DRIVER="${R36_PREFIX}/usr/lib/libEGL.so.1"
export SDL_NOMOUSE=1
export HOME="/storage"

# Mapeamento do micro_gamepad para o SDL2, com o botão 10 (FN / BTN_MODE) como guide
DB_FILE="${R36_PREFIX}/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt"
DEFAULT_SDL_MAPPING="190000006d6963726f5f67616d657000,micro_gamepad,dpleft:b15,rightx:a2,dpright:b16,rightshoulder:b5,dpdown:b14,righty:a3,leftshoulder:b4,y:b3,x:b2,b:b1,a:b0,dpup:b13,back:b8,leftstick:b11,start:b9,lefty:a1,guide:b10,lefttrigger:b6,righttrigger:b7,rightstick:b12,leftx:a0,platform:Linux,"
SDL_CFG=""
if [ -f "$DB_FILE" ]; then
    while IFS= read -r linha || [ -n "$linha" ]; do
        case "$linha" in
            *micro_gamepad*|*retrogame_joypad*) SDL_CFG="${SDL_CFG}${linha}"$'\n' ;;
        esac
    done < "$DB_FILE"
fi
if [ -n "$SDL_CFG" ]; then
    SDL_CFG="${SDL_CFG//guide:b8/guide:b10}"
    case "$SDL_CFG" in
        *guide:b10*) ;;
        *) SDL_CFG="${SDL_CFG%,},guide:b10," ;;
    esac
    export SDL_GAMECONTROLLERCONFIG="$SDL_CFG"
else
    export SDL_GAMECONTROLLERCONFIG="$DEFAULT_SDL_MAPPING"
fi

echo "$CONSOLE_LANG" > "${R36_PREFIX}/tmp/console_lang" 2>/dev/null || true

log "processo: $NOME_PROCESSO (symlink $LINK)"
log "CONSOLE_LANG=$CONSOLE_LANG"
log "--- ldd $ROM ---"
{ ldd "$ROM" 2>&1 || true; } >> "$LOG_OUT" 2>/dev/null

if [ -f "$DIAG_CHAVE" ]; then
    log "--- diagnóstico ---"
    log "CONSOLE_LANG_SHORT=$CONSOLE_LANG_SHORT"
    log "LANG=$LANG"
    log "LANGUAGE=$LANGUAGE"
    log "SDL_AUDIODRIVER=$SDL_AUDIODRIVER"
    log "SDL_VIDEO_GL_DRIVER=$SDL_VIDEO_GL_DRIVER"
    log "SDL_GAMECONTROLLERCONFIG=$SDL_GAMECONTROLLERCONFIG"
fi

# FN + Start (guide + start) encerra o jogo com SIGTERM. O perfil só vincula os atalhos do
# sistema: sem ele o gptokeyb injetaria teclas sobre os botões do jogo, então não sobe.
if [ ! -f "$GPTK_CONF" ]; then
    log "ERRO: perfil $GPTK_CONF ausente; gptokeyb não iniciado (FN + Start não encerra o jogo)"
elif command -v gptokeyb >/dev/null 2>&1; then
    killall -9 gptokeyb 2>/dev/null
    gptokeyb 1 "$NOME_PROCESSO" -c "$GPTK_CONF" -killsignal 15 >/dev/null 2>&1 &
    GPTK_PID=$!
    sleep 0.3
else
    log "ERRO: gptokeyb não encontrado; FN + Start não encerra o jogo"
fi

ln -sf "$ROM" "$LINK" 2>/dev/null
cd "$(dirname "$ROM")" 2>/dev/null || true
log "--- execução ---"
"$LINK" >> "$LOG_OUT" 2>&1
RC=$?
log "saída: $RC"
exit "$RC"
