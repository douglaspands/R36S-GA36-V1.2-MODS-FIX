# Spec Delta

## Purpose

Definir qual emulador e core o Nintendinho (NES) usa por padrão na imagem gerada, priorizando a leveza no hardware do A33 sem remover as alternativas.

## ADDED Requirements

### Requirement: fceumm como core padrão do NES
A configuração do EmuELEC SHALL fazer os jogos de NES abrirem no core fceumm do RetroArch, sem o usuário precisar escolher o core.

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmuELEC declara `nes.emulator=libretro` e `nes.core=fceumm`

#### Scenario: Jogo de NES sem escolha prévia
- **WHEN** o usuário abre um jogo de NES que não tem core próprio escolhido
- **THEN** o jogo roda no fceumm, e o registro térmico traz o core `fceumm` nas linhas desse jogo

### Requirement: Outros cores de NES continuam disponíveis
Os demais cores de NES instalados na imagem base, como o nestopia, SHALL continuar instalados e selecionáveis pelo menu do EmulationStation, por sistema ou por jogo.

#### Scenario: Jogo escolhido para outro core
- **WHEN** o usuário escolhe o nestopia para um jogo específico de NES no menu do ES
- **THEN** esse jogo abre no nestopia, e os demais jogos de NES continuam no fceumm

### Requirement: Outros sistemas de Nintendo 8 bits não mudam
O padrão de core do Famicom Disk System (`fds`) SHALL permanecer o da imagem base.

#### Scenario: Configuração do FDS
- **WHEN** a configuração do EmuELEC da imagem é inspecionada
- **THEN** ela não declara `fds.core`
