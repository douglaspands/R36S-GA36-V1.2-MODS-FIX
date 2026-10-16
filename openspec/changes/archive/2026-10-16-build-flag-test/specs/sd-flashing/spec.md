## MODIFIED Requirements

### Requirement: Modos de gravação
O script de gravação SHALL oferecer dois modos, sempre sobre um build escolhido pelo identificador (`--build`), pelo menu interativo ou, quando nenhum dos dois se aplica, pelo build mais recente. O identificador de um build é o nome do diretório dele em `out/`: o timestamp `AAAAMMDD-HHMMSS`, com o sufixo `-test` quando o build foi gerado como teste. Builds de teste SHALL ser tratados como quaisquer outros: SHALL aparecer no menu e na listagem, SHALL poder ser indicados em `--build` e SHALL entrar na escolha do mais recente. Na gravação completa, ele grava a imagem inteira do build. Na gravação parcial, ele grava uma ou mais partições escolhidas entre `boot`, `system`, `storage` e `roms`, e nenhum byte fora delas SHALL ser escrito.

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

#### Scenario: Build de teste indicado em --build
- **WHEN** existe o build `20261016-150632-test` e o usuário indica `--build 20261016-150632-test`
- **THEN** o script usa esse build e mostra o nome dele no plano antes da confirmação

#### Scenario: Build de teste como mais recente
- **WHEN** existem os builds `20261016-120000` e `20261016-150632-test`, e o usuário grava sem `--build` fora de um terminal interativo
- **THEN** o script usa o build `20261016-150632-test` sem perguntar, como usaria qualquer build mais recente

#### Scenario: Identificador malformado
- **WHEN** o usuário indica `--build 20261016-150632-teste`
- **THEN** o script recusa informando o formato esperado (`AAAAMMDD-HHMMSS`, com `-test` opcional)

### Requirement: Informações de cada build
O menu, a listagem e o plano antes da confirmação SHALL mostrar, para cada build, o identificador, o tamanho do cartão em MiB e as features aplicadas, lidos do manifest do build. Um build sem features SHALL aparecer como "sem features". Um build gerado como teste SHALL aparecer com o marcador `test` na linha, além do sufixo `-test` do identificador.

#### Scenario: Linha de um build
- **WHEN** o build `20261013-124416` foi gerado para 15000 MiB com as features `10-ptbr-sao-paulo` e `20-controle-posicional`
- **THEN** a linha dele mostra `20261013-124416`, `15000 MiB` e os dois identificadores de feature

#### Scenario: Build de referência
- **WHEN** o build foi gerado com `--no-features`
- **THEN** a linha dele mostra "sem features"

#### Scenario: Linha de um build de teste
- **WHEN** o build `20261016-150632-test` foi gerado com `--test` para 15000 MiB
- **THEN** a linha dele mostra `20261016-150632-test`, `15000 MiB`, as features e o marcador `test`
