# Tasks

## 1. Testes primeiro

- [x] 1.1 Atualizar `tests/test_shaders_gba.py` para o shader novo: o `.glsl` declara os quatro parâmetros (`VIBRANCE`, `CONTRAST`, `HIGHLIGHT`, `SOFTNESS`) e nenhum dos antigos (`CORRECTION_STRENGTH`, `SATURATION`, `GAMMA_BOOST`, `PIXEL_SOFTNESS`), não contém `pow(`, `GBA_Matrix` nem `highp` fora de `GL_FRAGMENT_PRECISION_HIGH`, e tem uma única chamada de textura. Verificar que o teste falha contra o shader atual: `uv run python -I -m unittest tests.test_shaders_gba` (deve apontar os parâmetros antigos e o `pow`).

## 2. Shader

- [x] 2.1 Criar a branch `shader-gba-vivo-r36s` a partir da `main`, conforme o `CLAUDE.md`.
- [x] 2.2 Reescrever `features/54-shaders-gba/system/usr/share/common-shaders/gba/gba-modern-remaster.glsl` seguindo a `design.md`: sharp-bilinear com largura pela escala, vibrance, curva em S com pivô 0.35, ombro de realce e proteção de clip com teto `+0.08`, mantendo a estrutura de compatibilidade GLSL/GLSL ES do arquivo atual, precisão `mediump` e permissão `0644`. Verificar com `uv run python -I -m unittest tests.test_shaders_gba` (todos passam).
- [x] 2.3 Conferir que o `.glslp` segue de um passe, com `shader0 = "gba-modern-remaster.glsl"` e `filter_linear0 = "true"`, sem alteração. Verificar pelo teste `test_shader_preset_syntax`.

## 3. Medição no PC

- [x] 3.1 Rodar o shader novo no RetroArch Flatpak com o core mGBA, pelo caminho de auto-shader descrito na `design.md`, em *Mario Kart: Super Circuit* (frame 1200) e *Super Mario Advance 3* (frame 500), e comparar com a captura sem shader. Verificar os números dos cenários da spec: saturação do vermelho a menos de 0.03 abaixo no Mario Kart e a menos de 0.05 abaixo no vermelho puro; saturação média da cena igual ou maior; nitidez de borda de pelo menos 97% da original. Registrar os números no PR.
- [x] 3.2 Olhar as capturas do logo e dos personagens do Mario Kart e da bandeira (frame 500) e conferir que o degradê do céu e a pele dos personagens não estouram. Se o céu achatar, reduzir o teto de `+0.08` para `+0.05` e repetir 3.1.

## 4. Documentação

- [x] 4.1 Atualizar a descrição da feature em `features/54-shaders-gba/feature.toml` (trocar "correção de cor sRGB D65 e suavização sem cintilação" por cor viva, vermelho preservado e filtro sharp-bilinear) e o parágrafo da `54-shaders-gba` no `README.md` (linhas 458 a 462), mantendo o texto sobre "vem desligado" e o local de instalação. Verificar com `uv run python -I -m unittest discover -s tests` (suíte inteira passa) e lendo o diff.

## 5. Validação no aparelho

- [x] 5.1 Gerar o cartão de teste e gravá-lo com `./flash.sh --target-file` para conferir a imagem (sem `sudo`), e entregar ao usuário a instrução de gravar no cartão real. Verificar que `usr/share/common-shaders/gba/gba-modern-remaster.glsl` está no SYSTEM da imagem gerada com `0644` e dono `0:0`.
- [x] 5.2 Instrução ao usuário, no R36S (640x480): escolher `gba/gba-modern-remaster.glslp` em "SHADER SET" do GBA, abrir o Mario Kart e olhar o logo e os personagens; conferir o vermelho do Mario, a nitidez em 2,67x e a fluidez (60 FPS). Os valores padrão dos parâmetros podem ser ajustados pelo menu de parâmetros do RetroArch e, se for o caso, ajustados no shader. Verificar com o relato do usuário.

## Estado para quem continua

Ver o fim da `design.md` ("Registro para quem continua"). Resumo: seções 1 a 4 e 6 a 8 feitas e testadas no PC; faltam 5.2, 7.6 e 8.3, que dependem de o usuário gravar o `system` (build `out/20261026-151033`) e olhar um jogo de GBA; depois, arquivar a change. A medição reproduzível está em `verificacao/`.

## Workflow follow-up

- Merge e push só a pedido do usuário.
- Arquivar a change depois da validação no aparelho.

## 6. Limpeza da p8 (descoberta na validação no aparelho)

- [x] 6.1 Cartões que receberam a versão de teste anterior têm na p8 (`/storage/shaders/gba/`) uma cópia do shader antigo, que esconde a do SYSTEM no overlay `/tmp/shaders`, e presets automáticos do RetroArch (`config/gpSP/`, `config/mGBA/`) que a referenciam e ligam o shader sempre. Adicionado o serviço `r36-shader-gba-limpa` (antes do ES), que apaga só a cópia com `CORRECTION_STRENGTH` e os presets que contêm apenas essa referência, com testes em `tests/test_shaders_gba.py`. Assim a correção chega com `--keep-storage`.
- [x] 6.2 Ajuste dos padrões após o relato no aparelho (brilho alto, branco, amarelo e verde estourados): `CONTRAST` 0.15, `HIGHLIGHT` 0.05 e teto de clip `+0.05` (ver "Ajuste após a validação no aparelho" na `design.md`). Verificado por réplica em numpy: 0% dos pixels claros estouram, saturação média 0.632 (original 0.606), vermelho e nitidez mantidos.
- [x] 6.3 A limpeza da 6.1 só apagava a cópia com `CORRECTION_STRENGTH`, e uma cópia da primeira versão do shader novo (copiada para a p8 em gravações anteriores) continuou escondendo a do SYSTEM, com os parâmetros antigos. O `shader-gba-limpa` agora apaga a cópia da p8 sempre que ela difere da do SYSTEM (e os presets que só a referenciam); cópia idêntica fica. Testes em `tests/test_shaders_gba.py`.

## 7. Efeito LCD (pedido do usuário após a validação no aparelho)

- [x] 7.1 Implementar o efeito LCD no `gba-modern-remaster.glsl` (Decisão 6): parâmetros `LCD_GRID` (padrão 0.10, sutil) e `BRIGHTNESS` (padrão 0), lacuna na borda de trás com cobertura por sobreposição, sem leitura de textura nem `pow`/`highp` novos; novos padrões `VIBRANCE` 0.60, `CONTRAST` 0.20, `SOFTNESS` 0.15. Verificar com `uv run python -I -m unittest tests.test_shaders_gba` via `discover`.
- [x] 7.2 Testes em `tests/test_shaders_gba.py`: os seis parâmetros e seus padrões, uma única leitura de textura, e o `LCD_GRID` no `#pragma`.
- [x] 7.3 Medir por réplica numérica (RetroArch Flatpak não está mais instalado): luma cerca de 4% abaixo da original, grade presente em 480x320 e 640x427, nenhum claro estourado, saturação média maior que a original, PSNR fp16 acima de 30 dB. Exemplos para o usuário em `var/exemplos-lcd/` (fora do git).
- [x] 7.4 Atualizar spec, design, README e `.gitignore` (`var/`).
- [x] 7.5 Cor de console (Decisão 7): parâmetros `SATURATION` e `HIGHLIGHT ROLLOFF`, `VIBRANCE` 0.20, e LCD sutil (`LCD_GRID` 0.10), a pedido do usuário. Medido por réplica: claros coloridos 25% abaixo em saturação, vermelho mantido, 0% de estouro, spec e testes atualizados.
- [x] 7.6 Validação no aparelho: olhar a grade em 2,67x (regular, sem moiré forte, sem irregularidade à direita da tela), a cor e o brilho, e o tempo de quadro (60 FPS). Verificar com o relato do usuário; ajustar `LCD GRID` e `BRIGHTNESS` pelo menu se preciso.

## 8. Shader ligado por padrão no GBA (pedido do usuário)

- [x] 8.1 Renomear o serviço para `r36-shader-gba-prepara` (script `shader-gba-prepara`): além de limpar a cópia velha da p8, cria no boot o preset automático de `gpSP`, `mGBA`, `VBA-M` e `VBA Next` (sem sobrescrever), e obedece à chave `r36-gba-sem-shader` na raiz da p1. Testes em `tests/test_shaders_gba.py` (criação, não sobrescrever, idempotência, chave, sem shader no SYSTEM).
- [x] 8.2 Spec (requisito "ligado por padrão", no lugar de "opcional"), design (Decisão 8), proposal, README, `CLAUDE.md` e `feature.toml`.
- [x] 8.3 Validação no aparelho (confirmada pelo usuário: "remover o shader funciona"): depois de gravar o `system` e ligar, abrir um jogo de GBA sem escolher nada no ES e ver o shader aplicado (menu de parâmetros mostra os oito). Criar `r36-gba-sem-shader` na p1, religar e ver o jogo sem shader. Verificar com o relato do usuário.
- [x] 8.4 Reajuste da cor (Decisão 9): `VIBRANCE` 0.45, `SATURATION` 1.10, `HIGHLIGHT ROLLOFF` 0.65, `S-CURVE Contrast` 0.28, para a cor ficar viva sem ficar saturada. Verificado por réplica nos cenários da spec; exemplos em `var/exemplos-lcd/`.
- [x] 8.12 Sem overlayfs (Decisão 15): o serviço monta `/storage/shaders` em `/tmp/shaders` por bind; `CLAUDE.md` corrigido (cores e shaders vêm da p8 copiada pelo rsync `--ignore-existing`).
- [x] 8.13 Validação no aparelho: "SHADER SET" do ES lista os shaders. Confirmado pelo usuário com o build `20261026-151033` ("apareceu a lista com todos os shaders"); cor aprovada ("ficou ótimo") e sem queda de quadros. O tearing segue para uma change própria (Decisão 14).
- [x] 8.10 Cópia da p8 regravada no lugar (Decisão 13): o rsync `--ignore-existing` do `emuelec_autostart.sh` deixa a cópia do build anterior; o serviço regrava o conteúdo em vez de apagar e remontar. Testes atualizados.
- [x] 8.11 Tearing (Decisão 14): `fb0` tem buffer duplo (`640,960`, pan em uso); a correção (espera do retrace a cada troca) fica para uma change própria.
- [x] 8.9 Capability `retroarch-shaders` (spec delta nova): todas as decisões e padrões do `gba-modern-remaster` como parâmetro para shaders novos. `openspec validate shader-gba-vivo-r36s --strict` passa.
- [x] 8.8 Diagnóstico do tearing: o `r36-shader-gba.log` da p1 registra os atributos de `/sys/class/graphics/fb*` (`virtual_size` com o dobro da altura indica buffer duplo). Pendente: ler o log depois do boot com o build novo e decidir a correção.
- [x] 8.7 Cor viva sem desbotar (Decisão 12): roll-off só do reforço, âncora no canal máximo nos claros, curva em S que protege cores saturadas e o teto, vibrance que some perto do cinza, `HIGHLIGHT ROLLOFF` 0.35. Medido na réplica com a cartela e o logo do SMA2; exemplos em `var/exemplos-cor/`.
- [x] 8.6 Correção após o aparelho (Decisão 11): preset também em `/storage/.config/retroarch/<core>/`, `After=tmp-shaders.mount` e remontagem do overlay depois de limpar a p8, diagnóstico no log da p1. Testes em `tests/test_shaders_gba.py`.
- [x] 8.5 Padrão do GBA pelos dois caminhos (Decisão 10): `gba.shaderset` no `emuelec.conf` mais presets de core que apontam para o SYSTEM, espera da p1 sem desistir, log em `R36-ROMS/r36-shader-gba.log`; testes em `tests/test_shaders_gba.py` e docs atualizadas.
