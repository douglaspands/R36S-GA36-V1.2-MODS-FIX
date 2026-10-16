# Spec Delta

## Purpose

Medir e, mais tarde, controlar o comportamento térmico do aparelho, para que ele não esquente além do necessário sem perder desempenho nos jogos.

## ADDED Requirements

### Requirement: Registro térmico periódico
Enquanto o aparelho estiver ligado e a feature estiver ativa, o sistema SHALL gravar uma linha de medição a cada 5 segundos em `/storage/roms/r36-thermal.csv`, sem usar cron.

#### Scenario: Uso normal
- **WHEN** o aparelho fica ligado por 1 minuto, no menu ou em jogo
- **THEN** o arquivo `/storage/roms/r36-thermal.csv` ganha cerca de 12 linhas novas

#### Scenario: Cron desligado
- **WHEN** o registro está ativo
- **THEN** o `cron.service` continua inativo

### Requirement: Conteúdo de cada medição
Cada linha SHALL trazer a data e hora, o tempo desde o boot, um identificador do boot, a temperatura de cada zona térmica, a frequência e o governor da CPU, a ocupação de cada núcleo no intervalo, a cena da DRAM e o estado e a carga da bateria.

#### Scenario: Linha completa
- **WHEN** uma linha é gravada
- **THEN** ela tem um valor para cada coluna do cabeçalho, e um campo cuja leitura falhou fica vazio, sem quebrar a linha

#### Scenario: Relógio sem hora certa
- **WHEN** o aparelho liga sem hora certa no relógio
- **THEN** o tempo desde o boot e o identificador do boot ainda permitem ordenar as medições e separar as sessões

### Requirement: Identificação do jogo em execução
Cada linha SHALL indicar o sistema, o emulador, o core e o nome do arquivo do jogo em execução, ou ficar com esses campos vazios quando nenhum jogo estiver rodando.

#### Scenario: Jogo em execução
- **WHEN** um jogo de GBA roda no mGBA
- **THEN** as linhas desse período trazem o sistema `gba`, o core `mgba` e o nome do arquivo da ROM

#### Scenario: Menu
- **WHEN** o aparelho está no menu do EmulationStation
- **THEN** os campos de sistema, emulador, core e jogo ficam vazios

### Requirement: Arquivo legível no PC
O log SHALL ser um único arquivo CSV com cabeçalho na primeira linha, gravado na partição de ROMs, para ser aberto direto no PC.

#### Scenario: Leitura no PC
- **WHEN** o cartão é colocado no PC
- **THEN** `r36-thermal.csv` aparece na partição `R36-ROMS` e abre como CSV, com o cabeçalho na primeira linha

### Requirement: Tamanho máximo do log
O log SHALL ocupar no máximo 2 MB no cartão: ao passar de 1 MB, o arquivo atual vira `r36-thermal.1.csv`, substituindo o anterior, e um novo `r36-thermal.csv` começa com cabeçalho.

#### Scenario: Rotação
- **WHEN** `r36-thermal.csv` passa de 1 MB
- **THEN** ele é renomeado para `r36-thermal.1.csv`, o `r36-thermal.1.csv` anterior deixa de existir, e as próximas linhas vão para um `r36-thermal.csv` novo

#### Scenario: Uso prolongado
- **WHEN** o aparelho registra por muitas horas seguidas
- **THEN** os dois arquivos somados nunca passam de 2 MB

### Requirement: Espaço livre preservado
O sistema SHALL NOT gravar no log quando a partição de ROMs tiver menos de 64 MB livres, e SHALL voltar a gravar quando houver espaço.

#### Scenario: Cartão quase cheio
- **WHEN** a partição de ROMs tem menos de 64 MB livres
- **THEN** nenhuma linha é gravada, e o espaço livre não diminui por causa do log

#### Scenario: Espaço liberado
- **WHEN** o espaço livre volta a passar de 64 MB
- **THEN** a gravação recomeça

### Requirement: Medição sem efeito no desempenho
O registro SHALL NOT alterar o governor, o clock da CPU, a cena da DRAM nem a forma como os jogos são iniciados.

#### Scenario: Jogo pesado
- **WHEN** um jogo roda com o registro ativo
- **THEN** o `maxperf` e o `normperf` agem como na imagem sem a feature, e o jogo roda com o mesmo desempenho

### Requirement: Falhas não afetam o aparelho
Se a partição de ROMs não estiver montada, ou se alguma leitura ou gravação falhar, o registro SHALL seguir tentando no próximo ciclo, sem travar o boot nem o EmulationStation.

#### Scenario: ROMs não montadas
- **WHEN** `/storage/roms` não é um ponto de montagem
- **THEN** nada é gravado, o boot segue normalmente e a gravação começa quando a partição estiver montada

### Requirement: Registro desligável
O registro SHALL fazer parte de uma feature própria, que pode ser desligada sem afetar as demais.

#### Scenario: Feature desligada
- **WHEN** a imagem é gerada com a feature do registro desligada
- **THEN** o serviço de registro não existe na imagem, e nenhum `r36-thermal.csv` é criado no uso
