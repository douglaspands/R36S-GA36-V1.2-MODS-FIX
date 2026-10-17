# Spec Delta

## Purpose

Definir qual emulador e core o Super Nintendo usa por padrão na imagem gerada, priorizando a leveza no hardware do A33 sem remover as alternativas.

## ADDED Requirements

### Requirement: snes9x2005_plus como core padrão do SNES
A configuração do EmuELEC SHALL fazer os jogos de Super Nintendo abrirem no core snes9x2005_plus do RetroArch, sem o usuário precisar escolher o core.

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmuELEC declara `snes.emulator=libretro` e `snes.core=snes9x2005_plus`

#### Scenario: Jogo de SNES sem escolha prévia
- **WHEN** o usuário abre um jogo de SNES que não tem core próprio escolhido
- **THEN** o jogo roda no snes9x2005_plus, e o registro térmico traz o core `snes9x2005_plus` nas linhas desse jogo

### Requirement: Outros cores de SNES continuam disponíveis
O snes9x, o snes9x2002 e o snes9x2010 SHALL continuar instalados e selecionáveis pelo menu do EmulationStation, por sistema ou por jogo.

#### Scenario: Jogo escolhido para outro core
- **WHEN** o usuário escolhe o snes9x para um jogo específico de SNES no menu do ES
- **THEN** esse jogo abre no snes9x, e os demais jogos de SNES continuam no snes9x2005_plus

### Requirement: Variantes do SNES não mudam
O padrão de core dos sistemas `snesh` e `snesmsu1` SHALL permanecer o da imagem base.

#### Scenario: Configuração das variantes
- **WHEN** a configuração do EmuELEC da imagem é inspecionada
- **THEN** ela não declara `snesh.core` nem `snesmsu1.core`
