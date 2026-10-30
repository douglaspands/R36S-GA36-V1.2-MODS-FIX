# Design

## Context

Ver `proposal.md` para a motivação. Fatos da base e do aparelho que moldam o desenho:

- **Resolução e escala no R36S:** Game Boy (`gb`) e Game Boy Color (`gbc`) têm resolução nativa de **160x144** (proporção 10:9). Na tela de 640x480 do R36S, a imagem ocupa **533x480** (escala fracionária de **3,333x**, `px = 160 / 533 = 0.300`).
- **GPU Mali-400 MP2 (Allwinner A33):** OpenGL ES 2.0, GLSL ES 1.00, precisão `mediump` (fp16) no fragment shader. A feature antiga `51-gameboy-fiel` usava `gameboy.glslp` de 5 passadas em resolução de tela mais overlay PNG 640x480, o que derrubou a taxa de quadros abaixo de 60 fps. O perfil de referência `gba-modern-remaster` provou que 1 passe, 1 leitura de textura (`COMPAT_TEXTURE`), sem `pow()` e sem laços mantém 60 fps constantes.
- **Cores compartilhados entre `gb`, `gbc` e `gba`:** no `es_systems.cfg`, tanto `gb` quanto `gbc` usam `gambatte` como padrão e listam `gearboy`, `sameboy`, `tgbdual`, `mgba`, `vbam` e `vba_next` (nomes de pasta no RetroArch: `Gambatte`, `Gearboy`, `SameBoy`, `TGB Dual`, `mGBA`, `VBA-M`, `VBA Next`). Os três últimos também atendem o `gba`.
- **Comportamento do Gambatte:** por padrão, o Gambatte pode aplicar `gambatte_gbc_color_correction` (que lava e amarronza as cores do GBC antes do shader) e `gambatte_gb_colorization` no GB. Com `global_core_options = "false"` e `game_specific_options = "true"`, o RetroArch lê opções por pasta de conteúdo em `<rgui_config_directory>/Gambatte/gb.opt` e `gbc.opt` (desde que `rgui_config_directory` aponte para `~/.config/retroarch/config`, já garantido pela feature `56-retroarch-ajustes`).

## Goals / Non-Goals

**Goals:**
- Game Boy Clássico (`gb`) com visual autêntico de console original DMG-01 (verde-oliva e matriz de pontos), mas com **alta clareza e separação entre os 4 tons** (`Delta Luma >= 0.20` entre tons vizinhos) e nitidez `sharp-bilinear`.
- Game Boy Color (`gbc`) com a mesma experiência do `gba-modern-remaster`: cores vivas próximas às de console (SNES), sem lavar amarelos/peles, sem estourar claros, com `sharp-bilinear` e grade LCD sutil.
- Custo mínimo na Mali-400: 1 passe, 1 leitura de textura, `mediump`, sem `pow()`.
- Ativação por padrão no boot para `gb` e `gbc` sem conflito entre si nem com o `gba`, funcionando com `--keep-storage`.
- Validação numérica e visual em `var/exemplos-gb-gbc/` usando capturas reais geradas com `~/AppImages/retroarch.appimage` e ROMs de `/mnt/backup/PC/R36S/roms/{gb,gbc}`.

**Non-Goals:**
- Molduras (bezels/overlays PNG) ou alteração do viewport do RetroArch.
- Recompilar o core `gambatte`.
- Shaders de múltiplas passadas ou efeitos de ghosting temporal por framebuffer.
- Os sistemas `gbh` e `gbch` (hacks de GB e GBC, em `features/53-cores-a33/.../es_systems.cfg`) ficam **sem shader**: o serviço só liga `gb` e `gbc`, e os presets por pasta de conteúdo são `gb.glslp` e `gbc.glslp`, que não valem para `roms/gbh` nem `roms/gbch`.

## Decisions

### Decisão 1: `gb-modern-dmg` — Curva de 4 tons DMG de Alta Clareza + Grade Dot-Matrix Reflexiva

Na paleta DMG tradicional (`#9bbc0f`, `#8bac0f`, `#306230`, `#0f380f`), o Tom 3 (fundo desligado, luma 0.68) e o Tom 2 (cinza claro, luma 0.60) têm apenas 0.08 de diferença de luminância, fazendo nuvens, pisos e detalhes claros sumirem no fundo, enquanto a tela inteira parece escura.

O shader `gb-modern-dmg.glsl` resolve isso em 4 etapas no mesmo passe:

1. **Sharp-bilinear adaptativo (`px = InputSize.x / OutputSize.x`):**
   Mesma equação do `gba-modern-remaster`, com `width = max(mix(px, 1.0, SOFTNESS), 0.0001)` e uma única leitura `COMPAT_TEXTURE`. Em 533x480 (`px = 0.30`), a transição entre pixels dura ~1 pixel da tela. `SOFTNESS` é 0.05 (e não 0.15 do GBA): os jogos de GB/GBC usam muito pontilhado de 1 pixel, e com 0.10 ou mais a nitidez em 2x cai abaixo de 97% na réplica (Pokémon Red 94,5% com 0.12). A spec mede a nitidez em **2x** (320x288). Em 3,33x (533x480) o vizinho mais próximo tem bordas de 3 e 4 pixels de saída e a nitidez do *Pokémon Red* dá 94,6% (95,2% mesmo com `SOFTNESS` 0, 97,6% no *Zelda* e 99,0% no *Mario Land 2*): o `SOFTNESS` não a leva a 97%, então a réplica só imprime o número de 3,33x, sem afirmá-lo.
2. **Luminância normalizada e curva de separação de tons (`TONE_SEP` e `CONTRAST`):**
   - Extrai a luminância `L = dot(c, vec3(0.2126, 0.7152, 0.0722))` (funciona mesmo se um core enviar cinza ou paleta levemente colorida).
   - Aplica a curva em S do perfil de referência (`L + CONTRAST * 2L(1-L)(L-0.35)`, pivô 0.35, o mesmo significado do GBA).
   - Divide `L` em três trechos (0-1/3, 1/3-2/3, 2/3-1) com um peso por trecho, `w = clamp(3L - (0, 1, 2), 0, 1)`, e puxa cada peso para as pontas com `w = mix(w, smoothstep, TONE_SEP)`: um nível perto de 1/3 ou 2/3 (os cinzas 82/173 do mGBA, por exemplo) cai na âncora.
3. **Mapeamento nos 4 pontos da paleta High-Clarity DMG-01 (`WARMTH`):**
   `c = T0 + (T1-T0) w.x + (T2-T1) w.y + (T3-T2) w.z`, sem laço nem tabela, entre 4 âncoras verde-oliva (luma Rec. 709 medida na réplica):
   - **T0 (Preto / Tinta 100% acesa):** verde-pinho profundo `rgb(20, 36, 12)` (`L ≈ 0.12`)
   - **T1 (Cinza escuro):** verde-musgo médio-escuro `rgb(56, 104, 44)` (`L ≈ 0.35`)
   - **T2 (Cinza claro):** verde-oliva médio-claro `rgb(136, 176, 68)` (`L ≈ 0.63`)
   - **T3 (Fundo LCD desligado):** verde-oliva claro iluminado `rgb(216, 234, 148)` (`L ≈ 0.88`)
   Com os padrões e a grade em 0, os 4 níveis saem com `L1 - L0 ≈ 0.23`, `L2 - L1 ≈ 0.29` e `L3 - L2 ≈ 0.24` (todas >= 0.20, mais de 3x a separação T2–T3 do DMG antigo), com `G > R > B` nos 4 tons (o T0 do rascunho, `rgb(14, 34, 20)`, tinha azul maior que vermelho). `WARMTH` soma `(WARMTH - 0.5) * (0.10, 0, -0.10) * G`: mais vermelho e menos azul, sem inverter a ordem dos canais.
4. **Grade Dot-Matrix reflexiva (substrato verde-oliva no vão entre pixels):**
   - No DMG-01 real, o vão entre dois pixels escuros não é uma máscara preta: é o próprio substrato reflexivo verde-oliva da tela, com leve sombra de relevo.
   - Usando a mesma cobertura analítica por caixa (`gap = min(px, 0.3)`, `cover` em X e Y), definimos a fração de grade `g = 1.0 - (1.0 - cover.x) * (1.0 - cover.y)` e o tom do substrato na lacuna `T3 * 0.55`, com `c = mix(c, T3 * 0.55, LCD_GRID * g)`.
   - Com `LCD_GRID` 0.22, a lacuna entre pixels T0 sobe de luma 0.12 para ~0.20 (o quadradinho escuro ganha a malha verde-oliva) e o fundo T3 desce no máximo para ~90% do pico (a spec pede 82% a 96%). O rascunho usava `T3 * 0.88`, que dá só ~2,6% de sombra no fundo e não cumpre o cenário.
   - *Alternativa descartada:* grade multiplicativa preta (`c *= lit.x * lit.y`) no GB Clássico — risca o fundo verde-claro de preto e transforma blocos escuros em manchas chapadas sem pontinhos.

| Identificador | Nome no menu | Faixa | Passo | Padrão GB |
|---|---|---|---|---|
| `TONE_SEP` | `TONE SEPARATION` | 0.0 a 1.0 | 0.05 | 0.50 |
| `CONTRAST` | `S-CURVE Contrast` | 0.0 a 1.0 | 0.05 | 0.20 |
| `WARMTH` | `OLIVE WARMTH` | 0.0 a 1.0 | 0.05 | 0.50 |
| `SOFTNESS` | `PIXEL SOFTNESS` | 0.0 a 1.0 | 0.05 | 0.05 |
| `LCD_GRID` | `DOT MATRIX GRID (0=Off)` | 0.0 a 1.0 | 0.05 | 0.22 |
| `BRIGHTNESS` | `BRIGHTNESS` | -0.30 a 0.30 | 0.01 | 0.00 |

### Decisão 2: `gbc-modern-remaster` — Pipeline de Cor Viva estilo SNES em 533x480

O GBC usa o mesmo pipeline matemático de 6 etapas do `gba-modern-remaster.glsl` (sharp-bilinear, luma/sat Rec. 709, ganho de croma com `VIBRANCE` que some perto do cinza e `ROLLOFF` nos claros ancorado em `mix(L, mx, hs)`, curva em S + ombro preservando cores saturadas e teto, proteção de clip em direção à luma, e grade LCD sutil), recalibrado na réplica em **533x480 (3,33x)** sobre capturas reais de GBC (*Super Mario Bros. Deluxe*, *Zelda: Link's Awakening DX*, *Donkey Kong Country*).
- **Por quê:** os jogos de GBC (especialmente ports e sequências de SNES como *Super Mario Bros. Deluxe*, *DKC* e *Zelda DX*) têm paletas RGB555 desenhadas com cores vivas. Quando a correção lavada do Gambatte é desligada, o pipeline do `gba-modern-remaster` entrega exatamente o pop de SNES sem estourar amarelos, peles ou céus claros.
- **Padrões remedidos:** o corpo do `main()` é o do GBA, com duas diferenças medidas na réplica: `SOFTNESS` 0.05 (com 0.15, a nitidez em 2x fica em 94% no *Zelda DX* e no *DKC*) e o teto `min(1, mx + 0.035)` em vez de `mx + 0.05` (com 0.05, cores com canal máximo 243-244 chegavam a 255 no *Super Mario Bros. Deluxe*). Os outros padrões (`VIBRANCE` 0.45, `SATURATION` 1.10, `ROLLOFF` 0.35, `CONTRAST` 0.28, `HIGHLIGHT` 0.05, `LCD_GRID` 0.10) passam nos cenários sem mudança. `tests/test_shaders_gb_gbc.py` confere que o `main()` só difere do GBA no teto.
- **Capturas:** o PC não tem o core Gambatte; as capturas de referência saíram do mGBA (também listado para `gb`/`gbc`) com modelo fixo, paleta `Grayscale` e sem correção de cor (ver `verificacao/LEIA-ME.md`).

### Decisão 3: Presets e `.opt` por pasta de conteúdo (`gb` e `gbc`)

Como `gb` e `gbc` dividem os mesmos cores (`Gambatte`, `Gearboy`, `SameBoy`, `TGB Dual`, `mGBA`, `VBA-M`, `VBA Next`) e os três últimos também rodam `gba`:
- O serviço `r36-shader-gb-gbc-prepara` cria presets automáticos **por pasta de conteúdo**:
  - `/storage/.config/retroarch/config/<Core>/gb.glslp` e `/storage/.config/retroarch/<Core>/gb.glslp` -> `#reference "/usr/share/common-shaders/gb/gb-modern-dmg.glslp"`
  - `/storage/.config/retroarch/config/<Core>/gbc.glslp` e `/storage/.config/retroarch/<Core>/gbc.glslp` -> `#reference "/usr/share/common-shaders/gbc/gbc-modern-remaster.glslp"`
- No RetroArch 1.17, a busca de preset automático tenta **Jogo -> Pasta do conteúdo (`gb` ou `gbc`) -> Core (`<Core>.glslp`)**. Assim:
  - ROMs em `/storage/roms/gb` carregam `<Core>/gb.glslp`;
  - ROMs em `/storage/roms/gbc` carregam `<Core>/gbc.glslp`;
  - ROMs em `/storage/roms/gba` continuam carregando `<Core>/<Core>.glslp` (da feature `54-shaders-gba`).
- Além disso, o serviço grava `gb.shaderset=gb/gb-modern-dmg.glslp` e `gbc.shaderset=gbc/gbc-modern-remaster.glslp` no `emuelec.conf` (se não existirem), que o `shaderset-aplica` (feature 56) entrega via `--set-shader` e `video_shader_enable = "true"`.
- Para o Gambatte, o serviço garante em `/storage/.config/retroarch/config/Gambatte/gb.opt` a linha `gambatte_gb_colorization = "disabled"` e em `gbc.opt` a linha `gambatte_gbc_color_correction = "disabled"` (somente se a chave não existir no arquivo).
- *Alternativa descartada:* preset por core (`Gambatte/Gambatte.glslp`) — impediria ter shaders diferentes para GB e GBC e colidiria com o GBA no `mGBA`.

### Decisão 4: Feature `55-shaders-gb-gbc` única para a família Game Boy (8-bit)

Os dois shaders e o serviço `r36-shader-gb-gbc-prepara.service` ficam juntos em `features/55-shaders-gb-gbc/` (`order = 55`, logo após `54-shaders-gba` e antes de `56-retroarch-ajustes`), com chaves independentes na p1 (`r36-gb-sem-shader` e `r36-gbc-sem-shader`) e log único `r36-shader-gb-gbc.log` condicionado à chave `r36-diagnostico`.
- **Por quê:** `gb` e `gbc` compartilham a mesma lista de 7 cores e a mesma rotina de atualização na p8 e bind de `/tmp/shaders`; um único serviço oneshot no boot evita trabalho duplicado e condição de corrida nos diretórios `<Core>/`.

## Risks / Trade-offs

- **[Risco] Jogos de GB abertos com paleta colorida se o usuário usar outro core que colore por padrão** → *Mitigação:* o `gb-modern-dmg.glsl` calcula `L = dot(c, W709)` no início e mapeia `L` para a paleta DMG verde-oliva, então qualquer entrada (cinza ou colorida) sai nos 4 tons verde-oliva com separação garantida.
- **[Risco] Precisão `mediump` (fp16) na Mali-400 em 533x480** → *Mitigação:* `TextureSize` é 160x144 (menor que 240x160 do GBA, logo com ainda mais precisão fracionária em fp16). Medido na réplica com `fp16=True` (PSNR > 30 dB).
- **[Trade-off] ROMs de GB colocadas por engano na pasta `roms/gbc`** → Receberão o perfil do GBC, pois o EmuELEC e o RetroArch separam os dois sistemas pela pasta (`gb` vs `gbc`).
- **[Risco, não confirmado] Preset por pasta de conteúdo com ROM em `.zip`** → os `es_systems.cfg` de gb e gbc listam `.zip` e `.7z`, mas não se sabe se o core abre o arquivo direto ou se o RetroArch o extrai para um diretório temporário; se extrair e o 1.17 usar esse diretório como "pasta do conteúdo", o `<Core>/gb.glslp` não é achado. *Mitigação:* o `gb.shaderset`/`gbc.shaderset` faz o `shaderset-aplica` (feature 56) passar `--set-shader` com o mesmo shader, então o GB e o GBC continuam com o shader certo. Conferir no aparelho pela linha `Specific shader preset found at` do `emuelec.log`.
- **[Risco] GB/GBC em core que também roda GBA** (`mGBA`, `VBA-M`, `VBA Next`) → sem o preset por pasta (chave `r36-gb-sem-shader`, ou o caso do `.zip` acima), o RetroArch cai no `<Core>/<Core>.glslp` da feature 54 e o jogo de GB abre com o shader do GBA. Era o comportamento antes desta change; o core padrão (`gambatte`) não tem preset de core.
- **[Risco] `gb.opt`/`gbc.opt` por pasta substituem as opções globais do Gambatte** → com `global_core_options = "false"` e `game_specific_options = "true"` (feature 10), quando existe um `.opt` por pasta de conteúdo o RetroArch usa só ele para aquela pasta. *Mitigação:* ao criar um `gb.opt`/`gbc.opt` que falta, o serviço parte de uma cópia do `Gambatte.opt` da p8 (se existir), tira dela a linha da chave de cor (`gambatte_gb_colorization` ou `gambatte_gbc_color_correction`: o arquivo é novo e o shader precisa da cor crua) e grava a chave. Sem `Gambatte.opt`, o arquivo nasce só com a chave. Um `.opt` que já existe nunca é reescrito: só ganha a chave, se faltar.
- **[Limitação conhecida] `gb.opt`/`gbc.opt` antigos da feature 51** → um `gb.opt` com `gambatte_gb_colorization = "auto"` ou um `gbc.opt` com `gambatte_gbc_color_correction = "GBC only"` (deixados pela moldura antiga, com `--keep-storage`) já têm a chave, e o serviço nunca muda uma opção existente. O GB sai colorido pelo core (o shader leva à luma, então ainda vira verde-oliva, mas sem os 4 cinzas puros) e o GBC sai com a correção que lava a cor. *Ação do usuário:* apagar esses arquivos pelo PC (ver `docs-shaders-gb-gbc-r36s.md`); no boot seguinte o serviço os recria a partir do `Gambatte.opt`.
- **[Risco] Dois serviços escrevem no mesmo `emuelec.conf` e montam `/tmp/shaders`** → `r36-shader-gb-gbc-prepara.service` tem `After=r36-shader-gba-prepara.service`: os dois rodam em série, sem corrida no `emuelec.conf` nem bind duplo em `/tmp/shaders`. O do GBA só apaga `<Core>/<Core>.glslp` e presets que apontam para o shader do GBA; o do GB/GBC só `<Core>/gb.glslp` e `<Core>/gbc.glslp` com o próprio `#reference` (testado com os dois scripts no mesmo `R36_ROOT`).

## Migration Plan

1. Os shaders novos (`gb-modern-dmg` e `gbc-modern-remaster`) ficam **ligados por padrão no boot** (decisão do usuário, D5 da change `integra-limite-idioma-shaders-gb`); as pranchas em `var/exemplos-gb-gbc/` são apresentadas ao usuário depois dos testes, sem perguntar o padrão. Se ele mudar de ideia, a reversão (só pelo menu) é uma change pequena.
2. Gravar o `system` (`./flash.sh --device /dev/sdc --part system --build <ts>`): funciona mesmo com `--keep-storage`, pois o serviço `r36-shader-gb-gbc-prepara` atualiza a p8 no boot.
3. Para desligar um dos shaders sem regravar basta criar `r36-gb-sem-shader` ou `r36-gbc-sem-shader` na raiz da partição `R36-ROMS` (p1).

## Open Questions

- Nenhuma sobre o padrão (ligado). Fica para o aparelho: se o RetroArch 1.17 acha o preset por pasta de conteúdo (`<Core>/gb.glslp`) com ROM em `.zip` (ver Riscos).
