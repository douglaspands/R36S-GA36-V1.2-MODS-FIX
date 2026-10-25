# Proposal

## Why

Um port é um script em `ports_scripts/` mais uma pasta em `ports/`, e o jogador quer tratá-lo como uma ROM: copiar pelo PC e jogar. Hoje isso só funciona para o que não é executável. Um binário copiado para a p1 (`R36-ROMS`, FAT32) não leva permissão de execução, e a montagem pode ter `noexec`; o Linux inventa as permissões da FAT pelas opções de montagem (`fmask`/`umask`), e as opções reais de `/storage/roms` nunca foram medidas neste aparelho.

O caso concreto é o ClassiCube: o binário mora no SYSTEM, e trocá-lo exige gerar a imagem e regravar a p7 com `./flash.sh --part system` (sudo), o que atrapalha a calibração dos analógicos, que depende de várias rodadas de "mexer no valor, recompilar, testar no aparelho". Mas o problema é de qualquer port, e o jogador não quer que o binário rode da p1 nem que o script do port precise de edição.

## What Changes

- Um serviço de boot novo, `r36-ports-exec.service`, ordenado `Before=emustation.service` (sem `After=emuelec-autostart.service`, que trava o boot), espera `/storage/roms` virar ponto de montagem e então:
  1. procura em `/storage/roms/ports/` arquivos ELF e bibliotecas `.so`;
  2. copia cada um para a p8, em `/storage/.config/r36-ports-exec/<sha256>`, com `chmod 0755`, só quando a cópia daquele conteúdo ainda não existe, e apaga as cópias que nenhum arquivo da p1 usa mais;
  3. monta cada cópia por cima do arquivo da p1 com `mount --bind`.
- O script do port continua chamando o caminho da p1 (`/storage/roms/ports/foo/foo` ou `./foo`), mas o processo roda da cópia na p8. O PC continua vendo o arquivo original, e saves e dados são gravados direto na p1. Nenhum script de port precisa mudar.
- O serviço grava `/storage/roms/ports/r36-ports-exec.log` a cada boot, com o caminho, o sha256 e o resultado da montagem de cada executável, para o jogador ler no PC. Erro em um arquivo é registrado e não impede o boot nem os demais arquivos.
- Instalar outro port amanhã não exige build nem gravar o SYSTEM: o jogador copia o script para `ports_scripts/` e a pasta do port para `ports/`, liga o aparelho, e o port aparece no menu "Ports" (o ES lista os `.sh` da pasta) e executa. O único passo do aparelho é o boot, no qual o serviço prepara os executáveis.
- O binário do ClassiCube deixa de ser entregue no SYSTEM e passa a ser entregue na p1 como o de qualquer port, em `roms/ports/classicube/ClassiCube`. O `compilar.sh` grava nessa pasta, e o serviço o torna executável no boot como os demais.
- O `ClassiCube.sh` executa só `/storage/roms/ports/classicube/ClassiCube`. Não há reserva no SYSTEM: se o arquivo faltar ou o sistema o recusar (126 ou 127), o lançador mostra um aviso e volta ao EmulationStation. O requisito "Binário único na partição SYSTEM" é renomeado e reescrito, e isso reverte a decisão de ter movido o binário da p1 para o SYSTEM.
- Com `--keep-roms` a p1 não é regravada, então um binário novo da imagem não chega a um cartão que já tinha o binário antigo: o jogador atualiza copiando pelo PC, como em qualquer port. O binário da p1 é sempre o que vale.
- O README documenta o comportamento (copiar o port pelo PC e jogar), o log, a atualização do ClassiCube por cópia e a necessidade de `--part system` uma vez para levar o serviço.

Fora do escopo: editar scripts de port de terceiros; bibliotecas ou executáveis fora de `/storage/roms/ports/`; ports que reescrevem o próprio binário em execução; assinar ou validar versão de binário; capturar o stderr do jogo; criar `/usr/bin/ports` ou qualquer overlay (a regra do `roms-mount` continua valendo).

## Capabilities

### New Capabilities

- `ports-executables`: executáveis e bibliotecas de qualquer port em `ports/` rodam de uma cópia fora da p1, montada por cima do arquivo, com log de diagnóstico na p1.

### Modified Capabilities

- `classicube-port`: o requisito "Binário único na partição SYSTEM" é renomeado para "Binário do ClassiCube na p1 como port normal" (a imagem entrega o binário na p1, sem cópia no SYSTEM), e o requisito "Lançador integrado aos Ports do EmulationStation" passa a executar o binário da p1 e a avisar quando ele falta.

## Impact

- Feature nova `features/58-ports-exec/` (`feature.toml`, `system/usr/lib/r36/ports-exec`, `system/usr/lib/systemd/system/r36-ports-exec.service`).
- `features/60-port-classicube/system/usr/share/classicube/ClassiCube` sai do SYSTEM e vira `features/60-port-classicube/roms/ports/classicube/ClassiCube` (`git mv`).
- `ports/classicube/compilar.sh` (destino do binário).
- `features/60-port-classicube/roms/ports_scripts/ClassiCube.sh` e o espelho em `features/60-port-classicube/system/usr/share/classicube/ports_scripts/ClassiCube.sh`.
- `tests/test_ports_exec.py` (novo) e `tests/test_port_classicube.py` (caminho do binário na ABI e na estrutura, e a escolha no lançador).
- `README.md` (itens `58-ports-exec` e `60-port-classicube`).
- `openspec/specs/ports-executables/spec.md` e `openspec/specs/classicube-port/spec.md` (via deltas desta change).
- Sem mudança na ABI do binário, no `classicube-sync` (que nunca tocou no binário) nem no `es_systems.cfg`.
- Depende do estado do repositório após a change `corrige-classicube-controles` (lançador com a regra de sensibilidade); as duas editam o mesmo `ClassiCube.sh`.
