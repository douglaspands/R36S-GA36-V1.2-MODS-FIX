# Proposal

## Why

A imagem de fábrica usa um swapfile de 300 MB no próprio cartão SD (`/storage/.cache/swapfile`). Isso gasta 300 MB da p8 de 1,5 GiB, pagina devagar e desgasta o cartão. O kernel (sunxi 3.4.39) já tem zram embutido, que faz swap comprimido em RAM. Além disso, o boot sobe serviços de controle remoto infravermelho e de agendamento que não servem para um portátil, e a partição de ROMs (FAT32) é montada atualizando a data de acesso dos arquivos.

## What Changes

- **A, swap em zram:** o swap passa a ser um dispositivo zram com metade da RAM, com prioridade maior que qualquer swap em arquivo. O swapfile de 300 MB sai da p8 e fica desligado na configuração de swap do STORAGE.
- **C, serviços enxutos:** deixam de subir no boot `lircd.socket`, `lircd.service`, `lircd-uinput.service` e `eventlircd.service` (controle remoto IR/USB, inexistente no R36S) e `cron.service` (não há crontabs). `wsdd2` e `iptables` já não iniciam (dependem de samba e de um arquivo de configuração ausentes) e ficam como estão.
- **D, ROMs sem atime:** a p1 (FAT32, `/storage/roms`) é remontada com `noatime` depois de montada pelo sistema. A p8 já é montada com `noatime` pelo initramfs e não muda.
- Três features novas, para poder desligar cada otimização separadamente: `40-zram-swap`, `41-servicos-enxutos` e `42-roms-noatime`.
- **No cartão:** o zram, os serviços e o `noatime` estão no SYSTEM e valem com qualquer gravação. A remoção do swapfile e o desligamento do swap em arquivo estão no STORAGE e só chegam com `--wipe-storage`. Com `--keep-storage`, o swapfile antigo continua existindo, mas o zram tem prioridade.

## Capabilities

### New Capabilities
- `swap-memory`: onde o sistema faz swap e com que prioridade.
- `system-services`: quais serviços do EmuELEC sobem no boot da imagem gerada.
- `roms-mount`: opções de montagem da partição de ROMs no aparelho.

### Modified Capabilities
(nenhuma)

## Impact

- Novos diretórios `features/40-zram-swap/`, `features/41-servicos-enxutos/` e `features/42-roms-noatime/`.
- SYSTEM: duas units novas com seus scripts (zram e remount das ROMs), os links de ativação delas e a remoção de 5 links em `usr/lib/systemd/system/*.wants/`.
- STORAGE: `.config/swap.conf` novo e remoção de `.cache/swapfile` (libera 300 MB na p8).
- Nenhuma mudança em `tools/r36img/`, salvo se a remoção de symlinks ou a adição de links de ativação não forem suportadas. Isso é verificado na primeira tarefa.
- Kernel, initramfs e U-Boot não mudam.
