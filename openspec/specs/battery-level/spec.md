# battery-level Specification

## Purpose

Definir o percentual de bateria que o aparelho publica em `/sys/class/power_supply/battery/capacity` e que o EmulationStation, o RetroArch, o LED de bateria baixa e o desligamento por bateria fraca leem, calculado pela tensão e pela corrente em vez do medidor do kernel, que se mostrou impreciso.

## Requirements

### Requirement: Percentual calculado por tensão e corrente
O aparelho SHALL calcular o percentual de bateria a partir da tensão e da corrente de descarga lidas da `power_supply` do tipo `Battery`, somando à tensão a queda proporcional à corrente e convertendo o resultado por uma curva monotônica, com filtro entre amostras, cujos parâmetros ficam num arquivo ajustável fora do script.

#### Scenario: Curva monotônica
- **WHEN** a tensão compensada sobe de 3500 mV para 4100 mV
- **THEN** o percentual calculado nunca diminui nesse intervalo e fica sempre entre 0 e 100

#### Scenario: Compensação pela corrente
- **WHEN** duas leituras têm a mesma tensão e a segunda tem corrente maior
- **THEN** o percentual da segunda é maior ou igual ao da primeira

#### Scenario: Parâmetros ajustáveis
- **WHEN** o arquivo de parâmetros da curva é trocado por outro com pontos diferentes
- **THEN** o percentual calculado passa a seguir a curva nova sem alterar o script

#### Scenario: Curva trocada pelo cartão
- **WHEN** a raiz da p1 tem um `r36-bateria-curva.conf` válido
- **THEN** o percentual calculado segue a curva dele, sem regravar o `system`

#### Scenario: Curva do cartão inválida
- **WHEN** o `r36-bateria-curva.conf` tem pontos fora de ordem ou menos de 2 pontos
- **THEN** o aparelho ignora o arquivo, registra o motivo e usa a curva do `system`

#### Scenario: Corrente indisponível
- **WHEN** o kernel não expõe `current_now`
- **THEN** o percentual é calculado só pela tensão, sem compensação

### Requirement: Publicação no caminho padrão do kernel
O aparelho SHALL publicar o percentual calculado de modo que a leitura de `/sys/class/power_supply/battery/capacity` devolva esse valor, para que o EmulationStation, o RetroArch e o desligamento por bateria fraca o usem sem alteração, e SHALL atualizá-lo enquanto o aparelho estiver ligado.

#### Scenario: Leitura pelos consumidores
- **WHEN** o ES, o RetroArch ou o `udt_battery.sh` leem o `capacity`
- **THEN** recebem o percentual calculado, um inteiro de 0 a 100

#### Scenario: Valor presente antes do ES
- **WHEN** o ES inicia
- **THEN** o percentual calculado já está publicado, e o ES não chega a ler o valor do kernel

#### Scenario: Valor atualizado
- **WHEN** a tensão da bateria muda durante o uso
- **THEN** a leitura do `capacity` reflete a mudança em poucos segundos

### Requirement: Em descarga o percentual só cai
Com a bateria em descarga, o percentual publicado SHALL NOT subir em relação ao valor anterior, mesmo quando a tensão sobe porque a carga do aparelho diminuiu.

#### Scenario: Alívio de carga
- **WHEN** o aparelho sai de um jogo pesado para o menu e a tensão sobe 60 mV
- **THEN** o percentual publicado fica igual ou menor que o de antes

#### Scenario: Início do boot
- **WHEN** o aparelho liga em descarga
- **THEN** o primeiro valor publicado vem da curva (sem histórico) e, dali em diante, só cai

### Requirement: Carregador reinicia a referência
Com o status da bateria em `Charging` ou `Full`, o percentual publicado SHALL seguir o valor do `capacity` do kernel, e ao voltar à descarga o cálculo SHALL recomeçar da curva, sem carregar o valor da descarga anterior.

#### Scenario: Carregando
- **WHEN** o status é `Charging`
- **THEN** o `capacity` publicado é o do kernel

#### Scenario: Volta à descarga
- **WHEN** o carregador é retirado com a bateria a 4150 mV
- **THEN** o percentual publicado parte do valor da curva para essa tensão, e não do valor da descarga anterior

### Requirement: Zero perto do corte de desligamento
O percentual publicado SHALL ser 0 quando a tensão lida (sem compensação) for 3450 mV ou menos, e SHALL ser maior que 0 enquanto ela for 3500 mV ou mais, para que o desligamento que exige `capacity` 0 e tensão no corte de 3400 mV aconteça no fim da carga e nunca antes dela.

#### Scenario: Fim da carga
- **WHEN** a tensão lida é 3440 mV com 850 mA
- **THEN** o percentual publicado é 0

#### Scenario: Ainda há carga
- **WHEN** a tensão lida é 3500 mV com 800 mA
- **THEN** o percentual publicado é maior que 0

#### Scenario: Meio da descarga
- **WHEN** a tensão é 3800 mV com 550 mA
- **THEN** o percentual publicado fica entre 30 e 60

### Requirement: Desligamento forçado independente
O desligamento forçado por tensão a 3350 mV SHALL continuar funcionando sem depender do percentual publicado, mesmo que o serviço de cálculo pare ou falhe.

#### Scenario: Serviço parado
- **WHEN** o serviço de cálculo está parado e a tensão cai a 3350 mV
- **THEN** o `udt_battery.sh` desliga o aparelho como antes

### Requirement: Falha volta ao medidor do kernel
Se a publicação não puder ser feita, ou se o serviço parar, o aparelho SHALL ficar com o valor do kernel em `capacity`, sem erro visível ao usuário e sem travar o boot.

#### Scenario: Publicação recusada
- **WHEN** o kernel recusa a publicação sobre o `capacity`
- **THEN** o `capacity` continua sendo o do kernel, o serviço registra o motivo e o boot segue normalmente

#### Scenario: Serviço encerrado
- **WHEN** o serviço é parado
- **THEN** o `capacity` volta a ser o do kernel

### Requirement: Chave para voltar ao valor do kernel
Um arquivo `r36-bateria-original` na raiz da partição `R36-ROMS` SHALL desligar a correção no boot seguinte, deixando o `capacity` do kernel como estava de fábrica.

#### Scenario: Chave presente
- **WHEN** `r36-bateria-original` existe na raiz da p1 no boot
- **THEN** nenhum percentual calculado é publicado e o ES mostra o valor do kernel

#### Scenario: Chave ausente
- **WHEN** o arquivo não existe
- **THEN** o percentual calculado é publicado
