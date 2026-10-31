# Design: Diagnóstico de Saúde do Cartão, Reconstrução Limpa de MBR e Ejeção Segura no Flash

## Context

O script `./flash.sh` (`tools/r36img/flash.py`) é o utilitário canônico para transferência das imagens de build para o cartão microSD utilizado no clone do R36S (GA36-MB V1.2, Allwinner A33).

O SoC Allwinner A33 possui requisitos estritos de boot via ROM interna (BootROM):
1. A BootROM lê exclusivamente o controlador `SMHC0` (físicamente ligado ao slot direito, rotulado como TF1/OS).
2. Ela busca o primeiro estágio de inicialização (`boot0`) nos setores 16 e 40 da mídia.
3. O `boot0` valida a tabela MBR e a tabela `softw411` no setor 40960 antes de carregar o U-Boot.
4. Qualquer divergência de alinhamento, cabeçalho de partição corrompido ou erro de I/O por cartão desgastado impede a subida do U-Boot, resultando no sintoma de tela preta absoluta sem acendimento do display LCD (Cenário A).

Este documento especifica a arquitetura técnica para blindar o processo de gravação contra falhas de hardware, inconsistências residuais de MBR e ejeções prematuras do cartão.

---

## 1. Reconstrução Analítica do MBR com `--keep-roms`

### 1.1 Problema da Abordagem Anterior
No código legado de `make_plan` em `flash.py`:
```python
entry = layout.p1_entry_bytes(card.sector0)
override = layout.replace_p1_entry(bootarea[:512], entry) + bootarea[512:]
```
Essa implementação copiava cegamente os 16 bytes brutos (`sector0[446:462]`). Se o cartão tivesse sido formatado anteriormente com flags CHS inválidas, tipo `0x0B` em vez de `0x0C` (LBA), ou com bytes de estado incoerentes, esses dados defeituosos eram mantidos no MBR regravado.

### 1.2 Solução Canônica
Em vez de ler os bytes do disco:
1. Validar se a partição `p1` atual inicia no setor canônico `4956160` (2.420 MiB).
2. Calcular o tamanho ótimo da partição em setores:
   $$\text{Setores}_{\text{p1}} = \left\lfloor \frac{\text{TargetSize} - (4956160 \times 512)}{4 \times 1024 \times 1024} \right\rfloor \times \frac{4 \times 1024 \times 1024}{512}$$
3. Montar a entrada MBR canônica de 16 bytes:
   * Byte 0 (`status`): `0x00` (não-bootável).
   * Bytes 1..3 (`start_chs`): `0xFE, 0xFF, 0xFF` (padrão LBA moderno para grandes volumes).
   * Byte 4 (`type`): `0x0C` (W95 FAT32 LBA).
   * Bytes 5..7 (`end_chs`): `0xFE, 0xFF, 0xFF`.
   * Bytes 8..11 (`lba_start`): `4956160` em Little-Endian (`0x00, 0x00, 0x4B, 0x00`).
   * Bytes 12..15 (`lba_sectors`): Setores calculados em Little-Endian.
4. Injetar essa entrada na `bootarea` oficial do build, garantindo que o bootstrap, a assinatura `0x55AA`, o Disk ID `0x815d9b77`, a entrada da `p2` de boot, a partição estendida `p3`, os EBRs e o U-Boot sejam sempre 100% novos e limpos da base.

---

## 2. Diagnóstico Prévio de Saúde do Cartão

Antes de qualquer operação destrutiva de escrita, `flash.py` executará `check_card_health(target, args)`:

### 2.1 Inspeção do Kernel (`dmesg`)
O script consulta mensagens recentes do kernel relacionadas ao dispositivo (`info.name`):
* Padrões de alerta: `buffer I/O error`, `reset high-speed USB device`, `device offline`, `blk_update_request: I/O error`.
* Se detectado: exibe aviso explícito e alerta que o leitor ou cartão está instável, recomendando porta USB direta e sem hub.

### 2.2 Teste de Trava de Hardware (Read-Only Lock)
Cartões flash danificados costumam aceitar comandos de escrita na camada de emulação do leitor USB sem retornar erro imediato, mas os blocos físicos não se alteram.
* **Teste atômico**:
  1. Lê os últimos 512 bytes utilizáveis do cartão (`target.size - 512`).
  2. Tenta escrever um bloco com padrão de bytes invertido (`bytes(~b & 0xFF for b in orig)`).
  3. Executa `sync` e relê o bloco.
  4. Restaura imediatamente os dados originais e valida.
* Se a releitura do bloco invertido falhar, o script aborta com erro irrecuperável: o cartão está com trava de hardware ativada e deve ser descartado.

### 2.3 Checagem não destrutiva da FAT32 (`fsck.fat -n`)
Ao usar `--keep-roms`, o script roda `fsck.fat -n` sobre `/dev/sdX1` montável (ou desmontado):
* Valida a integridade da tabela de alocação de arquivos e do Boot Sector da FAT32.
* Avisa se o sistema de arquivos já possui corrupção antes da regravação do sistema operacional.

---

## 3. Sincronização Rigorosa e Ejeção Segura (Safe Eject)

### 3.1 Sequência de Finalização
Na classe `DeviceTarget`:
```python
def sync(self):
    subprocess.run(["sync"])
    subprocess.run(["sudo", "blockdev", "--flushbufs", self.path], capture_output=True)
    subprocess.run(["udevadm", "settle"], capture_output=True)
```

### 3.2 Ejeção Segura com `udisksctl power-off`
Após a confirmação por SHA256 (`readback_sha256` verificado com sucesso):
1. Se a opção `--no-eject` não estiver presente:
   ```python
   subprocess.run(["udisksctl", "power-off", "-b", self.path], capture_output=True)
   ```
2. O comando desliga a alimentação elétrica da porta/leitor e desassocia o dispositivo `/dev/sdX` do kernel com segurança absoluta.
3. Uma mensagem clara é exibida ao usuário:
   ```text
   ==> Dispositivo /dev/sdX desenergizado e desconectado com segurança.
   O cartão microSD pode ser removido fisicamente do computador.
   ```
4. Se o comando `udisksctl` falhar ou não estiver disponível, o fallback invoca `echo 1 > /sys/block/sdX/device/delete` via sudo.

---

## 4. Matriz de Compatibilidade e Testes Automatizados

* Em alvos de teste (`--target-file` / `FileTarget`), o `udisksctl power-off` e as verificações físicas de hardware são ignorados elegantemente, mantendo a compatibilidade integral com a suíte de testes em `tests/test_flash.py`.
* Novos testes unitários em `tests/test_flash.py` cobrirão:
  - Reconstrução canônica da entrada MBR da p1 para diferentes capacidades (16 GB, 32 GB, 64 GB, 128 GB);
  - Detecção e tratamento de trava de leitura/escrita física;
  - Respeito à flag `--no-eject`;
  - Comportamento de fallback caso `udisksctl` não esteja instalado.
