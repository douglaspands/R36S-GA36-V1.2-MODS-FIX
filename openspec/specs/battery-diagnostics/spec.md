# battery-diagnostics Specification

## Purpose

Definir o que o aparelho registra para avaliar a precisão do percentual de bateria (colunas do CSV, estimativa sombra e retrato do boot) e a análise desse registro no PC, sem alterar o que o EmulationStation exibe.

## Requirements

### Requirement: Grandezas de bateria no registro
Cada linha do registro térmico SHALL trazer, depois de `bat_voltage`, as colunas `bat_current` (corrente, em mA, com o sinal que o kernel informa), `bat_pct_pub` (o percentual publicado pelo aparelho em `capacity`) e `lcdbl` (brilho da tela, de 0 a 255), lidas da primeira `power_supply` do tipo `Battery`. A coluna `bat_pct` SHALL trazer o percentual do kernel, lido do `uevent` do driver e não do `capacity`, que pode estar sobreposto pelo percentual publicado.

#### Scenario: Colunas no cabeçalho
- **WHEN** o registro cria um arquivo novo
- **THEN** o cabeçalho traz `bat_current`, `bat_pct_pub` e `lcdbl` logo depois de `bat_voltage`, não traz `bat_charge_now`, `bat_charge_full` nem `bat_pct_est`, e cada linha tem tantos campos quanto o cabeçalho

#### Scenario: Unidades convertidas
- **WHEN** o kernel informa `current_now` de `-450000` µA
- **THEN** a linha traz `-450`

#### Scenario: Percentual do kernel com a publicação ativa
- **WHEN** o `uevent` informa `POWER_SUPPLY_CAPACITY=5` e o `capacity` publicado vale 41
- **THEN** a linha traz `5` em `bat_pct` e `41` em `bat_pct_pub`

#### Scenario: Leitura indisponível
- **WHEN** o kernel não expõe `current_now`, o `uevent` ou o brilho
- **THEN** o campo correspondente fica vazio, sem quebrar a linha nem impedir as demais colunas

### Requirement: Retrato da bateria no boot
O retrato do boot (`r36-sysinfo.txt`) SHALL trazer, na seção da bateria, o conteúdo de `uevent` de cada `power_supply`, cada valor ao lado do caminho de onde foi lido, as linhas do `dmesg` que citam o `axp`, e a listagem de `/sys/class/axppower` com o valor de cada atributo legível (incluindo o `axpdebug`), para mostrar o que o driver acredita sobre a célula e o estado do primeiro instante do boot.

#### Scenario: Conteúdo da seção
- **WHEN** o cartão é lido no PC depois de um boot
- **THEN** a seção da bateria de `r36-sysinfo.txt` traz o `uevent` da bateria (com o percentual, a tensão e, quando existirem, `charge_full_design` e `capacity_level`) e os `uevent` das demais fontes, como carregador e USB

#### Scenario: Mensagens do driver
- **WHEN** o `dmesg` contém linhas com `axp`
- **THEN** o retrato traz as últimas 80 dessas linhas na seção da bateria

#### Scenario: Atributos do driver
- **WHEN** `/sys/class/axppower` existe
- **THEN** o retrato traz, para cada atributo legível, uma linha `caminho: valor`

#### Scenario: Item ausente
- **WHEN** não há `power_supply` do tipo bateria, o `dmesg` não tem linhas com `axp` ou `/sys/class/axppower` não existe
- **THEN** o retrato registra o item como ausente e segue com os demais, sem travar o boot

### Requirement: Análise do registro no PC
O projeto SHALL trazer um script de análise que lê `r36-thermal.csv` (e o `.1`) no PC e resume cada ciclo de descarga, juntando os boots que o compõem, com o tempo, a carga entregue (a corrente integrada, em mAh), o erro do percentual do kernel e do publicado contra a carga restante calculada por essa integração, e os patamares em que o percentual do kernel ficou parado, sem precisar do aparelho.

#### Scenario: Resumo de uma sessão
- **WHEN** o script recebe um `r36-thermal.csv` com uma descarga completa feita em vários boots
- **THEN** ele imprime um ciclo, com a duração, os mAh entregues, o erro médio e máximo (em pontos) do kernel e do publicado, e, para o kernel, o tempo e a carga em cada patamar (por exemplo 100% e 5%) com a tensão de entrada e saída

#### Scenario: Início do ciclo
- **WHEN** o CSV tem várias descargas separadas por carga
- **THEN** o script separa os ciclos pelo status `Charging` ou `Full`, ou por um boot que começa com a tensão bem acima da do fim do boot anterior, e permite escolher um ciclo pelo `boot` inicial

#### Scenario: Arquivo sem as colunas novas
- **WHEN** o script recebe um CSV gravado antes desta change
- **THEN** ele usa as colunas que existem, avisa quais faltam e termina sem erro

### Requirement: Roteiro de coleta documentado
O manual (`docs/DESENVOLVIMENTO.md`) SHALL descrever as colunas de bateria, a descarga completa que gera o log útil, o que copiar do cartão, a chave que desliga a correção e a validação da curva com um segundo ciclo.

#### Scenario: Seguir o roteiro
- **WHEN** o usuário segue o roteiro do manual (`docs/DESENVOLVIMENTO.md`)
- **THEN** ele sabe carregar a bateria até 100%, ligar o aparelho, jogar ou deixar no menu até desligar sozinho, e copiar `r36-thermal.csv`, `r36-thermal.1.csv` e `r36-sysinfo.txt` da partição `R36-ROMS`

#### Scenario: Validar a curva
- **WHEN** o usuário termina um segundo ciclo com a correção ligada
- **THEN** o manual (`docs/DESENVOLVIMENTO.md`) diz que o erro do publicado, medido pelo script de análise, é o critério para aceitar ou reajustar os parâmetros da curva

### Requirement: Ajuste da curva no PC
O projeto SHALL trazer um script que, a partir de um ciclo de descarga completo do `r36-thermal.csv`, gera o arquivo de parâmetros da curva de `battery-level` (resistência de compensação e pontos tensão/percentual), no formato que o aparelho aceita em `r36-bateria-curva.conf`.

#### Scenario: Curva gerada de um ciclo
- **WHEN** o script recebe um CSV com um ciclo completo
- **THEN** ele escolhe a resistência de menor erro contra a carga integrada, escreve o arquivo com pontos crescentes em tensão e em percentual, e imprime o erro médio e máximo da curva nova

#### Scenario: Ciclo incompleto
- **WHEN** o ciclo não termina em desligamento
- **THEN** o script avisa que a referência de carga é relativa e não escreve o arquivo sem confirmação explícita por opção
