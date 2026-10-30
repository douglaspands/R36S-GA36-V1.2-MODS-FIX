# Design

## Context

Ver `proposal.md` para a motivação. Restrições de arquitetura e do hardware do R36S:

- **Tela e Resolução:** Painel LCD IPS de 3.5 polegadas, resolução nativa de **640x480** (4:3).
- **Resoluções Nativas dos Sistemas Alvo:**
  - Mega Drive: 320x224 (H40) ou 256x224 (H32). Em 640x480, a escala horizontal é exatamente 2.0x (em H40) e vertical fracionária de ~2.14x (480 / 224).
  - SNES / NES: 256x224 ou 256x240 (escala horizontal 2.5x, vertical 2.14x ou 2.0x).
  - Arcades (CPS1/2/3, Neo Geo): 384x224 ou 320x224.
- **GPU Mali-400 MP2 (Allwinner A33):**
  - Contexto `fbdev_mali`, OpenGL ES 2.0, GLSL ES 1.00.
  - Precisão `mediump` (fp16) no fragment shader.
  - Orçamento estrito: passes múltiplos (`shaders > 1`) ou laços dinâmicos derrubam a taxa de quadros abaixo de 60 fps.
- **Kernel sunxi 3.4.39 e Armazenamento:**
  - Sem overlayfs; `/usr/share/common-shaders` é copiado para `/storage/shaders` no primeiro boot com `rsync --ignore-existing`. O serviço de boot atualiza arquivos modificados no mesmo inode e monta `/tmp/shaders` por bind se necessário.
  - A partição p1 (`R36-ROMS`) armazena chaves de escape (`r36-tv-sem-shader`) e logs sob a chave `r36-diagnostico`.

## Goals / Non-Goals

**Goals:**
- **60 fps cravados na Mali-400** em resolução total de 640x480 em todos os sistemas atendidos.
- **Fusão de dither seletiva e autêntica:** transformar o quadriculado de dither do Mega Drive (água de Sonic, luz de Streets of Rage 2, fumaça) em transparência suave e limpa, exatamente como ocorria na largura de banda de croma das TVs analógicas.
- **Preservação de nitidez:** contornos de personagens, HUD, números e fontes de texto permanecem afiados sem o embaçamento de filtros bilineares comuns.
- **Visual PVM limpo e claro:** modulação suave de feixe vertical (~12% a 15% de contraste), mantendo a tela pequena de 3.5" clara e viva, sem moiré na escala vertical fracionária.
- **Cores vivas padrão remaster:** contraste rico e saturação balanceada sem desbotar amarelos e peles, e sem queimar claros.
- **Ativação padrão automática:** ligar o shader no boot para consoles de mesa e arcades sem sobrescrever customizações manuais do usuário.

**Non-Goals:**
- Curvatura geométrica de tubo CRT (efeito barril): reduz a área útil na tela de 3.5" e consome instruções preciosas na Mali-400.
- Máscaras de fósforo RGB (shadow mask / aperture grille): impossíveis de representar em 640 colunas sem criar aberrações cromáticas e moiré horizontal.
- Sistemas portáteis (GBA, GB, GBC): continuam com seus shaders dedicados (`gba-modern-remaster`, `gb-modern-dmg`, `gbc-modern-remaster`).

## Decisions

### Decisão 1: Dither Blending Seletivo Horizontal em 1 Passe (3 taps na mesma scanline)

No sinal analógico de TV (NTSC/PAL composto), a largura de banda estreita causava sangramento de cor exclusivamente na dimensão horizontal (ao longo da scanline). O dither do Mega Drive foi desenhado para essa característica física.

O shader implementa a detecção analítica de dither com 3 amostras horizontais:
- $L = \text{COMPAT\_TEXTURE}(uv - (\Delta x, 0))$
- $C = \text{COMPAT\_TEXTURE}(uv)$
- $R = \text{COMPAT\_TEXTURE}(uv + (\Delta x, 0))$

Onde $\Delta x = 1.0 / \text{TextureSize.x}$.
1. **Diferença entre extremos:** $\Delta_{LR} = |L - R|$.
2. **Alternância do centro:** $\Delta_C = |C - 0.5 \cdot (L + R)|$.
3. **Métrica de dither:** quando $\Delta_{LR}$ é pequeno (pixels vizinhos repetem a mesma cor) e $\Delta_C$ é significativo (o centro alterna bruscamente), temos um padrão $A-B-A$ (xadrez ou barra vertical).
   $$w_{\text{dither}} = \text{clamp}\left(\frac{\Delta_C - \Delta_{LR}}{\Delta_C + 0.001}, 0.0, 1.0\right) \cdot \text{DITHER\_BLEND}$$
4. **Mistura seletiva:** $\text{Cor} = \text{mix}(C, \; 0.5 \cdot C + 0.25 \cdot (L + R), \; w_{\text{dither}})$.

- **Por quê:** funde 100% da água do Sonic e luzes de Streets of Rage, enquanto em uma borda sólida ($L \neq R$ e $\Delta_{LR}$ é alto) $w_{\text{dither}}$ resulta em 0, mantendo o contorno intacto e nítido.
- **Desempenho no Mali-400:** As três leituras residem na mesma linha horizontal de texels, garantindo 100% de acerto no cache L1 de textura da GPU sem pressão no barramento de memória DDR.
- **Alternativas descartadas:**
  - *Filtro bilinear genérico:* borra textos, HUD e contornos de personagens.
  - *Shaders multipasse (`mdapt`, `gdapt`):* 3 a 5 passadas com overhead de framebuffer que reduzem a taxa de quadros para menos de 30 fps na Mali-400.

### Decisão 2: Modulação de Feixe CRT para Telas Compactas (Perfil PVM Suave)

Em 640x480, jogos de 224 linhas sofrem escala vertical de ~2.14x. Scanlines pretas duras convencionais cortam metade da iluminação da tela e produzem cintilação/moiré desagradável.

O shader calcula a modulação de feixe analítica contínua:
- Posição vertical relativa na linha do jogo: $y_{\text{pos}} = \text{fract}(\text{TEX0.y} \cdot \text{TextureSize.y}) - 0.5$.
- Modulação cosseno centrada no núcleo da linha:
  $$\text{beam} = 1.0 - \text{TV\_SCANLINES} \cdot \cos^2(\pi \cdot y_{\text{pos}})$$
- Com `TV_SCANLINES = 0.12` (padrão), o centro da linha emite 100% de luz e a borda suave atinge ~88%, reproduzindo a separação analógica de linhas de um monitor Sony PVM profissional sem escurecer a imagem e sem efeito moiré.
- Uma ligeira compensação de ganho no parâmetro `BRIGHTNESS` (ou integrada ao pipeline) recupera os ~3% de luminância atenuada.

### Decisão 3: Pipeline de Cores Remaster Moderno

O shader incorpora o pipeline de preservação de matiz calibrado nos shaders de Game Boy:
1. **Sharp-bilinear:** transição de ~1 pixel de tela entre vizinhos verticais.
2. **Luma Rec. 709:** $L = \text{dot}(c, [0.2126, 0.7152, 0.0722])$.
3. **Vibrance seletiva:** realça tons apagados e fundos sem estourar cores primárias puras.
4. **Curva em S na luma (pivô 0.35):** contraste aprofundado sem distorcer matizes.
5. **Highlight roll-off e proteção de clip:** transições de degradê e áreas de alta luma não sofrem ceifamento de canal isolado.

### Decisão 4: Parâmetros Padronizados no RetroArch

| Identificador | Nome no menu | Faixa | Passo | Padrão | Finalidade |
|---|---|---|---|---|---|
| `DITHER_BLEND` | `DITHER BLEND (0=Off)` | 0.0 a 1.0 | 0.05 | 0.75 | Fusão de transparências de dither |
| `TV_SCANLINES` | `TV SCANLINES (0=Off)` | 0.0 a 0.50 | 0.02 | 0.12 | Modulação de feixe CRT PVM |
| `PIXEL_SOFTNESS` | `PIXEL SOFTNESS` | 0.0 a 1.0 | 0.05 | 0.10 | Largura de transição dos pixels |
| `VIBRANCE` | `VIBRANCE` | 0.0 a 1.0 | 0.05 | 0.40 | Reforço seletivo de saturação |
| `SATURATION` | `SATURATION` | 0.5 a 1.3 | 0.01 | 1.08 | Saturação global de console |
| `CONTRAST` | `S-CURVE Contrast` | 0.0 a 1.0 | 0.05 | 0.25 | Contraste na luma (pivô 0.35) |
| `ROLLOFF` | `HIGHLIGHT ROLLOFF` | 0.0 a 1.0 | 0.05 | 0.35 | Proteção de saturação nos claros |
| `BRIGHTNESS` | `BRIGHTNESS` | -0.3 a 0.3 | 0.01 | 0.00 | Ajuste fino de ganho de luz |

### Decisão 5: Feature `57-shaders-tv` e Ordem de Boot

- Nova feature `features/57-shaders-tv/` (`order = 57`, após `55-shaders-gb-gbc` e antes de `58-retroarch-ajustes`).
- Unit `r36-shader-tv-prepara.service`:
  - `Before=emustation.service`
  - `After=r36-shader-gb-gbc-prepara.service`
  - `After=tmp-shaders.mount`
  - `WantedBy=emuelec.target`
- Gerencia os sistemas: `megadrive`, `genesis`, `snes`, `nes`, `mastersystem`, `pce`, `psx`, `mame`, `fbneo`, `cps1`, `cps2`, `cps3`, `neogeo`.
- Cria referências `#reference "/usr/share/common-shaders/tv/tv-modern-remaster.glslp"` para os cores de cada sistema em `/storage/.config/retroarch/config/<Core>/<Core>.glslp` caso não existam.
- Se o arquivo `r36-tv-sem-shader` estiver presente em `/storage/roms`, desfaz os presets e o `shaderset` criados pelo serviço.

## Risks / Trade-offs

- **[Risco] Textos finos de 1 pixel em alguns jogos sofrendo blend de dither indesejado:**
  - *Mitigação:* A fórmula de dither blend compara $\Delta_C$ e $\Delta_{LR}$. Linhas verticais isoladas com fundo assimétrico não ativam a condição $A-B-A$. Caso o jogador queira desligar ou atenuar, o parâmetro `DITHER_BLEND` no menu permite reduzir para 0.50 ou 0.0 a qualquer momento.
- **[Risco] Queda de desempenho com 3 amostras na Mali-400:**
  - *Mitigação:* As amostras são na mesma linha horizontal de textura (cache L1 hit). O fragment shader é validado com medição de taxa de quadros e na réplica em Python para garantir que nenhuma operação proibida (`pow`, laços) seja introduzida.
- **[Risco] Conflito com cores compartilhados (ex: mGBA roda GBA e GB):**
  - *Mitigação:* O serviço de TV só atua nos cores de consoles de mesa e arcade (ex: `Genesis Plus GX`, `PicoDrive`, `Snes9x`, `FCEUmm`, `FBNeo`, etc.), não interferindo nas pastas de cores portáteis já gerenciadas pelas features 54 e 55.

## Migration Plan

1. A imagem é construída com a feature `57-shaders-tv`.
2. No primeiro boot, `r36-shader-tv-prepara.service` sincroniza os arquivos para `/storage/shaders/tv/` e cria as entradas nos sistemas de mesa e arcade.
3. Usuários que desejarem desativar podem colocar o arquivo vazio `r36-tv-sem-shader` na raiz do cartão SD pelo PC.
