# Spec Delta

## MODIFIED Requirements

### Requirement: Perfil de referência para shaders novos
Todo shader novo da imagem SHALL partir do `gba-modern-remaster` como perfil de referência para sistemas em cores (como GBC e GBA) ou do `gb-modern-dmg` para sistemas monocromáticos de 4 tons (como o Game Boy Clássico). Nesta spec, `<sistema>` é o id do sistema no EmulationStation (`gb`, `gbc`, `gba`, `snes`...), `<nome>` é o nome do shader e `<Core>` é a pasta que o RetroArch grava para o core (`Gambatte`, `gpSP`, `mGBA`, `VBA-M`, `VBA Next`...).

#### Scenario: Shader novo para outro sistema
- **WHEN** um shader é criado para um sistema novo
- **THEN** ele segue os requisitos desta spec, e os padrões numéricos são remedidos para o sistema em vez de copiados sem medir

### Requirement: Local e permissões dos arquivos
O shader SHALL ficar no SYSTEM em `/usr/share/common-shaders/<sistema>/<nome>.glsl` e `<nome>.glslp`, dono `0:0` e permissão `0644`, instalado por uma feature `features/<NN>-shaders-<sistema>/` (ou feature agrupada como `features/55-shaders-gb-gbc/` para sistemas da mesma família).

#### Scenario: Imagem gerada
- **WHEN** o SYSTEM do build é listado com `unsquashfs -lls`
- **THEN** os dois arquivos estão no caminho acima, com dono root e `-rw-r--r--`

### Requirement: Parâmetros padronizados
Um shader de cor SHALL reutilizar os identificadores, nomes no menu, faixas e significados do perfil de referência. Um shader monocromático de 4 tons (como o do Game Boy Clássico) SHALL reutilizar `CONTRAST`, `SOFTNESS`, `LCD_GRID` e `BRIGHTNESS` e MAY definir `TONE_SEP` e `WARMTH` para a paleta DMG. Um parâmetro que não se aplica MAY ser omitido, mas um identificador SHALL NOT ganhar outro significado.

#### Scenario: Tabela de parâmetros
- **WHEN** o usuário abre os parâmetros do shader no RetroArch
- **THEN** os parâmetros presentes seguem esta tabela (identificador, nome no menu, faixa, passo, padrão do GBA, significado):
  - `VIBRANCE`, "VIBRANCE", 0 a 1, 0.05, 0.45: reforço de croma maior para o que está pouco saturado, que some perto do cinza
  - `SATURATION`, "SATURATION", 0.5 a 1.3, 0.01, 1.10: multiplicador global de croma (1.0 neutro)
  - `ROLLOFF`, "HIGHLIGHT ROLLOFF", 0 a 1, 0.05, 0.35: quanto do reforço de croma sai dos tons claros
  - `CONTRAST`, "S-CURVE Contrast", 0 a 1, 0.05, 0.28: curva em S na luma, pivô 0.35
  - `HIGHLIGHT`, "HIGHLIGHT SHOULDER", 0 a 1, 0.05, 0.05: ombro de realce nos claros
  - `TONE_SEP`, "TONE SEPARATION", 0 a 1, 0.05, 0.50: abertura entre os tons intermediários da paleta de 4 tons do DMG
  - `WARMTH`, "OLIVE WARMTH", 0 a 1, 0.05, 0.50: equilíbrio do tom verde-oliva do substrato reflexivo do DMG
  - `SOFTNESS`, "PIXEL SOFTNESS", 0 a 1, 0.05, 0.15: largura da transição entre pixels (0 = um pixel de saída, 1 = bilinear)
  - `LCD_GRID`, "LCD GRID (0=Off)" ou "DOT MATRIX GRID (0=Off)", 0 a 1, 0.05, 0.10 (GBA/GBC) / 0.22 (GB): força da grade entre os pixels do jogo
  - `BRIGHTNESS`, "BRIGHTNESS", -0.30 a 0.30, 0.01, 0.00: ganho final de brilho

Os shaders do Game Boy divergem do GBA em alguns padrões, remedidos para 160x144 e 533x480: `SOFTNESS` é 0.05 no `gb-modern-dmg` e no `gbc-modern-remaster` (0.15 no GBA), `CONTRAST` é 0.20 no `gb-modern-dmg` (0.28 no GBA e no GBC), `LCD_GRID` é 0.22 no GB, e o `gbc-modern-remaster` usa o teto de croma `mx + 0.035` (`mx + 0.05` no GBA). Os demais padrões do GBC são os do GBA.

### Requirement: Liga o shader sem sobrescrever escolhas
O serviço SHALL ligar o shader pelo `emuelec.conf` e pelos presets automáticos dos cores do sistema (`<Core>/<Core>.glslp` quando o core é exclusivo do sistema, ou `<Core>/<sistema>.glslp` por pasta de conteúdo quando sistemas como `gb`, `gbc` e `gba` compartilham cores), sem alterar uma chave ou preset que já existam.

#### Scenario: Primeiro boot
- **WHEN** não existe `<sistema>.shaderset` no `emuelec.conf` nem preset do sistema/core
- **THEN** o serviço acrescenta `<sistema>.shaderset=<sistema>/<nome>.glslp` (que faz o ES escrever `video_shader_enable = "true"`) e cria `/storage/.config/retroarch/config/<Core>/<alvo>.glslp` e `/storage/.config/retroarch/<Core>/<alvo>.glslp` (onde `<alvo>` é `<Core>` no GBA e `<sistema>` no GB/GBC), cada um com a única linha `#reference "/usr/share/common-shaders/<sistema>/<nome>.glslp"`

#### Scenario: Escolha do usuário
- **WHEN** o usuário já escolheu outro shader ou `none` no "SHADER SET", ou salvou um preset pelo menu do RetroArch
- **THEN** o serviço não altera essa escolha

### Requirement: Sem correção de cor do LCD original
O shader de cor SHALL NOT reproduzir a cor do LCD do aparelho original nem usar matriz de correção de cor; o objetivo é aparência de remaster, viva e sem estouro. O shader monocromático de 4 tons do Game Boy Clássico (`gb-modern-dmg`) é a exceção: ele SHALL mapear os 4 tons para uma paleta verde-oliva de DMG-01 de alta clareza (não uma matriz de correção do LCD) e SHALL NOT usar `CORRECTION_STRENGTH`, `GAMMA_BOOST`, `PIXEL_SOFTNESS` nem `GBA_Matrix`.

#### Scenario: Identificadores proibidos
- **WHEN** o `.glsl` é inspecionado
- **THEN** ele não contém `CORRECTION_STRENGTH`, `GAMMA_BOOST`, `PIXEL_SOFTNESS` nem `GBA_Matrix`

### Requirement: Ganho de croma que não desbota
O ganho de croma de um shader de cor SHALL reforçar mais o que está pouco saturado, sumir perto do cinza, tirar dos claros só o reforço (nunca a croma original) e, nos claros, aprofundar os canais fracos em vez de clarear. O `gb-modern-dmg` SHALL NOT ter ganho de croma: ele leva a luma à paleta de 4 tons.

#### Scenario: Fórmula do ganho
- **WHEN** o pipeline de um shader de cor é inspecionado, com luma Rec. 709 `L`, canal máximo `mx`, saturação HSV `sat` e `hs = smoothstep(0.5, 1.0, L)`
- **THEN** o ganho é `g = (1 + VIBRANCE * min(1 - sat, 4 sat (1 - sat))) * SATURATION`, reduzido a `1 + (g - 1) * (1 - ROLLOFF * hs)`, aplicado em torno da âncora `mix(L, mx, hs)` e com os canais limitados a zero

### Requirement: Curva de luma que preserva cor
A curva em S e o ombro de um shader de cor SHALL ser aplicados como uma razão única nos três canais (matiz mantido), sem escurecer cores saturadas e sem clarear o que já está no teto. O `gb-modern-dmg` SHALL aplicar a curva em S só à luma (`L + CONTRAST * 2 L (1 - L) (L - 0.35)`) antes de mapeá-la na paleta, sem razão por canal nem ombro.

#### Scenario: Fórmula da curva
- **WHEN** o pipeline de um shader de cor é inspecionado
- **THEN** a razão é `k = (L + CONTRAST * 2 L (1 - L) (L - 0.35) + HIGHLIGHT * hs * (1 - L) * 0.5) / L`, depois `k = max(k, mix(k, 1, sat²))` e `k <= max(teto / max(c), 1)`, com teto `min(1, mx + 0.05)` (`mx + 0.035` no `gbc-modern-remaster`)

### Requirement: Cores vivas com matiz mantido
O resultado do pipeline de um shader de cor SHALL manter o matiz de cada cor, não desbotar nenhuma cor e dar mais cor a pele, amarelos e tons pastel, sem tingir fundos quase brancos. O `gb-modern-dmg` SHALL NOT manter o matiz: ele entrega 4 tons verde-oliva separados em pelo menos 0.20 de luma Rec. 709, medidos na capability `gb-gbc-emulation`.

#### Scenario: Cartela de cores
- **WHEN** a cartela de 24 cores da réplica é renderizada por um shader de cor com os padrões e `LCD GRID` em 0
- **THEN** nenhuma cor muda de matiz mais de 2 graus, nenhuma perde mais de 0.05 de saturação, e a luma de nenhuma cor com canal máximo de 245 ou mais sobe mais de 0.02

#### Scenario: Cores de referência
- **WHEN** a pele do Mario (248, 184, 136), o amarelo puro, o vermelho do Mario em *Mario Kart: Super Circuit*, o azul puro e o fundo bege do logo de *Super Mario Advance 2* (246, 226, 213) são comparados com e sem o shader do GBA
- **THEN** a saturação da pele sobe pelo menos 0.08, a do amarelo puro fica a menos de 0.05 de 1.00, a do vermelho fica a menos de 0.04 abaixo da original, o canal azul do azul puro perde menos de 3 pontos (em 255) e a saturação do fundo bege fica abaixo de 0.18

### Requirement: Grade LCD sutil e estável
Quando houver efeito LCD, a grade SHALL escurecer de leve a borda de trás de cada pixel do jogo, em escala inteira e não inteira, sem leitura extra de textura, e `LCD_GRID` em 0 SHALL dar a imagem sem grade. No `gb-modern-dmg`, a grade SHALL levar a lacuna ao tom do substrato verde-oliva (`mix(c, T3 * 0.55, LCD_GRID * g)`), o que clareia a lacuna entre pixels escuros e escurece de leve o fundo claro.

#### Scenario: Geometria da grade
- **WHEN** o pipeline é inspecionado
- **THEN** a lacuna é `min(InputSize.x / OutputSize.x, 0.3)` pixel do jogo e a cobertura é a sobreposição do pixel de saída com a lacuna do próprio pixel do jogo e do anterior

#### Scenario: Grade presente e leve
- **WHEN** um shader de cor roda com os padrões em 640x427 e em 480x320 sobre uma cena plana de luma 0.6 com a cor neutra
- **THEN** o menor valor fica entre 75% e 92% do maior, e entre 40% e 60% das colunas e linhas ficam abaixo de 98% do pico; para o `gb-modern-dmg` vale o cenário de blocos T0 e T3 em 533x480 da capability `gb-gbc-emulation`

#### Scenario: Grade desligada
- **WHEN** `LCD_GRID` é posto em 0
- **THEN** a cena plana sai uniforme

### Requirement: Serviço de boot sem travar o boot
Um shader que vem ligado num sistema SHALL ser preparado pelo serviço oneshot `r36-shader-<sistema>-prepara.service`, que roda antes do ES e depois da tentativa de montar `/tmp/shaders`, sem depender do `emuelec-autostart.service`. Uma feature de família que liga shaders de vários sistemas num serviço só (como `55-shaders-gb-gbc`) SHALL nomear o serviço pela família, `r36-shader-<família>-prepara.service` (`r36-shader-gb-gbc-prepara.service`), e MAY ordenar-se depois de outro serviço de shader (`After=r36-shader-gba-prepara.service`) para não competir pelo `emuelec.conf` nem pelo bind de `/tmp/shaders`.

#### Scenario: Ordenação da unit
- **WHEN** a unit é lida
- **THEN** ela tem `Before=emustation.service`, `After=tmp-shaders.mount`, `WantedBy=emuelec.target` e nenhum `After=emuelec-autostart.service`, e o script espera até 20 s a p1 montar em `/storage/roms` antes de seguir

### Requirement: Chave para desligar e log na p1
O serviço SHALL obedecer ao arquivo vazio `r36-<sistema>-sem-shader` na raiz da R36-ROMS, desfazendo só o que ele mesmo criou, e SHALL registrar o que fez em `r36-shader-<sistema>.log` na raiz da R36-ROMS somente quando existir o arquivo vazio `r36-diagnostico` na raiz da R36-ROMS. Um serviço de família SHALL ter uma chave por sistema (`r36-gb-sem-shader`, `r36-gbc-sem-shader`) e um log só, nomeado pela família (`r36-shader-gb-gbc.log`). Sem `r36-diagnostico`, o serviço SHALL NOT criar nem atualizar o log e SHALL fazer o mesmo trabalho.

#### Scenario: Desligar pelo PC
- **WHEN** existe `r36-<sistema>-sem-shader` e o aparelho é religado
- **THEN** a linha do `emuelec.conf` e os presets criados pelo serviço somem, os do usuário ficam, e, havendo `r36-diagnostico`, o log registra a chave

#### Scenario: Sem a chave de diagnóstico
- **WHEN** a p1 não tem `r36-diagnostico` e o aparelho liga
- **THEN** o log do serviço (`r36-shader-<sistema>.log` ou `r36-shader-<família>.log`) não é criado nem alterado, e o shader, os presets e a lista "SHADER SET" ficam como com a chave
