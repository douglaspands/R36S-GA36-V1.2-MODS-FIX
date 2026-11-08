/* ELF de teste do console gba-recomp: abre a tela (SDL2 + GLES2), toca um tom
 * de 440 Hz e espera SIGTERM (o que o gptokeyb envia no FN + Start).
 * Receita de build em LEIAME.md. Registra o nome do processo e cada sinal em
 * stdout, que o recomp.sh grava no recomp.log. */
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengles2.h>
#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>

static volatile sig_atomic_t parar = 0;

static void ao_sinal(int sig) { parar = sig; }

static void tom(void *dados, Uint8 *fluxo, int tam) {
    static double fase = 0.0;
    Sint16 *amostras = (Sint16 *)fluxo;
    int n = tam / (int)sizeof(Sint16);
    (void)dados;
    for (int i = 0; i < n; i += 2) {
        Sint16 v = (Sint16)(sin(fase) * 6000.0);
        fase += 2.0 * M_PI * 440.0 / 44100.0;
        amostras[i] = v;
        amostras[i + 1] = v;
    }
}

int main(void) {
    char comm[32] = {0};
    prctl(PR_GET_NAME, comm, 0, 0, 0);
    printf("teste: processo=%s\n", comm);
    fflush(stdout);

    signal(SIGTERM, ao_sinal);
    signal(SIGINT, ao_sinal);

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_JOYSTICK) != 0) {
        fprintf(stderr, "teste: SDL_Init falhou: %s\n", SDL_GetError());
        return 2;
    }
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_ES);
    SDL_Window *janela = SDL_CreateWindow("teste", 0, 0, 640, 480, SDL_WINDOW_OPENGL | SDL_WINDOW_FULLSCREEN);
    if (!janela || !SDL_GL_CreateContext(janela)) {
        fprintf(stderr, "teste: janela GLES2 falhou: %s\n", SDL_GetError());
        return 3;
    }

    SDL_AudioSpec want;
    SDL_zero(want);
    want.freq = 44100;
    want.format = AUDIO_S16SYS;
    want.channels = 2;
    want.samples = 1024;
    want.callback = tom;
    if (SDL_OpenAudio(&want, NULL) == 0)
        SDL_PauseAudio(0);
    else
        fprintf(stderr, "teste: áudio falhou: %s\n", SDL_GetError());

    int quadro = 0;
    while (!parar) {
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_JOYBUTTONDOWN)
                printf("teste: botao %d\n", e.jbutton.button), fflush(stdout);
        }
        float c = (float)(quadro++ % 120) / 120.0f;
        glClearColor(c, 0.2f, 1.0f - c, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        SDL_GL_SwapWindow(janela);
    }
    printf("teste: sinal=%d, saindo\n", (int)parar);
    SDL_CloseAudio();
    SDL_Quit();
    return 0;
}
