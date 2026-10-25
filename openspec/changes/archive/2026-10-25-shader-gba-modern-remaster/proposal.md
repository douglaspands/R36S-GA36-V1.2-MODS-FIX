# Proposal

## Why

Os jogos originais de Game Boy Advance foram desenvolvidos para a tela reflexiva e sem iluminação do GBA original (AGB-001), apresentando cores intencionalmente estouradas e supersaturadas para compensar a falta de luz. Em telas LCD IPS modernas como a do clone do R36S, essas paletas resultam em verdes fluorescentes e vermelhos agressivos, além de cintilação de pixels (*pixel shimmering*) em resoluções não inteiras. O shader `gba-modern-remaster` resolve essa distorção cromática restaurando o ponto branco sRGB (D65) e aplicando interpolação adaptativa de bordas em uma única passada GLSL otimizada para GPUs Mali (OpenGL ES 2.0).

Como é uma questão de gosto (há quem prefira as cores originais e o pixel sem filtro), o shader fica **disponível mas desligado**: o usuário o liga pelo próprio EmulationStation quando quiser.

## What Changes

- Instala `gba-modern-remaster.glsl` e `gba-modern-remaster.glslp` em `/usr/share/common-shaders/gba/` no SYSTEM, através da feature `features/54-shaders-gba`. Essa pasta é a camada de baixo do overlay `/tmp/shaders` (`tmp-shaders.mount`), que o EmulationStation varre para montar a lista "SHADER SET".
- Não cria preset automático do RetroArch (`config/<core>/*.glslp`): o padrão continua sem shader, e a escolha do ES vale.
- Garante que a suíte de testes e o pipeline de build validem a presença e a sintaxe dos arquivos e a ausência de presets automáticos.

## Capabilities

### New Capabilities

*(Nenhuma nova capability necessária)*

### Modified Capabilities

- `gba-emulation`: Adiciona o requisito de presença dos arquivos do shader do GBA em `/usr/share/common-shaders/gba/` e o de que ele fica desligado por padrão e selecionável no "SHADER SET" do EmulationStation.

## Impact

- **Imagem:** Adiciona dois arquivos estáticos no SYSTEM (`usr/share/common-shaders/gba/`), que chegam ao cartão em qualquer gravação do `system`, inclusive com `--keep-storage`. Nada muda na p8.
- **Desempenho no A33:** Operação single-pass em fragment shader GLSL ES sem laços ou dependências pesadas, projetada para manter 60 FPS estáveis na GPU Mali-400 MP2. Só pesa quando o usuário liga o shader.
- **Compatibilidade:** Não muda o visual de nenhum sistema por padrão.
