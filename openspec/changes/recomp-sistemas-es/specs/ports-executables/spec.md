# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
