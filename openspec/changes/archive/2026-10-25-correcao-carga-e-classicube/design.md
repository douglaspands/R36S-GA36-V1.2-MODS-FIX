# Design

## Context

O console R36S clone (Allwinner A33) executa EmuELEC 4.7 com três partições principais:
1. `SYSTEM` (`p5`, squashfs `/` somente leitura): contém `/usr/bin/emuelecRunEmu.sh` e telas padrão em `/usr/config/splash/`.
2. `STORAGE` (`p8`, ext4 `/storage`): configurações e temas locais (`.config/emulationstation/themes/`). Possui ~960 MiB livres na base atual.
3. `ROMS` (`p1`, FAT32 `/storage/roms`): armazena ROMs, scripts em `ports_scripts/` e temas ricos em mídia em `themes/`.

Consulte o `proposal.md` para motivação e o `specs/` para os requisitos normativos.

## Goals / Non-Goals

**Goals:**
- Garantir que o ClassiCube inicie diretamente com `--singleplayer` e exiba imagem/capa no menu "Ports".
- Fazer com que o `emuelecRunEmu.sh` busque a imagem da tela de carregamento na partição `SYSTEM` (`/usr/config/splash/loading-game.png`), garantindo que o ícone do controle apareça mesmo em cartões gravados com `--keep-storage`.
- Mover o tema `Epic Cody` para a partição default (`storage`, `.config/emulationstation/themes/Epic Cody`) e torná-lo o padrão ativo em `es_settings.cfg`.
- Mover o tema `NES-BOX` para a partição de ROMs do cartão (`roms`, `themes/NES-BOX`), removendo a cópia do `storage` para não ocupar espaço interno.

**Non-Goals:**
- Não recompilar o binário C do ClassiCube (o binário atual é compatível com ARMv7-A e GLES2).
- Não alterar o `bootlogo.bmp` do U-Boot na partição `boot` (p2) nesta change.

## Decisions

### 1. Invocação direta do ClassiCube com `--singleplayer` e metadados completos
- **Decisão:** Em `features/60-port-classicube/roms/ports_scripts/ClassiCube.sh`, invocar `"$BIN" --singleplayer`. Em `ports_scripts/gamelist.xml`, fornecer tags `<image>`, `<thumbnail>` e `<marquee>` apontando para `./img/ClassiCube.png` e sincronizar arquivos nas pastas `img/` e `images/`.
- **Racional:** Sem parâmetros do ES, o jogo não tenta interpretar flags como dados de servidor multiplayer. A inclusão de todas as tags de imagem garante que qualquer visualização do ES (detailed, video, grid) renderize a capa do jogo.

### 2. Leitura da tela de carregamento a partir do SYSTEM em `emuelecRunEmu.sh`
- **Decisão:** Em `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`, definir a imagem de splash de jogo com fallback seguro:
  ```bash
  SPLASH_IMG="/usr/config/splash/loading-game.png"
  [ ! -f "$SPLASH_IMG" ] && SPLASH_IMG="/storage/.config/splash/loading-game.png"
  mpv "$SPLASH_IMG" &
  ```
- **Racional:** A partição `SYSTEM` contém o ícone neutro do controle e é sempre atualizada. Lendo do `SYSTEM`, elimina-se a dependência do arquivo legado do God of War que persiste no `storage` quando o usuário usa `--keep-storage` ou `--part system`.

### 3. Epic Cody padrão no storage e NES-BOX no cartão
- **Decisão:**
  - Em `features/50-temas-extras/feature.toml`:
    - `Epic Cody` passa a ter `layer = "storage"` e `dest = ".config/emulationstation/themes/Epic Cody"`.
    - Declara remoção da cópia do `NES-BOX` da partição storage:
      ```toml
      [[remove]]
      layer = "storage"
      path = ".config/emulationstation/themes/NES-BOX"
      ```
    - Extrai e inclui os assets do `NES-BOX` de fábrica na camada `roms` em `themes/NES-BOX`.
  - Em `features/10-ptbr-sao-paulo/storage/.config/emulationstation/es_settings.cfg`:
    - Alterar `<string name="ThemeSet" value="NES-BOX" />` para `<string name="ThemeSet" value="Epic Cody" />`.
- **Racional:** O `storage` tem quase 1 GiB livre; os ~200 MiB do Epic Cody cabem com ampla folga, tornando o tema mais sofisticado e moderno o padrão logo após a gravação. O NES-BOX continua disponível na partição FAT32 do cartão em `themes/NES-BOX`, onde o EmulationStation o detecta automaticamente.

## Risks / Trade-offs

- **[Risco] O usuário personalizou manualmente o arquivo `/storage/.config/splash/loading-game.png`:**
  - *Mitigação:* Telas customizadas por jogo continuam tendo prioridade máxima através de `/storage/roms/splash/<sistema>/` ou `/storage/roms/splash/<sistema>.png`.
- **[Risco] Limite de tamanho da partição `storage`:**
  - *Mitigação:* `storage.img` tem 1536 MiB e mais de 900 MiB livres. Epic Cody ocupa cerca de 200 MiB, deixando mais de 700 MiB livres para RetroArch e saves.
