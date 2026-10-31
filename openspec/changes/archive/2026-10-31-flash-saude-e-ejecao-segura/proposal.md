# Proposal: Diagnóstico de Saúde do Cartão, Reconstrução Limpa de MBR e Ejeção Segura no Flash

## Why

Durante a gravação de imagens no cartão SD pelo `./flash.sh`, usuários podem enfrentar falhas silenciosas de hardware ou corrupções sutis que impedem o console clone do R36S (GA36-MB V1.2, Allwinner A33) de inicializar:

1. **MBR com entrada de partição degradada na opção `--keep-roms`**:
   - Atualmente, o script copia cegamente os 16 bytes brutos da entrada da partição `p1` (offset 446 a 461 do setor 0) do cartão anterior para a nova `bootarea`. Se o MBR anterior possuir cabeçalhos CHS inconsistentes, flags inválidas ou tipo de partição descalibrado, esses vícios são perpetuados no novo MBR, impedindo a BootROM do processador A33 de carregar o `boot0` ou localizar a partição de boot.
2. **Ausência de checagem prévia de saúde e integridade física do cartão**:
   - Cartões microSD degradados frequentemente entram em modo silencioso de proteção contra escrita (*flash read-only lock*), onde comandos `dd` aparentam sucesso mas os dados não são persistidos, ou geram tempestades de erros de barramento I/O no kernel do PC (`buffer I/O error`, `reset high-speed USB device`). O script atual só percebe falhas na releitura final por SHA256.
   - A partição de ROMs (FAT32) pode conter dirty bits ou tabela FAT desarticulada, sem aviso prévio antes da tentativa de preservação.
3. **Ausência de desligamento/ejeção segura de hardware (`udisksctl power-off`)**:
   - Ao término do `flash.sh`, o script apenas exibe a mensagem de término e encerra, deixando o dispositivo energizado no barramento USB. Se o usuário desconectar o leitor antes da finalização de sincronizações em segundo plano ou durante polling de montagem automática do desktop (GNOME/Fedora), a tabela de partições recém-gravada ou os diários do ext4 (`p8`) podem se corromper.

## What Changes

1. **Reconstrução Matemática Canônica do MBR com `--keep-roms`**:
   - Em vez de copiar os 16 bytes da entrada anterior, o `flash.sh` reconstrói a entrada da `p1` do zero: setor inicial canônico `4956160`, tipo `0x0C` (W95 FAT32 LBA), e número de setores calculado matematicamente a partir da capacidade real do cartão (`(target.size // 512) - 4956160`), garantindo MBR 100% puro e canônico.
2. **Rotina de Diagnóstico de Saúde Pré-Gravação (`--check-health` / padrão)**:
   - Inspeção de mensagens recentes de I/O no `dmesg` do kernel para o dispositivo selecionado.
   - Verificação de trava de hardware (teste atômico de escrita e restauração em bloco de rascunho de 512 bytes no final do disco para atestar persistência real da flash).
   - Validação da integridade do sistema de arquivos FAT32 da `p1` com `fsck.fat -n` (somente leitura) quando `--keep-roms` for solicitado.
3. **Sincronização e Ejeção Segura de Hardware (`udisksctl power-off`)**:
   - Reforço do pipeline pós-gravação: `sync` -> `blockdev --flushbufs` -> `udevadm settle` -> releitura `readback_sha256`.
   - Execução automática de `udisksctl power-off -b /dev/sdX` ao concluir com sucesso a gravação em dispositivos físicos, garantindo desenergização da porta USB e desligamento seguro do cartão antes da remoção física.
   - Nova opção `--no-eject` para casos onde o usuário queira inspecionar as partições no PC imediatamente após o flash sem precisar reconectar o leitor.

## Capabilities

### Modified Capabilities

- `sd-flashing`: Adiciona rotina de diagnóstico de saúde física e lógica do cartão, reconstrução analítica do MBR ao preservar a partição de ROMs, e ciclo de sincronização rigorosa com corte de energia/ejeção segura de hardware.
