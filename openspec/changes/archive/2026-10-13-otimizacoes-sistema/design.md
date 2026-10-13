# Design

## Context

- **Kernel:** sunxi 3.4.39, sem código-fonte. A imagem do kernel (p6) contém `drivers/staging/zram/zram_drv.c` e o parâmetro `zram.num_devices`, então o zram está embutido. Ele usa a interface antiga: `/sys/block/zram0/disksize`, compressão LZO fixa e sem `comp_algorithm`.
- **Swap atual:** o `swap.service` (em `basic.target`) roda `/usr/lib/libreelec/mount-swap`. Ele lê `/etc/swap.conf` e, por cima, `/storage/.config/swap.conf`, e cria e ativa `/storage/.cache/swapfile` (300 MiB) com `swapon -p 10000`. O swapfile já vem pronto na p8 da base. `vm.swappiness=10`.
- **Montagens (initramfs):** `/storage` é montada com `rw,noatime`. A p1 é montada como `vfat` só com `-o utf8`. O `mount_romfs.sh` (chamado no `emuelec_autostart.sh`) pode remontar a p1 com as mesmas opções em casos de recuperação.
- **Serviços:** os links de ativação ficam em `usr/lib/systemd/system/*.wants/` no SYSTEM. A regra udev `98-eventlircd.rules` só marca controles remotos (IR, USB HID de remotos, BD/Wii remotes), não o `udt_joystick`. `cron` não tem crontabs (`/storage/.cache/cron/crontabs` vazio).
- **Build:** as camadas `system` e `storage` aceitam symlinks, e `[[remove]]` remove caminhos da base.

## Goals / Non-Goals

**Goals:**
- Cada otimização é uma feature separada, que pode ser desligada sozinha.
- Nada que dependa de recompilar ou reempacotar kernel ou initramfs.

**Non-Goals:**
- Ajustar `vm.swappiness`, o governor de CPU ou o `commit` do ext4. Ficam para depois de medir no aparelho.
- Pular os `rsync` do `emuelec_autostart.sh` (item B da exploração, adiado).
- Mudar a montagem da p8: ela já usa `noatime`.

## Decisions

1. **zram por unit própria no SYSTEM, não pela configuração de swap do LibreELEC.** O `mount-swap` só sabe criar arquivo de swap. Então entra uma unit nova `r36-zram-swap.service` (`Type=oneshot`, `RemainAfterExit=yes`, `DefaultDependencies=no`, `Before=swap.target`, ativada em `basic.target.wants`). Ela chama um script `usr/lib/r36/zram-swap`, que:
   - lê `MemTotal`;
   - grava metade em bytes em `/sys/block/zram0/disksize`;
   - roda `mkswap /dev/zram0` e `swapon -p 32767 /dev/zram0`.

   Se `/dev/zram0` não existir ou se algum passo falhar, o script registra no journal e sai com 0, para não travar o boot. A prioridade 32767 (a máxima) fica acima dos 10000 do swapfile, o que importa com `--keep-storage`, quando o swapfile antigo continua lá.
   - Alternativa descartada: colocar a unit em `/storage/.config/system.d`. Com `--keep-storage`, ela não chegaria ao cartão.

2. **Swapfile: remoção no STORAGE mais `SWAP_ENABLED="no"`.** A feature `40-zram-swap` declara `[[remove]]` de `.cache/swapfile` na camada `storage` e adiciona `storage/.config/swap.conf` com `SWAP_ENABLED="no"`, para o `mount-swap` não recriar o arquivo. O `swap.service` continua habilitado e sai cedo ("swap disabled via configfile"). Alternativa descartada: remover o `swap.service`. Isso mexeria em mais um link e ainda deixaria o swapfile ocupando a p8.

3. **Serviços: remoção dos links de ativação, não das units.** A feature `41-servicos-enxutos` remove só os links:
   - `sockets.target.wants/lircd.socket`;
   - `multi-user.target.wants/lircd.service`;
   - `multi-user.target.wants/lircd-uinput.service`;
   - `multi-user.target.wants/eventlircd.service`;
   - `multi-user.target.wants/cron.service`.

   As units e os binários ficam, então qualquer serviço pode ser religado depois. `wsdd2` (`BindsTo=smbd.service`) e `iptables` (`ConditionPathExists` de um arquivo ausente) não sobem hoje e ficam como estão.
   - Alternativa descartada: `systemctl mask` via symlink para `/dev/null` em `/etc/systemd/system`. O `/etc` do LibreELEC é parcialmente regenerado, e remover o link é mais simples de auditar no `changes.txt`.

4. **ROMs: remount depois do autostart.** A feature `42-roms-noatime` adiciona a unit `r36-roms-noatime.service` (`Type=oneshot`, `After=emuelec-autostart.service`, ativada em `emuelec.target.wants`). Ela roda `mountpoint -q /storage/roms && mount -o remount,noatime /storage/roms`. Rodar depois do autostart garante que o `mount_romfs.sh` já terminou, inclusive nas remontagens de recuperação. Alternativa descartada: mudar o `mount` do initramfs, que exigiria reempacotar a p6.

5. **Ordem das features: 40, 41 e 42, sem sobreposição de caminhos.** Nenhuma toca arquivos das features 10, 20 ou 30, então não é preciso `[[override]]`.

## Risks / Trade-offs

- [Algum controle ou atalho depende do `eventlircd`] → A regra udev mostra que ele só trata remotos. A validação no aparelho cobre controle, hotkeys, volume e brilho. Rollback: `enabled = false` na feature 41.
- [zram de metade da RAM aperta jogos pesados] → O zram só ocupa RAM com o que é de fato paginado, comprimido (tipicamente 2:1 a 3:1). Com `swappiness=10`, ele é pouco usado. Se houver travamento, reduzir para 25% é uma mudança de uma linha.
- [`--keep-storage` mantém o swapfile] → O zram tem prioridade maior, então o swapfile só é usado se o zram encher. O README explica como apagar o swapfile manualmente, se o usuário quiser.
- [O remount da p1 falha em algum cenário (ex.: ROMs em USB)] → O script só remonta se `/storage/roms` for ponto de montagem, ignora falhas e não bloqueia o EmulationStation.

## Migration Plan

1. Build e conferência do `changes.txt`: units, scripts e links adicionados; 5 links removidos; `swap.conf` adicionado e `swapfile` removido.
2. Inspeção pelo PC: `unsquashfs -lls` dos links e `debugfs` da p8.
3. Gravação com `--wipe-storage` e validação no aparelho (`/proc/swaps`, `systemctl is-active`, `/proc/mounts`).
4. Rollback: desligar a feature específica e gerar de novo.
