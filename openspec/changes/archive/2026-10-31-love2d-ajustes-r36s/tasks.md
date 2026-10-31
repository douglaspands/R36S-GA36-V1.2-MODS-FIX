# Tasks: love2d-ajustes-r36s

## 1. Atalho de Saída e Perfil gptokeyb

- [x] 1.1 Declarar o botão 10 (`BTN_MODE` emitido pelo FN) como `guide:b10` na string `SDL_GAMECONTROLLERCONFIG` em `features/64-love2d/system/usr/bin/love.sh` e validar sintaxe e mapeamento
- [x] 1.2 Atualizar `features/64-love2d/system/usr/config/gptokeyb/love.gptk` e `features/64-love2d/system/usr/bin/love.gptk` definindo `hotkey = guide` e `start = enter`, removendo mapeamentos concorrentes de teclas de ação do teclado (`space`, `c`, `x`, `v`, mouse) e validar o arquivo resultante

## 2. Telas de Splash e Ciclo de Execução

- [x] 2.1 Adicionar exibição do splash neutro de carregamento `/usr/config/splash/loading-game.png` com `mpv` em segundo plano e `blank_buffer` no início de `features/64-love2d/system/usr/bin/love.sh`
- [x] 2.2 Integrar exibição do splash neutro de saída na função `cleanup()` do lançador, com encerramento gracioso de daemons e processos em segundo plano (`mpv`, `gptokeyb`), e verificar o fluxo com simulação de encerramento

## 3. Compatibilização de Áudio e Diagnóstico

- [x] 3.1 Exportar `SDL_AUDIODRIVER=alsa`, configurar o caminho de áudio (`Speaker Function`) conforme o fone em `/sys/class/switch/h2w/state` e chamar `/usr/lib/r36/audio-ganho aplica` no início e no `cleanup()` de `features/64-love2d/system/usr/bin/love.sh`
- [x] 3.2 Implementar verificação da chave `r36-diagnostico` em `/storage/roms` no lançador para ativar `ALSOFT_LOGLEVEL=3` e direcionar `ALSOFT_LOGFILE` para `/storage/roms/love/r36-love-alsoft.log`

## 4. Viewport 640x480 e Controles no Runtime LÖVE

- [x] 4.1 Criar patches C++ para o código do LÖVE 11.5 em `ports/love2d/` ajustando a criação de janela em modo framebuffer para a resolução física de 640x480 com escala proporcional e ajustando os botões de joystick para a disposição física do portátil
- [x] 4.2 Atualizar `ports/love2d/compilar.sh` para aplicar os patches durante o build hermético no container Podman
- [x] 4.3 Compilar e atualizar o binário `features/64-love2d/system/usr/bin/love`, verificando ausência de símbolos glibc > 2.36 e arquitetura ARMv7-A hard-float

## 5. Validação e Testes Automatizados

- [x] 5.1 Verificar a inicialização e os binds padrão do jogo *Mr. Rescue* (`features/64-love2d/roms/love/mrrescue.love`), garantindo que não ocorra colisão ou erro `table index is nil`
- [x] 5.2 Expandir e executar os testes unitários em `tests/test_love2d.py` validando todas as novas configurações do lançador, gptokeyb e diagnósticos via `uv run python -I -m unittest discover -s tests`
- [x] 5.3 Atualizar o manual técnico `docs/DESENVOLVIMENTO.md` documentando os novos recursos do LÖVE 2D Standalone

## 6. Correções de Áudio (OpenAL Soft) e Entrada Digital (Mr. Rescue)

- [x] 6.1 Criar configuração otimizada do OpenAL Soft (`alsoft.conf`) em `usr/config/openal/` e `etc/openal/` com `sample-type = int16`, `frequency = 48000`, `dither = false`, `resampler = cubic` e `allow-resampler = false`, exportando `ALSOFT_CONF` no `love.sh`
- [x] 6.2 Adicionar suporte abrangente ao D-pad no `mrrescue.love` cobrindo Gamepad API (`dpup/dpdown/dpleft/dpright`), POV Hat (`getHat(1)`) e botões brutos (14 a 17) para movimentação, escadas e menus com cooldown
- [x] 6.3 Atualizar `tests/test_love2d.py` com testes dedicados de OpenAL Soft e D-pad do *Mr. Rescue*, validando 100% da suíte com 765 testes passando
- [x] 6.4 Eliminar duplicação de acionamento de botões (remoção de teclas virtuais direcionais no `love.gptk` e segregação estrita entre Gamepad API e Joystick API no `mrrescue.love`) e maximizar a nitidez sonora (reamostragem Sinc de 12 pontos `bsinc12`, desativação do compressor de pico `output-limiter = false`, `stereo-encoding = pan` e volumes balanceados)
