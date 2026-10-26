# Proposal

## Why

O `gba-modern-remaster` atual lava o vermelho. Medido no mGBA (RetroArch 1.22.2) em *Mario Kart: Super Circuit* e *Super Mario Advance 3*, a matriz `GBA_Matrix` mistura verde e azul no vermelho e derruba o pico, e a saturação do vermelho do Mario cai de 0.879 para 0.665 (de 1.000 para 0.712 no vermelho puro). O filtro também borra a imagem (nitidez de borda 12.40 contra 14.01 do original). O objetivo do shader no R36S é um visual vivo de remaster, sem a correção de LCD do hardware do GBA, e com contraste que preserva os tons de vermelho.

## What Changes

- Reescrever `gba-modern-remaster.glsl` no lugar, mantendo o nome do arquivo e do preset, para que a escolha no "SHADER SET" do ES continue valendo.
- Trocar a correção por matriz por um pipeline de cor leve: vibrance (só empurra o que está pouco saturado), curva em S na luma com pivô em 0.35, ombro de realce ("HDR" em SDR) e proteção de clip que reduz croma em vez de cortar o canal.
- Trocar o `smoothstep` de largura fixa por um sharp-bilinear cuja transição vem da escala (`OutputSize / InputSize`), com 1 leitura de textura, sem `pow` e em `mediump`, para o Mali-400 do A33.
- Reduzir os parâmetros antigos e expor oito: `VIBRANCE`, `SATURATION`, `HIGHLIGHT ROLLOFF`, `S-CURVE Contrast`, `HIGHLIGHT SHOULDER`, `PIXEL SOFTNESS`, `LCD GRID` e `BRIGHTNESS`. Somem `CORRECTION_STRENGTH`, `SATURATION` e `GAMMA_BOOST`.
- Cor de console viva: o reforço de croma sai dos claros sem desbotar nenhuma cor, pele e amarelos ganham cor sem clarear, e o matiz não muda (Decisão 12 da `design.md`).
- Efeito LCD no mesmo passe (grade de pixels com cobertura por sobreposição, leve, desligável), para uma experiência de console. Isso substitui o Non-Goal de grade LCD da primeira versão.
- Atualizar `tests/test_shaders_gba.py` para o conteúdo novo.
- O shader passa a vir ligado por padrão nos jogos de GBA (pedido do usuário), por um preset automático do RetroArch criado no boot, com uma chave na p1 para desligar. A escolha no "SHADER SET" continua existindo.

## Capabilities

### New Capabilities

- `retroarch-shaders`: regras e parâmetros para qualquer shader da imagem (custo no Mali-400, formato dos arquivos, parâmetros padronizados, pipeline de cor, escala, grade LCD, ativação por padrão no boot e verificação), com o `gba-modern-remaster` como perfil de referência.

### Modified Capabilities

- `gba-emulation`: ganha dois requisitos de qualidade visual do shader (vermelho preservado e filtro nítido e leve, sem `pow` nem `highp`). Os requisitos de presença dos arquivos e de "desligado por padrão" não mudam.

## Impact

- `features/54-shaders-gba/system/usr/share/common-shaders/gba/gba-modern-remaster.glsl` (reescrito); o `.glslp` e o `feature.toml` (a descrição cita "sRGB D65") mudam só no texto.
- `tests/test_shaders_gba.py`.
- Sem mudança em cores, `es_systems.cfg`, `retroarch.cfg` ou p8. A medição de tempo de quadro no Mali-400 só pode ser feita no aparelho.
