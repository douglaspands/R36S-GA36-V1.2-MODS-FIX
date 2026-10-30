# savestate-thumbnails Specification

## Purpose
Garantir que os save states e suas miniaturas `.png` gerados pelo RetroArch fiquem visíveis e carregáveis no Save State Manager do EmulationStation.

## Requirements

### Requirement: Gravação de save states e miniaturas na pasta lida pelo EmulationStation
A imagem gerada SHALL manter `savestate_thumbnail_enable = "true"` e `sort_savestates_enable = "false"` no `retroarch.cfg` para que o RetroArch grave `<rom>.state` e `<rom>.state.png` diretamente em `/storage/roms/savestates/<sistema>/`, sem criar subpasta por core.

#### Scenario: Configuração conferida na imagem
- **WHEN** o `retroarch.cfg` da p8 da imagem gerada é inspecionado
- **THEN** ele declara `savestate_thumbnail_enable = "true"` e `sort_savestates_enable = "false"`

#### Scenario: Salvar estado durante o jogo
- **WHEN** o usuário salva estado em um jogo Libretro
- **THEN** o arquivo `.state` e a miniatura `.state.png` são gravados em `/storage/roms/savestates/<sistema>/` e aparecem no Save State Manager do EmulationStation

### Requirement: Pasta de savestates por plataforma criada antes do jogo
Antes de iniciar qualquer emulador Libretro, o sistema SHALL garantir com `mkdir -p` a existência de `/storage/roms/savestates/<sistema>` na partição de ROMs.

#### Scenario: Primeiro save state em plataforma nova
- **WHEN** um jogo Libretro é aberto em um cartão sem `/storage/roms/savestates`
- **THEN** o diretório `/storage/roms/savestates/<sistema>` é criado antes de o RetroArch iniciar

### Requirement: Correção e migração de save states no boot em cartão já gravado
No boot, o serviço de preparação do RetroArch SHALL trocar `sort_savestates_enable = "true"` por `"false"` no `retroarch.cfg` da p8 e mover sem sobrescrever arquivos `*.state*` que estejam em subpastas `/storage/roms/savestates/<sistema>/<core>/` para `/storage/roms/savestates/<sistema>/`.

#### Scenario: Cartão gravado com --keep-storage e saves em subpasta de core
- **WHEN** o cartão tem `sort_savestates_enable = "true"` no `retroarch.cfg` e arquivos `Jogo.state` e `Jogo.state.png` em `/storage/roms/savestates/gba/gpSP/`
- **THEN** após o boot `sort_savestates_enable` vale `"false"` e `Jogo.state` e `Jogo.state.png` estão em `/storage/roms/savestates/gba/`

#### Scenario: Arquivo de mesmo nome já existente na pasta do sistema
- **WHEN** já existe `/storage/roms/savestates/gba/Jogo.state` e também `/storage/roms/savestates/gba/gpSP/Jogo.state`
- **THEN** o arquivo já existente em `/storage/roms/savestates/gba/Jogo.state` não é sobrescrito

### Requirement: Abertura de slot pelo Save State Manager do EmulationStation
Ao iniciar um jogo pelo Save State Manager do EmulationStation, o script de lançamento SHALL extrair `-autosave`, `-state_slot` e `-state_file` de `CONTROLLERCONFIG` na ordem emitida pelo EmulationStation e repassar o slot escolhido ao RetroArch.

#### Scenario: Argumentos com -autosave antes de -state_slot
- **WHEN** o EmulationStation chama o `emuelecRunEmu.sh` com `-autosave 0 -state_slot 2 -state_file "/storage/roms/savestates/gba/Jogo.state2"`
- **THEN** `CONTROLLERCONFIG` fica sem os argumentos de save state e `SNAPSHOT` recebe `2`

#### Scenario: Abertura do slot Auto sem -state_slot
- **WHEN** o EmulationStation chama o `emuelecRunEmu.sh` apenas com `-autosave 1`
- **THEN** `CONTROLLERCONFIG` fica limpo e o carregamento automático do `.state.auto` não é desfeito
