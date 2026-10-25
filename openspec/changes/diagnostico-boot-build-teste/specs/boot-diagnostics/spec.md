# Spec Delta

## Purpose

Mostrar na tela e guardar no cartão o que o systemd faz durante o boot de um build de teste, para diagnosticar travamentos sem rede, SSH nem console do kernel na tela.

## ADDED Requirements

### Requirement: Diagnóstico só em build de teste
As features de diagnóstico de boot SHALL ser `test_only` e SHALL entrar na imagem só em builds gerados com `./build.sh --test`. Um build sem `--test` SHALL NOT conter nenhum arquivo delas.

#### Scenario: Build de teste
- **WHEN** a imagem é gerada com `./build.sh --test`
- **THEN** o `changes.txt` e o `R36-BUILD.txt` listam `90-boot-log-tela` e `91-boot-log-cartao`

#### Scenario: Build normal
- **WHEN** a imagem é gerada com `./build.sh`
- **THEN** nenhum arquivo das features `90-boot-log-tela` e `91-boot-log-cartao` existe no SYSTEM gerado

### Requirement: Log do boot na tela
Num build de teste, o aparelho SHALL mostrar na tela, por cima da imagem do controle, as mensagens do journal do boot atual, atualizadas enquanto o boot avança, até o EmulationStation abrir.

#### Scenario: Boot normal
- **WHEN** o aparelho liga com um build de teste e o boot chega ao EmulationStation
- **THEN** as linhas do journal aparecem na tela durante o boot e somem quando o EmulationStation abre, que funciona normalmente

#### Scenario: Boot travado
- **WHEN** um serviço trava o boot antes de o EmulationStation abrir
- **THEN** a tela continua mostrando o journal, com as últimas linhas indicando os serviços que iniciaram ou falharam

### Requirement: Log do boot no cartão
Num build de teste, o aparelho SHALL gravar a cada 5 s, nos primeiros 3 min do boot, um retrato em texto com os jobs pendentes do systemd, as units com falha, o journal do boot e as mensagens do kernel, num arquivo legível no PC sem root.

#### Scenario: Leitura no PC
- **WHEN** o aparelho dá boot com um build de teste e o cartão é lido no PC depois
- **THEN** `R36-ROMS/r36-boot-log/boot-<n>.txt` existe, tem a hora do retrato, a saída de `systemctl list-jobs`, de `systemctl --failed`, de `journalctl -b` e de `dmesg`

#### Scenario: Deadlock entre serviços
- **WHEN** dois serviços esperam um pelo outro e o boot não chega ao EmulationStation
- **THEN** o último retrato gravado mostra, em `systemctl list-jobs`, os jobs dos dois serviços parados em `waiting`

#### Scenario: Vários boots
- **WHEN** o aparelho dá boot várias vezes com o mesmo cartão
- **THEN** cada boot grava num arquivo próprio, com número maior que o anterior, e são mantidos só os 10 mais recentes

### Requirement: Fallback do log na partição do SYSTEM
Se a partição de ROMs não estiver montada em `/storage/roms` 60 s depois de o serviço iniciar, o log SHALL ser gravado em `R36-SYSTEM/r36-boot-log/` (p7, FAT16). A p7 SHALL ficar montada só leitura fora de cada gravação, e SHALL NOT ter nenhum outro arquivo alterado.

#### Scenario: ROMs não montadas
- **WHEN** o boot trava antes de o `mount_romfs.sh` montar a p1
- **THEN** o PC encontra `R36-SYSTEM/r36-boot-log/boot-<n>.txt` com os retratos, e o arquivo `SYSTEM` da p7 continua idêntico ao do build

### Requirement: Diagnóstico sem efeito na ordem do boot
Os serviços de diagnóstico SHALL NOT declarar ordem (`After=` ou `Before=`) em relação ao `emuelec-autostart.service` nem ao `emustation.service`, e uma falha neles SHALL NOT impedir nem atrasar o EmulationStation.

#### Scenario: Ferramenta de log ausente ou com erro
- **WHEN** o terminal de tela não consegue abrir o display ou a gravação no cartão falha
- **THEN** o serviço correspondente termina com erro registrado no journal, e o EmulationStation abre no mesmo tempo que abriria sem o diagnóstico
