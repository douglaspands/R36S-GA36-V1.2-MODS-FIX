# Spec Delta

## MODIFIED Requirements

### Requirement: Modos de gravação
O script de gravação SHALL oferecer dois modos, sempre sobre um build escolhido pelo timestamp (`--build`), pelo menu interativo ou, quando nenhum dos dois se aplica, pelo build mais recente. Na gravação completa, ele grava a imagem inteira do build. Na gravação parcial, ele grava uma ou mais partições escolhidas entre `boot`, `system`, `storage` e `roms`, e nenhum byte fora delas SHALL ser escrito.

#### Scenario: Build mais recente por padrão
- **WHEN** existem os builds `20261013-153045` e `20261014-090000`, e o usuário grava sem `--build` fora de um terminal interativo
- **THEN** o script usa o build `20261014-090000` sem perguntar e mostra o nome dele no plano antes da confirmação

#### Scenario: Build inexistente
- **WHEN** o usuário indica `--build 20990101-000000`, que não existe em `out/`
- **THEN** o script recusa e lista os builds disponíveis

#### Scenario: Gravação parcial do system
- **WHEN** o usuário grava só `system` num cartão com o layout esperado
- **THEN** só a região da p7 é escrita, e p1, p2, p5, p6, p8, o MBR e a área de boot permanecem intactos

#### Scenario: Gravação completa
- **WHEN** o usuário grava a imagem completa com a confirmação exigida
- **THEN** o cartão passa a ter o layout, as partições e os labels do build gravado

## ADDED Requirements

### Requirement: Escolha interativa do build
Sem `--build`, num terminal interativo e com mais de um build disponível, o script SHALL mostrar um menu numerado com os builds, do mais recente para o mais antigo, e SHALL pedir a escolha antes de qualquer verificação do cartão. Enter sem resposta SHALL escolher o mais recente. Uma resposta inválida SHALL repetir a pergunta.

#### Scenario: Escolha de um build antigo
- **WHEN** existem os builds `20261013-101231` e `20261013-124416`, o usuário roda o script sem `--build` num terminal e responde `2`
- **THEN** o script usa o build `20261013-101231`, e o plano mostrado antes da confirmação cita esse timestamp

#### Scenario: Enter escolhe o mais recente
- **WHEN** o menu é mostrado e o usuário só aperta Enter
- **THEN** o script usa o build mais recente

#### Scenario: Resposta inválida
- **WHEN** o usuário responde `9` num menu com 2 builds
- **THEN** o script avisa que a opção não existe e pergunta de novo, sem escrever nada

#### Scenario: Um só build
- **WHEN** existe um único build em `out/` e o usuário roda o script sem `--build`
- **THEN** o script usa esse build sem mostrar o menu

#### Scenario: Build indicado na linha de comando
- **WHEN** o usuário passa `--build 20261013-101231` num terminal interativo
- **THEN** o script não mostra o menu e usa esse build

### Requirement: Informações de cada build
O menu, a listagem e o plano antes da confirmação SHALL mostrar, para cada build, o timestamp, o tamanho do cartão em MiB e as features aplicadas, lidos do manifest do build. Um build sem features SHALL aparecer como "sem features".

#### Scenario: Linha de um build
- **WHEN** o build `20261013-124416` foi gerado para 15000 MiB com as features `10-ptbr-sao-paulo` e `20-controle-posicional`
- **THEN** a linha dele mostra `20261013-124416`, `15000 MiB` e os dois identificadores de feature

#### Scenario: Build de referência
- **WHEN** o build foi gerado com `--no-features`
- **THEN** a linha dele mostra "sem features"

### Requirement: Listagem de builds
O script SHALL oferecer a opção `--list-builds`, que lista os builds disponíveis com suas informações, do mais recente para o mais antigo, e termina sem acessar nenhum dispositivo. Essa opção SHALL dispensar as opções de alvo e de modo de gravação.

#### Scenario: Listagem
- **WHEN** o usuário roda `./flash.sh --list-builds`
- **THEN** o script lista os builds de `out/` com timestamp, tamanho do cartão e features, e termina com sucesso sem pedir sudo

#### Scenario: Nenhum build
- **WHEN** o usuário roda `./flash.sh --list-builds` com `out/` vazio
- **THEN** o script informa que não há builds e sugere rodar `./build.sh`
