# Tasks: Diagnóstico de Saúde do Cartão, Reconstrução Limpa de MBR e Ejeção Segura no Flash

## 1. Reconstrução Canônica e Matemática da Entrada MBR da p1
- [x] 1.1 Implementar a função `build_canonical_p1_entry(target_size_bytes)` em `tools/r36img/layout.py`, calculando o tamanho alinhado e gerando a estrutura binária de 16 bytes padrão LBA (`0x0C`) para a partição `p1`.
- [x] 1.2 Atualizar `make_plan` em `tools/r36img/flash.py` para utilizar `build_canonical_p1_entry` ao processar `--keep-roms`, eliminando a cópia cega de bytes legados do `card.sector0`.
- [x] 1.3 Adicionar validação estrita de setor inicial (`4956160`) antes de aceitar a reconstrução com `--keep-roms`.

## 2. Diagnóstico de Saúde Pré-Gravação do Cartão SD
- [x] 2.1 Implementar a função `check_dmesg_io_errors(device_name)` para inspecionar logs do kernel e alertar sobre instabilidades de conexão do leitor USB.
- [x] 2.2 Implementar a função `test_hardware_write_lock(target)` em `tools/r36img/flash.py` para executar teste atômico de escrita/releitura/restauração no último setor do cartão e abortar se a mídia estiver travada em somente leitura.
- [x] 2.3 Implementar a validação não destrutiva `check_p1_filesystem(device_path)` com `fsck.fat -n` ao preservar ROMs, alertando o usuário sobre possíveis corrupções prévias da FAT32.

## 3. Sincronização Estrita e Ejeção Segura de Hardware
- [x] 3.1 Expandir o método `sync()` da classe `DeviceTarget` em `tools/r36img/flash.py` com `udevadm settle` após `sync` e `blockdev --flushbufs`.
- [x] 3.2 Adicionar o argumento `--no-eject` no parser de linha de comando (`PtParser`) do `./flash.sh`.
- [x] 3.3 Implementar o método `power_off()` em `DeviceTarget` utilizando `udisksctl power-off -b /dev/sdX` com fallback para `echo 1 > /sys/block/sdX/device/delete`.
- [x] 3.4 Invocar `power_off()` ao término bem-sucedido de `write_plan` e exibir instruções amigáveis ao usuário confirmando a desenergização do leitor.

## 4. Testes Automatizados e Documentação
- [x] 4.1 Adicionar testes unitários em `tests/test_flash.py` para a geração analítica do MBR em diferentes tamanhos de cartão (16 GB, 32 GB, 64 GB, 128 GB).
- [x] 4.2 Adicionar testes unitários em `tests/test_flash.py` simulando a detecção de trava de hardware e o comportamento da flag `--no-eject`.
- [x] 4.3 Atualizar a documentação técnica de gravação em `docs/DESENVOLVIMENTO.md` explicando o novo diagnóstico de saúde e a ejeção automática de hardware.
- [x] 4.4 Executar a suíte de testes de regressão completa (`python3 -I -m unittest discover -s tests`) e atestar 100% de aprovação.
