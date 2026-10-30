# diagnostic-logs Specification

## Purpose

Definir a chave `r36-diagnostico` na p1 que liga os logs de diagnóstico de áudio, bateria e shader, para que o aparelho não escreva na p1 a cada boot quando ninguém os está lendo.

## Requirements

### Requirement: Chave de diagnóstico na p1
Os logs de diagnóstico de áudio (`r36-audio.log` e `r36-audio-dac.log`), de bateria (`r36-bateria.log`) e de shader (`r36-shader-gba.log`) SHALL ser gravados na raiz da p1 somente quando existir o arquivo vazio `r36-diagnostico` na raiz da p1. Sem ele, o sistema SHALL NOT criar nem atualizar nenhum desses arquivos.

#### Scenario: Aparelho sem a chave
- **WHEN** a p1 não tem `r36-diagnostico` e o aparelho liga e joga
- **THEN** nenhum dos quatro logs é criado nem alterado na p1

#### Scenario: Aparelho com a chave
- **WHEN** o usuário cria `r36-diagnostico` na raiz da p1 pelo PC e religa o aparelho
- **THEN** os quatro logs passam a ser gravados com o mesmo conteúdo que tinham antes desta chave

#### Scenario: Logs antigos no cartão
- **WHEN** a p1 tem logs de um boot anterior e não tem a chave
- **THEN** o sistema os deixa como estão e só o usuário os apaga

### Requirement: Funcionamento igual com ou sem a chave
A chave SHALL controlar apenas a leitura de diagnóstico e a gravação dos logs. O áudio (modo, chaves do RetroArch, `Speaker Function`, volume salvo), o percentual da bateria publicado e o shader por padrão no GBA SHALL se comportar do mesmo modo com e sem a chave.

#### Scenario: Áudio sem a chave
- **WHEN** o aparelho liga sem `r36-diagnostico`
- **THEN** o `retroarch.cfg` recebe os mesmos valores de áudio de antes, o `Speaker Function` é aplicado e o volume salvo vale

#### Scenario: Bateria sem a chave
- **WHEN** o aparelho liga sem `r36-diagnostico`
- **THEN** o `capacity` continua publicando o percentual calculado, e a chave `r36-bateria-original` continua devolvendo o valor do kernel

#### Scenario: Shader sem a chave
- **WHEN** o aparelho liga sem `r36-diagnostico`
- **THEN** o shader `gba-modern-remaster` continua ligado por padrão no GBA, e `r36-gba-sem-shader` continua desligando-o

### Requirement: Registro térmico fora da chave
O registro térmico (`r36-thermal.csv` e `r36-sysinfo.txt`) SHALL continuar sendo gravado com ou sem `r36-diagnostico`.

#### Scenario: Registro térmico sem a chave
- **WHEN** o aparelho liga sem `r36-diagnostico`
- **THEN** `r36-thermal.csv` e `r36-sysinfo.txt` são gravados como antes

### Requirement: Boot não depende da chave
Ler a chave SHALL NOT atrasar nem travar o boot. Se a p1 não montar a tempo, o serviço SHALL tratar a chave como ausente e seguir.

#### Scenario: p1 indisponível
- **WHEN** `/storage/roms` não monta no tempo de espera do serviço
- **THEN** nenhum log é gravado, o serviço termina sem erro e o EmulationStation abre normalmente

### Requirement: Log de brilho sob a chave
O log do ajuste de brilho (`r36-brilho.log`) SHALL ser gravado na raiz da p1 somente quando existir o arquivo vazio `r36-diagnostico` na raiz da p1. Sem ele, o sistema SHALL NOT criar nem atualizar esse arquivo, e o ajuste de brilho SHALL funcionar do mesmo modo.

#### Scenario: Sem a chave
- **WHEN** a p1 não tem `r36-diagnostico` e o usuário ajusta o brilho
- **THEN** o brilho muda e persiste, e `r36-brilho.log` não é criado nem alterado

#### Scenario: Com a chave
- **WHEN** a p1 tem `r36-diagnostico` e o usuário ajusta o brilho
- **THEN** `r36-brilho.log` registra o dispositivo de entrada, o tipo de evento do D-pad (botão ou eixo), o código do L3 quando visto e os níveis aplicados
