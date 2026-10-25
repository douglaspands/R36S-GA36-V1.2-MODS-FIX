# Design

## Context

Motivação e escopo em `proposal.md`; requisitos em `specs/`. Estado atual, lido no repositório:

- **Ports.** O ES lê o sistema `ports` de `/storage/roms/ports_scripts` (pasta FAT32 da p1) e chama cada script com `/usr/bin/bash %ROM% ...`. Os dados de cada port ficam em `/storage/roms/ports/<nome>/`. O `CLAUDE.md` proíbe criar `/usr/bin/ports` (ativaria um overlay que esconde a p1) e documenta o padrão de serviço de boot `Before=emustation.service` que espera `/storage/roms` virar ponto de montagem.
- **ClassiCube hoje.** O binário mora no SYSTEM (`features/60-port-classicube/system/usr/share/classicube/ClassiCube`, gravado pelo `ports/classicube/compilar.sh`). `ClassiCube.sh` tem `BIN="$SHARE_DIR/ClassiCube"` com `SHARE_DIR=/usr/share/classicube` e termina com `"$BIN" --singleplayer; exit 0`, sob `set -euo pipefail`. O `r36-classicube-sync.service` restaura o lançador na p1 a partir de `/usr/share/classicube/ports_scripts/` quando difere, então um lançador novo só chega ao aparelho com `./flash.sh --part system`; ele não toca no binário. O teste `test_launcher_script` exige `BIN="$SHARE_DIR/ClassiCube"` e proíbe `/tmp/classicube` e `"$@"`; o `test_binary_architecture_and_abi` exige que a imagem não leve `roms/ports/classicube/ClassiCube` e confere o binário no SYSTEM.
- **Execução a partir da FAT32.** Não medida. O Linux dá às FAT as permissões de `fmask`/`umask` da montagem e `noexec` bloqueia tudo, inclusive `mmap` executável de `.so`. O `mount_romfs.sh` está no SYSTEM da base, não no repositório.
- **Testabilidade.** O `classicube-sync` usa `R36_ROOT` para os testes apontarem para um diretório temporário; o padrão se repete aqui.
- **Restrições.** Sem sudo; Python via `uv run`; o aparelho só é acessível pelo cartão, então o diagnóstico vai para um arquivo na p1; `/storage` (p8) é ext4 e executa.

## Goals / Non-Goals

**Goals:**
- Que qualquer port copiado pelo PC para `ports_scripts/` e `ports/` abra sem edição de script e sem o jogador dar permissão de execução.
- Que nenhum binário rode a partir da p1.
- Que o primeiro boot no aparelho responda, só pelo log, se a técnica funciona.
- Que o jogador troque o binário do ClassiCube pelo PC, sem `flash.sh`.
- Que um port novo, instalado amanhã, só precise ser copiado e o aparelho religado: sem build, sem gravar o SYSTEM, sem editar `gamelist.xml` (o ES lista os `.sh` de `ports_scripts/`).
- Que o ClassiCube seja um port como os outros: binário na p1, sem cópia no SYSTEM.

**Non-Goals:**
- Editar scripts de terceiros ou interceptar o comando do sistema `ports` no `es_systems.cfg`.
- Cobrir executáveis fora de `/storage/roms/ports/`.
- Ports que reescrevem o próprio binário ou bibliotecas em execução.
- Verificar assinatura ou versão de binário; capturar stderr do jogo.

## Decisions

### 1. `mount --bind` arquivo a arquivo, feito no boot
O serviço monta uma cópia executável da p8 por cima de cada ELF e `.so` da p1. O caminho não muda, então o script do port continua igual, e só os executáveis são escondidos; dados e saves seguem na p1.
- *Alternativa:* biblioteca no SYSTEM que o script chama (`r36_port_run`). Rejeitada: exige editar o script de cada port, contra o pedido de copiar e jogar.
- *Alternativa:* trocar o `<command>` do sistema `ports` por um wrapper. Rejeitada: o script ainda aponta para a p1, então o wrapper precisaria da mesma montagem, e mexer no `es_systems.cfg` obriga a editar as duas cópias e conflita com a feature `53-cores-a33`, dona do arquivo.
- *Alternativa:* overlay sobre `ports/`. Rejeitada: o `CLAUDE.md` já registra que overlay ali esconde a p1, e os saves iriam para a p8, invisíveis no PC.
- *Alternativa:* remontar a p1 com `exec`. Rejeitada: roda da p1, que o jogador não quer.

### 2. Cópias na p8 chamadas pelo sha256, em `/storage/.config/r36-ports-exec/`
O nome é o hash do conteúdo, então a cópia só é refeita quando o conteúdo muda, dois caminhos com o mesmo conteúdo dividem uma cópia, e um binário trocado pelo PC vira um arquivo novo sem invalidação por data (a FAT32 do aparelho pode não ter relógio). A cópia é gravada em arquivo temporário e renomeada, para uma queda de energia não deixar cópia truncada com nome válido. A cada boot o serviço apaga as cópias que nenhum arquivo da p1 usou.
- *Alternativa:* copiar para `/tmp` a cada boot. Rejeitada: gasta RAM e tempo de boot proporcionais ao tamanho dos ports; fica como plano de contingência (Open Questions).

### 3. Quais arquivos são tratados
`find /storage/roms/ports -maxdepth 4 -type f`, e de cada arquivo lê-se só os 4 primeiros bytes: o que for `\x7fELF` (executáveis e `.so`, que também precisam de `mmap` executável) entra. O limite de profundidade e a leitura de 4 bytes mantêm o custo baixo em pastas de ROMs grandes. Os logs e arquivos do próprio serviço (`r36-ports-exec.log`) não são ELF e ficam de fora naturalmente.

### 4. Montagem idempotente e tolerante a falha
Antes de montar, o serviço procura o caminho em `/proc/mounts`; se já está coberto, só registra. Cada passo (copiar, `chmod`, montar) é verificado por arquivo; falha vira linha `ERRO` no log e o laço segue. O serviço sempre sai com 0 para nunca atrasar o ES. A espera por `/storage/roms` repete o padrão do `classicube-sync` (até 20 s, sem `After=emuelec-autostart.service`).

### 5. `log.txt` do serviço na p1
`/storage/roms/ports/r36-ports-exec.log` é montado em memória e gravado de uma vez no fim (`|| true`), com uma linha por executável (`ok|ERRO caminho sha256 [mensagem]`) e as opções de montagem do diretório das cópias (`grep` em `/proc/mounts`). O `sha256sum` é obrigatório aqui (ele nomeia a cópia); sem ele o serviço registra e termina.

### 6. O ClassiCube executa só o binário da p1
O binário sai do SYSTEM (`git mv` para `features/60-port-classicube/roms/ports/classicube/ClassiCube`) e o `compilar.sh` passa a gravar nessa pasta. O lançador usa `BIN="$PORT_DIR/ClassiCube"` e roda:
```
[ -f "$BIN" ] || { aviso; exit 0; }
rc=0; "$BIN" --singleplayer || rc=$?
se rc é 126 ou 127: aviso (o serviço não montou a cópia)
```
Só 126 (existe mas não executa) e 127 (interpretador ELF ausente) viram aviso; qualquer outro código é jogo que rodou e saiu, inclusive crash, e o lançador não reabre o jogo. O aviso é uma linha no stdout e uma linha em `$PORT_DIR/log.txt` apontando para o `r36-ports-exec.log`; o lançador sempre sai com 0 para devolver o foco ao ES. `R36_ROOT` entra como prefixo de `PORT_DIR`, `SHARE_DIR` e `DB_FILE` para os testes, no estilo do `classicube-sync`. O teste `test_launcher_script` passa a exigir `BIN="$PORT_DIR/ClassiCube"`.
- *Alternativa:* manter o binário no SYSTEM como reserva. Rejeitada por pedido: o ClassiCube é um port normal, e a reserva escondia falha do serviço.

### 7. O binário da p1 sempre vale; `--keep-roms` não o atualiza
Não há versão nem data para comparar (a FAT32 do aparelho pode não ter relógio), e a regravação com `--keep-roms` não escreve na p1. Um cartão que já tinha o binário continua com ele até o jogador copiar outro pelo PC. É a mesma regra de qualquer port, e o log do serviço traz o sha256 do binário em uso para o jogador conferir. Isso reverte a decisão anterior de manter o binário no SYSTEM justamente para o `--keep-roms` trazê-lo.

### 8. Feature separada, `58-ports-exec`
O serviço vale para qualquer port, então não mora na `60-port-classicube`. Instalar um port novo continua sendo só copiar arquivos: o menu lê `ports_scripts/` direto da p1, e o serviço varre `ports/` inteiro a cada boot, sem lista de ports na imagem. A ordem 58 a coloca antes da feature do ClassiCube e depois dos cores/shaders (53/54), sem dependência entre elas.

### 9. Testes sem root
O script lê `R36_ROOT` (raiz das pastas) e `R36_MOUNT` (comando de montagem, padrão `mount`); os testes apontam `R36_MOUNT` para um script que registra os argumentos e simula erro para um caminho. Os "binários" de teste têm o cabeçalho `\x7fELF` seguido de lixo. Isso cobre seleção, cache, limpeza, idempotência, falha parcial e log sem precisar de ARM nem de bind real.

## Risks / Trade-offs

- [Bind-mount de arquivo no kernel 3.4.39 do fork não foi medido] → O log mostra `ERRO` por arquivo e o ClassiCube cai no SYSTEM; o primeiro boot real responde. Plano de contingência nas Open Questions.
- [`--keep-roms` não traz o binário novo da imagem para a p1] → README explica e manda copiar o binário compilado; o log mostra o sha256 em uso. Mesma regra de qualquer port.
- [Sem reserva no SYSTEM, falha do serviço deixa o ClassiCube sem abrir] → O lançador mostra o aviso e o log do serviço traz o erro por arquivo.
- [Cópias antigas na p8] → Limpeza a cada boot; o diretório fica pequeno (conteúdo único por sha256).
- [Port que cria ou troca executável com o aparelho ligado] → A montagem só reflete o boot; fora do escopo.
- [Mudar o `ClassiCube.sh`, criar o serviço e tirar o binário do SYSTEM exige regravar o SYSTEM uma vez] → O sync restaura o lançador a partir do SYSTEM, então o primeiro uso precisa de `--part system`, e a p1 precisa ter o binário (gravação completa ou cópia pelo PC). Depois o ciclo é só copiar pelo PC e religar.
- [Port com biblioteca fora de `ports/`] → Não coberto; o log não lista o que não é varrido.
- [As duas changes mexem no `ClassiCube.sh`] → `corrige-classicube-controles` já está na `main`; esta parte do estado atual do arquivo e mantém a regra de sensibilidade.

## Migration Plan

1. Implementar e gerar a imagem de teste (sem sudo, `--target-file`).
2. O usuário grava uma vez `./flash.sh --device /dev/sdX --part system` para levar o serviço e o lançador novo.
3. Cartão com `--keep-roms`: copiar o binário compilado para `R36-ROMS/ports/classicube/ClassiCube`. Gravação completa: o binário já vem na p1.
4. Depois, para cada teste ou port novo: copiar os arquivos pelo PC, ligar o aparelho, abrir o jogo e ler `ports/r36-ports-exec.log` no PC.
5. Rollback: reverter o commit e regravar o SYSTEM e a p1; sem reserva, o ClassiCube só abre se a p1 tiver um binário que execute.

## Open Questions

- Se o primeiro `r36-ports-exec.log` mostrar que o bind-mount de arquivo falha neste kernel, trocar a técnica por copiar o port para `/tmp` a cada abertura via wrapper no comando do sistema `ports`; isso viraria outra change.
- Registrar no `CLAUDE.md`, na seção "O aparelho", o fato medido (bind-mount de arquivo funciona ou não, opções de montagem de `/storage/roms` e da p8).
