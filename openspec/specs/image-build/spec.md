# image-build Specification

## Purpose

Gerar, a partir da imagem base de fábrica do R36S clone (GA36-MB V1.2, Allwinner A33) e das features do repositório, imagens graváveis em cartão SD que mantêm a compatibilidade de boot do aparelho.

## Requirements

### Requirement: Imagem base imutável e verificada
O build SHALL ler a imagem base apenas para leitura e SHALL verificar o sha256 dela contra o valor registrado no repositório antes de qualquer outra etapa. Se o sha256 divergir ou a imagem não existir, o build SHALL falhar sem gerar saída.

#### Scenario: Base íntegra
- **WHEN** o build é executado e o sha256 da imagem base confere com o valor registrado
- **THEN** o build prossegue, e a imagem base continua byte a byte idêntica ao final

#### Scenario: Base divergente ou ausente
- **WHEN** a imagem base não existe ou o sha256 dela difere do registrado
- **THEN** o build falha com uma mensagem que mostra o caminho esperado e os dois hashes, sem gerar nenhum arquivo de saída

### Requirement: Build sem privilégios de root
O build SHALL rodar inteiramente como usuário comum, sem sudo, sem montar loop devices e sem exigir pertencer ao grupo `disk`.

#### Scenario: Execução como usuário comum
- **WHEN** um usuário sem privilégios executa o build num host com as dependências instaladas
- **THEN** o build termina com sucesso sem pedir senha nem chamar `sudo`, `mount` ou `losetup`

### Requirement: Tamanho do cartão parametrizável
O build SHALL aceitar o tamanho alvo do cartão como parâmetro em MiB, com padrão de 15000 MiB e mínimo de 7000 MiB. O tamanho SHALL ser alinhado para baixo a múltiplo de 4 MiB, e esse valor alinhado SHALL ser registrado no manifest.

#### Scenario: Tamanho padrão
- **WHEN** o build é executado sem informar o tamanho
- **THEN** a imagem completa tem exatamente 15000 MiB (15.728.640.000 bytes)

#### Scenario: Tamanho personalizado válido
- **WHEN** o build é executado com tamanho de 30000 MiB
- **THEN** a imagem completa tem 30000 MiB, e a partição de ROMs termina no último setor da imagem

#### Scenario: Tamanho abaixo do mínimo
- **WHEN** o build é executado com tamanho de 6000 MiB
- **THEN** o build falha antes de gerar saída, informando que o mínimo é 7000 MiB

#### Scenario: Tamanho não alinhado
- **WHEN** o build é executado com tamanho de 7462 MiB
- **THEN** a imagem é gerada com 7460 MiB, e o manifest registra 7460 MiB

### Requirement: Layout de boot preservado
A imagem gerada SHALL manter, idênticos aos da base: a numeração das partições, os setores de início e o tamanho de p2, p3, p5, p6, p7 e p8, a tabela Allwinner softw411 (setor 40960), a área de boot0/U-Boot antes do setor 73728 e o conteúdo byte a byte de p5 (env) e p6 (kernel).

#### Scenario: Comparação estrutural com a base
- **WHEN** uma imagem é gerada com qualquer conjunto de features
- **THEN** a verificação pós-build confirma que os setores 0 a 73727, incluindo MBR, EBRs (setores 1 a 4), boot0, U-Boot e softw411, são idênticos aos da base exceto pela entrada da p1 no MBR, que p5 e p6 são idênticas aos da base, e que as entradas do MBR diferem apenas no tamanho da p1

### Requirement: Partição de ROMs expandida até o fim do cartão
A p1 SHALL começar no mesmo setor da base (4956160) e terminar no último setor da imagem. Ela SHALL ser formatada como FAT32 e SHALL conter todos os arquivos e diretórios que a p1 da base contém, mais os adicionados por features da camada ROMS.

#### Scenario: P1 ocupa o restante do cartão
- **WHEN** a imagem é gerada com o tamanho padrão
- **THEN** a entrada da p1 no MBR começa no setor 4956160 e termina no setor 30719999, e o FAT32 dela reporta um tamanho compatível com a partição

#### Scenario: Conteúdo da base preservado na p1
- **WHEN** a imagem é gerada sem features
- **THEN** a listagem de arquivos e diretórios da p1 (pastas de sistemas, `bios`, `bezels`, `.update`) é igual à da base, com os mesmos conteúdos

### Requirement: Labels legíveis nos filesystems
A imagem SHALL usar os labels `R36-BOOT` (p2), `R36-SYSTEM` (p7), `R36-STORAGE` (p8) e `R36-ROMS` (p1). A troca de label SHALL alterar apenas o campo de label de cada filesystem.

#### Scenario: Labels aplicados
- **WHEN** a imagem gerada é inspecionada com `blkid` ou `lsblk -o LABEL`
- **THEN** p2, p7, p8 e p1 mostram, respectivamente, `R36-BOOT`, `R36-SYSTEM`, `R36-STORAGE` e `R36-ROMS`

### Requirement: Metadados do SYSTEM preservados
O squashfs SYSTEM gerado SHALL preservar uid, gid, modo, bits setuid/setgid/sticky, links simbólicos e nós de dispositivo de todo caminho da base que nenhuma feature alterou. O build SHALL comparar a listagem de metadados da base com a do resultado, e SHALL falhar se houver qualquer divergência em caminhos não tocados.

#### Scenario: Setuid preservado
- **WHEN** a imagem é gerada sem features que toquem `usr/bin/busybox`
- **THEN** o SYSTEM gerado lista `usr/bin/busybox` como `-rwsr-xr-x 0/0`, e `usr/lib/dbus/dbus-daemon-launch-helper` como `-rwsr-x--- 0/81`

#### Scenario: Divergência detectada
- **WHEN** o reempacotamento produz um caminho não tocado com dono, grupo ou modo diferente da base
- **THEN** o build falha e lista cada caminho divergente com os metadados esperados e os obtidos

### Requirement: SYSTEM legível pelo kernel do aparelho
O SYSTEM gerado SHALL usar compressão LZO e blocos de 512 KiB, iguais aos da base. Ele SHALL caber na p7 junto com os demais arquivos dela; caso contrário, o build SHALL falhar.

#### Scenario: Parâmetros de compressão
- **WHEN** o SYSTEM gerado é inspecionado com `unsquashfs -s`
- **THEN** ele reporta compressão `lzo` e block size 524288

#### Scenario: SYSTEM grande demais
- **WHEN** as features fazem o SYSTEM e os demais arquivos da p7 excederem a capacidade da p7
- **THEN** o build falha, informando o tamanho obtido e o espaço disponível

### Requirement: P2 limitada a 16 MiB
O filesystem da p2 SHALL ter todos os dados, FATs e diretórios dentro dos primeiros 16 MiB da partição (o tamanho real na softw411), apesar de o MBR declarar 128 MiB. A imagem da p2 para gravação parcial SHALL ter exatamente 16 MiB.

#### Scenario: Conteúdo da p2 dentro do limite
- **WHEN** a imagem é gerada
- **THEN** nenhum cluster alocado, FAT ou entrada de diretório da p2 fica além do byte 16.777.216 da partição, e a imagem parcial da p2 tem 16.777.216 bytes

#### Scenario: Conteúdo da p2 excede o limite
- **WHEN** features da camada BOOT exigiriam ocupar clusters além dos primeiros 16 MiB
- **THEN** o build falha e informa quanto espaço foi excedido

### Requirement: Marcador de redimensionamento proibido
O build SHALL recusar gerar uma imagem que contenha o arquivo `.please_resize_me` em qualquer partição, porque ele faz o aparelho formatar a p1 e a p8 no boot.

#### Scenario: Marcador presente
- **WHEN** uma feature ou a base faria existir `.please_resize_me` em qualquer filesystem da imagem
- **THEN** o build falha e informa a feature e o caminho responsáveis

### Requirement: Artefatos de saída versionados
Cada build SHALL ser identificado pelo timestamp local da geração, no formato `AAAAMMDD-HHMMSS`. A imagem completa SHALL se chamar `<prefixo>_build_<timestamp>.img.xz`, com prefixo configurado (`r36s_ga36-mb_v1.2-20260416`). O diretório `<timestamp>` SHALL conter a imagem, uma imagem por partição gravável e um manifest (timestamp, tamanho do cartão, sha256, offsets e features). Um diretório existente SHALL NOT ser sobrescrito.

#### Scenario: Saída completa
- **WHEN** um build termina com sucesso
- **THEN** o diretório do build contém a imagem completa comprimida, as quatro imagens de partição (boot, system, storage, roms) e o manifest, e o sha256 de cada arquivo confere com o manifest

#### Scenario: Nome da imagem
- **WHEN** um build é gerado em 13/10/2026 às 15:30:45, hora local
- **THEN** a imagem completa se chama `r36s_ga36-mb_v1.2-20260416_build_20261013-153045.img.xz`, o diretório se chama `20261013-153045`, e o manifest e o `R36-BUILD.txt` registram o timestamp `20261013-153045`

#### Scenario: Build no mesmo segundo
- **WHEN** um build é iniciado no mesmo segundo de outro, cujo diretório de saída já existe
- **THEN** o build falha sem alterar o diretório existente

### Requirement: Build sem features equivalente à base
Um build sem nenhuma feature SHALL produzir uma imagem cujo SYSTEM, p8, p5, p6 e área de boot sejam funcionalmente idênticos aos da base. As únicas diferenças permitidas são os labels, o tamanho e a formatação da p1, e o registro do build.

#### Scenario: Feature vazia
- **WHEN** o build é executado sem features
- **THEN** a listagem completa de arquivos e metadados do SYSTEM e da p8 é igual à da base, exceto pelo registro do build, e a verificação estrutural passa
