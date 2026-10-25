# Proposal

## Why

Na última entrega, foram observados problemas e necessidades de ajuste no console clone do R36S (Allwinner A33):
1. **Lançamento e Imagem do ClassiCube (Minecraft / Classic Craft):**
   - O jogo encerra imediatamente ao ser acionado no menu "Ports" do EmulationStation porque o inicializador repassa os argumentos do ES (`-Pports --core=ports ...`), que o ClassiCube tenta interpretar como dados de rede multiplayer (`ARG_RESULT_INVALID_ARGS`).
   - A imagem/capa (boxart) do jogo não está aparecendo na lista do EmulationStation para o usuário.
2. **Tela de Carregamento de Jogos (God of War residual):**
   - Ao abrir um jogo em um cartão gravado com `--keep-storage` ou `--part system`, a tela de carga exibe a arte legada do God of War em vez do ícone de controle padronizado, pois o `emuelecRunEmu.sh` lê exclusivamente de `/storage/.config/splash/loading-game.png` (p8).
3. **Reorganização de Temas (Epic Cody como padrão na partição default e NES-BOX no cartão):**
   - O usuário quer que o tema **Epic Cody** seja o tema padrão do sistema e fique instalado na partição default do sistema (`storage`, p8).
   - O tema **NES-BOX** deve ser movido para a partição do cartão SD (`roms`, FAT32 em `themes/NES-BOX`), liberando o armazenamento interno e mantendo o tema acessível.

## What Changes

- **Port ClassiCube / Classic Craft (`features/60-port-classicube`):**
  - Ajusta o script `ClassiCube.sh` para iniciar diretamente com `--singleplayer` sem repassar flags externas do ES.
  - Atualiza o `gamelist.xml` com tags completas (`<image>`, `<thumbnail>`, `<marquee>`), nome legível ("Classic Craft (ClassiCube)") e garante os arquivos de imagem em `ports_scripts/img/` e `ports_scripts/images/` para exibição garantida em qualquer modo de exibição de lista (basic, detailed, video, grid).
- **Tela de Carregamento Neutra (`features/10-ptbr-sao-paulo`):**
  - Ajusta o `emuelecRunEmu.sh` para priorizar a leitura de `/usr/config/splash/loading-game.png` (camada `SYSTEM`), garantindo que o ícone do controle apareça em todas as telas de carga, mesmo em atualizações parciais (`--keep-storage` ou `--part system`).
- **Temas do EmulationStation (`features/50-temas-extras` e `features/10-ptbr-sao-paulo`):**
  - Move o tema **Epic Cody** para a camada `storage` (`.config/emulationstation/themes/Epic Cody`), tornando-o nativo da partição do sistema.
  - Define o **Epic Cody** como tema padrão de fábrica em `es_settings.cfg` (`<string name="ThemeSet" value="Epic Cody" />`).
  - Move o tema **NES-BOX** para a camada `roms` (`themes/NES-BOX` na partição FAT32 do cartão), removendo a duplicata pesada da partição `storage`.

## Capabilities

### New Capabilities
Nenhuma.

### Modified Capabilities
- `classicube-port`: ajusta o requisito de inicialização para execução local direta (`--singleplayer`) e a disponibilidade dos metadados e imagem de capa na lista de jogos.
- `splash-screens`: ajusta o requisito da tela de carregamento para usar a imagem do SYSTEM de forma resiliente a `--keep-storage`.
- `es-themes`: atualiza o tema padrão para Epic Cody, instala-o no storage e move o NES-BOX para a partição de ROMs do cartão.

## Impact

- **Inicializador de Ports:** `features/60-port-classicube/roms/ports_scripts/ClassiCube.sh` e `gamelist.xml` ajustados para lançamento estável e exibição correta da capa.
- **Transição de Emuladores:** `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh` busca a splash padronizada do controle na partição `SYSTEM`.
- **Configuração e Temas:** `features/50-temas-extras/feature.toml` e `features/10-ptbr-sao-paulo/storage/.config/emulationstation/es_settings.cfg` alterados para promover o Epic Cody a padrão e mover o NES-BOX para o cartão.
