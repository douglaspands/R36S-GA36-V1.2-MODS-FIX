# Spec Delta: roms-mount

## ADDED Requirements

### Requirement: Pasta ports_scripts da p1 sem overlay
`/storage/roms/ports_scripts`, pasta do sistema "Ports", SHALL continuar sendo a pasta FAT32 da partição de ROMs, e nenhuma feature SHALL criar `/usr/bin/ports`: esse é o `lowerdir` do overlay que o `mount_romfs.sh` tenta montar ali, e com ele presente o overlay esconde a p1. Arquivos que precisem sobreviver a `--keep-roms` SHALL ficar no SYSTEM e ser restaurados na p1 por um serviço de boot posterior a `emuelec-autostart.service`.

#### Scenario: Port copiado pelo PC
- **WHEN** o usuário copia um script `.sh` para `R36-ROMS/ports_scripts/` no PC e liga o aparelho
- **THEN** o script aparece no menu "Ports" do EmulationStation

#### Scenario: Build com feature que cria /usr/bin/ports
- **WHEN** alguma feature traz arquivos em `system/usr/bin/ports/`
- **THEN** os testes do projeto falham antes da gravação
