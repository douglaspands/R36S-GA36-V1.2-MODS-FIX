# Tasks

## 1. Serviço que prepara os executáveis dos ports

- [x] 1.1 Criar a branch `ports-executaveis-como-roms` a partir da `main` (regra do projeto) e conferir com `git branch --show-current`.
- [x] 1.2 Criar a feature `features/58-ports-exec/` com `feature.toml` (ordem 58) e `system/usr/lib/r36/ports-exec` (modo `0755`) com os ganchos `R36_ROOT` e `R36_MOUNT`, a espera de até 20 s por `/storage/roms` (design, decisões 4 e 9) e a varredura de `ports/` por ELF (decisão 3). Cobrir em `tests/test_ports_exec.py`, com um `R36_ROOT` temporário e um `R36_MOUNT` falso: só os arquivos com cabeçalho `\x7fELF` são tratados; dados e textos são ignorados. Verificar que os testes passam.
- [x] 1.3 Implementar as cópias por sha256 em `/storage/.config/r36-ports-exec/` com `chmod 0755`, gravação em temporário e `mv`, compartilhamento de conteúdo igual e limpeza das cópias não usadas (decisão 2). Cobrir: binário novo vira cópia, boot repetido não copia de novo, binário trocado cria cópia nova e apaga a antiga, port removido apaga as cópias, dois caminhos de mesmo conteúdo dividem uma cópia. Verificar que os testes passam.
- [x] 1.4 Implementar a montagem idempotente e a tolerância a falha, com saída sempre 0 (decisão 4). Cobrir: caminho já presente em `/proc/mounts` não é montado de novo, erro em um arquivo não impede os outros, `/storage/roms` ausente termina sem montar. Verificar que os testes passam.
- [x] 1.5 Implementar `ports/r36-ports-exec.log` (decisão 5): uma linha por executável com resultado e sha256, opções de montagem do diretório das cópias, conteúdo substituído a cada boot, falha de escrita ignorada. Cobrir: log com sha256 e `ok`, linha `ERRO` com a mensagem, só o registro do último boot, serviço termina com 0 com `ports/` somente leitura. Verificar que os testes passam.
- [x] 1.6 Criar `system/usr/lib/systemd/system/r36-ports-exec.service` (oneshot, `Before=emustation.service`, sem `After=emuelec-autostart.service`, `TimeoutStartSec=60`, `WantedBy=emuelec.target`), no padrão do `r36-classicube-sync.service`. Habilitar o serviço com o symlink `system/usr/lib/systemd/system/emuelec.target.wants/r36-ports-exec.service` -> `../r36-ports-exec.service`, como o do `classicube-sync`. Cobrir em teste que a unit existe, é ordenada antes do ES, não depende do autostart e tem o symlink. Verificar que os testes passam e que `shellcheck`/`bash -n`/`sh -n` aceitam o script quando disponíveis.

## 2. ClassiCube vira um port normal

- [x] 2.1 Mover o binário com `git mv features/60-port-classicube/system/usr/share/classicube/ClassiCube features/60-port-classicube/roms/ports/classicube/ClassiCube`, trocar `dest_system` por `dest_roms="$root/features/60-port-classicube/roms/ports/classicube"` no `ports/classicube/compilar.sh` e ajustar `tests/test_port_classicube.py` (`test_binary_architecture_and_abi` e a estrutura): o binário passa a ser conferido na p1, o SYSTEM não pode levar `usr/share/classicube/ClassiCube`. Verificar `bash -n` no `compilar.sh` e que os testes passam.
- [x] 2.2 No `ClassiCube.sh`, introduzir o gancho `R36_ROOT` (prefixo de `PORT_DIR`, `SHARE_DIR` e `DB_FILE`) sem mudar o comportamento, ajustar `test_launcher_script` para `BIN="$PORT_DIR/ClassiCube"` e verificar com `bash -n` e `uv run python -I -m unittest discover -s tests -p "test_port_classicube.py"` que os testes existentes (incluindo os de sensibilidade) continuam passando.
- [x] 2.3 Implementar a execução (design, decisão 6): `BIN="$PORT_DIR/ClassiCube"`; binário ausente ou código 126/127 mostram o aviso e saem com 0; qualquer outro código termina sem reabrir o jogo. Cobrir em `tests/test_port_classicube.py` com um `R36_ROOT` temporário e binários em shell: binário executável na p1 roda; binário ausente avisa e sai com 0; binário sem permissão de execução avisa; binário que sai com código 3 não dispara segunda abertura. Verificar que os testes passam.
- [x] 2.4 Copiar o `ClassiCube.sh` para `features/60-port-classicube/system/usr/share/classicube/ports_scripts/ClassiCube.sh`, verificar `bash -n` e `cmp` entre as duas cópias (coberto por `test_system_ports_mirror_and_sync`).
- [x] 2.5 Garantir em `tests/test_ports_exec.py` que o serviço trata o binário entregue pela imagem como o de qualquer port (cenário "Binário entregue pela imagem") e que um port novo qualquer, só com script em `ports_scripts/` e executável em `ports/<nome>/`, é preparado sem nenhuma lista ou configuração na imagem. Verificar que os testes passam.

## 3. Documentação

- [x] 3.1 Atualizar o `README.md`: item novo `58-ports-exec` (copiar o port pelo PC e jogar, o log, a limitação de varrer só `ports/`) e o item `60-port-classicube` (binário na p1 como port normal, atualização por cópia pelo PC porque `--keep-roms` não regrava a p1, `--part system` uma vez, e como instalar outro port só copiando arquivos). Verificar que o texto bate com os specs desta change.

## 4. Fechamento

- [x] 4.1 Rodar `uv run python -I -m unittest discover -s tests` completo e verificar que não há falhas novas.
- [x] 4.2 Rodar `openspec validate ports-executaveis-como-roms --strict` e verificar que passa.
- [x] 4.3 Gerar o cartão de teste com `./build.sh --test --offline` (sem sudo), gravá-lo num arquivo temporário com `./flash.sh --target-file` e verificar, extraindo da `system.img` (`mcopy` e `unsquashfs`) e da `roms.img` (`mdir`), que o SYSTEM leva o serviço, o script e o lançador novo igual ao da p1, que o symlink de habilitação do serviço está presente, que a p1 leva `ports/classicube/ClassiCube` (ELF ARM) e que o SYSTEM não leva `usr/share/classicube/ClassiCube`.

## Workflow follow-up

- O usuário grava o SYSTEM (`./flash.sh --device /dev/sdX --part system`), (em cartão com `--keep-roms`) copia o binário para `R36-ROMS/ports/classicube/ClassiCube`, liga o aparelho, abre o jogo e lê `R36-ROMS/ports/r36-ports-exec.log` no PC.
- Registrar no `CLAUDE.md`, na seção "O aparelho", o fato medido do bind-mount de arquivo no kernel 3.4.39 e das opções de montagem de `/storage/roms`, e resolver a contingência da Open Question do design.
- Arquivar a change depois de revisada.
