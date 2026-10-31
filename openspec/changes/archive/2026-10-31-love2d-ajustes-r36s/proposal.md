# Proposal: love2d-ajustes-r36s

## Why

A execução de jogos no runtime standalone do LÖVE 2D no R36S clone (GA36-MB V1.2) apresenta falhas críticas de experiência: o atalho de saída com o botão dedicado do console (`FN + Start`) não encerra a partida, a tela fica desalinhada/cortada fora da resolução nativa de 640x480, a tela de splash neutra de carregamento não é exibida, nenhum áudio é reproduzido pelo subsistema de som e o layout dos botões de ação fica desajustado em relação à disposição física dos botões do portátil. Esta change soluciona esses problemas de integração, adequando o runtime, o lançador e os mapeamentos para paridade com os demais sistemas do console.

## What Changes

- **Atalho de encerramento universal com FN + Start**: Adiciona mapeamento do botão `FN` (`BTN_MODE`, botão 10 do `micro_gamepad`) como `guide:b10` na variável `SDL_GAMECONTROLLERCONFIG` e ajusta `love.gptk` para usar `hotkey = guide` e `start = enter`, permitindo ao daemon `gptokeyb` interceptar `FN + Start` e finalizar o processo do jogo com segurança.
- **Tela de splash neutra na inicialização e saída**: Integra no script lançador `/usr/bin/love.sh` a exibição da tela de carregamento `/usr/config/splash/loading-game.png` via `mpv` em background e `blank_buffer`, replicando o padrão do sistema e ocultando resíduos de console na entrada e na saída de qualquer jogo LÖVE.
- **Adequação e compatibilização do subsistema de som (ALSA/OpenAL)**: Define explicitamente `SDL_AUDIODRIVER=alsa`, reaplica a rota analógica de áudio (`amixer cset name='Speaker Function' ...` conforme `/sys/class/switch/h2w/state`) e chama `/usr/lib/r36/audio-ganho aplica` antes e depois da execução. Sob a chave `r36-diagnostico` na partição `R36-ROMS`, exporta `ALSOFT_LOGLEVEL=3` e direciona o log para `/storage/roms/love/r36-love-alsoft.log` para isolamento de problemas no ALSA/OpenAL.
- **Alinhamento e viewport no display 640x480**: Aplica ajuste no LÖVE 11.5 (compilação/patches ou viewport shim) para forçar o escalonamento proporcional com letterboxing/pillarboxing para a resolução física de 640x480 no framebuffer da Mali-400 (`/dev/fb0`), prevenindo cortes de tela causados por resoluções de janela incompatíveis (como 768x600).
- **Mapeamento posicional dos botões (Layout Nintendo no hardware)**: Ajusta o mapeamento SDL2 e os índices dos botões de joystick no runtime LÖVE para que a disposição física dos botões de face (A na direita, B embaixo, X em cima, Y na esquerda) coincida com as posições esperadas em jogos de console portátil, eliminando a discrepância do padrão Xbox nos botões crus.
- **Limpeza do perfil gptokeyb**: Remove mapeamentos conflitantes de teclado (`space`, `c`, `x`, `v`, `a`, `s`, `d`, `f`, mouse) do `love.gptk`, mantendo o daemon exclusivo para o atalho de saída e navegação direcional/menus, prevenindo comandos duplicados nos jogos.

## Capabilities

### New Capabilities
- `love2d-engine`: Runtime LÖVE 2D standalone no R36S clone (Allwinner A33), cobrindo inicialização em tela cheia 640x480, integração de áudio via ALSA/OpenAL, saída por FN+Start via gptokeyb, telas de splash de abertura/encerramento e conformidade posicional dos botões de controle.

### Modified Capabilities
<!-- Nenhuma capability prévia em openspec/specs teve requisitos alterados; esta change estabelece a especificação completa do LÖVE no repositório principal. -->

## Impact

- `features/64-love2d/system/usr/bin/love.sh`: Lançador com suporte a splash, configuração de variáveis de áudio/diagnóstico, SDL controller config e encerramento.
- `features/64-love2d/system/usr/config/gptokeyb/love.gptk` e `features/64-love2d/system/usr/bin/love.gptk`: Configuração simplificada focada no atalho de encerramento via `guide` (`FN`) e `start`.
- `ports/love2d/`: Receita de compilação do executável `love` com suporte a viewport fixo 640x480 no fbdev e alinhamento posicional dos botões.
- `features/64-love2d/roms/love/`: Jogo *Mr. Rescue* (`mrrescue.love`) com configurações e inicialização compatíveis.
- `tests/test_love2d.py`: Testes automatizados validando as variáveis de ambiente, splash, regras do gptokeyb e integridade do executável.
