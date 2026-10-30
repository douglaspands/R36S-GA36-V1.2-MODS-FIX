# Tasks

## 1. Modelagem Matemática e Réplica Numérica

- [x] 1.1 Criar script de réplica numérica `replica_tv.py` em `openspec/changes/shader-tv-modern-remaster/verificacao/` implementando a detecção seletiva de dither horizontal (3 taps), modulação de feixe CRT PVM suave e pipeline de cores vivas.
- [x] 1.2 Obter ou gerar capturas de referência sem shader (Mega Drive e SNES) e validar numericamenta a fusão do padrão xadrez da água de *Sonic* mantendo mais de 95% de nitidez de borda nos contornos dos personagens.
- [x] 1.3 Avaliar estabilidade numérica em precisão `fp16` (mediump) na réplica, verificando ausência de estouro de brancos e saturação balanceada.

## 2. Shader GLSL e Preset de Passe Único

- [x] 2.1 Criar `tv-modern-remaster.glsl` em conformidade com GLSL ES 1.00 e `mediump`, contendo os pragmas de parâmetros padronizados (`DITHER_BLEND`, `TV_SCANLINES`, `PIXEL_SOFTNESS`, `VIBRANCE`, `SATURATION`, `CONTRAST`, `ROLLOFF`, `BRIGHTNESS`) e reservas `#define`.
- [x] 2.2 Criar `tv-modern-remaster.glslp` configurando 1 passe de renderização pela viewport com filtro linear.
- [x] 2.3 Criar testes unitários em `tests/test_shaders_tv.py` conferindo ausência de `pow(`, limite de no máximo 3 leituras `COMPAT_TEXTURE`, bloco de precisão `mediump`, e conformidade dos parâmetros e valores padrão.

## 3. Feature 57-shaders-tv e Ativação por Padrão no Boot

- [x] 3.1 Criar descritor `features/57-shaders-tv/feature.toml` (ordem 57) e instalar os arquivos do shader sob `features/57-shaders-tv/system/usr/share/common-shaders/tv/` com permissão 0644.
- [x] 3.2 Implementar script de inicialização `shader-tv-prepara` sob `features/57-shaders-tv/system/usr/lib/r36/` que detecta a partição p1 montada, sincroniza cópias da p8 em `/storage/shaders/tv/` e monta `/tmp/shaders` por bind se necessário.
- [x] 3.3 Implementar configuração padrão de `<sistema>.shaderset=tv/tv-modern-remaster.glslp` no `emuelec.conf` e presets de core em `/storage/.config/retroarch/config/<Core>/<Core>.glslp` para os consoles de mesa e arcades (`megadrive`, `genesis`, `snes`, `nes`, `mastersystem`, `pce`, `psx`, `mame`, `fbneo`, `cps1`, `cps2`, `cps3`, `neogeo`), respeitando escolhas manuais existentes.
- [x] 3.4 Implementar tratamento da chave de escape `r36-tv-sem-shader` na raiz da p1 e geração de log em `r36-shader-tv.log` condicionada à chave `r36-diagnostico`.
- [x] 3.5 Criar unit systemd `r36-shader-tv-prepara.service` configurada com `Before=emustation.service`, `After=r36-shader-gb-gbc-prepara.service` e `After=tmp-shaders.mount`.
- [x] 3.6 Adicionar testes unitários em `tests/test_shaders_tv.py` validando a execução do script `shader-tv-prepara` em cenários com e sem chave de escape, preservação de presets do usuário e geração condicional de log.

## 4. Integração, Validação e Documentação

- [x] 4.1 Executar a suíte de testes completa do repositório (`uv run python -I -m unittest discover -s tests`) e verificar que todos os testes passam sem regressões.
- [x] 4.2 Atualizar o `CLAUDE.md` com as especificidades do novo shader `tv-modern-remaster`, lista de consoles suportados, comportamento de dither e chave de desativação na p1.

## Workflow follow-up

- Arquivar a change com `openspec archive shader-tv-modern-remaster` após validação visual e aprovação no aparelho real.
