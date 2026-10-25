## Purpose

Definir o que o aparelho registra para avaliar a precisão do percentual de bateria (colunas do CSV, estimativa sombra e retrato do boot) e a análise desse registro no PC, sem alterar o que o EmulationStation exibe.

## ADDED Requirements

### Requirement: Grandezas de bateria no registro
Cada linha do registro térmico SHALL trazer, depois de `bat_voltage`, as colunas `bat_current` (corrente, em mA, com o sinal que o kernel informa), `bat_charge_now` e `bat_charge_full` (carga atual e carga cheia que o driver acredita ter, em mAh) e `bat_pct_est` (estimativa própria do percentual), todas lidas da primeira `power_supply` do tipo `Battery`.

#### Scenario: Colunas no cabeçalho
- **WHEN** o registro cria um arquivo novo
- **THEN** o cabeçalho traz `bat_current`, `bat_charge_now`, `bat_charge_full` e `bat_pct_est` logo depois de `bat_voltage`, e cada linha tem tantos campos quanto o cabeçalho

#### Scenario: Unidades convertidas
- **WHEN** o kernel informa `current_now` de `-450000` µA, `charge_now` de `1200000` µAh e `charge_full` de `2000000` µAh
- **THEN** a linha traz `-450`, `1200` e `2000`

#### Scenario: Leitura indisponível
- **WHEN** o kernel não expõe `current_now`, `charge_now` ou `charge_full`
- **THEN** o campo correspondente fica vazio, sem quebrar a linha nem impedir as demais colunas

### Requirement: Estimativa de percentual só para avaliação
O registro SHALL calcular `bat_pct_est` a partir da tensão da bateria, com uma curva genérica de célula Li-ion e filtro entre amostras consecutivas, e SHALL NOT usar essa estimativa em nada além do CSV: o `capacity` do kernel, o que o EmulationStation e o RetroArch exibem e o desligamento por bateria fraca continuam vindo do kernel.

#### Scenario: Valores de referência
- **WHEN** a tensão estável é 4200 mV, 3300 mV ou um valor entre dois pontos da curva
- **THEN** `bat_pct_est` vale 100, 0 ou o valor interpolado entre os dois pontos, sempre entre 0 e 100

#### Scenario: Filtro entre amostras
- **WHEN** a tensão cai 200 mV de uma amostra para a seguinte por causa de um pico de carga
- **THEN** `bat_pct_est` varia menos do que o percentual calculado direto da tensão nova

#### Scenario: Carregando
- **WHEN** o estado da bateria é `Charging` ou `Full`
- **THEN** `bat_pct_est` fica vazio, porque a tensão com carregador não representa a carga

#### Scenario: Sem tensão
- **WHEN** a tensão da bateria não pode ser lida
- **THEN** `bat_pct_est` fica vazio

#### Scenario: Exibição inalterada
- **WHEN** a feature está ativa
- **THEN** o ícone e o texto de bateria do EmulationStation e o menu do RetroArch mostram o mesmo valor que mostrariam sem a feature

### Requirement: Retrato da bateria no boot
O retrato do boot (`r36-sysinfo.txt`) SHALL trazer, na seção da bateria, o conteúdo de `uevent` de cada `power_supply`, cada valor ao lado do caminho de onde foi lido, e as linhas do `dmesg` que citam o `axp`, para mostrar o que o driver acredita sobre a célula e o estado do primeiro instante do boot.

#### Scenario: Conteúdo da seção
- **WHEN** o cartão é lido no PC depois de um boot
- **THEN** a seção da bateria de `r36-sysinfo.txt` traz o `uevent` da bateria (com o percentual, a tensão e, quando existirem, `charge_full_design` e `capacity_level`) e os `uevent` das demais fontes, como carregador e USB

#### Scenario: Mensagens do driver
- **WHEN** o `dmesg` contém linhas com `axp`
- **THEN** o retrato traz as últimas 80 dessas linhas na seção da bateria

#### Scenario: Item ausente
- **WHEN** não há `power_supply` do tipo bateria, ou o `dmesg` não tem linhas com `axp`
- **THEN** o retrato registra o item como ausente e segue com os demais, sem travar o boot

### Requirement: Análise do registro no PC
O projeto SHALL trazer um script de análise que lê `r36-thermal.csv` no PC e resume, por boot, o ponto de partida (tensão, percentual do kernel e percentual estimado nas primeiras amostras) e a descarga (tempo, tensão, percentual do kernel e percentual estimado), sem precisar do aparelho.

#### Scenario: Resumo de uma sessão
- **WHEN** o script recebe um `r36-thermal.csv` com uma descarga
- **THEN** ele imprime, para cada boot, a diferença entre o percentual do kernel e o estimado no início e a taxa de queda do percentual do kernel e do estimado por hora

#### Scenario: Arquivo sem as colunas novas
- **WHEN** o script recebe um CSV gravado antes desta change
- **THEN** ele usa as colunas que existem, avisa quais faltam e termina sem erro

### Requirement: Roteiro de coleta documentado
O README SHALL descrever as colunas de bateria, a descarga completa que gera o log útil e o que copiar do cartão.

#### Scenario: Seguir o roteiro
- **WHEN** o usuário segue o roteiro do README
- **THEN** ele sabe carregar a bateria até 100%, ligar o aparelho, jogar ou deixar no menu até desligar sozinho, e copiar `r36-thermal.csv`, `r36-thermal.1.csv` e `r36-sysinfo.txt` da partição `R36-ROMS`
