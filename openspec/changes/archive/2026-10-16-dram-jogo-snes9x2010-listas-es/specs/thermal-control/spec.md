# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Conteúdo de cada medição
Cada linha SHALL trazer a data e hora, o tempo desde o boot, um identificador do boot, a temperatura de cada zona térmica, a frequência, o teto de frequência e o governor da CPU, a ocupação de cada núcleo no intervalo, a cena e a frequência da DRAM e o estado, a carga e a tensão da bateria.

#### Scenario: Linha completa
- **WHEN** uma linha é gravada
- **THEN** ela tem um valor para cada coluna do cabeçalho, e um campo cuja leitura falhou fica vazio, sem quebrar a linha

#### Scenario: Relógio sem hora certa
- **WHEN** o aparelho liga sem hora certa no relógio
- **THEN** o tempo desde o boot e o identificador do boot ainda permitem ordenar as medições e separar as sessões

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
