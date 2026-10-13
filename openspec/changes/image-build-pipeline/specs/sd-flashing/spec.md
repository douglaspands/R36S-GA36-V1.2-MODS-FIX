# Spec Delta

## Purpose

Gravar no cartão SD uma imagem gerada pelo build, inteira ou por partição, sem risco de atingir o disco errado e sem apagar ROMs ou dados do usuário por acidente.

## ADDED Requirements

### Requirement: Modos de gravação
O script de gravação SHALL oferecer dois modos, sempre sobre um build escolhido pelo timestamp (`--build`), e SHALL usar o build mais recente quando nenhum for indicado. Na gravação completa, ele grava a imagem inteira do build. Na gravação parcial, ele grava uma ou mais partições escolhidas entre `boot`, `system`, `storage` e `roms`, e nenhum byte fora delas SHALL ser escrito.

#### Scenario: Build mais recente por padrão
- **WHEN** existem os builds `20261013-153045` e `20261014-090000`, e o usuário grava sem `--build`
- **THEN** o script usa o build `20261014-090000` e mostra o nome dele no plano antes da confirmação

#### Scenario: Build inexistente
- **WHEN** o usuário indica `--build 20990101-000000`, que não existe em `out/`
- **THEN** o script recusa e lista os builds disponíveis

#### Scenario: Gravação parcial do system
- **WHEN** o usuário grava só `system` num cartão com o layout esperado
- **THEN** só a região da p7 é escrita, e p1, p2, p5, p6, p8, o MBR e a área de boot permanecem intactos

#### Scenario: Gravação completa
- **WHEN** o usuário grava a imagem completa com a confirmação exigida
- **THEN** o cartão passa a ter o layout, as partições e os labels do build gravado

### Requirement: Somente cartões removíveis e com capacidade suficiente
O script SHALL recusar gravar em qualquer dispositivo que não seja um disco inteiro removível (`RM=1`) ou um cartão em leitor SD interno (`mmcblk`), que contenha a partição raiz ou outra partição montada do host fora das do cartão, ou que seja menor que a imagem a gravar. O script SHALL NOT impor limite máximo de capacidade.

#### Scenario: Disco interno
- **WHEN** o usuário indica um disco com `RM=0`, como o SSD do PC
- **THEN** o script recusa a gravação sem escrever nada, informando que o disco não é removível

#### Scenario: Cartão menor que a imagem
- **WHEN** a imagem completa tem 15000 MiB e o cartão tem 7600 MiB
- **THEN** o script recusa a gravação completa, mostrando os dois tamanhos e sugerindo gerar a imagem com tamanho menor

#### Scenario: Cartão grande
- **WHEN** a imagem tem 15000 MiB e o cartão removível tem 128 GB
- **THEN** o script aceita a gravação e avisa quanto espaço do cartão ficará sem uso

#### Scenario: Partição indicada no lugar do disco
- **WHEN** o usuário indica `/dev/sdc1` em vez de `/dev/sdc`
- **THEN** o script recusa e pede o disco inteiro

### Requirement: Confirmação explícita do dispositivo
Antes de escrever, o script SHALL mostrar dispositivo, modelo, capacidade, labels atuais e o que será sobrescrito. Ele SHALL exigir que o usuário digite o nome do dispositivo para confirmar. Sem confirmação válida, SHALL encerrar sem escrever.

#### Scenario: Confirmação correta
- **WHEN** o script mostra o plano e o usuário digita `sdc`, que é o dispositivo indicado
- **THEN** a gravação começa

#### Scenario: Confirmação incorreta
- **WHEN** o usuário digita algo diferente do nome do dispositivo
- **THEN** o script encerra sem escrever nada

### Requirement: Simulação sem escrita
O script SHALL oferecer uma opção de simulação que executa todas as verificações e mostra o plano de gravação, abrindo o dispositivo apenas para leitura e sem escrever nada nele.

#### Scenario: Simulação
- **WHEN** o usuário executa o script com a opção de simulação
- **THEN** o script mostra as verificações, as regiões que seriam escritas e os dados que seriam perdidos, e não escreve nada

### Requirement: Gravação parcial exige layout compatível
A gravação parcial SHALL ser permitida só se o cartão já tiver o layout desta família de imagens: assinatura softw411 no setor 40960, e setores de início e tamanhos de p2, p5, p6, p7 e p8 iguais aos do manifest. Caso contrário, o script SHALL recusar e indicar a gravação completa.

#### Scenario: Cartão com layout compatível
- **WHEN** o usuário grava só `storage` num cartão gravado antes por este repositório
- **THEN** o script valida o layout e grava só a p8

#### Scenario: Cartão novo ou de outra origem
- **WHEN** o usuário tenta gravação parcial num cartão sem a softw411 ou com partições em outras posições
- **THEN** o script recusa, informando que é preciso fazer a gravação completa primeiro

### Requirement: Proteção das ROMs
Se a p1 do cartão tiver arquivos além dos da base, a gravação completa SHALL exigir escolher entre manter as ROMs (`--keep-roms`) e apagá-las (`--wipe-roms`). Manter ROMs SHALL gravar tudo exceto a p1 e a entrada dela no MBR. Gravar `roms` parcialmente SHALL sempre exigir `--wipe-roms`.

#### Scenario: ROMs presentes sem escolha
- **WHEN** o usuário pede gravação completa num cartão compatível cuja p1 tem ROMs, sem `--keep-roms` nem `--wipe-roms`
- **THEN** o script recusa, mostra quanto espaço as ROMs ocupam e explica as duas opções

#### Scenario: Manter ROMs
- **WHEN** o usuário grava a imagem completa com `--keep-roms`
- **THEN** a p1 e a entrada dela no MBR permanecem intactas, as demais partições são gravadas, e as ROMs continuam acessíveis no aparelho

#### Scenario: Manter ROMs com layout incompatível
- **WHEN** o usuário usa `--keep-roms` num cartão cuja p1 não começa no setor 4956160
- **THEN** o script recusa, porque não consegue preservar a p1 com segurança

### Requirement: Proteção dos dados do usuário na p8
A p8 contém saves, savestates e configurações. Sobrescrevê-la, na gravação completa ou na parcial de `storage`, SHALL exigir `--wipe-storage`. Na gravação completa, a alternativa `--keep-storage` SHALL preservar a p8 do cartão.

#### Scenario: Gravação completa mantendo dados
- **WHEN** o usuário grava a imagem completa com `--keep-roms --keep-storage`
- **THEN** só a área de boot (com a entrada da p1 no MBR preservada), p2, p5, p6 e p7 são escritas, e saves e ROMs permanecem

#### Scenario: Storage sem confirmação
- **WHEN** o usuário pede gravação parcial de `storage` sem `--wipe-storage`
- **THEN** o script recusa, explicando que saves e configurações serão apagados

### Requirement: P2 gravada só dentro de 16 MiB
Ao gravar `boot`, o script SHALL escrever no máximo 16 MiB a partir do início da p2, independentemente do tamanho declarado no MBR.

#### Scenario: Gravação da p2
- **WHEN** o usuário grava só `boot`
- **THEN** são escritos exatamente 16.777.216 bytes a partir do setor 73728, e p5, p6 e p7 permanecem intactas

### Requirement: Integridade antes e depois da gravação
Antes de escrever, o script SHALL conferir o sha256 dos artefatos contra o manifest. Depois de escrever, SHALL sincronizar o dispositivo, reler cada região escrita e comparar o sha256 com o esperado. Qualquer divergência SHALL ser reportada como falha.

#### Scenario: Artefato corrompido
- **WHEN** o sha256 de uma imagem de partição não confere com o manifest
- **THEN** o script recusa a gravação antes de escrever

#### Scenario: Verificação pós-gravação
- **WHEN** a gravação termina
- **THEN** o script relê as regiões escritas, mostra "verificado" para cada uma e termina com sucesso só se todas conferirem

### Requirement: Partições do cartão desmontadas antes da escrita
Antes de escrever, o script SHALL desmontar todas as partições montadas do cartão alvo. Se alguma não puder ser desmontada, SHALL encerrar sem escrever.

#### Scenario: Cartão montado automaticamente
- **WHEN** o desktop montou p1, p2 e p7 do cartão ao conectá-lo
- **THEN** o script as desmonta antes de gravar e informa isso ao usuário
