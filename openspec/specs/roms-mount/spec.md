# roms-mount Specification

## Purpose

Definir as opções de montagem da partição de ROMs no aparelho, para que ler ROMs não gere escritas no cartão.

## Requirements

### Requirement: ROMs montadas sem atime
Depois que o sistema monta a partição de ROMs em `/storage/roms`, ela SHALL ficar montada com `noatime`, mantendo as demais opções.

#### Scenario: Boot
- **WHEN** o aparelho termina o boot com a p1 montada
- **THEN** `/proc/mounts` mostra `/storage/roms` com `noatime`, e as ROMs e os saves gravados na p1 continuam acessíveis para leitura e escrita

#### Scenario: ROMs não montadas
- **WHEN** `/storage/roms` não é um ponto de montagem
- **THEN** nada é remontado, e o boot continua normalmente

### Requirement: Pasta ports_scripts da p1 sem overlay
`/storage/roms/ports_scripts`, pasta do sistema "Ports", SHALL continuar sendo a pasta FAT32 da partição de ROMs, e nenhuma feature SHALL criar `/usr/bin/ports`: esse é o `lowerdir` do overlay que o `mount_romfs.sh` tenta montar ali, e com ele presente o overlay esconde a p1. Arquivos que precisem sobreviver a `--keep-roms` SHALL ficar no SYSTEM e ser restaurados na p1 por um serviço de boot ordenado antes do `emustation.service`, que espera o `mount_romfs.sh` montar `/storage/roms`. Esse serviço SHALL NOT ter `After=emuelec-autostart.service`: o autostart só termina depois de iniciar o ES com `systemctl start emustation`, e essa ordem trava o boot.

#### Scenario: Port copiado pelo PC
- **WHEN** o usuário copia um script `.sh` para `R36-ROMS/ports_scripts/` no PC e liga o aparelho
- **THEN** o script aparece no menu "Ports" do EmulationStation

#### Scenario: Serviço de restauração no boot
- **WHEN** o aparelho dá boot com um serviço que restaura arquivos na p1 antes do ES
- **THEN** o boot sai do splash e o EmulationStation abre, com os arquivos já restaurados

#### Scenario: Build com feature que cria /usr/bin/ports
- **WHEN** alguma feature traz arquivos em `system/usr/bin/ports/`
- **THEN** os testes do projeto falham antes da gravação
