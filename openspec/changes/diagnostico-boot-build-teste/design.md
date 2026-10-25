# Design

## Context

Veja `proposal.md` (Why) para a motivação. Fatos conferidos na imagem base que moldam a solução:

- **Kernel sem console na tela:** a configuração embutida no kernel (p6) tem `CONFIG_VT=y`, `CONFIG_DUMMY_CONSOLE=y`, `CONFIG_FB=y`, `CONFIG_FB_SUNXI=m` e `# CONFIG_FRAMEBUFFER_CONSOLE is not set`. Existem VTs (`/dev/tty0`, `/dev/tty1`), mas nada do kernel nem do systemd chega ao display. O env do U-Boot (p5, 128 KiB com CRC32) usa `console=ttyS2,115200 loglevel=0`.
- **Imagem do controle:** o `init` do initramfs (LibreELEC) desenha o splash no `/dev/fb0` com `splash-image`. Ninguém redesenha a tela até o EmulationStation abrir.
- **Ferramentas no SYSTEM:** `/usr/bin/fbterm` (terminal que desenha direto no framebuffer, sem console do kernel), `libfontconfig`, `/etc/fonts/fonts.conf`, a fonte `/usr/share/fonts/liberation`, `journalctl`, `timeout`, `setterm` e `chvt`.
- **Ordem do boot:** o `emuelec-autostart.service` (oneshot) roda o `mount_romfs.sh`, que monta a p1 em `/storage/roms`, e termina com `systemctl start emustation` síncrono. O `emustation.service` tem `ConditionPathExists=/var/lock/start.games` e `Restart=always`. A p7 fica em `/flash`, montada só leitura (o `mount_romfs.sh` a remonta em leitura e escrita para gravar `ee_fstype`).
- **Seleção de features:** `features.select(all, names, none)` em `tools/r36img/features.py`. O `build.py` já recebe `test` e o usa só para nome, manifest e `R36-BUILD.txt`.

## Goals / Non-Goals

**Goals:**
- Ver o journal na tela durante o boot de um build de teste, e o último estado se ele travar.
- Ter um retrato em texto no cartão, legível no PC sem root, mesmo que o boot trave antes de a p1 montar.
- Build normal byte a byte igual ao de hoje.

**Non-Goals:**
- Mostrar mensagens do kernel antes de o systemd subir (exige kernel com console na tela, e o fonte não é público).
- Alterar a p5 ou a p6. A spec `image-build` exige que fiquem idênticas à base, e a imagem do controle continua aparecendo até o `fbterm` abrir.
- Usar a serial `ttyS2` (exige abrir o aparelho).
- Journal persistente na p8 (ext4 de root, não dá para ler no PC sem root).

## Decisions

### 1. Campo `test_only` no descritor, aplicado pela seleção
`load_feature` aceita `test_only` (booleano, padrão `false`). `select(all, names, none, test=False)`:
- padrão: habilitadas, menos as `test_only` quando `test` é falso;
- `names`: se alguma pedida é `test_only` e `test` é falso, falha com mensagem;
- `none`: nenhuma, como hoje.

O manifest e o `R36-BUILD.txt` já listam as features aplicadas, então registram as de teste sem mudança.
**Alternativa descartada:** uma pasta separada (`features-test/`), que duplicaria descoberta, ordem e conflitos.

### 2. Duas features, uma por saída
`90-boot-log-tela` e `91-boot-log-cartao`, ambas `test_only = true` e `enabled = true`. Ordem 90 para ficarem depois de todas as normais. Separadas para desligar uma sem a outra, por exemplo se o `fbterm` atrapalhar o display.

### 3. Tela: `fbterm` num VT, encerrado pelo ES
- `r36-boot-log-tela.service`: `Type=simple`, `DefaultDependencies=no`, `After=systemd-journald.service`, `WantedBy=sysinit.target`, para subir o mais cedo possível. Sem ordem em relação ao autostart ou ao ES.
- `ExecStart=/usr/lib/r36/boot-log-tela` roda `fbterm` em `/dev/tty1` (`TTYPath=/dev/tty1`, `StandardInput=tty`, `StandardOutput=tty`), com fonte Liberation Mono pequena para caber umas 30 linhas em 640×480. Dentro dele roda `journalctl -b -f -n 40 -o short-monotonic --no-hostname`.
- **Encerrar ao abrir o ES:** drop-in `usr/lib/systemd/system/emustation.service.d/r36-boot-log-tela.conf` com `ExecStartPre=-/usr/bin/systemctl stop r36-boot-log-tela.service`. É um stop de uma unit sem relação de ordem com o ES: não cria espera circular. O `-` faz uma falha não impedir o ES. Ao parar, o script restaura o VT (`chvt` de volta e `setterm --cursor on`).
- **Alternativa descartada:** `Before=emustation.service` com `Conflicts=`. Ordenar o diagnóstico em relação ao ES é justamente o tipo de acoplamento que travou o boot no caso do ClassiCube.
- **Alternativa de reserva** (só se o `fbterm` não funcionar no aparelho): desenhar o texto numa imagem com o `magick` da base a cada 2 s e copiá-la para o `/dev/fb0`. Mais lento e sem rolagem, por isso fica como reserva.

### 4. Cartão: retrato periódico na p1, fallback na p7
- `r36-boot-log-cartao.service`: `Type=simple`, `WantedBy=emuelec.target`, sem `After=`/`Before=` em relação ao autostart ou ao ES, `Nice=10`.
- `/usr/lib/r36/boot-log-cartao` faz 36 ciclos (5 s × 3 min). Em cada um, monta o retrato num arquivo em `/tmp`: data, uptime e as saídas de `systemctl list-jobs`, `systemctl --failed`, `journalctl -b --no-pager -o short-monotonic` e `dmesg`, cada comando com `timeout 5` para um systemd travado não travar o log. Depois copia o retrato para o destino.
- **Destino:** se `/storage/roms` é ponto de montagem, `/storage/roms/r36-boot-log/`. Se 60 s passarem sem isso, `/flash/r36-boot-log/`, com `mount -o remount,rw /flash`, cópia, `sync` e `mount -o remount,ro /flash` a cada gravação. Quando a p1 montar depois do fallback, as gravações voltam para ela.
- **Numeração:** `boot-<n>.txt`, com `n` = maior existente + 1 no primeiro retrato. Remove os mais antigos acima de 10. O arquivo é regravado inteiro a cada ciclo (cópia para `.tmp` e `mv`), para nunca ficar pela metade.
- **Alternativa descartada:** só a p7. Escrever a cada 5 s na FAT onde está o `SYSTEM` aumenta o risco de corromper a partição que dá boot. A p1 já recebe o `r36-sysinfo.txt` do registro térmico, e a p7 fica só para quando a p1 nem chegou a montar.
- **Alternativa descartada:** p2 (`R36-BOOT`), que tem só 16 MiB válidos e é lida pelo U-Boot.

## Risks / Trade-offs

- **[Risco] `fbterm` não abre sem console do kernel ou briga com o Mali pelo `/dev/fb0`** → Mitigação: a tela é a feature 90, separada. Se falhar, o serviço sai com erro no journal (que o log do cartão captura) e o ES abre igual. A tarefa de validação no aparelho decide entre manter, ajustar ou trocar pela reserva com `magick`.
- **[Risco] o ES abre com o `fbterm` ainda desenhando** → Mitigação: o `ExecStartPre` do drop-in é síncrono (sem `--no-block`), então o ES só sobe depois de o `fbterm` encerrar.
- **[Risco] corromper a p7 no fallback** → Mitigação: a escrita é só no fallback, numa pasta própria, com remount de leitura e escrita pelo tempo da cópia e `sync` antes de voltar a só leitura. No pior caso, `./flash.sh --part system` regrava a p7.
- **[Trade-off] build de teste muda o boot** (tela de log e uns segundos de CPU nos primeiros minutos) → aceito, porque o build de teste existe para diagnosticar. O build normal não muda.
- **[Trade-off] `journalctl -b` cresce a cada ciclo** → o retrato substitui o anterior (não acumula), e o journal de um boot cabe em poucos MiB.

## Migration Plan

Nada a migrar. Os builds normais seguem iguais. Para tirar o diagnóstico de um cartão de teste, basta gravar um build normal (`--part system` basta, porque as duas features ficam só no SYSTEM). As pastas `r36-boot-log/` na p1 e na p7 podem ser apagadas pelo PC.

## Open Questions

- Tamanho de fonte do `fbterm` que fica legível em 640×480 (ajuste no aparelho, sem mudar spec nem tarefas).
