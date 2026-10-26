## ADDED Requirements

### Requirement: Perfil de referência para shaders novos
Todo shader novo da imagem SHALL partir do `gba-modern-remaster` como perfil de referência. Nesta spec, `<sistema>` é o id do sistema no EmulationStation (`gba`, `snes`...), `<nome>` é o nome do shader e `<Core>` é a pasta que o RetroArch grava para o core (`gpSP`, `mGBA`, `VBA-M`, `VBA Next`...).

#### Scenario: Shader novo para outro sistema
- **WHEN** um shader é criado para um sistema novo
- **THEN** ele segue os requisitos desta spec, e os padrões numéricos são remedidos para o sistema em vez de copiados sem medir

### Requirement: Custo compatível com o Mali-400
O shader SHALL rodar no Mali-400 (OpenGL ES 2.0, GLSL ES 1.00, contexto `fbdev_mali`) na tela de 640x480 sem perder quadros: um passe, uma leitura de textura por pixel, sem `pow` e sem laço.

#### Scenario: Restrições no arquivo
- **WHEN** o `.glsl` é inspecionado pelos testes
- **THEN** ele não chama `pow(`, tem exatamente uma chamada `COMPAT_TEXTURE(Texture` e o `.glslp` tem um passe

#### Scenario: Tempo de quadro no aparelho
- **WHEN** o usuário liga a exibição da taxa de quadros do RetroArch e joga um trecho com rolagem com o shader
- **THEN** a taxa fica na nativa do sistema (60 no GBA) e não cai em relação ao jogo sem shader

### Requirement: Precisão mediump
O fragment shader SHALL usar `mediump`. `highp` SHALL aparecer só dentro de `#ifdef GL_FRAGMENT_PRECISION_HIGH`, que o Mali-400 não define.

#### Scenario: Precisão conferida
- **WHEN** os testes removem o bloco `GL_FRAGMENT_PRECISION_HIGH` e procuram `highp`
- **THEN** não encontram, e encontram `mediump`

### Requirement: Local e permissões dos arquivos
O shader SHALL ficar no SYSTEM em `/usr/share/common-shaders/<sistema>/<nome>.glsl` e `<nome>.glslp`, dono `0:0` e permissão `0644`, instalado por uma feature `features/<NN>-shaders-<sistema>/`.

#### Scenario: Imagem gerada
- **WHEN** o SYSTEM do build é listado com `unsquashfs -lls`
- **THEN** os dois arquivos estão no caminho acima, com dono root e `-rw-r--r--`

### Requirement: Estrutura GLSL compatível
O `.glsl` SHALL seguir a estrutura de compatibilidade GLSL e GLSL ES do perfil de referência, com o comentário de topo em inglês descrevendo cada etapa.

#### Scenario: Estrutura conferida
- **WHEN** o `.glsl` é lido
- **THEN** ele tem os blocos `#if defined(VERTEX)` e `#elif defined(FRAGMENT)`, as macros `COMPAT_VARYING`, `COMPAT_ATTRIBUTE`, `COMPAT_TEXTURE` e `COMPAT_PRECISION`, os uniforms `MVPMatrix`, `OutputSize`, `TextureSize`, `InputSize`, `FrameCount` e `FrameDirection`, e cada `#pragma parameter` tem um `#define` de reserva com o mesmo padrão fora de `PARAMETER_UNIFORM`

### Requirement: Preset de um passe pela viewport
O `.glslp` SHALL ter um passe com filtro linear e escala pela viewport.

#### Scenario: Preset conferido
- **WHEN** o `.glslp` é lido
- **THEN** ele declara `shaders = "1"`, `shader0 = "<nome>.glsl"`, `filter_linear0 = "true"`, `scale_type0 = "viewport"` e `scale0 = "1.0"`

### Requirement: Parâmetros padronizados
Um shader de cor SHALL reutilizar os identificadores, nomes no menu, faixas e significados do perfil de referência. Um parâmetro que não se aplica MAY ser omitido, mas um identificador SHALL NOT ganhar outro significado.

#### Scenario: Tabela de parâmetros
- **WHEN** o usuário abre os parâmetros do shader no RetroArch
- **THEN** os parâmetros presentes seguem esta tabela (identificador, nome no menu, faixa, passo, padrão do GBA, significado):
  - `VIBRANCE`, "VIBRANCE", 0 a 1, 0.05, 0.45: reforço de croma maior para o que está pouco saturado, que some perto do cinza
  - `SATURATION`, "SATURATION", 0.5 a 1.3, 0.01, 1.10: multiplicador global de croma (1.0 neutro)
  - `ROLLOFF`, "HIGHLIGHT ROLLOFF", 0 a 1, 0.05, 0.35: quanto do reforço de croma sai dos tons claros
  - `CONTRAST`, "S-CURVE Contrast", 0 a 1, 0.05, 0.28: curva em S na luma, pivô 0.35
  - `HIGHLIGHT`, "HIGHLIGHT SHOULDER", 0 a 1, 0.05, 0.05: ombro de realce nos claros
  - `SOFTNESS`, "PIXEL SOFTNESS", 0 a 1, 0.05, 0.15: largura da transição entre pixels (0 = um pixel de saída, 1 = bilinear)
  - `LCD_GRID`, "LCD GRID (0=Off)", 0 a 1, 0.05, 0.10: força da grade entre os pixels do jogo
  - `BRIGHTNESS`, "BRIGHTNESS", -0.30 a 0.30, 0.01, 0.00: ganho final de brilho

### Requirement: Sem correção de cor do LCD original
O shader SHALL NOT reproduzir a cor do LCD do aparelho original nem usar matriz de correção de cor; o objetivo é aparência de remaster, viva e sem estouro.

#### Scenario: Identificadores proibidos
- **WHEN** o `.glsl` é inspecionado
- **THEN** ele não contém `CORRECTION_STRENGTH`, `GAMMA_BOOST`, `PIXEL_SOFTNESS` nem `GBA_Matrix`

### Requirement: Ganho de croma que não desbota
O ganho de croma SHALL reforçar mais o que está pouco saturado, sumir perto do cinza, tirar dos claros só o reforço (nunca a croma original) e, nos claros, aprofundar os canais fracos em vez de clarear.

#### Scenario: Fórmula do ganho
- **WHEN** o pipeline é inspecionado, com luma Rec. 709 `L`, canal máximo `mx`, saturação HSV `sat` e `hs = smoothstep(0.5, 1.0, L)`
- **THEN** o ganho é `g = (1 + VIBRANCE * min(1 - sat, 4 sat (1 - sat))) * SATURATION`, reduzido a `1 + (g - 1) * (1 - ROLLOFF * hs)`, aplicado em torno da âncora `mix(L, mx, hs)` e com os canais limitados a zero

### Requirement: Curva de luma que preserva cor
A curva em S e o ombro SHALL ser aplicados como uma razão única nos três canais (matiz mantido), sem escurecer cores saturadas e sem clarear o que já está no teto.

#### Scenario: Fórmula da curva
- **WHEN** o pipeline é inspecionado
- **THEN** a razão é `k = (L + CONTRAST * 2 L (1 - L) (L - 0.35) + HIGHLIGHT * hs * (1 - L) * 0.5) / L`, depois `k = max(k, mix(k, 1, sat²))` e `k <= max(teto / max(c), 1)`, com teto `min(1, mx + 0.05)`

### Requirement: Proteção de clip sem cortar canal
Se o maior canal passar do teto, o shader SHALL puxar a croma para a luma até caber, sem cortar um canal isolado.

#### Scenario: Claros sem estouro
- **WHEN** as telas de referência são renderizadas com os padrões
- **THEN** nenhum pixel que estava abaixo de 245 (em 255) no canal máximo chega a 255

### Requirement: Cores vivas com matiz mantido
O resultado do pipeline SHALL manter o matiz de cada cor, não desbotar nenhuma cor e dar mais cor a pele, amarelos e tons pastel, sem tingir fundos quase brancos.

#### Scenario: Cartela de cores
- **WHEN** a cartela de 24 cores da réplica é renderizada com os padrões e `LCD GRID` em 0
- **THEN** nenhuma cor muda de matiz mais de 2 graus, nenhuma perde mais de 0.05 de saturação, e a luma de nenhuma cor com canal máximo de 245 ou mais sobe mais de 0.02

#### Scenario: Cores de referência
- **WHEN** a pele do Mario (248, 184, 136), o amarelo puro, o vermelho do Mario em *Mario Kart: Super Circuit*, o azul puro e o fundo bege do logo de *Super Mario Advance 2* (246, 226, 213) são comparados com e sem o shader
- **THEN** a saturação da pele sobe pelo menos 0.08, a do amarelo puro fica a menos de 0.05 de 1.00, a do vermelho fica a menos de 0.04 abaixo da original, o canal azul do azul puro perde menos de 3 pontos (em 255) e a saturação do fundo bege fica abaixo de 0.18

### Requirement: Escala nítida sharp-bilinear
O shader SHALL suavizar a borda dos pixels do jogo em cerca de um pixel de saída, em escala inteira e não inteira, com uma leitura de textura.

#### Scenario: Largura da transição
- **WHEN** o pipeline é inspecionado
- **THEN** a largura da transição, em pixels do jogo, é `mix(InputSize.x / OutputSize.x, 1, SOFTNESS)`

#### Scenario: Nitidez mantida
- **WHEN** a nitidez de borda (gradiente horizontal médio do canal verde) é medida com e sem o shader, em escala inteira e com `LCD GRID` em 0
- **THEN** a nitidez com o shader é de pelo menos 97% da do vizinho mais próximo

### Requirement: Grade LCD sutil e estável
Quando houver efeito LCD, a grade SHALL escurecer de leve a borda de trás de cada pixel do jogo, em escala inteira e não inteira, sem leitura extra de textura, e `LCD_GRID` em 0 SHALL dar a imagem sem grade.

#### Scenario: Geometria da grade
- **WHEN** o pipeline é inspecionado
- **THEN** a lacuna é `min(InputSize.x / OutputSize.x, 0.3)` pixel do jogo e a cobertura é a sobreposição do pixel de saída com a lacuna do próprio pixel do jogo e do anterior

#### Scenario: Grade presente e leve
- **WHEN** o shader roda com os padrões em 640x427 e em 480x320 sobre uma cena plana de luma 0.6 com a cor neutra
- **THEN** o menor valor fica entre 75% e 92% do maior, e entre 40% e 60% das colunas e linhas ficam abaixo de 98% do pico

#### Scenario: Grade desligada
- **WHEN** `LCD_GRID` é posto em 0
- **THEN** a cena plana sai uniforme

### Requirement: Serviço de boot sem travar o boot
Um shader que vem ligado num sistema SHALL ser preparado pelo serviço oneshot `r36-shader-<sistema>-prepara.service`, que roda antes do ES e depois da tentativa de montar `/tmp/shaders`, sem depender do `emuelec-autostart.service`.

#### Scenario: Ordenação da unit
- **WHEN** a unit é lida
- **THEN** ela tem `Before=emustation.service`, `After=tmp-shaders.mount`, `WantedBy=emuelec.target` e nenhum `After=emuelec-autostart.service`, e o script espera até 20 s a p1 montar em `/storage/roms` antes de seguir

### Requirement: Liga o shader sem sobrescrever escolhas
O serviço SHALL ligar o shader pelo `emuelec.conf` e pelos presets automáticos dos cores do sistema, sem alterar uma chave ou preset que já existam.

#### Scenario: Primeiro boot
- **WHEN** não existe `<sistema>.shaderset` no `emuelec.conf` nem preset do core
- **THEN** o serviço acrescenta `<sistema>.shaderset=<sistema>/<nome>.glslp` (que faz o ES escrever `video_shader_enable = "true"`) e cria `/storage/.config/retroarch/config/<Core>/<Core>.glslp` e `/storage/.config/retroarch/<Core>/<Core>.glslp`, cada um com a única linha `#reference "/usr/share/common-shaders/<sistema>/<nome>.glslp"`

#### Scenario: Escolha do usuário
- **WHEN** o usuário já escolheu outro shader ou `none` no "SHADER SET", ou salvou um preset pelo menu do RetroArch
- **THEN** o serviço não altera essa escolha

### Requirement: Cópia da p8 atualizada no lugar
O kernel não tem overlayfs, e o `emuelec_autostart.sh` copia `/usr/share/common-shaders` para `/storage/shaders` a cada boot com `rsync --ignore-existing`, que nunca atualiza. O serviço SHALL regravar, no mesmo arquivo, a cópia da p8 que difere da do SYSTEM, e SHALL NOT apagá-la nem criar uma que não existe.

#### Scenario: Cópia de build anterior
- **WHEN** `/storage/shaders/<sistema>/<nome>.glsl` existe e difere do arquivo do SYSTEM
- **THEN** o serviço regrava o conteúdo do SYSTEM no mesmo inode e apaga os presets cujo conteúdo é só o `#reference` a essa cópia

### Requirement: /tmp/shaders por bind
Sem overlayfs, o `tmp-shaders.mount` falha e `/tmp/shaders`, de onde o ES tira a lista do "SHADER SET", fica vazio. O serviço SHALL montar `/storage/shaders` em `/tmp/shaders` por bind quando nada estiver montado ali.

#### Scenario: Lista do ES
- **WHEN** o aparelho liga com o build e o usuário abre "SHADER SET" de um sistema
- **THEN** a lista mostra os shaders da p8, inclusive `<sistema>/<nome>.glslp`, e o log do serviço registra o bind

### Requirement: Chave para desligar e log na p1
O serviço SHALL obedecer ao arquivo vazio `r36-<sistema>-sem-shader` na raiz da R36-ROMS, desfazendo só o que ele mesmo criou, e SHALL registrar o que fez em `r36-shader-<sistema>.log` na raiz da R36-ROMS.

#### Scenario: Desligar pelo PC
- **WHEN** existe `r36-<sistema>-sem-shader` e o aparelho é religado
- **THEN** a linha do `emuelec.conf` e os presets criados pelo serviço somem, os do usuário ficam, e o log registra a chave

### Requirement: Vídeo e áudio do RetroArch intocados
O shader e o serviço SHALL NOT alterar `video_threaded`, `video_vsync`, o driver de vídeo nem o de áudio.

#### Scenario: retroarch.cfg depois do boot
- **WHEN** o `retroarch.cfg` da p8 é comparado antes e depois do serviço rodar
- **THEN** essas chaves não mudaram (neste aparelho, desligar o vídeo em thread trava o RetroArch e estraga o som)

### Requirement: Réplica numérica do shader
Todo shader SHALL ter uma réplica em Python (numpy) que espelha o `.glsl` e repete os padrões, mede os cenários da sua spec e grava exemplos em `var/` (fora do git).

#### Scenario: Exemplos de comparação
- **WHEN** a réplica roda sobre capturas sem shader feitas pelo core libretro no PC (resolução nativa ou 2x com vizinho mais próximo, fora do git)
- **THEN** ela imprime as medidas dos cenários e grava, para cada tela, o RetroArch sem shader (bilinear sobre a cor crua), a versão anterior e a nova

#### Scenario: Meia precisão
- **WHEN** a réplica compara a saída em float32 com a de meia precisão nas telas de referência, em 640x427
- **THEN** o PSNR fica acima de 30 dB

### Requirement: Testes de estrutura do shader
O shader SHALL ter testes em `tests/` que conferem a estrutura e o serviço, rodados pela suíte do projeto.

#### Scenario: Suíte
- **WHEN** `uv run python -I -m unittest discover -s tests` roda
- **THEN** os testes conferem parâmetros, padrões, nomes no menu, reserva `#define`, restrições do Mali-400, o preset e o serviço de boot, e passam
