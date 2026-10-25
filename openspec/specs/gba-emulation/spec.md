# gba-emulation Specification

## Purpose
Definir qual emulador e core o Game Boy Advance usa por padrão na imagem gerada, priorizando a leveza no hardware do A33 sem remover as alternativas.

## Requirements

### Requirement: gpSP como core padrão do GBA
A configuração do EmuELEC SHALL fazer os jogos de Game Boy Advance abrirem no core gpSP do RetroArch, sem o usuário precisar escolher o core.

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmuELEC declara `gba.emulator=libretro` e `gba.core=gpsp`

#### Scenario: Jogo de GBA sem escolha prévia
- **WHEN** o usuário abre um jogo de GBA que não tem core próprio escolhido
- **THEN** o jogo roda no gpSP

### Requirement: Outros cores de GBA continuam disponíveis
O mGBA, o vbam e o vba_next SHALL continuar instalados e selecionáveis pelo menu do EmulationStation, por sistema ou por jogo.

#### Scenario: Jogo escolhido para outro core
- **WHEN** o usuário escolhe o mGBA para um jogo específico no menu do ES
- **THEN** esse jogo abre no mGBA, e os demais continuam no gpSP

### Requirement: Jogos de GBA rodam sem BIOS de GBA
O padrão gpSP SHALL funcionar sem o arquivo `gba_bios.bin`, e a imagem NÃO SHALL exigir que o usuário o forneça.

#### Scenario: Cartão sem a BIOS
- **WHEN** não existe `gba_bios.bin` em `/storage/roms/bios` e o usuário abre um jogo de GBA
- **THEN** o gpSP inicia o jogo com a BIOS interna do core

### Requirement: Presença dos shaders de remasterização do GBA
A imagem gerada SHALL incluir os arquivos `gba-modern-remaster.glsl` e `gba-modern-remaster.glslp` em `/usr/share/common-shaders/gba/`, na partição SYSTEM, que é a camada de baixo do overlay `/tmp/shaders`.

#### Scenario: Arquivos no SYSTEM
- **WHEN** o SYSTEM da imagem gerada é inspecionado
- **THEN** `usr/share/common-shaders/gba/gba-modern-remaster.glsl` e `.glslp` estão presentes com permissão `0644` e dono `0:0`

#### Scenario: Atualização com --keep-storage
- **WHEN** o cartão é gravado com `--keep-storage`
- **THEN** o shader fica disponível em `/tmp/shaders/gba/`, porque vem do SYSTEM e não da p8

#### Scenario: Sintaxe do preset de shader
- **WHEN** o arquivo `gba-modern-remaster.glslp` é lido
- **THEN** ele define `shaders = "1"` e aponta para `shader0 = "gba-modern-remaster.glsl"` com `filter_linear0 = "true"`

### Requirement: Shader do GBA opcional, escolhido no EmulationStation
O shader `gba-modern-remaster` SHALL ficar desligado por padrão e SHALL poder ser ligado pelo usuário na opção "SHADER SET" do EmulationStation, que lista os `.glslp` de `/tmp/shaders`. A imagem SHALL NOT trazer preset automático do RetroArch (`.glslp` em `/storage/.config/retroarch/config/<core>/`) para ele, porque esse preset ligaria o shader sempre e passaria por cima da escolha feita no ES.

#### Scenario: Padrão de fábrica
- **WHEN** o usuário abre um jogo de GBA sem ter escolhido shader no EmulationStation
- **THEN** o jogo roda sem shader, como na imagem base

#### Scenario: Escolha no EmulationStation
- **WHEN** o usuário escolhe `gba/gba-modern-remaster.glslp` em "SHADER SET" nas configurações avançadas do sistema GBA e abre um jogo
- **THEN** o RetroArch abre o jogo com o shader `gba-modern-remaster` aplicado

#### Scenario: Volta ao padrão
- **WHEN** o usuário troca o "SHADER SET" do GBA de volta para nenhum
- **THEN** os jogos seguintes de GBA abrem sem shader
