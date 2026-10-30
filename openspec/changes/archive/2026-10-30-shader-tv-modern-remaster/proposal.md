# Proposal

## Why

Os consoles de mesa de 8, 16 e 32 bits (Mega Drive, SNES, NES, Master System, PC Engine, PlayStation) e os sistemas de arcade (Capcom CPS1/CPS2/CPS3, Neo Geo, MAME/FBNeo) foram projetados para telas CRT analógicas. No Mega Drive e em vários clássicos, efeitos cruciais de transparência (como a água e fumaça em *Sonic the Hedgehog*, a água em *Shinobi III* e a iluminação em *Streets of Rage 2*) dependiam da limitação horizontal de largura de banda das TVs para fundir o quadriculado de dithering em transparência translúcida límpida.

Na tela LCD de 3.5 polegadas (640x480) do R36S, a emulação padrão exibe o dithering como uma malha dura e feia de xadrez, enquanto os shaders CRT existentes (`crt-easymode`, `zfast-crt`, `crt-lottes`) tornam a experiência ruim: escurecem a imagem em até 50% com scanlines grossas, geram artefatos de moiré na escala vertical não inteira (~2.14x) e borram a imagem. É necessário um shader remasterizado de alta qualidade, de passe único para a GPU Mali-400, que una a nitidez do pixel art moderno, cores vivas equilibradas (semelhantes ao `gba-modern-remaster`), fusão seletiva de dither para restaurar as transparências originais e um perfil de feixe CRT suave tipo monitor broadcast (Sony PVM), ativado por padrão em consoles de mesa e arcades.

## What Changes

- **Novo shader `tv-modern-remaster` (`.glsl` e `.glslp`):**
  - Implementado em passe único (`shaders = 1`) sob `/usr/share/common-shaders/tv/`.
  - **Dither Blending seletivo horizontal (3 taps):** detecta alternância de alta frequência $A-B-A$ (xadrez e barras verticais) na mesma scanline e funde apenas o dithering (água do Sonic, feixes de luz, sombras), preservando bordas sólidas, contornos de sprites e textos 100% nítidos.
  - **Escala sharp-bilinear:** transições afiadas com pixel art limpo e sem artefatos em resoluções inteiras e fracionárias.
  - **Textura de TV limpa e nítida (perfil PVM):** modulação suave de feixe vertical (~12% a 15% de contraste entre linhas), sem scanlines pretas pesadas, sem máscaras de fósforo que causem moiré em 640x480 e com brilho compensado.
  - **Pipeline de cor viva moderna:** vibrance seletiva, contraste por curva em S na luma (pivô 0.35), highlight roll-off nos tons claros e proteção de corte de canais preservando os matizes originais.
  - Compatibilidade estrita com a Mali-400 (GLSL ES 1.00, `mediump`, sem laços, sem `pow`).
- **Ativação por padrão para consoles de mesa e arcades:**
  - Serviço de boot `r36-shader-tv-prepara.service` configurando `<sistema>.shaderset` no `emuelec.conf` e presets automáticos nos diretórios dos cores do RetroArch para:
    - Mega Drive / Genesis (`megadrive`, `genesis`)
    - Super Nintendo (`snes`)
    - Nintendo Entertainment System (`nes`)
    - Master System (`mastersystem`)
    - PC Engine / TurboGrafx-16 (`pce`)
    - Sony PlayStation (`psx`)
    - Arcades (`mame`, `fbneo`, `cps1`, `cps2`, `cps3`, `neogeo`)
  - Atualização automática de cópias desatualizadas na p8 (`/storage/shaders/tv/`).
  - Suporte à chave de desativação na p1 (`r36-tv-sem-shader`) e diagnóstico condicionado à chave `r36-diagnostico` (`r36-shader-tv.log`).
- **Nova feature `57-shaders-tv` no repositório:**
  - Estrutura completa de empacotamento no SYSTEM, units systemd e scripts de inicialização.
- **Réplica numérica e suíte de testes:**
  - Script de verificação numérica em Python/numpy medindo dither blend, nitidez, precisão fp16 e ausência de estouro em capturas de referência.
  - Testes unitários em `tests/test_shaders_tv.py` validando integridade estrutural, restrições da Mali-400 e serviço de boot.

## Capabilities

### Modified Capabilities
- `retroarch-shaders`: Atualiza os requisitos de shaders para acomodar o perfil `tv-modern-remaster`, permitindo até 3 leituras horizontais na mesma scanline para fusão seletiva de dither em passe único, introduzindo o perfil de feixe CRT suave para telas compactas de 480p e formalizando a ativação por padrão nos consoles de mesa e arcades com chave de escape na p1.

## Impact

- **Sistemas afetados:** EmulationStation e RetroArch ao abrir jogos de consoles de mesa e arcades.
- **Armazenamento / Partições:**
  - SYSTEM: novos arquivos `/usr/share/common-shaders/tv/tv-modern-remaster.glsl` e `.glslp`, script `/usr/lib/r36/shader-tv-prepara` e unit `r36-shader-tv-prepara.service`.
  - p8 (`R36-STORAGE`): presets referenciados em `/storage/.config/retroarch/config/<Core>/` e entradas `<sistema>.shaderset` em `emuelec.conf`.
  - p1 (`R36-ROMS`): chave opcional `r36-tv-sem-shader` e log opcional `r36-shader-tv.log`.
- **Desempenho no R36S:** Custo de fragment shader calibrado para manter 60 fps constantes em 640x480 na Mali-400 MP2.
