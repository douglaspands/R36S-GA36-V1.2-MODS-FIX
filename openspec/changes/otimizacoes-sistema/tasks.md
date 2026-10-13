# Tasks

## 1. Feature 40-zram-swap

- [x] 1.1 Criar `features/40-zram-swap/feature.toml` (`order = 40`, `enabled = true`) com `[[remove]]` de `.cache/swapfile` na camada `storage`. Verificar com `./build.sh --features 40-zram-swap` que a remoção aparece no `changes.txt`.
- [x] 1.2 Adicionar `system/usr/lib/r36/zram-swap` (executável): `MemTotal`/2 em `/sys/block/zram0/disksize`, `mkswap`, `swapon -p 32767`, registro no journal (`logger`) e saída 0 em qualquer falha. Adicionar `system/usr/lib/systemd/system/r36-zram-swap.service` e o link `basic.target.wants/r36-zram-swap.service`. Verificar com `bash -n` no script e com um teste rápido em `tests/` que confere as diretivas da unit (`DefaultDependencies=no`, `Before=swap.target`) e que o link aponta para a unit.
- [x] 1.3 Adicionar `storage/.config/swap.conf` com `SWAP_ENABLED="no"`. Verificar no teste rápido que o arquivo define essa variável e que o `mount-swap` da base o lê (`/storage/.config/swap.conf`).

## 2. Feature 41-servicos-enxutos

- [x] 2.1 Criar `features/41-servicos-enxutos/feature.toml` (`order = 41`, `enabled = true`) com `[[remove]]` na camada `system` dos 5 links: `usr/lib/systemd/system/sockets.target.wants/lircd.socket` e `multi-user.target.wants/{lircd,lircd-uinput,eventlircd,cron}.service`. Verificar com `./build.sh --features 41-servicos-enxutos` que o `changes.txt` lista exatamente essas 5 remoções e que as units em `usr/lib/systemd/system/` continuam no SYSTEM gerado (`unsquashfs -lls`).

## 3. Feature 42-roms-noatime

- [x] 3.1 Criar `features/42-roms-noatime/feature.toml` (`order = 42`, `enabled = true`), o script `system/usr/lib/r36/roms-noatime` (só remonta se `/storage/roms` for ponto de montagem e ignora falhas), a unit `r36-roms-noatime.service` (`Type=oneshot`, `After=emuelec-autostart.service`) e o link em `emuelec.target.wants/`. Verificar com `bash -n` e com um teste rápido que confere `After=` e o link.

## 4. Documentação

- [x] 4.1 Adicionar as três features ao README: o que cada uma faz, que zram, serviços e `noatime` valem com qualquer gravação do SYSTEM, e que a remoção do swapfile exige `--wipe-storage`. Incluir como apagar o swapfile antigo à mão num cartão gravado com `--keep-storage`. Verificar que os comandos citados existem.

## 5. Integração (build e inspeção pelo PC)

- [x] 5.1 Rodar `./build.sh` com todas as features e verificar no `changes.txt` as adições, as 5 remoções de links, a remoção do swapfile, e que nenhuma feature conflita com 10, 20 ou 30.
- [x] 5.2 Inspecionar o build somente leitura: os links novos apontam para as units (`unsquashfs -lls`); a p8 não tem `.cache/swapfile` e tem pelo menos 300 MB livres a mais que a base (`debugfs -R stats`); `e2fsck -fn` passa.
- [x] 5.3 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage` e verificar que termina com "verificado". Rodar a suíte completa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`) e verificar que ela passa.

## Workflow follow-up

- O usuário grava o cartão com `--wipe-storage` e valida no aparelho (por SSH ou terminal):
  - `cat /proc/swaps` mostra só `/dev/zram0` com a maior prioridade;
  - `systemctl is-active lircd eventlircd cron` mostra `inactive`;
  - `grep /storage/roms /proc/mounts` mostra `noatime`;
  - controle, hotkeys, volume, brilho, bateria, fone e um jogo pesado (PS1/N64) funcionam.
- Commit na branch `feat/otimizacoes-sistema` quando o usuário pedir. Arquivar com `/opsx:archive`.
