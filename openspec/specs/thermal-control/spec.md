# thermal-control Specification

## Purpose

Medir e, mais tarde, controlar o comportamento térmico do aparelho, para que ele não esquente além do necessário sem perder desempenho nos jogos.

## Requirements

### Requirement: Registro térmico periódico
Enquanto o aparelho estiver ligado e a feature estiver ativa, o sistema SHALL gravar uma linha de medição a cada 5 segundos em `/storage/roms/r36-thermal.csv`, sem usar cron.

#### Scenario: Uso normal
- **WHEN** o aparelho fica ligado por 1 minuto, no menu ou em jogo
- **THEN** o arquivo `/storage/roms/r36-thermal.csv` ganha cerca de 12 linhas novas

#### Scenario: Cron desligado
- **WHEN** o registro está ativo
- **THEN** o `cron.service` continua inativo

### Requirement: Conteúdo de cada medição
Cada linha SHALL trazer a data e hora, o tempo desde o boot, um identificador do boot, a temperatura de cada zona térmica, a frequência, o teto de frequência e o governor da CPU, a ocupação de cada núcleo no intervalo, a cena e a frequência da DRAM e o estado, a carga e a tensão da bateria.

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

### Requirement: Máximo desempenho desligado por padrão
A imagem SHALL sair com a opção "Enable max performance" desligada para todos os sistemas e jogos, e SHALL manter a opção ligável por sistema ou por jogo no menu do EmulationStation.

#### Scenario: Imagem recém-gravada
- **WHEN** a imagem é gravada em um cartão novo e o aparelho liga
- **THEN** a configuração global do máximo desempenho está desligada, e nenhum sistema ou jogo tem a opção ligada

#### Scenario: Jogo sem ajuste próprio
- **WHEN** um jogo de um sistema sem ajuste de máximo desempenho é aberto
- **THEN** o aparelho esquenta menos do que com a opção ligada, e o governor registrado no log segue o modo normal (`ondemand`), com a cena da DRAM definida pelo afinamento de frequência

#### Scenario: Ligar onde for preciso
- **WHEN** o usuário liga o máximo desempenho para um sistema ou jogo pelo menu do EmulationStation
- **THEN** o ajuste vale só para esse sistema ou jogo, e os demais continuam com a opção desligada

### Requirement: Ajustes de teste fora da imagem
A imagem SHALL NOT trazer ajustes de máximo desempenho por sistema ou por jogo; só o ajuste global desligado.

#### Scenario: Conteúdo da configuração
- **WHEN** a configuração do EmuELEC da imagem é inspecionada
- **THEN** a única chave de máximo desempenho é a global, com o valor desligado

### Requirement: Início do jogo respeita a chave de máximo desempenho
Ao abrir um jogo, o sistema SHALL ligar o modo de máximo desempenho (governor `performance` e cena da DRAM `0`) apenas quando a chave de máximo desempenho do jogo, do sistema ou global, nessa ordem de precedência, tiver o valor `1`; nos demais casos SHALL usar o modo normal (governor `ondemand`, com a cena da DRAM definida pelo afinamento de frequência).

#### Scenario: Imagem recém-gravada
- **WHEN** um jogo de qualquer sistema é aberto numa imagem recém-gravada
- **THEN** o governor registrado nas linhas desse jogo é `ondemand`

#### Scenario: Sistema com a opção ligada
- **WHEN** o usuário liga o máximo desempenho para um sistema no menu e abre um jogo dele
- **THEN** o governor registrado nas linhas desse jogo é `performance`, e o de um jogo de outro sistema continua `ondemand`

#### Scenario: Jogo com a opção desligada num sistema ligado
- **WHEN** o máximo desempenho está ligado para o sistema e desligado para um jogo dele
- **THEN** o governor registrado nas linhas desse jogo é `ondemand`

### Requirement: Ocupação por núcleo e cena da DRAM registradas
Cada linha do registro SHALL trazer a ocupação de `cpu0` a `cpu3` e a cena da DRAM lida do mesmo caminho em que o modo de máximo desempenho a escreve.

#### Scenario: Linha com ocupação
- **WHEN** uma linha é gravada com o aparelho ligado e os núcleos acessíveis
- **THEN** os quatro campos de ocupação trazem um número de 0 a 100, e a linha tem tantos campos quanto o cabeçalho

#### Scenario: Cena da DRAM
- **WHEN** o sistema tem a cena da DRAM em `sunxi-ddrfreq/devfreq/sunxi-ddrfreq/dsm/scene`
- **THEN** a coluna `dram_scene` traz o valor desse arquivo

### Requirement: Teto de frequência, DRAM e tensão da bateria registrados
Cada linha do registro SHALL trazer também o teto de frequência da CPU em vigor, em MHz, a frequência atual da DRAM, em MHz, e a tensão da bateria, em mV.

#### Scenario: Colunas novas no cabeçalho
- **WHEN** o registro cria um arquivo novo
- **THEN** o cabeçalho traz as colunas `cpu_max_mhz`, `dram_mhz` e `bat_voltage`, e cada linha tem tantos campos quanto o cabeçalho

#### Scenario: Teto abaixo do máximo
- **WHEN** algo no sistema baixa o teto de frequência da CPU durante um jogo
- **THEN** a coluna `cpu_max_mhz` dessas linhas mostra o teto reduzido, e não o máximo do hardware

#### Scenario: Leitura indisponível
- **WHEN** o sistema não expõe a frequência da DRAM ou a tensão da bateria
- **THEN** o campo correspondente fica vazio, sem quebrar a linha

#### Scenario: Log antigo no cartão
- **WHEN** o cartão já tem um `r36-thermal.csv` com o cabeçalho anterior
- **THEN** o arquivo antigo vira `r36-thermal.1.csv` e o novo começa com o cabeçalho atual

### Requirement: Retrato do sistema no boot
A cada boot, com a feature ativa, o sistema SHALL gravar em `/storage/roms/r36-sysinfo.txt` um retrato legível no PC dos parâmetros de frequência e temperatura, substituindo o do boot anterior.

#### Scenario: Conteúdo do retrato
- **WHEN** o cartão é lido no PC depois de um boot
- **THEN** `r36-sysinfo.txt` traz os governors e as frequências disponíveis da CPU, o teto e o máximo de frequência, os tunables do ondemand, a cena e as frequências da DRAM, os trip points das zonas térmicas e o estado dos dispositivos de resfriamento, cada valor ao lado do caminho de onde foi lido

#### Scenario: Retrato depois do afinamento
- **WHEN** o retrato é gravado
- **THEN** os tunables do ondemand e a frequência mínima registrados são os já afinados no boot

#### Scenario: Item ausente
- **WHEN** um dos caminhos lidos não existe no aparelho
- **THEN** o retrato registra o item como ausente e segue com os demais, sem travar o boot

#### Scenario: Cartão sem espaço ou ROMs não montadas
- **WHEN** `/storage/roms` não está montado ou tem menos de 64 MB livres
- **THEN** o retrato não é gravado, e o registro térmico segue normalmente
