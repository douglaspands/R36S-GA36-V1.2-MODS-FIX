# Proposal

## Why

O NES-BOX, tema padrão da imagem, não tem pasta para 15 dos sistemas que o `es_systems.cfg` declara (`pce-cd`, `tic-80`, `sharpx1`, `prboom`, `ecwolf`, `megadrivemsu`, `ggh`, `wii`, `pgm2`, `fmtmarty`, `mplayer`, `freej2me`, `gmloader`, `karaoke`, `imageviewer`). Esses sistemas aparecem no EmulationStation sem logo e sem arte de personagem, só com o visual genérico, e destoam do resto da lista.

## What Changes

- Novo tema **NES-BOX-V2**, instalado na p8 ao lado do NES-BOX. É uma cópia completa do NES-BOX (tirada da própria imagem base) mais uma pasta por sistema faltante. Cada pasta nova tem `theme.xml` (mesmo formato das existentes), `system.png` (logo) e `background_icon.png` (arte de personagem 960x540, fundo transparente).
- O **NES-BOX continua sendo o tema padrão** e não é alterado. O V2 aparece na lista de temas do ES (Start > Configurações da interface > Tema).
- Os 7 sistemas que só diferem de um existente no nome (`pce-cd`←`pcenginecd`, `tic-80`←`tic80`, `sharpx1`←`x1`, `prboom`←`doom`, `ecwolf`←`wolf`, `megadrivemsu`←`megadrive`, `ggh`←`gamegear`) ganham uma pasta só com o `theme.xml`, que aponta para a arte da pasta equivalente dentro do V2 (`../<existente>/system.png`). Nada é duplicado.
- Os 8 restantes (`wii`, `pgm2`, `fmtmarty`, `mplayer`, `freej2me`, `gmloader`, `karaoke`, `imageviewer`) recebem arte nova. Ela vem da internet, na ordem: logo oficial do sistema, fabricante ou projeto, e arte de personagem oficial (mascote, arte promocional, render). Cada arquivo baixado tem origem (URL) e sha256 registrados.
- Quando não houver logo ou arte na internet para um sistema, a imagem é criada com base no assunto dele (por exemplo, `karaoke` e `imageviewer`), no estilo do tema.
- Um registro de origem no `LEIA-ME.txt` da feature mostra, por sistema, se a arte é oficial (com a URL), referenciada ou criada.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `es-themes`: passa a trazer o tema NES-BOX-V2, que cobre todo sistema do `es_systems.cfg` da imagem, com a origem de cada arte acrescentada registrada. O NES-BOX continua o padrão.

## Impact

- Código novo: `features/51-tema-nes-box-v2/` (descritor, camada `storage`, script de geração e `LEIA-ME.txt`), mais um teste que cruza os temas do `es_systems.cfg` com as pastas do NES-BOX-V2.
- Efeito só chega ao cartão com `--wipe-storage`, como os temas de `50-temas-extras`.
- Tamanho: cerca de 21 MiB do NES-BOX copiado, mais os PNGs novos (16 arquivos). Somando os temas extras de `50-temas-extras`, o orçamento de 400 MiB da spec `es-themes` precisa continuar valendo (a conferir no build).
- Direitos: o Readme do NES-BOX (Travis Wilson) proíbe compartilhar versões modificadas e reusar os gráficos em outros projetos. A cópia é para uso pessoal nesta imagem, e a parte copiada do NES-BOX não entra no git: o `gerar.sh` a extrai da imagem base (que já é pré-requisito do build), e um `.gitignore` gerado a mantém fora do versionamento. Logos e personagens novos são marcas e obras de terceiros, também para uso pessoal.
- Build: sem mudança no código de build. A arte nova fica no git, e nada é baixado no build.
