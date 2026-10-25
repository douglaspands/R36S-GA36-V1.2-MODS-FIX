# Spec Delta

## MODIFIED Requirements

### Requirement: Binário único na partição SYSTEM
O binário `ClassiCube` entregue pela imagem SHALL existir só em `/usr/share/classicube/ClassiCube`, na partição SYSTEM, com permissão `0755`. A partição `roms` SHALL NOT levar cópia desse binário, porque ela não é regravada com `--keep-roms`. A p1 pode levar, em `/storage/roms/ports/classicube/ClassiCube-pc`, um binário opcional copiado pelo jogador pelo PC, que nenhuma feature entrega. Na p1 ficam também os arquivos que o jogador ou o PC alteram (opções, mapas, texturas e sons em `/storage/roms/ports/classicube/`).

#### Scenario: Atualização com --keep-roms
- **WHEN** o cartão é gravado com `--keep-roms` a partir de um build com binário novo e a p1 não tem `ClassiCube-pc`
- **THEN** o jogo abre com o binário novo, porque ele vem do SYSTEM, sem depender de nada na p1

#### Scenario: Boot sem regravar a FAT32
- **WHEN** o aparelho dá boot com o lançador, a capa e os ativos já presentes e iguais aos do SYSTEM
- **THEN** o `r36-classicube-sync.service` não grava nenhum arquivo na p1 e não copia o binário para ela

#### Scenario: Imagem não entrega binário na p1
- **WHEN** uma imagem é gerada com a feature `60-port-classicube`
- **THEN** a p1 não contém `ports/classicube/ClassiCube` nem `ports/classicube/ClassiCube-pc`

#### Scenario: Binário antigo de gravação anterior não vale
- **WHEN** a p1 de um cartão antigo ainda tem um arquivo `ports/classicube/ClassiCube` de uma gravação anterior
- **THEN** o lançador o ignora e usa o binário do SYSTEM, porque só o `ClassiCube-pc` é considerado

## ADDED Requirements

### Requirement: Escolha do binário do ClassiCube pelo lançador
O `ClassiCube.sh` SHALL usar o `ClassiCube-pc` da p1 quando ele existir, tentando primeiro executá-lo direto da p1 e, se o sistema recusar a execução, copiá-lo para a RAM (`/tmp`) e executá-lo de lá. Quando não houver `ClassiCube-pc`, ou quando nenhuma das duas formas executar, o lançador SHALL usar o binário do SYSTEM. O jogo SHALL abrir com um binário em qualquer um desses casos.

#### Scenario: Sem binário na p1
- **WHEN** o jogador abre o ClassiCube e não existe `ClassiCube-pc` na p1
- **THEN** o jogo abre com o binário do SYSTEM

#### Scenario: Binário da p1 executa direto
- **WHEN** existe um `ClassiCube-pc` na p1 e o sistema permite executá-lo de lá
- **THEN** o jogo abre com esse binário, sem copiá-lo para a RAM

#### Scenario: Binário da p1 não executa direto
- **WHEN** existe um `ClassiCube-pc` na p1 e o sistema recusa executá-lo de lá (sem permissão de execução ou partição montada sem execução)
- **THEN** o lançador copia o binário para `/tmp`, dá permissão de execução e abre o jogo com a cópia

#### Scenario: Binário da p1 não executa em lugar nenhum
- **WHEN** existe um `ClassiCube-pc` na p1 e o sistema recusa executá-lo tanto da p1 quanto de `/tmp`
- **THEN** o jogo abre com o binário do SYSTEM, em vez de voltar ao EmulationStation sem abrir

#### Scenario: Saída normal do jogo não dispara a reserva
- **WHEN** o jogador sai do jogo pelo menu de pausa ou por `Select + Start` depois de o binário da p1 ter executado
- **THEN** o lançador encerra e volta ao EmulationStation, sem abrir o jogo uma segunda vez

### Requirement: Diagnóstico do binário em log.txt
A cada abertura, o `ClassiCube.sh` SHALL gravar em `/storage/roms/ports/classicube/log.txt`, substituindo o conteúdo anterior, qual binário foi usado (p1 direto, p1 via `/tmp` ou SYSTEM), o código de saída de cada tentativa de execução, as linhas de montagem de `/storage/roms` e de `/tmp` e o sha256 do binário do SYSTEM e do `ClassiCube-pc` quando existir. O arquivo SHALL ser texto simples legível no PC.

#### Scenario: Saber se a FAT32 executa direto
- **WHEN** o jogador abre o ClassiCube com um `ClassiCube-pc` na p1 e lê o `log.txt` no PC
- **THEN** o log mostra se a execução direta da p1 funcionou ou foi recusada e as opções de montagem de `/storage/roms`

#### Scenario: Binário esquecido na p1
- **WHEN** o `ClassiCube-pc` da p1 é diferente do binário do SYSTEM
- **THEN** o `log.txt` traz os dois sha256, para o jogador perceber que o binário em uso não é o do SYSTEM

#### Scenario: Log não cresce
- **WHEN** o jogador abre o ClassiCube várias vezes
- **THEN** o `log.txt` contém só o registro da última abertura
