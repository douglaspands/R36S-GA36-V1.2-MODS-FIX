# gba-emulation Specification

## Purpose
Definir qual emulador e core o Game Boy Advance usa por padrão na imagem gerada, priorizando a leveza no hardware do A33 sem remover as alternativas.

## Requirements

### Requirement: gpSP como core padrão do GBA
A configuração do EmuELEC SHALL fazer os jogos de Game Boy Advance abrirem no core gpSP do RetroArch, sem o usuário precisar escolher o core.

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmuELEC declara `gba.emulator=libretro` e `gba.core=gpsp`

#### Scenario: Jogo de GBA sem escolha prévia
- **WHEN** o usuário abre um jogo de GBA que não tem core próprio escolhido
- **THEN** o jogo roda no gpSP

### Requirement: Outros cores de GBA continuam disponíveis
O mGBA, o vbam e o vba_next SHALL continuar instalados e selecionáveis pelo menu do EmulationStation, por sistema ou por jogo.

#### Scenario: Jogo escolhido para outro core
- **WHEN** o usuário escolhe o mGBA para um jogo específico no menu do ES
- **THEN** esse jogo abre no mGBA, e os demais continuam no gpSP

### Requirement: Jogos de GBA rodam sem BIOS de GBA
O padrão gpSP SHALL funcionar sem o arquivo `gba_bios.bin`, e a imagem NÃO SHALL exigir que o usuário o forneça.

#### Scenario: Cartão sem a BIOS
- **WHEN** não existe `gba_bios.bin` em `/storage/roms/bios` e o usuário abre um jogo de GBA
- **THEN** o gpSP inicia o jogo com a BIOS interna do core

### Requirement: Presença dos shaders de remasterização do GBA
A imagem gerada SHALL incluir os arquivos `gba-modern-remaster.glsl` e `gba-modern-remaster.glslp` em `/usr/share/common-shaders/gba/`, na partição SYSTEM, que é a camada de baixo do overlay `/tmp/shaders`.

#### Scenario: Arquivos no SYSTEM
- **WHEN** o SYSTEM da imagem gerada é inspecionado
- **THEN** `usr/share/common-shaders/gba/gba-modern-remaster.glsl` e `.glslp` estão presentes com permissão `0644` e dono `0:0`

#### Scenario: Atualização com --keep-storage
- **WHEN** o cartão é gravado com `--keep-storage`
- **THEN** o shader fica disponível em `/tmp/shaders/gba/`, porque vem do SYSTEM e não da p8

#### Scenario: Sintaxe do preset de shader
- **WHEN** o arquivo `gba-modern-remaster.glslp` é lido
- **THEN** ele define `shaders = "1"` e aponta para `shader0 = "gba-modern-remaster.glsl"` com `filter_linear0 = "true"`

### Requirement: Shader do GBA ligado por padrão, com chave para desligar
O shader `gba-modern-remaster` SHALL vir ligado por padrão nos jogos de GBA, em qualquer core de GBA da imagem (gpSP, mGBA, VBA-M e VBA Next), pela chave `gba.shaderset` do `emuelec.conf` (a mesma que a opção "SHADER SET" do EmulationStation grava) e por um preset automático do RetroArch (`<core>/<core>.glslp` nas pastas em que o RetroArch o procura), que o sistema cria no boot e que apontam para o shader da partição SYSTEM. O sistema SHALL NOT sobrescrever uma chave `gba.shaderset` nem um preset que já existem, e SHALL registrar o que fez em um arquivo legível pelo PC na raiz da R36-ROMS. O usuário SHALL poder desligar o padrão criando o arquivo vazio `r36-gba-sem-shader` na raiz da partição R36-ROMS pelo PC, e a opção "SHADER SET" do EmulationStation SHALL continuar listando o shader.

#### Scenario: Padrão de fábrica
- **WHEN** o usuário abre um jogo de GBA sem ter escolhido shader no EmulationStation, depois de gravar a imagem e ligar o aparelho
- **THEN** o RetroArch abre o jogo com o shader `gba-modern-remaster` aplicado

#### Scenario: Cartão gravado com --keep-storage
- **WHEN** o cartão recebe só a partição SYSTEM, sem regravar a p8
- **THEN** a chave `gba.shaderset` e o preset do core de GBA são criados no boot seguinte, e o shader entra sem outro passo

#### Scenario: Escolha do usuário preservada
- **WHEN** `gba.shaderset` já existe no `emuelec.conf` (inclusive `none`) ou o preset de um core de GBA já existe, por exemplo salvo pelo usuário com outros valores
- **THEN** o boot não os altera

#### Scenario: Chave para desligar
- **WHEN** o usuário cria o arquivo `r36-gba-sem-shader` na raiz da R36-ROMS e liga o aparelho
- **THEN** a linha `gba.shaderset` e os presets criados pelo sistema são apagados (e só eles) e os jogos de GBA abrem sem shader, e eles não voltam enquanto o arquivo existir

#### Scenario: Escolha no EmulationStation
- **WHEN** o usuário escolhe `gba/gba-modern-remaster.glslp` em "SHADER SET" nas configurações avançadas do sistema GBA e abre um jogo
- **THEN** o RetroArch abre o jogo com o shader `gba-modern-remaster` aplicado

#### Scenario: Volta ao padrão
- **WHEN** o usuário troca o "SHADER SET" do GBA de volta para nenhum
- **THEN** os jogos seguintes de GBA continuam abrindo com o shader padrão, a menos que a chave `r36-gba-sem-shader` exista

### Requirement: Shader do GBA com cor de console, viva e sem estouro
O shader `gba-modern-remaster` SHALL dar à imagem uma cor viva de console, sem lavar e sem a cor do LCD do GBA original: mantém o vermelho e o azul, deixa mais vivos a pele, os amarelos e os pastéis sem clareá-los, e não desbota nem muda o matiz de nenhuma cor. É o perfil de referência da capability `retroarch-shaders`.

#### Scenario: Vermelho do Mario preservado
- **WHEN** a tela de título de *Mario Kart: Super Circuit* é capturada com o shader e sem ele em escala inteira, e os pixels vermelhos da captura sem shader (R>150, G<110, B<110) são comparados posição a posição
- **THEN** a saturação média desses pixels com o shader fica a menos de 0.04 abaixo da saturação sem shader, e o pico de vermelho fica a menos de 8 pontos (em 255) abaixo

#### Scenario: Vermelho puro preservado
- **WHEN** os pixels de vermelho puro (255, 40, 0) de *Super Mario Advance 3: Yoshi's Island* são comparados com e sem o shader
- **THEN** a saturação média com o shader fica a menos de 0.08 abaixo de 1.000

#### Scenario: Claros coloridos vivos
- **WHEN** os pixels claros e coloridos (luma acima de 0.6 e saturação acima de 0.25) da tela de título de *Mario Kart: Super Circuit* são comparados com e sem o shader
- **THEN** a saturação média deles com o shader fica igual ou acima da sem shader, e a dos tons médios coloridos (luma entre 0.2 e 0.5, saturação acima de 0.3) fica a menos de 0.04 abaixo

#### Scenario: Nenhuma cor desbota nem muda de matiz
- **WHEN** a cartela de cores da réplica (amarelos, laranja, vermelho, magenta, verdes, ciano, céus, azuis, roxo, lilás, rosa, peles, marrom, cinza e branco) é renderizada com os valores padrão e `LCD GRID` em 0
- **THEN** a saturação de nenhuma cor cai mais de 0.05, o matiz de nenhuma cor muda mais de 2 graus, e a luma de nenhuma cor com canal máximo de 245 ou mais (em 255) sobe mais de 0.02

#### Scenario: Pele e azul
- **WHEN** a pele do Mario (248, 184, 136) e o azul puro (0, 0, 255) da cartela são comparados com e sem o shader
- **THEN** a saturação da pele sobe pelo menos 0.08, e o canal azul do azul puro fica a menos de 3 pontos (em 255) abaixo do original

#### Scenario: Parâmetros expostos
- **WHEN** o usuário abre o menu de parâmetros do shader no RetroArch
- **THEN** ele encontra exatamente estes oito parâmetros, com estes nomes no menu e estes valores padrão, e nenhum outro:
  - `VIBRANCE` = 0.45
  - `SATURATION` = 1.10
  - `HIGHLIGHT ROLLOFF` = 0.35
  - `S-CURVE Contrast` = 0.28
  - `HIGHLIGHT SHOULDER` = 0.05
  - `PIXEL SOFTNESS` = 0.15
  - `LCD GRID (0=Off)` = 0.10
  - `BRIGHTNESS` = 0.00

### Requirement: Shader do GBA com filtro de pixel nítido e leve
O shader `gba-modern-remaster` SHALL suavizar as bordas dos pixels em qualquer escala de saída, inclusive não inteira, sem borrar a imagem, e SHALL ser leve o bastante para o Mali-400 do A33: um passe, uma leitura de textura por pixel, sem `pow` e sem precisão `highp` no fragment shader.

#### Scenario: Nitidez mantida
- **WHEN** a nitidez de borda (gradiente horizontal médio do canal verde) da tela de título de *Mario Kart: Super Circuit* é medida com e sem o shader, em escala inteira e com `LCD GRID` em 0
- **THEN** a nitidez com o shader é igual ou maior que 97% da sem shader

#### Scenario: Escala não inteira
- **WHEN** o shader é usado no R36S, com tela 640x480, e o jogo é visto em escala de 2,67x
- **THEN** as bordas dos pixels aparecem suavizadas em cerca de um pixel de saída, sem a cintilação do vizinho mais próximo e sem o borrão do bilinear puro

#### Scenario: Restrições de custo
- **WHEN** o arquivo `gba-modern-remaster.glsl` é inspecionado
- **THEN** ele declara um único passe no `.glslp`, não chama `pow`, e não usa precisão `highp` fora de um bloco `GL_FRAGMENT_PRECISION_HIGH`

#### Scenario: Claros sem estourar
- **WHEN** os pixels claros (luma acima de 0.7) de *Mario Kart: Super Circuit* são comparados com e sem o shader, com os valores padrão
- **THEN** nenhum pixel que estava abaixo de 245 (em 255) no canal máximo chega a 255 com o shader, de modo que branco, amarelo e verde não estouram

### Requirement: Shader do GBA com efeito LCD leve e estável
O shader `gba-modern-remaster` SHALL, com `LCD GRID` acima de 0, escurecer de forma bem sutil a borda de cada pixel do jogo, para dar a aparência de uma tela de console. A grade SHALL se manter em escala inteira e não inteira, SHALL NOT acrescentar leitura de textura, passe, `pow` nem `highp`, e SHALL NOT fazer cores claras estourarem.

#### Scenario: Grade presente e leve
- **WHEN** o shader roda com os valores padrão em 640x427 (R36S) e em 480x320 sobre a tela de título de *Mario Kart: Super Circuit*, e sobre uma cena plana de luma 0.6 com a cor e a curva neutras
- **THEN** a luma média da tela de título fica entre 2% e 6% abaixo da sem shader, e na cena plana o menor valor fica entre 75% e 92% do maior (a grade existe e é sutil)

#### Scenario: Grade a cada pixel do jogo
- **WHEN** a cena plana é renderizada em 480x320 (escala 2x) e em 640x427 (escala 2.67x) com os valores padrão
- **THEN** entre 40% e 60% das colunas e das linhas de saída ficam abaixo de 98% do pico, ou seja, todo pixel do jogo tem a sua borda escura, sem trechos sem grade

#### Scenario: Grade desligável
- **WHEN** `LCD GRID` é posto em 0
- **THEN** o menor e o maior valor da cena plana são iguais, e o resultado é o mesmo do shader sem efeito LCD

#### Scenario: Claros e cores preservados com o LCD ligado
- **WHEN** a tela de título de *Mario Kart: Super Circuit* e a de *Super Mario Advance 3: Yoshi's Island* são renderizadas com os valores padrão
- **THEN** nenhum pixel que estava abaixo de 245 (em 255) no canal máximo chega a 255

#### Scenario: Precisão mediump
- **WHEN** o shader é emulado com os pontos críticos arredondados para meia precisão em 640x427
- **THEN** a diferença para a versão em precisão cheia tem PSNR de pelo menos 30 dB nas telas de título medidas
