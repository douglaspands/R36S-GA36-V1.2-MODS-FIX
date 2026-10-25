# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Binário único na partição SYSTEM`
- TO: `### Requirement: Binário do ClassiCube na p1 como port normal`

## MODIFIED Requirements

### Requirement: Binário do ClassiCube na p1 como port normal
O binário `ClassiCube` SHALL ser entregue pela imagem em `/storage/roms/ports/classicube/ClassiCube`, na p1, como o executável de qualquer port, e SHALL NOT existir cópia dele na partição SYSTEM. A p1 (FAT32) não guarda permissão de execução, então ele SHALL executar de uma cópia fora da p1 preparada pelo serviço da capability `ports-executables`. O binário que está na p1 SHALL ser sempre o que vale: o jogador pode substituí-lo pelo PC, e uma gravação com `--keep-roms` SHALL NOT sobrescrevê-lo. Na p1 ficam também os arquivos que o jogador ou o PC alteram (opções, mapas, texturas e sons em `/storage/roms/ports/classicube/`).

#### Scenario: Atualização com --keep-roms
- **WHEN** o cartão é gravado com `--keep-roms` a partir de um build com binário novo
- **THEN** a p1 não é regravada e o jogo continua abrindo com o binário que já estava nela, e o jogador atualiza copiando o binário novo pelo PC

#### Scenario: Gravação completa
- **WHEN** o cartão é gravado por completo a partir do build
- **THEN** a p1 traz `ports/classicube/ClassiCube` e o jogo abre sem o jogador copiar nada

#### Scenario: Boot sem regravar a FAT32
- **WHEN** o aparelho dá boot com o lançador, a capa e os ativos já presentes e iguais aos do SYSTEM
- **THEN** o `r36-classicube-sync.service` não grava nenhum arquivo na p1 e não mexe no binário

#### Scenario: Imagem não entrega binário no SYSTEM
- **WHEN** uma imagem é gerada com a feature `60-port-classicube`
- **THEN** o SYSTEM não contém `usr/share/classicube/ClassiCube` e a p1 contém `ports/classicube/ClassiCube`

#### Scenario: Binário do jogador na p1
- **WHEN** o jogador copia pelo PC um `ClassiCube` novo para `ports/classicube/` e liga o aparelho
- **THEN** o jogo abre com esse binário, sem regravar o SYSTEM

### Requirement: Lançador integrado aos Ports do EmulationStation
A imagem SHALL manter o lançador `ClassiCube.sh`, a entrada no `gamelist.xml` e as capas em `/storage/roms/ports_scripts/` (p1), com cópia mestre em `/usr/share/classicube/ports_scripts/` que o `r36-classicube-sync.service` restaura no boot quando falta ou difere, inclusive após `--keep-roms`. O serviço SHALL rodar antes do `emustation.service` e esperar até 20 s o `/storage/roms` ser montado, sem `After=emuelec-autostart.service`; se a montagem não vier, ele sai sem gravar e o ES abre normalmente. A imagem SHALL NOT criar `/usr/bin/ports`, para que o overlay do `mount_romfs.sh` continue falhando como na base e a pasta da p1 siga visível e editável pelo PC. O lançador SHALL executar só `/storage/roms/ports/classicube/ClassiCube`; se esse arquivo faltar ou o sistema o recusar (código de saída 126 ou 127), o lançador SHALL mostrar um aviso e encerrar, devolvendo o foco ao EmulationStation.

#### Scenario: Inicialização pelo menu
- **WHEN** o usuário seleciona o ClassiCube no menu de Ports do EmulationStation
- **THEN** o script define as variáveis de ambiente necessárias (`SDL_VIDEO_GL_DRIVER`, `SDL_VIDEO_EGL_DRIVER`, `SDL_GAMECONTROLLERCONFIG`), garante que os ativos offline existam em `/storage/roms/ports/classicube`, muda o diretório de trabalho para `/storage/roms/ports/classicube` e executa `/storage/roms/ports/classicube/ClassiCube` no modo local com `--singleplayer`, sem repassar argumentos externos do EmulationStation

#### Scenario: Binário ausente ou recusado
- **WHEN** o usuário abre o ClassiCube e `ports/classicube/ClassiCube` não existe, ou o sistema o recusa com código de saída 126 ou 127
- **THEN** o lançador mostra um aviso e volta ao EmulationStation, sem reabrir o jogo

#### Scenario: Saída normal do jogo não repete a execução
- **WHEN** o jogador sai do jogo pelo menu de pausa ou por `Select + Start`
- **THEN** o lançador encerra e volta ao EmulationStation, sem abrir o jogo uma segunda vez

#### Scenario: Exibição da capa na lista mesmo após atualização com --keep-roms
- **WHEN** o cartão é gravado por completo ou com `./flash.sh --keep-roms` e o aparelho termina o boot
- **THEN** `/storage/roms/ports_scripts/` contém `ClassiCube.sh`, as capas e uma entrada `<path>./ClassiCube.sh</path>` no `gamelist.xml`, e o menu "Ports" exibe "Classic Craft (ClassiCube)" com a capa

#### Scenario: Boot até o EmulationStation
- **WHEN** o aparelho liga com a feature `60-port-classicube` na imagem
- **THEN** o boot passa do splash e o EmulationStation abre, sem esperar pelo fim do `emuelec-autostart.service`

#### Scenario: Ports do usuário preservados
- **WHEN** o usuário copia pelo PC outro script `.sh` para `R36-ROMS/ports_scripts/` e o `gamelist.xml` dessa pasta já tem entradas de outros jogos
- **THEN** o script aparece no menu "Ports", e o serviço de boot acrescenta a entrada do ClassiCube só quando ela falta, sem apagar nem substituir as outras entradas, e sem duplicá-la em boots seguintes

#### Scenario: Retorno limpo ao EmulationStation
- **WHEN** o jogador seleciona "Quit game" no menu de pausa ou pressiona simultaneamente `Select + Start` no controle
- **THEN** o processo encerra sem travar o framebuffer e retorna o foco à interface do EmulationStation
