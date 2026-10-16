# Spec Delta

## Purpose

Definir qual emulador e core o Capcom Play System 2 usa por padrão na imagem gerada, priorizando o desempenho no hardware do A33 sem remover as alternativas.

## ADDED Requirements

### Requirement: fbalpha2012 como core padrão do CPS2
A configuração do EmuELEC SHALL fazer os jogos de CPS2 abrirem no core fbalpha2012 do RetroArch, sem o usuário precisar escolher o core.

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmuELEC declara `cps2.emulator=libretro` e `cps2.core=fbalpha2012`

#### Scenario: Jogo de CPS2 sem escolha prévia
- **WHEN** o usuário abre um jogo de CPS2 que não tem core próprio escolhido
- **THEN** o jogo roda no fbalpha2012, e o registro térmico traz o core `fbalpha2012` nas linhas desse jogo

### Requirement: Outros cores de CPS2 continuam disponíveis
O fbneo, o mame2003_plus, o mame2010 e o AdvanceMame SHALL continuar instalados e selecionáveis pelo menu do EmulationStation, por sistema ou por jogo.

#### Scenario: Jogo escolhido para outro core
- **WHEN** o usuário escolhe o fbneo para um jogo específico de CPS2 no menu do ES
- **THEN** esse jogo abre no fbneo, e os demais jogos de CPS2 continuam no fbalpha2012

### Requirement: Outros sistemas de arcade não mudam
O padrão de core do CPS1, do CPS3, do Neo Geo, do FBNeo e do MAME SHALL permanecer o da imagem base.

#### Scenario: Jogo de CPS1
- **WHEN** o usuário abre um jogo de CPS1 sem core próprio escolhido
- **THEN** o core usado é o mesmo da imagem base, e a configuração do EmuELEC não declara `cps1.core`
