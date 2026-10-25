# Design

## Context

O console R36S clone (GA36-MB V1.2) utiliza o SoC Allwinner A33 (CPU Quad-Core Cortex-A7 @ 1.2 GHz e GPU Mali-400 MP2 com suporte a OpenGL ES 2.0). O sistema roda EmuELEC 4.7 com RetroArch 1.17.
Na arquitetura do sistema (conferido no SYSTEM da imagem base):
- `/tmp/shaders` é um overlay (`tmp-shaders.mount`) com `lowerdir=/usr/share/common-shaders` (SYSTEM) e `upperdir=/storage/shaders` (p8). A base traz `crt/`, `kurg/`, `rpi/` e `sharp/` no SYSTEM.
- O EmulationStation monta a opção "SHADER SET" (global e por sistema) com `emuelec-utils getshaders`, que lista os `.glslp` de `/tmp/shaders` pelo caminho relativo (por exemplo `gba/gba-modern-remaster.glslp`). Ao abrir o jogo, o ES grava `video_shader` e `video_shader_enable` no `retroarch.cfg` conforme a escolha.
- O RetroArch tem `auto_shaders_enable = "true"`: um `.glslp` em `/storage/.config/retroarch/config/<core>/` é carregado sempre que o core abre e passa por cima do `video_shader` do `retroarch.cfg`.

Veja `proposal.md` para a motivação e `specs/gba-emulation/spec.md` para os requisitos de comportamento.

## Goals / Non-Goals

**Goals:**
- Criar a feature modular `features/54-shaders-gba` (ordem 54) com descritor `feature.toml` no pipeline de build do repositório.
- Instalar `gba-modern-remaster.glsl` e `gba-modern-remaster.glslp` em `system/usr/share/common-shaders/gba/`.
- Deixar o shader desligado por padrão e selecionável no "SHADER SET" do EmulationStation.
- Adicionar testes de unidade em `tests/` para validar presença, permissões, sintaxe do preset e ausência de presets automáticos.

**Non-Goals:**
- Não ligar shader por padrão em nenhum sistema.
- Não alterar o `setsettings.sh`, o `emuelecRunEmu.sh` nem o `es_systems.cfg`.

## Decisions

### Decisão 1: Modularização via Feature Dedicada (`features/54-shaders-gba`)
- **Escolha:** Isolar o shader em `features/54-shaders-gba` com `order = 54` e `enabled = true`.
- **Racional:** Segue a arquitetura do projeto definida em `feature-layers` e permite ligar/desligar a feature sem interferir na `10-ptbr-sao-paulo`.

### Decisão 2: Instalação em `/usr/share/common-shaders/gba/` (SYSTEM)
- **Escolha:** Instalar os arquivos na camada `system`, em `usr/share/common-shaders/gba/`.
- **Racional:**
  1. É a camada de baixo do overlay `/tmp/shaders`, que o ES varre: o shader aparece no "SHADER SET" como `gba/gba-modern-remaster.glslp`.
  2. O SYSTEM é gravado em toda atualização. Em `/storage/shaders` (p8) o arquivo só chegaria ao cartão com `--wipe-storage`.
  3. O usuário ainda pode pôr uma versão própria em `/storage/shaders/gba/` (upperdir), que tem prioridade no overlay.
- **Alternativa descartada:** `/storage/shaders/gba/` na p8 (versão anterior desta change), que não chega com `--keep-storage`.

### Decisão 3: Sem preset automático; escolha pelo EmulationStation
- **Escolha:** Não criar `gpSP/gpSP.glslp`, `gpSP/gba.glslp` nem `mGBA/gba.glslp`.
- **Racional:** Com `auto_shaders_enable = "true"`, esses presets ligariam o shader sempre e passariam por cima do "SHADER SET" do ES, então o usuário não conseguiria desligá-lo nem trocá-lo pelo ES. Sem eles, o padrão é sem shader, como na base, e o ES controla a escolha global ou por sistema.
- **Alternativa descartada:** Presets automáticos por core (versão anterior desta change), que deixavam o shader ligado por padrão.

## Risks / Trade-offs

- **[Risco] Cartão que já recebeu a versão anterior com `--wipe-storage`:** os presets `gpSP/gpSP.glslp`, `gpSP/gba.glslp` e `mGBA/gba.glslp` ficam na p8 e mantêm o shader ligado.
  → *Mitigação:* gravar a p8 de novo com `--wipe-storage` ou apagar esses três arquivos no aparelho (a p8 é ext4 de root, não dá para mexer pelo PC sem root). Os builds desta versão não os criam.
- **[Risco] Compatibilidade GLSL ES com o driver Mali-400 MP2**
  → *Mitigação:* O shader usa tipos e diretivas padrão `GL_ES`, precisão `mediump`, sem instruções de GLSL 1.30+ e com cálculos leves (mat3, smoothstep, pow). Só roda quando o usuário o escolhe.
