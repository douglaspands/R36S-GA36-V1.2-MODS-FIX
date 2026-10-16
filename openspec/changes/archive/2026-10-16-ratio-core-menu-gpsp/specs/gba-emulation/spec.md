# Spec Delta

## Purpose

Definir qual emulador e core o Game Boy Advance usa por padrão na imagem gerada, priorizando a leveza no hardware do A33 sem remover as alternativas.

## ADDED Requirements

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
