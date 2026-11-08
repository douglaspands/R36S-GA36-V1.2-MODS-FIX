# ports-executables Specification

## Purpose

Definir como os executáveis e bibliotecas dos ports em `/storage/roms/ports/` rodam a partir de uma cópia na p8, montada por cima do arquivo da p1, para que o jogador copie um port pelo PC e jogue sem permissão de execução, edição de script ou gravação do SYSTEM.

## Requirements

### Requirement: Executáveis dos ports rodam fora da p1
Para cada arquivo ELF ou biblioteca `.so` em `/storage/roms/ports/` e em `/storage/roms/*-recomp/`, o sistema SHALL montar por cima dele, antes de o EmulationStation abrir, uma cópia com permissão `0755` guardada na p8, de modo que o processo execute dessa cópia e nunca do arquivo da p1. O arquivo original na p1 SHALL NOT ser alterado, e o caminho que o script do port ou o lançador usa SHALL continuar o mesmo. Nenhum script de port SHALL precisar de edição.

#### Scenario: Port copiado pelo PC
- **WHEN** o jogador copia um port (script em `ports_scripts/` e pasta com binário e dados em `ports/<nome>/`) para a p1 pelo PC e liga o aparelho
- **THEN** o port aparece no menu "Ports", abre e executa o binário a partir de uma cópia fora da p1, sem o jogador dar permissão de execução

#### Scenario: Port novo sem build nem gravação do sistema
- **WHEN** o jogador instala um port que nenhuma imagem anterior conhecia, só copiando arquivos para a p1, sem gerar imagem e sem rodar `./flash.sh`
- **THEN** no boot seguinte o port aparece no menu "Ports" e executa, e nenhuma etapa de build ou gravação do SYSTEM foi necessária

#### Scenario: Dados e saves continuam na p1
- **WHEN** o port grava um save, um mapa ou uma opção dentro da própria pasta `ports/<nome>/`
- **THEN** o arquivo é gravado na p1 e fica visível no PC

#### Scenario: Binário trocado pelo PC
- **WHEN** o jogador substitui pelo PC o binário de um port na p1 e liga o aparelho
- **THEN** o novo conteúdo vira a cópia montada naquele caminho, sem regravar a imagem, e a cópia do conteúdo antigo é apagada

#### Scenario: Arquivo que não é executável
- **WHEN** a pasta `ports/` ou uma pasta `*-recomp/` tem arquivos de dados, textos ou ROMs de outros sistemas
- **THEN** nenhum deles é copiado nem montado

#### Scenario: Jogo recompilado copiado pelo PC
- **WHEN** o jogador copia `Jogo.sh` e a pasta `Jogo/` (com `launch.sh` e o `.elf`) para `/storage/roms/gba-recomp/` pelo PC e liga o aparelho
- **THEN** o `.sh`, o `launch.sh` e o ELF abrem e executam a partir de cópias `0755` fora da p1, sem permissão de execução dada pelo jogador e sem regravar a imagem

### Requirement: Cópias na p8 com cache por conteúdo
As cópias SHALL ficar em `/storage/.config/r36-ports-exec/`, nomeadas pelo sha256 do conteúdo. O serviço SHALL copiar só o conteúdo que ainda não tem cópia e SHALL apagar, a cada boot, as cópias que nenhum arquivo da p1 usa.

#### Scenario: Boot sem mudanças
- **WHEN** o aparelho dá boot e os executáveis de `ports/` são os mesmos do boot anterior
- **THEN** o serviço não copia nenhum arquivo, só refaz as montagens

#### Scenario: Port removido
- **WHEN** o jogador apaga pelo PC a pasta de um port
- **THEN** no boot seguinte as cópias daquele port somem da p8

#### Scenario: Mesmo conteúdo em dois caminhos
- **WHEN** dois arquivos da p1 têm o mesmo conteúdo
- **THEN** existe uma única cópia na p8 e as duas montagens apontam para ela

### Requirement: Falha de um executável não derruba o boot
Erro ao copiar, dar permissão ou montar um executável SHALL ser registrado no log e SHALL NOT impedir o serviço de tratar os demais arquivos, nem o boot, nem o EmulationStation. O serviço SHALL esperar `/storage/roms` virar ponto de montagem por no máximo 20 segundos e, se isso não ocorrer, terminar sem montar nada. O serviço SHALL NOT ter `After=emuelec-autostart.service`.

#### Scenario: Montagem recusada
- **WHEN** o kernel recusa montar a cópia sobre um dos arquivos
- **THEN** o log traz o caminho e o erro, os outros executáveis continuam montados e o EmulationStation abre

#### Scenario: p1 não montada
- **WHEN** `/storage/roms` não vira ponto de montagem em 20 segundos
- **THEN** o serviço termina sem montar nada e o boot continua

#### Scenario: Montagem repetida
- **WHEN** o serviço roda de novo com um arquivo já coberto por uma montagem
- **THEN** ele não empilha uma segunda montagem sobre o mesmo caminho

### Requirement: Diagnóstico dos executáveis em log na p1
A cada boot, o serviço SHALL gravar `/storage/roms/ports/r36-ports-exec.log`, substituindo o conteúdo anterior, com uma linha por executável encontrado (caminho, sha256 e resultado da montagem) e as opções de montagem do diretório das cópias. O arquivo SHALL ser texto simples legível no PC, e falha ao gravá-lo SHALL NOT interromper o serviço.

#### Scenario: Conferir o que está em uso
- **WHEN** o jogador lê o log no PC depois de copiar um binário novo
- **THEN** a linha do binário traz o sha256 do arquivo copiado e se a montagem funcionou

#### Scenario: Log não cresce
- **WHEN** o aparelho dá boot várias vezes
- **THEN** o log contém só o registro do último boot

### Requirement: Executáveis entregues pela imagem seguem a mesma regra
Um executável que uma feature entrega em `roms/ports/` SHALL ser tratado pelo serviço como o de qualquer port copiado pelo jogador: executar de uma cópia fora da p1, sem permissão de execução na FAT32 nem tratamento especial no lançador.

#### Scenario: Binário entregue pela imagem
- **WHEN** a imagem entrega um binário em `ports/<nome>/` e o aparelho dá boot
- **THEN** o log do serviço lista esse binário com o sha256 e o resultado da montagem, e o port o executa da cópia fora da p1

#### Scenario: Binário trocado depois da gravação
- **WHEN** o jogador substitui pelo PC o binário entregue pela imagem
- **THEN** o binário do jogador passa a valer no boot seguinte, e a imagem não o sobrescreve em cartões gravados com `--keep-roms`

### Requirement: Pastas de recomp varridas por padrão de nome
O serviço SHALL tratar como pasta de recomp todo diretório de primeiro nível em `/storage/roms/` cujo nome termine em `-recomp`, sem lista fixa de consoles. Nessas pastas SHALL tratar como executável todo ELF, de qualquer extensão, e todo script com `#!`; em `ports/` só o ELF vale. Os demais arquivos, `recomp.log` e `recomp.log.1` SHALL NOT ser tratados como executáveis.

#### Scenario: Console novo sem mudança no serviço
- **WHEN** uma imagem futura declara o sistema `snes-recomp` e o jogador copia um ELF para `/storage/roms/snes-recomp/`
- **THEN** o ELF é montado a partir de uma cópia `0755` na p8 sem nenhuma alteração no serviço

#### Scenario: Log do lançador não é executável
- **WHEN** a pasta `gba-recomp/` contém `recomp.log` e `recomp.log.1`
- **THEN** nenhum deles é copiado nem montado

#### Scenario: Cartão sem pasta de recomp
- **WHEN** `/storage/roms/` não tem nenhuma pasta `*-recomp`
- **THEN** o serviço termina normalmente, só com os ports, e o boot segue sem atraso

### Requirement: Executáveis de recomp no mesmo log e no mesmo cache
Os executáveis de recomp SHALL usar o mesmo diretório de cópias e o mesmo log `r36-ports-exec.log` dos ports, com a regra de apagar a cada boot as cópias que nenhum arquivo da p1 usa. Uma falha ao tratar um recomp SHALL NOT impedir o tratamento dos ports nem dos outros recomps.

#### Scenario: Log lista os recomps
- **WHEN** o jogador lê `r36-ports-exec.log` depois de copiar um jogo recomp
- **THEN** o log traz uma linha com o caminho em `gba-recomp/`, o sha256 e o resultado da montagem

#### Scenario: Recomp removido
- **WHEN** o jogador apaga `Jogo.sh` e a pasta `Jogo/` pelo PC
- **THEN** no boot seguinte a cópia dele some da p8, e as dos ports ficam intactas

#### Scenario: Recomp com erro
- **WHEN** o kernel recusa montar a cópia de um recomp
- **THEN** o log traz o caminho e o erro, e os demais recomps e os ports continuam montados
