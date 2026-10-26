# Design

## Context

O `gba-modern-remaster` atual (ver `proposal.md` - Why) é um passe único com matriz 3x3 em luz linear (`pow` 2,2 e 1/2,2), `smoothstep` de largura fixa (`PIXEL_SOFTNESS` 0.35) e quatro parâmetros que brigam entre si. O alvo é o Mali-400 MP2 do A33, que só tem `mediump` (fp16) no fragment shader. A instalação (feature `54-shaders-gba`, SYSTEM, `/usr/share/common-shaders/gba/`, desligado por padrão, escolhido no "SHADER SET") não muda; só muda o conteúdo do `.glsl`.

Esta design parte de um rascunho validado no PC (RetroArch Flatpak 1.22.2, core mGBA, janela 480x320). Os números abaixo vêm dessa medição; o rascunho e os scripts estavam no scratchpad da sessão de exploração e não fazem parte do repositório.

## Goals / Non-Goals

**Goals:**
- Vermelho do Mario sem perda de pico nem de saturação, e mais cor nos tons pouco saturados.
- Filtro nítido em escala não inteira (2,67x no R36S), com uma leitura de textura.
- Custo mínimo no Mali-400: um passe, sem `pow`, sem `highp`.

**Non-Goals:**
- Reproduzir a cor do LCD do GBA ou oferecer um modo "fiel".
- Efeitos de grade LCD, scanlines ou máscara de fósforo.
- ~~Ligar o shader por padrão~~ (revisto: o usuário pediu o shader ligado por padrão no GBA; ver Decisão 8).
- Medir tempo de quadro no Mali-400 (só no aparelho).

## Decisions

### Decisão 1: Operar em espaço gama, com operações que preservam o matiz
Tudo roda direto nos valores do jogo (espaço gama). Luma por Rec. 709, croma como diferença para a luma, e a curva de contraste vira um fator multiplicativo `L2 / L` aplicado aos três canais, que mantém a razão entre eles.
- **Por quê:** sem `pow`, sem linearização e estável em fp16. Escalar os canais por uma razão comum não gira o matiz.
- **Alternativa descartada:** matriz em luz linear (shader atual). Misturar G e B no vermelho é o que derruba a saturação, e o par de `pow` em fp16 dá banding nas sombras.

### Decisão 2: Pipeline de cor em cinco passos
1. **Sharp-bilinear** (ver Decisão 3).
2. **Luma e saturação por pixel:** `L = dot(c, 0.2126/0.7152/0.0722)`, `sat = (max - min) / max`.
3. **Vibrance:** `c = L + (c - L) * (1 + VIBRANCE * (1 - sat))`. O ganho cai à medida que a saturação sobe, então o vermelho já saturado quase não muda e os tons apagados ganham cor.
4. **Curva em S e ombro na luma, preservando matiz:** `L2 = L + CONTRAST * 2 * L * (1 - L) * (L - 0.35) + HIGHLIGHT * smoothstep(0.55, 1.0, L) * (1 - L) * 0.5`, e `c *= L2 / L`. O pivô em 0.35 deixa os médios do vermelho do Mario (L perto de 0.3) praticamente intactos; a curva aprofunda só as sombras e abre os realces, o "HDR" em SDR.
5. **Proteção de clip:** se algum canal passar do teto, a croma é reduzida em direção à luma até o canal máximo caber, em vez de cortar o canal. O teto é `min(1, max_original + 0.05)`, para a vibrance não empurrar o degradê do céu para 255.

Valores padrão e nomes no menu do RetroArch (o identificador no código é o da coluna da esquerda):

| Identificador | Nome no menu | Padrão |
|---|---|---|
| `VIBRANCE` | `VIBRANCE` | 0.45 |
| `SATURATION` | `SATURATION` | 1.10 |
| `ROLLOFF` | `HIGHLIGHT ROLLOFF` | 0.35 |
| `CONTRAST` | `S-CURVE Contrast` | 0.28 |
| `HIGHLIGHT` | `HIGHLIGHT SHOULDER` | 0.05 |
| `SOFTNESS` | `PIXEL SOFTNESS` | 0.15 |
| `LCD_GRID` | `LCD GRID (0=Off)` | 0.10 |
| `BRIGHTNESS` | `BRIGHTNESS` | 0.00 |
- **Alternativa descartada:** curva em S clássica `x*x*(3-2x)` com pivô em 0.5. Medido, ela baixou o pico do vermelho do Mario em 6% (210 para 197) porque escurece os médios.

### Decisão 3: Sharp-bilinear com largura de transição pela escala
`scale = OutputSize.x / InputSize.x`, `width = mix(1/scale, 1, SOFTNESS)`, e a fração do texel `f` vira `clamp((f - 0.5) / width + 0.5, 0, 1)`. A leitura usa `(floor(p) + 0.5 + f') / TextureSize`, com o filtro linear do hardware.
- **Por quê:** a transição dura cerca de um pixel de saída em qualquer escala, então bordas ficam nítidas em 2x e em 2,67x. Com `SOFTNESS` 1 vira bilinear puro. O custo é uma leitura de textura, e a coordenada calculada no fragment tem custo desprezível em 640x480.
- **Alternativas descartadas:** `smoothstep` de largura fixa (o atual; o resultado borrava, nitidez 12.40 contra 14.01); bicúbico ou Catmull-Rom (4 a 9 leituras, pesado e com halo); dois passes com pré-escala inteira (framebuffer extra e mais banda de memória no A33).

### Decisão 4: Reescrever o arquivo no lugar
O `.glsl` e o `.glslp` mantêm os nomes, e o `.glslp` não muda (um passe, `filter_linear0 = "true"`, `scale_type0 = "viewport"`). Assim a escolha `gba/gba-modern-remaster.glslp` que o usuário já fez no ES continua valendo e nada fora da feature precisa mudar. Os parâmetros antigos somem; quem tinha valores salvos para eles perde esses valores, o que aceito (shader opcional, sem preset automático).

### Decisão 5: Como validar
- **No PC (este repositório):** `tests/test_shaders_gba.py` confere cabeçalho, os quatro parâmetros, ausência de `pow(`, de `highp` fora de `GL_FRAGMENT_PRECISION_HIGH`, de `GBA_Matrix`/`CORRECTION_STRENGTH`, a leitura única de textura e que o preset continua de um passe.
- **Medição visual (manual, RetroArch Flatpak + mGBA):** o RetroArch ignora `--set-shader` e `video_shader` no modo de linha de comando; só carrega o preset pelo caminho de auto-shader. Aponte `rgui_config_directory` para uma pasta temporária com `mGBA/mGBA.glslp`, `auto_shaders_enable = "true"` e `video_gpu_screenshot = "true"`, rode `--max-frames=1200 --max-frames-ss` e compare as capturas com e sem shader pixel a pixel. O Mario Kart no frame 1200 (logo e personagens) é a cena de referência. A janela só abre em múltiplos inteiros do jogo, então 2,67x não se mede no PC.
- **No aparelho:** tela 640x480, olhar o logo e os personagens do Mario Kart e medir o tempo de quadro.

## Risks / Trade-offs

- **[Risco] Azul do céu pode chegar a 255 e achatar o degradê.** Medido: 39% dos pixels da tela da bandeira (Mario Kart, frame 500) saem a 255 vindo de abaixo de 240; visualmente o degradê segue liso. → *Mitigação:* o teto `+0.08` é uma constante e pode cair para `+0.05`; conferir no aparelho.
- **[Risco] Vibrance e curva em S podem estourar tons de pele.** → *Mitigação:* o ganho cai com a saturação e a proteção de clip reduz a croma; conferir Pokémon e Metroid no aparelho.
- **[Risco] fp16 no Mali-400.** Sem `pow` e sem `highp`, mas divisões por `L` perto de zero podem dar ruído nas sombras. → *Mitigação:* o rascunho usa `max(L, 0.001)`.
- **[Risco] Correção de cor dupla.** Se o core já aplicar correção de cor (o mGBA tem opção própria), o resultado desatura. → *Mitigação:* conferir a opção no `core-mgba-a33` (change em andamento); o gpSP, padrão do GBA, não corrige.
- **[Trade-off] Parâmetros antigos removidos:** os quatro novos são suficientes, mas quem usava `SATURATION` ou `GAMMA_BOOST` terá de reajustar.

## Open Questions

- Valores padrão finais dos quatro parâmetros (os do rascunho são o ponto de partida; o usuário ajusta no aparelho).
- Se o teto de `+0.08` fica ou cai para `+0.05` depois da prova no aparelho.

## Ajuste após a validação no aparelho

Com os padrões do rascunho (`CONTRAST` 0.30, `HIGHLIGHT` 0.25, teto `+0.08`) o usuário achou o brilho alto e branco, amarelo e verde estourados. A réplica em numpy mostrou 24% dos pixels claros do Mario Kart indo a 255. Os padrões passaram a `CONTRAST` 0.15, `HIGHLIGHT` 0.05 e teto `+0.05` (o fallback previsto): 0% estouram, a saturação média segue acima da original (0.632 contra 0.606), o vermelho e a nitidez ficam iguais. Depois o usuário achou o resultado parecido com o shader desligado e pediu uma experiência de console: entrou o efeito LCD abaixo, e os padrões foram reajustados.

## Decisão 6: Efeito LCD com cobertura por sobreposição (muda o Non-Goal)

O Non-Goal "efeitos de grade LCD" caiu a pedido do usuário: o visual de console é o objetivo do ajuste acima. O efeito vai no mesmo passe, depois do clip, sem leitura de textura.

- **Lacuna na borda de trás.** Dentro de cada pixel do jogo, `pos = fract(TEX0 * TextureSize)` vai de 0 a 1, e a lacuna ocupa `[1 - gap, 1)`, com `gap = min(px, 0.3)` e `px = InputSize.x / OutputSize.x` (o pixel de saída em pixels do jogo). Em 2x a lacuna é exatamente o segundo pixel de saída de cada pixel do jogo; em 2.67x vale 0.3 pixel do jogo (cerca de 0.8 pixel de saída).
- **Por que borda de trás e não centrada.** Uma lacuna centrada na fronteira cai metade em cada pixel de saída em 2x e some como grade: tudo fica meio escuro. Na borda de trás, em 2x um pixel de saída fica claro e o outro escuro.
- **Cobertura, não amostra.** A escuridão do pixel de saída é a sobreposição da janela `[pos - px/2, pos + px/2]` com a lacuna do próprio pixel do jogo e com a do anterior (janela que vaza abaixo de 0), dividida por `px`. É um filtro de caixa exato, então a grade não pisca nem some em escala fracionária. Custo: algumas operações em `vec2`, um eixo por componente.
- **Força.** `lit = (1 - LCD_GRID * cobertura_x) * (1 - LCD_GRID * cobertura_y)`, multiplicado na cor final junto de `(1 + BRIGHTNESS)`. Padrão `LCD_GRID` 0.10, "bem sutil" a pedido do usuário depois de ver 0.25 (a luma média caía 12% e o menor valor de uma cena plana ficava em 64% do pico, agressivo): a luma média cai cerca de 4% em relação à imagem sem shader (2% a 6% na spec), e o menor valor de uma cena plana fica em 85% do pico em 640x427 (88% em 480x320). Para uma grade mais marcada, `LCD GRID` 0.15 a 0.25 pelo menu. `BRIGHTNESS` (-0.30 a 0.30) deixa o usuário recuperar ou tirar luz sem rebuild; fica em 0 porque o centro dos pixels mais claros estouraria.
- **Alternativas descartadas:** lacuna de um pixel inteiro com `LCD_GRID` 0.35 (a luma cai 23%, pesado; 0.25 também pareceu agressivo); compensar a média automaticamente (clareia o centro dos pixels e estoura brancos, que o usuário já tinha reclamado); máscara de fósforo RGB (precisa de mais resolução que 640x480 e de uma tabela).
- **Risco de precisão no Mali-400.** O fragment shader só tem `mediump` (fp16) e a coordenada `TEX0 * TextureSize` chega a 240, onde fp16 só distingue cerca de 0.12 pixel do jogo. A réplica com arredondamento fp16 dá PSNR de 33.3 dB (Mario Kart) e 36.6 dB (Super Mario Advance 3) contra a precisão cheia em 640x427, e 49 dB ou mais em 480x320, onde as frações são exatas. É uma estimativa: o arredondamento real do Mali-400 só se confere no aparelho. Se a grade ficar irregular à direita da tela, a saída é reduzir `LCD GRID` ou calcular a fase da grade a partir de um contador reduzido; o filtro sharp-bilinear tem a mesma exposição desde o shader original.


## Decisão 7: Cor de console com roll-off de croma nos claros (HDR sem lavar)

O usuário achou as cores ainda muito saturadas e pediu um visual de console, com aparência HDR e sem imagem lavada. A saturação alta estava nos tons claros (amarelo, verde, céu claro), que têm luma alta; o vermelho do Mario tem luma baixa (perto de 0.3) e o usuário o aprovou. Reduzir a saturação de forma global derrubaria o vermelho, então o ganho de croma depende da luma:

`ganho = (1 + VIBRANCE * (1 - sat)) * SATURATION * (1 - ROLLOFF * hs)`, com `hs = smoothstep(0.5, 1.0, L)`, e `c = L + (c - L) * ganho`.

- **HDR sem lavar:** é o que o tone mapping de filme faz, a croma some conforme a luz sobe (as cores claras vão para o branco) e as sombras e os médios mantêm a cor cheia. A curva em S (pivô 0.35) segue aprofundando as sombras, e o `hs` é o mesmo que alimenta o `HIGHLIGHT SHOULDER`, então o custo é uma multiplicação e uma subtração a mais.
- **Efeito do padrão** (réplica, Mario Kart em 480x320 e 640x427): saturação dos claros coloridos 25% abaixo, vermelhos 0.890 para 0.869 (480x320; 0.852 em 640x427, onde o filtro de borda também pesa), tons médios 0.879 para 0.868, pico de vermelho em 255, luma 3.6% abaixo da original, 0% de claros estourados.
- **O LCD fica sutil** (`LCD GRID` 0.10, queda de 4% na luma) por pedido do usuário; ele e o roll-off juntos tiram o aspecto "aceso". `VIBRANCE` caiu de 0.60 para 0.20: só empurra o que está apagado, e `SATURATION` 0.97 fecha o ajuste fino. O usuário pode subir o `SATURATION` até 1.3 ou baixar até 0.5 pelo menu.
- **Alternativas descartadas:** saturação global fixa (derruba o vermelho); correção por matriz como no shader original (mistura canais e lava o vermelho); LUT de cor (leitura de textura extra).
- **Referência de qualidade:** o RetroArch sem shader aplica bilinear puro sobre a imagem crua e saturada. O shader troca isso por sharp-bilinear (nitidez de 97% a 100% do vizinho mais próximo, sem cintilar em 2.67x), cor contida e a grade sutil.

## Decisão 8: Shader ligado por padrão no GBA, com chave para desligar

O usuário pediu o shader como padrão do GBA, sem escolher em "SHADER SET". Isso inverte o requisito de "desligado por padrão".

- **Preset automático do RetroArch por core.** `/storage/.config/retroarch/config/<core>/<core>.glslp` com uma linha `#reference "/tmp/shaders/gba/gba-modern-remaster.glslp"`, para `gpSP` (padrão do GBA), `mGBA`, `VBA-M` e `VBA Next` (os nomes de pasta que o RetroArch usa). O RetroArch carrega esse preset ao abrir um jogo do core, sem passar pelo ES.
- **Criado no boot, não na imagem.** A p8 não é regravada com `--keep-storage`, então um preset em `storage/` da feature só chegaria em cartão novo. O mesmo serviço `r36-shader-gba-prepara` (que já limpava a cópia velha da p8) cria o preset no boot, antes do ES, quando falta. Preset existente nunca é sobrescrito, inclusive um que o usuário salvou com parâmetros, que valem mais que os padrões do shader.
- **Chave para desligar.** Arquivo vazio `r36-gba-sem-shader` na raiz da p1, que o usuário cria pelo PC sem root. Com ele o serviço apaga os presets que ele mesmo criou (só os que contêm exatamente a referência, e não um preset editado) e não os recria. O serviço espera o `/storage/roms` montar (até 20 s, como o `classicube-sync`) sem `After=emuelec-autostart`, que travaria o boot; se a p1 não montar, não cria nem apaga nada.
- **Alternativas descartadas:** `gba.shaderset` no `emuelec.conf` (também fica na p8 e só vale em cartão novo); preset em `/usr/config` no SYSTEM (a pasta não é lida pelo RetroArch); trazer o preset na imagem da p8 (não vale com `--keep-storage`).
- **Risco:** não confirmei no aparelho como o ES se comporta com "SHADER SET" em nenhum quando há preset de core. O primeiro boot e um jogo de GBA mostram se o shader entra.

## Decisão 9: Cor viva sem saturar (reajuste da Decisão 7)

Com `SATURATION` 0.97, `HIGHLIGHT ROLLOFF` 0.60 e `VIBRANCE` 0.20 o usuário achou que o shader tinha perdido a cor viva, e lembrou que "viva" não é "muito saturada". A réplica explicou: os tons graves e médios do Mario Kart caíam 11% em croma (parte pelo LCD, que escurece a imagem em 3% a 4%) e o vermelho caía de 0.890 para 0.852. Os padrões passaram a `VIBRANCE` 0.45, `SATURATION` 1.10, `HIGHLIGHT ROLLOFF` 0.65 e `S-CURVE Contrast` 0.28: a saturação global sobe um pouco e o roll-off maior segura os claros, então os tons graves e médios ficam em -2% (Mario Kart) e +23% (Super Mario Advance 3, mais apagado), o vermelho vai a 0.877 (0.896 em escala inteira), os claros coloridos continuam 18% a 26% mais contidos, só 1.9% dos pixels ficam neon (contra 6.8% sem shader) e a luma segue 2% a 3% abaixo da original, sem estouro. O contraste maior (0.28) dá o pop de HDR nos médios sem clarear. Medido por réplica; a validação visual é do usuário.

## Decisão 10: Padrão do GBA pelos dois caminhos (corrige a Decisão 8)

O build com o preset automático por core, sozinho, não ligou o shader no aparelho. Lendo o `setsettings.sh` do EmuELEC (que o `emuelecRunEmu.sh` roda): o RetroArch recebe `--set-shader /tmp/shaders/<valor>` quando existe `<sistema>.shaderset` no `emuelec.conf`, e `video_shader_enable` pode estar em `false` no `retroarch.cfg`, o que impediria um preset de core de valer sozinho. Não consegui provar no PC qual dos dois o aparelho usa, então o serviço liga os dois:

- acrescenta `gba.shaderset=gba/gba-modern-remaster.glslp` ao `emuelec.conf` se a chave não existe (é o que o ES grava ao escolher "SHADER SET"); uma chave existente, inclusive `none`, é respeitada;
- cria os presets de core, agora apontando para `/usr/share/common-shaders/gba/gba-modern-remaster.glslp` (o arquivo do SYSTEM, sem depender do overlay `/tmp/shaders`);
- espera a p1 montar por até 20 s e, se ela não montar, segue sem a chave (o padrão é ligado), em vez de desistir como antes;
- grava `r36-shader-gba.log` na raiz da p1, para diagnosticar pelo PC sem root.

A chave `r36-gba-sem-shader` desfaz só o que o serviço criou. **Risco aberto:** a leitura do `setsettings.sh` mostra que o `--set-shader` só é emitido para alguns valores do `gba.shaderset`; se o ES grava outro formato, esse caminho não acende o shader e quem vale é o preset de core. O log e o relato do primeiro boot dizem qual dos dois entrou.

## Decisão 11: Pasta certa do preset e overlay remontado (corrige a Decisão 10)

No aparelho, com o build `20261026-004031`, o shader não ficou padrão e não apareceu no "SHADER SET" do ES. Lido no SYSTEM e no fonte do RetroArch 1.17:

- A lista do ES é `emuelec-utils getshaders` = `find /tmp/shaders -name '*.glslp'`. O serviço apagava a cópia velha direto em `/storage/shaders/gba` (camada de cima) com o overlay `/tmp/shaders` já montado; a vista mesclada pode perder a pasta `gba` até o próximo boot. Agora o serviço roda `After=tmp-shaders.mount` e, se limpou a p8, faz `systemctl restart tmp-shaders.mount`.
- O RetroArch 1.17 procura o preset de core em `rgui_config_directory` (`/config` no nosso `retroarch.cfg`, inexistente), na pasta do `retroarch.cfg` e em `video_shader_dir/presets`. O preset em `config/<core>/` não era achado. Agora o serviço cria também `/storage/.config/retroarch/<core>/<core>.glslp` (a chave desliga os dois).
- `video_shader_get_current_shader_preset` devolve nada se `video_shader_enable` é falso, inclusive para preset automático. Essa linha só é escrita pelo ES quando há `<sistema>.shaderset`, então a chave do `emuelec.conf` continua necessária (é ela que liga o `video_shader_enable`), e o preset de core garante o arquivo certo mesmo que o ES monte o caminho de outro jeito.
- O log na p1 diz se `/tmp/shaders/gba/gba-modern-remaster.glslp` está visível e mostra as linhas de shader do `retroarch.cfg`.

## Decisão 12: Cor viva sem desbotar nenhuma cor (corrige as Decisões 7 e 9)

Com o shader ligado no aparelho (build `20261026-103244`), o usuário achou o amarelo pouco vivo e a pele do Mario pálida no Super Mario World, e pediu cor viva sem distorcer as outras. A réplica mostrou a causa: o roll-off multiplicava o ganho de croma por `1 - ROLLOFF * hs`, então as cores de luma alta (amarelo, pele, pastéis) ficavam **abaixo** da cor crua, e a proteção de clip tirava mais croma do que já estava no teto. No logo do SMA2 o amarelo (255, 242, 57) ia de 0.78 a 0.40 de saturação; os tons de pele, de 0.43 a 0.33.

Quatro mudanças, sem leitura de textura nem `pow` novos:

- **Roll-off só do reforço:** o ganho vira `1 + (ganho - 1) * (1 - ROLLOFF * hs)`; nenhuma cor fica abaixo da própria croma.
- **Âncora no canal máximo nos claros:** o ganho gira em torno de `mix(L, max, hs)`. Nos escuros e médios é o de antes; nos claros, a cor ganha croma aprofundando os canais fracos, sem clarear e sem mudar o matiz. Por isso o `HIGHLIGHT ROLLOFF` pôde cair de 0.65 para 0.35.
- **Curva em S que não apaga cor saturada e não clareia o que está no teto:** `k = max(k, mix(k, 1, sat²))` (o azul puro não perde brilho) e `k <= max(teto / canal máximo, 1)` (o amarelo puro não é clareado, então não perde croma no clip).
- **Vibrance some perto do cinza:** peso `min(1 - sat, 4 sat (1 - sat))`, para brancos e fundos bege não ganharem tom.

Medido na réplica (`verificacao/replica.py`, que agora inclui uma cartela de 24 cores e aceita capturas do SMA2): nenhuma cor da cartela nem do logo do SMA2 muda de matiz mais de 1.5 grau; no logo nenhuma perde saturação (amarelo 0.88, verde 0.86); a pele do Mario vai de 0.45 a 0.57; o azul puro fica em 255; claros sem estouro (0%); a luma das cores no teto sobe no máximo 0.007. As únicas quedas são em cores já saturadas ao máximo (laranja e ciano, 1.00 para 0.95), pela proteção de clip. Os cenários da spec "Claros coloridos contidos" e "saturação média até +0.02" foram trocados pelos de cor viva sem desbotar. Exemplos em `var/exemplos-cor/`. As capturas do SMA2 (quadros 400 e 640, nativas 240x160) foram feitas rodando o core mGBA por um frontend libretro mínimo em Python, sem RetroArch, e estão em `~/.cache/shader-gba-test/smw_sem/`.

## Decisão 13: Cópia da p8 regravada no lugar (corrige a Decisão 11)

O log do boot com o build `20261026-135846` mostrou `copia velha do shader na p8 removida` seguido de `AVISO: /tmp/shaders/gba/gba-modern-remaster.glslp nao visivel`, sem a remontagem. Lendo o SYSTEM: o `emuelec_autostart.sh` roda `rsync -a --ignore-existing /usr/share/common-shaders/ /storage/shaders/` a cada boot. É ele que põe na p8 a cópia de todos os shaders, e o `--ignore-existing` nunca a atualiza; depois de gravar um `system` novo, a cópia do build anterior fica por cima no overlay. Apagá-la com o overlay montado deixa a pasta `gba` invisível em `/tmp/shaders` (lista do ES e caminho do `video_shader`) até o próximo boot, quando o rsync a recria.

O serviço passa a regravar o conteúdo do SYSTEM no mesmo arquivo da p8 (`cat > arquivo`, mesmo inode), sem apagar e sem remontar, e não cria a cópia quando ela não existe. Os presets que só referenciam a cópia continuam sendo apagados. O `After=tmp-shaders.mount` fica, para a regravação acontecer com o overlay já montado.

## Decisão 14: Tearing com buffer duplo (diagnóstico)

O mesmo log trouxe o framebuffer: `fb0 virtual_size: 640,960`, `bits_per_pixel: 32`, `pan: 0,480` e `modes: U:640x480p-0`. Há buffer duplo e o driver da Mali troca de quadro por pan (a tela estava no segundo buffer). O tearing não vem de buffer único; vem de a troca não esperar o retrace (o driver não chama `FBIO_WAITFORVSYNC`, ou o GPU desenha no buffer que ainda está na tela). A taxa da tela não é informada (`p-0`), então o RetroArch usa 60 Hz. A correção possível sem o fonte do kernel é uma biblioteca de `LD_PRELOAD` que espera o retrace (`FBIO_WAITFORVSYNC` no `/dev/fb0`) a cada `eglSwapBuffers`; fica para uma change própria, porque mexe em todos os sistemas e precisa de teste no aparelho.

## Decisão 15: Sem overlayfs, /tmp/shaders por bind (corrige as Decisões 11 e 13)

Com o build `20261026-142401`, a cópia da p8 estava certa e nada foi apagado, mas o log ainda dizia `nao visivel`, e o usuário viu a lista "SHADER SET" do ES **vazia** (nem `crt/` nem `rpi/`); o shader só aparecia pelo menu do RetroArch. O kernel 3.4.39 da p6 não tem overlayfs: nenhuma string do driver (`lowerdir`, `upperdir`) no binário, e os módulos do SYSTEM são de um kernel 5.10. Todo `tmp-*.mount` falha. A versão de fábrica já contorna isso: o `emuelecRunEmu.sh` carrega `/storage/cores`, e o `emuelec_autostart.sh` copia o SYSTEM para a p8 com `rsync --ignore-existing`. O menu do RetroArch lista `video_shader_dir` (`/storage/shaders`), por isso o shader aparecia ali.

O serviço passa a montar `/storage/shaders` em `/tmp/shaders` por bind (`mount -o bind`, que o kernel tem) quando nada está montado ali, antes do ES. A regravação no lugar da Decisão 13 continua: é a cópia da p8 que vale. As explicações das Decisões 11 e 13 sobre "apagar com o overlay montado" estavam erradas (não havia overlay); o efeito visto vinha de `/tmp/shaders` vazio.

Consequência fora desta change: um core recompilado com o mesmo nome não chega a um cartão que já tem o arquivo em `/storage/cores` (changes `core-mgba-a33` e `core-picodrive-a33`). Registrado no `CLAUDE.md`.

## Registro para quem continua (outros harnesses)

### Estado em 2026-10-26

- Implementado e testado no PC (361 testes): shader com oito parâmetros, efeito LCD, cor de console, serviço `r36-shader-gba-prepara` (limpeza da p8 e shader padrão do GBA), docs. Tudo **sem commit**, na branch `shader-gba-vivo-r36s`; merge e push só a pedido do usuário.
- Último build completo e verificado: `out/20261026-151033` (o `SYSTEM` tem o shader com os padrões da Decisão 12 e o serviço das Decisões 10 e 11). Pastas de `out/` sem `manifest.json` são builds interrompidos e não servem para gravar.
- **Nada disto foi visto no aparelho.** Pendentes: tarefas 7.6 e 8.3 (o usuário grava o `system` e abre um jogo de GBA) e, depois, arquivar a change (`/opsx:archive`).
- Pedidos que o usuário fez em ordem, e que o código atende: cor viva que preserve o vermelho; brilho e estouro de claros menores; sharp-bilinear com nitidez; efeito LCD **bem sutil**; cores **vivas sem serem saturadas** (HDR sem lavar); shader **ligado por padrão no GBA**. O usuário compara sempre com o RetroArch sem shader (bilinear puro sobre a cor crua) e quer algo claramente melhor.

### Como o EmuELEC liga shaders (lido nos scripts do SYSTEM, não testado no aparelho)

- O ES chama `/usr/bin/emuelecRunEmu.sh`, que roda `/usr/bin/setsettings.sh <sistema> <rom> <core>` e, se este imprimir algo, insere a saída antes de `--config` na linha de comando do RetroArch (`SHADERSET`). Esses dois arquivos estão no `SYSTEM` (squashfs dentro do FAT `SYSTEM` da p7; para ler no PC: `mcopy -i out/<build>/parts/system.img ::SYSTEM <dest>` e `unsquashfs -cat <dest> usr/bin/setsettings.sh`).
- `setsettings.sh` lê `/storage/.config/emuelec/configs/emuelec.conf` na ordem `<sistema>["<rom>"]...shaderset=`, `<sistema>.shaderset=`, `global.*shaderset=`, e no ramo `shaderset` só imprime `--set-shader /tmp/shaders/<valor>` para alguns valores (o código do SYSTEM compara com `true` e `1`; as linhas que tratam `none` e gravam `video_shader` estão comentadas). Por isso o `gba.shaderset=gba/gba-modern-remaster.glslp` **pode não bastar**.
- `default_settings` (que escreveria `video_shader_enable = "false"` no `retroarch.cfg`) está comentada, e o `emuelecRunEmu.sh` apaga `video_shader` e `video_shader_enable` do `retroarch.cfg` depois de cada jogo.
- Presets de core: `/storage/.config/retroarch/config/<core>/<core>.glslp` (nomes de pasta como o RetroArch grava: `gpSP`, `mGBA`, `VBA-M`, `VBA Next`). Versões de teste anteriores deixaram presets assim na p8 (`gpSP/gpSP.glslp`, `gpSP/gba.glslp`, `mGBA/gba.glslp`, cada um com `#reference` para uma cópia do shader em `/storage/shaders/gba/`) e os parâmetros do shader antigo apareceram no menu do RetroArch, o que mostra que o preset de core é carregado; se também é **aplicado** sem `video_shader_enable`, não foi confirmado.
- `/tmp/shaders` é um overlay: camada de baixo `/usr/share/common-shaders` (SYSTEM), camada de cima `/storage/shaders` (p8). Arquivo na p8 vence o do SYSTEM.

### Como decidir depois do primeiro boot

1. Ler `R36-ROMS/r36-shader-gba.log` (o serviço rodou? criou a linha e os presets? a p1 montou a tempo?).
2. Abrir um jogo de GBA sem escolher nada no ES. Se o shader entrou, conferir os parâmetros no RetroArch (Shaders, Shader Parameters): devem ser os oito da spec.
3. Se **não** entrou: ver o log do EmuELEC em `/storage/.config/emuelec/logs/` (copiar a p8 com `sudo`) para saber qual linha de comando o RetroArch recebeu (`--set-shader` presente ou não). Opções, em ordem: (a) trocar a escolha para gravar o valor que o `setsettings.sh` realmente trata; (b) forçar `video_shader_enable = "true"` com o `video_shader` apontando para o shader em um `--appendconfig`; (c) um override por jogo em `config/<core>/<jogo>.glslp`. Cada uma é um acréscimo à Decisão 10 e precisa de teste.
4. Se entrou mas a grade ou a cor incomodam: tudo se ajusta no menu do RetroArch; para trocar o padrão, mude `.glsl` (`#pragma` e `#define`), `tests/test_shaders_gba.py`, a spec, a `design.md` (tabela da Decisão 2) e `verificacao/replica.py` (`DEF`), e gere novo build.

### Armadilhas já pagas

- A p8 esconde o SYSTEM nos shaders e os valores de parâmetros salvos em preset valem mais que os `#pragma`; ver o parágrafo correspondente no `CLAUDE.md`.
- Os `#pragma parameter` precisam repetir nos `#define` de reserva os mesmos padrões (o teste confere).
- `SATURATION` existia no shader antigo com outro significado (1.0 neutro, valores salvos de 1.0 voltam a valer); `CORRECTION_STRENGTH`, `GAMMA_BOOST`, `PIXEL_SOFTNESS` e `GBA_Matrix` continuam proibidos pelo teste.
- A saturação média **não** mede cor contida: o que mede é a saturação dos claros coloridos (luma > 0.6, saturação > 0.25) e dos médios, como nos cenários da spec.
- Mudar `px` ou a janela da grade LCD sem reconferir o caso de escala inteira (2x) faz a grade sumir ou escurecer a tela inteira: a lacuna fica na borda de trás de cada pixel do jogo (Decisão 6).
- Medição: `verificacao/replica.py` e `verificacao/LEIA-ME.md`. O RetroArch Flatpak não está mais na máquina do usuário.
