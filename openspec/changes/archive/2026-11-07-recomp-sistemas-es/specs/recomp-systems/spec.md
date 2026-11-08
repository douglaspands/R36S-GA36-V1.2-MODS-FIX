# Spec Delta

## Purpose

Definir como jogos recompilados estaticamente (ROM convertida em executável nativo armhf, sem core nem RetroArch) aparecem em listas próprias do EmulationStation por console, como são executados e como o jogador sai deles com o FN.

## ADDED Requirements

### Requirement: Sistema de recomp por console
O EmulationStation SHALL listar cada console com recomp como um sistema próprio `<console>-recomp`, lendo a pasta `/storage/roms/<console>-recomp` e aceitando arquivos de extensão `.sh` (em minúsculas ou maiúsculas): o jogo é o script da raiz da pasta. Nesta mudança SHALL existir apenas o sistema `gba-recomp`. Um sistema `*-recomp` sem nenhum jogo SHALL NOT aparecer no menu.

#### Scenario: Jogo recompilado aparece na lista
- **WHEN** o jogador copia `Jogo.sh` e a pasta `Jogo/` (com o binário do jogo, o script de disparo e os saves) para `/storage/roms/gba-recomp/` pelo PC e liga o aparelho
- **THEN** a lista de sistemas mostra "GBA Recomp" e a lista do sistema mostra "Jogo", sem a extensão

#### Scenario: Sistema vazio fica escondido
- **WHEN** `/storage/roms/gba-recomp/` não tem nenhum arquivo `.sh`
- **THEN** o sistema não aparece na lista de sistemas

#### Scenario: Outros consoles ainda não existem
- **WHEN** o `es_systems.cfg` da imagem é inspecionado
- **THEN** não há sistema `snes-recomp`, `genesis-recomp` nem outro `*-recomp` além de `gba-recomp`

### Requirement: Formato do jogo recompilado
O jogo SHALL ser um script (`.sh`, começa com `#!`) que dispara um binário ELF armhf (ARMv7-A, hard-float) com bibliotecas só da imagem (glibc até 2.36, libstdc++ até GLIBCXX 3.4.29). O script decide como disparar o binário, que SHALL poder ter qualquer nome e extensão: o formato é decidido pela assinatura ELF, nunca pela extensão. O lançador SHALL executar o script com `bash` explícito (a p1 não tem bit de execução), sem core nem RetroArch, e SHALL aceitar também um ELF passado direto.

#### Scenario: Execução do script
- **WHEN** o jogador abre um jogo da lista `gba-recomp`
- **THEN** o lançador roda o `.sh` com `bash` na pasta dele, o ELF do jogo é executado pelo script, e nenhum processo `retroarch` é iniciado

#### Scenario: Arquivo que não é script nem ELF
- **WHEN** o jogador abre um arquivo que não começa com `#!` nem com a assinatura ELF
- **THEN** o lançador registra o erro no log, devolve o controle ao EmulationStation e não deixa o aparelho preso na tela de carga

### Requirement: Lançador único para todos os consoles
Todos os sistemas `*-recomp` SHALL usar o mesmo lançador, que recebe o caminho do jogo e o nome do sistema. Acrescentar um console novo SHALL exigir apenas declarar o sistema, a pasta e o tema, sem lançador novo.

#### Scenario: Comando do sistema
- **WHEN** o `es_systems.cfg` do sistema `gba-recomp` é inspecionado
- **THEN** o comando chama `/usr/bin/recomp.sh` com `%ROM%` e `%SYSTEM%`, sem `emuelecRunEmu.sh` e sem `--core`

#### Scenario: Nome do sistema chega ao lançador
- **WHEN** um jogo de `gba-recomp` é aberto
- **THEN** o log do lançador registra o sistema `gba-recomp` e o caminho do jogo

### Requirement: Saída do jogo por FN + Start
Durante um jogo recompilado, o pressionamento simultâneo de FN e Start SHALL encerrar o processo do jogo com `SIGTERM` e devolver o aparelho ao EmulationStation. O Select, sozinho ou combinado com outros botões, SHALL chegar ao jogo sem encerrá-lo. O FN sozinho SHALL NOT encerrar o jogo.

#### Scenario: FN e Start juntos
- **WHEN** o jogador segura o FN e aperta o Start durante um jogo recompilado
- **THEN** o processo do jogo termina e o EmulationStation reaparece

#### Scenario: Select livre
- **WHEN** o jogador aperta o Select durante o jogo
- **THEN** o jogo recebe o botão e nada é encerrado

#### Scenario: FN sozinho
- **WHEN** o jogador aperta só o FN durante o jogo
- **THEN** o jogo continua rodando

#### Scenario: Nome do processo de um jogo em script
- **WHEN** o jogo é um `.sh` e um arquivo com assinatura ELF (que não seja biblioteca `.so`, com qualquer nome ou extensão) fica na pasta do jogo (a pasta com o nome do `.sh`) ou ao lado do `.sh`
- **THEN** o `gptokeyb` é iniciado com o nome desse arquivo cortado em 15 caracteres (o `comm` do processo), e o log registra o nome usado

#### Scenario: Binário com extensão qualquer
- **WHEN** o recompilador gera o binário como `Jogo.bin`, `Jogo.gba.out` ou sem extensão, e o `.sh` o dispara
- **THEN** o jogo é achado pela assinatura e o FN + Start o encerra

#### Scenario: Script sem binário achado
- **WHEN** o jogo é um `.sh` e nenhum arquivo ELF é achado
- **THEN** o jogo roda, o `gptokeyb` não é iniciado e o log registra que o FN + Start não encerra o jogo

#### Scenario: ELF passado direto
- **WHEN** o lançador recebe um ELF
- **THEN** ele roda pelo symlink `/tmp/r36-recomp-game` e o `gptokeyb` usa esse nome

### Requirement: Retorno limpo ao EmulationStation
Ao fim do jogo, por saída normal, falha ou FN + Start, o lançador SHALL encerrar o `gptokeyb`, restaurar a rota analógica e o ganho de áudio do sistema, mostrar a tela neutra de saída e devolver o controle ao EmulationStation, sem deixar processo do jogo nem do `gptokeyb` vivo.

#### Scenario: Jogo que falha ao abrir
- **WHEN** o ELF termina com erro logo ao iniciar
- **THEN** o log registra o código de saída, o áudio volta ao estado do sistema e o EmulationStation reaparece

#### Scenario: Sem processos sobrando
- **WHEN** o EmulationStation reaparece depois de qualquer saída
- **THEN** não resta processo do jogo nem `gptokeyb` em execução

### Requirement: Áudio e idioma como no console LÖVE
O lançador SHALL ajustar a rota analógica (`Speaker Function` conforme `h2w/state`) e chamar `/usr/lib/r36/audio-ganho aplica` antes e depois do jogo, e SHALL exportar `CONSOLE_LANG`, `CONSOLE_LANG_SHORT`, `LANG` e `LANGUAGE` com o idioma do sistema (`emuelec.conf`, depois `es_settings.cfg`, padrão `en_US`).

#### Scenario: Som no alto-falante e no fone
- **WHEN** o jogo toca som com e sem fone ligado
- **THEN** o áudio sai pela rota correta no volume salvo do sistema

#### Scenario: Idioma do sistema
- **WHEN** o jogo lê `CONSOLE_LANG` com o sistema em `pt_BR`
- **THEN** o valor é `pt_BR`

### Requirement: Registro do lançador com rotação e chave de diagnóstico
O lançador SHALL manter `/storage/roms/<console>-recomp/recomp.log`, rotacionado em `recomp.log.1` ao passar de 100 KB, com o caminho do jogo, o sistema, o código de saída e o resultado do `ldd`. Registros extras de diagnóstico SHALL só ser gravados na p1 com o arquivo `r36-diagnostico` na raiz dela.

#### Scenario: Rotação do log
- **WHEN** `recomp.log` passa de 100 KB no início de uma execução
- **THEN** o arquivo vira `recomp.log.1` e um `recomp.log` novo é iniciado

#### Scenario: Biblioteca faltando
- **WHEN** o ELF depende de uma biblioteca que a imagem não tem
- **THEN** o `ldd` no log mostra a dependência como não encontrada, para o jogador diagnosticar pelo PC

### Requirement: FN reservado no EmulationStation e sem bind novo
Nenhum sistema `*-recomp` SHALL alterar o `es_input.cfg`: o FN continua sem função nas telas do EmulationStation e o Select continua servindo como antes. O perfil do `gptokeyb` do lançador SHALL vincular só os atalhos do sistema (`guide`/`hotkey`, `start`, `back`) e SHALL NOT injetar teclas de ação do teclado sobre os botões do jogo.

#### Scenario: es_input.cfg intacto
- **WHEN** o `es_input.cfg` da imagem gerada é inspecionado
- **THEN** o `micro_gamepad` continua sem entrada `id="10"`

#### Scenario: Botões de ação só chegam como joystick
- **WHEN** o jogador aperta A, B, X ou Y durante o jogo
- **THEN** o jogo recebe apenas o evento do botão do joystick, sem tecla de teclado simulada

### Requirement: Validação sem o recompilador
A imagem SHALL poder ser validada com um pacote de teste (`Teste.sh` e a pasta `Teste/` com um ELF armhf) colocado em `/storage/roms/gba-recomp/` pelo PC, sem nenhum recompilador, cobrindo o aparecimento na lista, a execução, o som e a saída por FN + Start.

#### Scenario: Pacote de teste
- **WHEN** o pacote de teste, cujo ELF abre a tela, toca um tom e espera um sinal, é copiado e `Teste` é aberto
- **THEN** ele roda, o som sai pelo alto-falante e FN + Start o encerra com `SIGTERM`
