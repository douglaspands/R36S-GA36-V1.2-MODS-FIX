# sd-flashing Specification Delta

## Purpose
Adicionar ao pipeline de gravação (`./flash.sh`) a reconstrução canônica analítica do MBR na opção `--keep-roms`, diagnóstico prévio de saúde física e lógica do cartão microSD, e rotina de sincronização rigorosa com corte de energia e ejeção segura de hardware (`udisksctl power-off`).

## Requirements

### Requirement: Reconstrução canônica do MBR ao manter ROMs
Na gravação completa com preservação da partição de ROMs (`--all --keep-roms`), o script SHALL reconstruir a entrada da partição `p1` no MBR matematicamente a partir da capacidade do dispositivo físico e dos parâmetros canônicos da imagem base, sem copiar bytes brutos da tabela de partição anterior do cartão. A entrada SHALL possuir obrigatoriamente:
- Setor inicial: `4956160` (offset fixo da partição de ROMs no layout da base);
- Tipo de partição: `0x0C` (W95 FAT32 com endereçamento LBA);
- Quantidade de setores: calculada como `(target_sectors - 4956160)`, respeitando o limite máximo do dispositivo e o alinhamento de 4 MiB;
- O restante dos 496 bytes do MBR (bootstrap, assinatura `0x55AA`, Disk ID `0x815d9b77`, entrada da `p2` de boot e entrada da `p3` estendida) e todos os setores de boot subsequentes (`0..73727`, contendo `boot0`, U-Boot e tabela `softw411`) SHALL ser gravados diretamente do artefato oficial `bootarea.img` do build.

#### Scenario: Reconstrução analítica da p1 com tamanho expandido
- **WHEN** o usuário grava um cartão de 16 GB, 32 GB ou 64 GB com `--all --keep-roms`
- **THEN** o script gera uma entrada MBR perfeitamente alinhada, canônica e livre de vícios do MBR anterior, apontando para o setor 4956160 e ocupando até o limite seguro do cartão físico

#### Scenario: Rejeição de cartão com p1 fora do setor canônico
- **WHEN** o cartão anterior possui a partição `p1` iniciando em setor diferente de `4956160`
- **THEN** o script recusa a preservação via `--keep-roms`, alertando sobre a incompatibilidade de layout e orientando a gravação completa com backup prévio

---

### Requirement: Diagnóstico prévio de saúde física e lógica do cartão
Antes de iniciar qualquer escrita em disco físico, o script SHALL executar verificações de saúde:
1. **Inspeção de erros de barramento/kernel**: O script SHALL verificar mensagens recentes no log do kernel (`dmesg`) para o dispositivo alvo e avisar/recusar se houver registros de `buffer I/O error`, `reset high-speed USB device` ou `device offline`.
2. **Detecção de trava de hardware (Read-Only Lock)**: O script SHALL realizar um teste atômico de escrita e restauração em bloco de rascunho de 512 bytes no final do disco para garantir que a controladora da memória flash não congelou silenciosamente em modo somente leitura.
3. **Verificação não destrutiva da FAT32**: Quando `--keep-roms` for solicitado, o script SHALL invocar `fsck.fat -n` na partição `p1` montável e alertar o usuário caso a estrutura de diretórios ou clusters da partição de jogos apresente corrupção prévia.

#### Scenario: Cartão com hardware bloqueado em somente leitura
- **WHEN** o usuário tenta gravar em um cartão microSD cujas células de memória flash sofreram desgaste e ativaram a trava de hardware
- **THEN** o teste atômico falha na releitura do bloco de teste e o script aborta antes de qualquer tentativa de particionamento, informando que o cartão está com proteção contra gravação física

#### Scenario: Alerta de erros de I/O pré-existentes
- **WHEN** o leitor USB ou cabo apresentar instabilidade reportada no `dmesg`
- **THEN** o script exibe aviso crítico de hardware e exige confirmação adicional ou sugere trocar de porta/leitor antes de prosseguir

---

### Requirement: Sincronização estrita e ejeção segura de hardware
Ao concluir a escrita de todas as regiões planejadas em dispositivos físicos (`--device`), o script SHALL garantir a persistência completa e a desconexão segura:
1. Executar `sync` global no sistema;
2. Descarregar os buffers pendentes do dispositivo com `blockdev --flushbufs`;
3. Aguardar o término do processamento de eventos do kernel via `udevadm settle`;
4. Efetuar a releitura bit a bit por SHA256 (`readback_sha256`) de todas as áreas gravadas contra o manifesto;
5. Executar `udisksctl power-off -b /dev/sdX` para desenergizar a porta USB e desconectar o dispositivo com segurança a nível de hardware, a menos que a opção `--no-eject` tenha sido fornecida.

#### Scenario: Desligamento seguro com confirmação
- **WHEN** a gravação e a verificação pós-gravação terminam com 100% de sucesso em um dispositivo `/dev/sdX`
- **THEN** o script invoca `udisksctl power-off`, confirma que o dispositivo foi desligado com segurança e avisa o usuário que o cartão pode ser removido fisicamente do computador

#### Scenario: Supressão de ejeção com --no-eject
- **WHEN** o usuário passa o argumento `--no-eject` junto com o comando de gravação
- **THEN** o script executa o `sync` e a verificação completa por SHA256, mas mantém o dispositivo conectado no sistema para inspeção imediata no PC
