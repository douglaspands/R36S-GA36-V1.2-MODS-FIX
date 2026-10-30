# gb-gbc-emulation Specification

## Purpose
Definir os shaders de modernização do Game Boy Clássico (`gb-modern-dmg`) e do Game Boy Color (`gbc-modern-remaster`), sua separação de tons e fidelidade de cores, a configuração por pasta de conteúdo do Gambatte, a ativação automática no boot e as chaves para desligar no R36S (Allwinner A33 / Mali-400).

## Requirements

### Requirement: Presença dos shaders do GB Clássico e do GBC no SYSTEM
A imagem gerada SHALL incluir `gb-modern-dmg.glsl` e `gb-modern-dmg.glslp` em `/usr/share/common-shaders/gb/`, e `gbc-modern-remaster.glsl` e `gbc-modern-remaster.glslp` em `/usr/share/common-shaders/gbc/`, na partição SYSTEM, com dono `0:0` e permissão `0644`.

#### Scenario: Arquivos presentes no SYSTEM
- **WHEN** o SYSTEM da imagem gerada é inspecionado
- **THEN** os quatro arquivos existem em `usr/share/common-shaders/gb/` e `usr/share/common-shaders/gbc/` com permissão `0644` e dono `0:0`

#### Scenario: Sintaxe dos presets
- **WHEN** `gb-modern-dmg.glslp` e `gbc-modern-remaster.glslp` são lidos
- **THEN** cada um declara `shaders = "1"`, `filter_linear0 = "true"`, `scale_type0 = "viewport"`, `scale0 = "1.0"` e aponta para o respectivo `.glsl`

### Requirement: Shaders do GB e do GBC ligados por padrão sem colisão entre sistemas
O serviço `r36-shader-gb-gbc-prepara.service` SHALL ligar `gb.shaderset=gb/gb-modern-dmg.glslp` e `gbc.shaderset=gbc/gbc-modern-remaster.glslp` no `emuelec.conf` e criar presets automáticos por pasta de conteúdo (`<Core>/gb.glslp` e `<Core>/gbc.glslp`) em `config/<Core>/` e na pasta do `retroarch.cfg` para `Gambatte`, `Gearboy`, `SameBoy`, `TGB Dual`, `mGBA`, `VBA-M` e `VBA Next`, sem sobrescrever escolhas existentes nem presets de `<Core>/<Core>.glslp`.

#### Scenario: Primeiro boot ativa GB e GBC separadamente
- **WHEN** o aparelho liga sem `gb.shaderset`, `gbc.shaderset` nem presets `gb.glslp` e `gbc.glslp`
- **THEN** o serviço grava as duas linhas no `emuelec.conf` e cria `<Core>/gb.glslp` e `<Core>/gbc.glslp` apontando para os shaders do SYSTEM, sem tocar em `mGBA/mGBA.glslp` do GBA

#### Scenario: Escolha do usuário preservada
- **WHEN** `gb.shaderset` ou `gbc.shaderset` já existe no `emuelec.conf` ou o preset `<Core>/gb.glslp` / `<Core>/gbc.glslp` já foi salvo pelo usuário
- **THEN** o serviço não altera a chave nem o preset existente

### Requirement: Chaves independentes para desligar o shader do GB e do GBC
O serviço SHALL obedecer aos arquivos vazios `r36-gb-sem-shader` e `r36-gbc-sem-shader` na raiz da R36-ROMS, removendo apenas a linha do `emuelec.conf` e os presets `<Core>/gb.glslp` ou `<Core>/gbc.glslp` que o próprio serviço criou para o respectivo sistema.

#### Scenario: Desligar apenas o GB Clássico
- **WHEN** o usuário cria `r36-gb-sem-shader` na raiz da R36-ROMS e religa o aparelho
- **THEN** `gb.shaderset` e os presets `<Core>/gb.glslp` criados pelo serviço são removidos, enquanto `gbc.shaderset` e `<Core>/gbc.glslp` continuam ativos

#### Scenario: Desligar apenas o GBC
- **WHEN** o usuário cria `r36-gbc-sem-shader` na raiz da R36-ROMS e religa o aparelho
- **THEN** `gbc.shaderset` e os presets `<Core>/gbc.glslp` criados pelo serviço são removidos, enquanto `gb.shaderset` e `<Core>/gb.glslp` continuam ativos

### Requirement: Opções de cor do Gambatte por pasta de conteúdo
O serviço SHALL garantir `gambatte_gb_colorization = "disabled"` em `/storage/.config/retroarch/config/Gambatte/gb.opt` e `gambatte_gbc_color_correction = "disabled"` em `/storage/.config/retroarch/config/Gambatte/gbc.opt` quando a respectiva chave não existir no arquivo, preservando qualquer valor já escolhido pelo usuário.

#### Scenario: GB entrega os 4 tons puros e GBC entrega RGB555 sem correção lavada
- **WHEN** o aparelho liga sem `gb.opt`, `gbc.opt` nem `Gambatte.opt` em `config/Gambatte/`
- **THEN** o serviço cria `gb.opt` com `gambatte_gb_colorization = "disabled"` e `gbc.opt` com `gambatte_gbc_color_correction = "disabled"`

#### Scenario: Limitação conhecida, .opt antigo da feature 51
- **WHEN** a p8 já tem um `gb.opt` com `gambatte_gb_colorization = "auto"` ou um `gbc.opt` com `gambatte_gbc_color_correction = "GBC only"`
- **THEN** o serviço mantém o valor (o GB sai colorido pelo core e o GBC com a correção que lava a cor), e a ação do usuário é apagar esses arquivos pelo PC, para o serviço recriá-los no boot seguinte

#### Scenario: Opção existente no Gambatte é preservada
- **WHEN** `gb.opt` ou `gbc.opt` já contém a chave configurada pelo usuário
- **THEN** o serviço mantém o valor existente e preserva as demais linhas do arquivo

### Requirement: Opções novas do Gambatte partem do arquivo global
Como o `.opt` por pasta de conteúdo substitui o `Gambatte.opt` global (`global_core_options = "false"` e `game_specific_options = "true"`), o serviço SHALL criar um `gb.opt` ou `gbc.opt` que falta a partir de uma cópia do `config/Gambatte/Gambatte.opt` da p8, se existir, sem a linha da chave de cor, e então gravar a chave. O serviço SHALL NOT reescrever um `.opt` que já existe, além de acrescentar a chave que falta.

#### Scenario: Opção nova herda as escolhas do Gambatte.opt global
- **WHEN** o aparelho liga sem `gb.opt` e `gbc.opt`, e o `Gambatte.opt` tem `gambatte_mix_frames = "mix"` e `gambatte_gb_colorization = "auto"`
- **THEN** o `gb.opt` novo tem `gambatte_mix_frames = "mix"` e uma única `gambatte_gb_colorization = "disabled"`, o `Gambatte.opt` não muda e um segundo boot não altera os `.opt`

### Requirement: Shader do GB Clássico com paleta DMG de alta clareza entre os 4 tons
O shader `gb-modern-dmg` SHALL converter a luminância dos 4 tons do Game Boy Clássico para uma paleta verde-oliva de console original DMG-01 modernizada, em que a diferença de luminância Rec. 709 entre qualquer par de tons vizinhos (T0 escuro, T1 médio-escuro, T2 médio-claro e T3 fundo desligado) seja de pelo menos 0.20 com a grade em 0.

#### Scenario: Quatro tons claramente separados
- **WHEN** uma imagem contendo os 4 níveis do Game Boy (0/255, 85/255, 170/255 e 255/255) é renderizada pelo `gb-modern-dmg` com os valores padrão e `LCD_GRID` em 0
- **THEN** as luminâncias resultantes `L0 < L1 < L2 < L3` cumprem `L1 - L0 >= 0.20`, `L2 - L1 >= 0.20` e `L3 - L2 >= 0.20`, o fundo `L3` fica acima de 0.82, o tom escuro `L0` fica abaixo de 0.14 e todos os 4 tons mantêm matiz verde-oliva (`G > R > B`)

#### Scenario: Parâmetros expostos no GB Clássico
- **WHEN** o usuário abre os parâmetros do `gb-modern-dmg` no RetroArch
- **THEN** ele encontra os parâmetros `TONE_SEP` ("TONE SEPARATION"), `CONTRAST` ("S-CURVE Contrast"), `WARMTH` ("OLIVE WARMTH"), `SOFTNESS` ("PIXEL SOFTNESS"), `LCD_GRID` ("DOT MATRIX GRID (0=Off)") e `BRIGHTNESS` ("BRIGHTNESS"), cada um com `#define` de reserva idêntico

### Requirement: Grade dot-matrix reflexiva e nitidez no GB Clássico
O shader `gb-modern-dmg` SHALL aplicar escala nítida `sharp-bilinear` e uma grade dot-matrix na borda de trás de cada pixel do jogo que aproxima a lacuna do tom do fundo reflexivo verde-oliva em áreas escuras e sombreia de leve o fundo claro, sem leitura extra de textura e sem `pow`.

#### Scenario: Nitidez de borda mantida em escala inteira (2x)
- **WHEN** a nitidez de borda é medida nas capturas de GB com os padrões e `LCD_GRID` em 0 em escala inteira (320x288, 2x)
- **THEN** a nitidez com o shader é de pelo menos 97% da do vizinho mais próximo; em 3,33x (533x480) a réplica só informa o número, sem afirmá-lo, porque o vizinho mais próximo tem bordas de 3 e 4 pixels de saída contra a transição de ~1 pixel do sharp-bilinear (*Pokémon Red* dá 94,6%, e 95,2% mesmo com `SOFTNESS` 0)

#### Scenario: Grade dot-matrix destaca pixels escuros sem riscar o fundo de preto
- **WHEN** o shader roda em 533x480 (escala 3,33x do R36S) com os padrões sobre blocos do tom escuro T0 e do fundo T3
- **THEN** a lacuna entre pixels T0 é mais clara que o centro do pixel T0 (revelando o substrato verde-oliva), e no fundo T3 o menor valor fica entre 82% e 96% do pico

### Requirement: Shader do GBC com cor viva estilo SNES, nitidez e efeito LCD sutil
O shader `gbc-modern-remaster` SHALL seguir o perfil de referência de cor (`VIBRANCE`, `SATURATION`, `ROLLOFF`, `CONTRAST`, `HIGHLIGHT`, `SOFTNESS`, `LCD_GRID`, `BRIGHTNESS`), entregando em 533x480 (escala 3,33x) cores vivas próximas às de SNES sem mudar matiz, sem desbotar e sem estourar claros.

#### Scenario: Cartela de cores e capturas de GBC sem desbotar nem estourar
- **WHEN** a cartela de 24 cores e as capturas de referência de GBC (*Super Mario Bros. Deluxe* e *The Legend of Zelda: Link's Awakening DX*) são renderizadas pelo `gbc-modern-remaster` com os padrões
- **THEN** nenhuma cor da cartela muda de matiz mais de 2 graus nem perde mais de 0.05 de saturação (com `LCD_GRID` em 0), a nitidez em 2x é de pelo menos 97% da do vizinho mais próximo, nenhum pixel abaixo de 245 (em 255) chega a 255 e o PSNR em meia precisão (`fp16`) em 533x480 fica acima de 30 dB
