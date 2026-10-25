# sega32x-emulation Specification

## Purpose
Definir os requisitos de emulação do sistema Sega 32X na imagem do R36S (GA36-MB V1.2), disponibilizando uma variante do PicoDrive compilada especificamente para o Allwinner A33 sem remover o core original da base.

## Requirements

### Requirement: PicoDrive recompilado para o A33 (picodrive_a33)
A imagem SHALL trazer o core `picodrive_a33`, compilado pelo `./cores.sh` a partir de uma receita versionada com otimizações para a arquitetura Cortex-A7 do A33 e Dynarec ARM SH-2 habilitado, ao lado do `picodrive` original da imagem base e sem substituí-lo.

#### Scenario: Core original preservado
- **WHEN** a partição SYSTEM da imagem gerada é comparada com a da base
- **THEN** `picodrive_libretro.so` e `picodrive_libretro.info` permanecem inalterados, e `picodrive_a33_libretro.so` e `picodrive_a33_libretro.info` são adicionados em `/usr/lib/libretro`

#### Scenario: Disponibilidade no EmulationStation
- **WHEN** o arquivo `es_systems.cfg` da imagem gerada é inspecionado
- **THEN** a entrada `<core>picodrive_a33</core>` está presente na lista de cores do sistema `sega32x`, permitindo sua seleção no menu do EmulationStation

#### Scenario: Compatibilidade de saves e opções
- **WHEN** um usuário alterna a execução de um jogo de 32X entre o `picodrive` original e o `picodrive_a33`
- **THEN** o `picodrive_a33` reconhece e carrega os mesmos arquivos de save de bateria (.srm) e preserva as opções de core aplicadas
