# Proposal

## Why

Na imagem de fábrica do R36S, o Game Boy Clássico (`gb`) e o Game Boy Color (`gbc`) abrem sem shader (bilinear puro que borra os pixels em 3,33x) e, no GBC, com a correção de cor interna do Gambatte ligada, que lava e amarronza as cores para imitar o LCD sem luz de 1998. Já a tentativa anterior (`51-gameboy-fiel`, removida) usava um shader de 5 passadas com a paleta verde-oliva clássica do DMG, que derrubava a taxa de quadros na Mali-400 do Allwinner A33 e embolava o cinza claro (Tom 2) com o fundo (Tom 3). Precisamos de dois shaders de passe único, leves para a Mali-400 e calibrados por réplica numérica com capturas do RetroArch AppImage em `var/`: um para o Game Boy Clássico com visual de console original DMG-01 mas com alta clareza e separação entre os 4 tons, e outro para o Game Boy Color com a mesma experiência do `gba-modern-remaster` (cores vivas próximas às de SNES e pixels nítidos).

## What Changes

- **Novo shader do Game Boy Clássico (`gb/gb-modern-dmg.glsl` e `.glslp`)** em `/usr/share/common-shaders/gb/`:
  - Passe único, uma leitura de textura por pixel (`COMPAT_TEXTURE`), precisão `mediump`, sem `pow()` e sem laços, garantindo 60 fps no A33.
  - Filtro `sharp-bilinear` adaptativo à escala (transição de ~1 pixel de saída em 3,33x, 533x480).
  - Paleta **High-Clarity DMG-01** (verde-oliva do console original modernizado): abre a distância de luminância entre os 4 tons (`Delta Luma >= 0.20` entre qualquer par de tons vizinhos), eliminando a fusão entre o Tom 2 (cinza claro) e o Tom 3 (fundo desligado) da paleta DMG antiga.
  - Grade **Dot-Matrix reflexiva**: a lacuna de 1 pixel de saída na borda de trás revela o tom do substrato verde-oliva claro entre os pixels escuros acesos, destacando cada ponto da matriz sem riscar o fundo claro com linhas pretas.
- **Novo shader do Game Boy Color (`gbc/gbc-modern-remaster.glsl` e `.glslp`)** em `/usr/share/common-shaders/gbc/`:
  - Mesmo pipeline de passe único do `gba-modern-remaster` (`VIBRANCE`, `SATURATION`, `ROLLOFF`, `CONTRAST`, `HIGHLIGHT`, `SOFTNESS`, `LCD_GRID`, `BRIGHTNESS`), calibrado em 533x480 (3,33x) sobre capturas reais de GBC para entregar cores vivas de console (SNES) sem desbotar amarelos/peles, sem estourar claros e com nitidez `sharp-bilinear` + grade LCD sutil.
- **Nova feature `55-shaders-gb-gbc`** com serviço de boot `r36-shader-gb-gbc-prepara.service`:
  - Atualiza no mesmo inode cópias antigas dos dois shaders em `/storage/shaders/{gb,gbc}` e garante o bind de `/tmp/shaders`, deixando ambos visíveis em "SHADER SET" do EmulationStation.
  - Configura as opções por pasta de conteúdo do Gambatte (`config/Gambatte/gb.opt` com `gambatte_gb_colorization = "disabled"` e `config/Gambatte/gbc.opt` com `gambatte_gbc_color_correction = "disabled"`), sem sobrescrever escolhas existentes do usuário.
  - **Ligados por padrão (decisão do usuário):** os novos shaders do GB e do GBC ficam ativados no boot, como o GBA na feature 54 (`gb.shaderset` / `gbc.shaderset` e presets `<Core>/gb.glslp` / `<Core>/gbc.glslp`), com as chaves `r36-gb-sem-shader` e `r36-gbc-sem-shader` na p1 para desligar cada um.
  - Grava diagnóstico em `r36-shader-gb-gbc.log` somente com `r36-diagnostico`.
- **Verificação numérica e visual em `var/`**:
  - Script de captura com `~/AppImages/retroarch.appimage` usando ROMs de `/mnt/backup/PC/R36S/roms/{gb,gbc}` e réplica numérica (`replica.py`) que valida todos os cenários da spec e gera as pranchas comparativas em `var/exemplos-gb-gbc/`.

## Capabilities

### New Capabilities
- `gb-gbc-emulation`: Shaders de modernização do Game Boy Clássico (`gb-modern-dmg`) e do Game Boy Color (`gbc-modern-remaster`), separação de 4 tons no DMG, cores estilo SNES no GBC, opções de cor do Gambatte por pasta de conteúdo, ativação por padrão no boot e chaves para desligar.

### Modified Capabilities
- `retroarch-shaders`: Estende os requisitos gerais de shaders para contemplar (1) o perfil monocromático de 4 tons modernizado (`gb-modern-dmg`) ao lado do perfil colorido (`gba-modern-remaster` e `gbc-modern-remaster`), e (2) presets automáticos por pasta de conteúdo (`<Core>/<sistema>.glslp`) quando sistemas diferentes compartilham os mesmos cores libretro.

## Impact

- Nova feature `features/55-shaders-gb-gbc/` (camada `system`: shaders `.glsl`/`.glslp`, script `/usr/lib/r36/shader-gb-gbc-prepara` e unit `r36-shader-gb-gbc-prepara.service`).
- Réplica numérica e scripts de captura em `openspec/changes/shaders-gb-gbc-r36s/verificacao/` e imagens comparativas geradas em `var/exemplos-gb-gbc/` (fora do git).
- Novos testes automatizados em `tests/test_shaders_gb_gbc.py`.
- Documentação para `README.md` e `CLAUDE.md` em `docs-shaders-gb-gbc-r36s.md` (pasta da change), consolidada pela integração.
