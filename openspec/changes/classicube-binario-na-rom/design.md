# Design

## Context

Motivação e escopo em `proposal.md`; requisitos em `specs/classicube-port/spec.md`. Estado atual, lido no repositório:

- **Lançador.** `ClassiCube.sh` (p1, `/storage/roms/ports_scripts/`) tem `BIN="$SHARE_DIR/ClassiCube"` com `SHARE_DIR=/usr/share/classicube` (SYSTEM) e termina com `"$BIN" --singleplayer; exit 0`. O ES o chama com `bash`, então o script não precisa de bit de execução. O `r36-classicube-sync.service` restaura o lançador na p1 a partir de `/usr/share/classicube/ports_scripts/` quando difere, então um lançador novo só chega ao aparelho com `./flash.sh --part system`.
- **Binário.** Só no SYSTEM. Cartões gravados antes da change que o moveu podem ter ainda um `ports/classicube/ClassiCube` na p1, que o lançador atual ignora. O teste `test_binary_architecture_and_abi` exige que a imagem não leve `roms/ports/classicube/ClassiCube`.
- **Execução a partir da FAT32.** Não medida. O Linux dá às FAT as permissões de `fmask`/`umask` da montagem e `noexec` bloqueia tudo; não há registro no projeto das opções reais de `/storage/roms` nem de `/tmp`. O `mount_romfs.sh` está no SYSTEM da base, não no repositório.
- **Testabilidade.** O lançador tem caminhos fixos; o `classicube-sync` já usa `R36_ROOT` para os testes apontarem para um diretório temporário. O teste `test_launcher_script` exige que o lançador contenha `BIN="$SHARE_DIR/ClassiCube"` e não contenha `/tmp/classicube` nem `"$@"`.
- **Restrições.** Sem sudo; Python via `uv run`; o aparelho só é acessível pelo cartão, então o diagnóstico vai para um arquivo na p1; o ES descarta o stderr do script.

## Goals / Non-Goals

**Goals:**
- Que o jogador troque o binário pelo PC, sem sudo e sem `flash.sh`, e o jogo abra com ele ou, na pior hipótese, com o do SYSTEM.
- Que o primeiro teste no aparelho responda se a FAT32 executa direto, lendo só o `log.txt`.
- Que um binário esquecido ou antigo na p1 nunca passe despercebido nem entre em uso por acidente.

**Non-Goals:**
- Verificar assinatura ou versão do binário da p1.
- Decidir agora se a execução direta ou a cópia para `/tmp` é a definitiva: o log dá a resposta para uma change futura.
- Capturar o stderr do jogo (erros do loader dinâmico) no log.

## Decisions

### 1. O binário opcional se chama `ClassiCube-pc`, não `ClassiCube`
O nome `ClassiCube` na p1 pode vir de gravações antigas (sem `--keep-roms` o arquivo some, com `--keep-roms` ele fica) e passaria a valer sem o jogador saber. Um nome novo só existe se o jogador o criar de propósito, e o próprio nome diz de onde ele vem.
- *Alternativa:* usar `ClassiCube`, como no pedido original. Rejeitada: reativaria binários velhos de cartões antigos e quebraria a promessa de que o `--keep-roms` não deixa binário velho valendo.
- *Alternativa:* uma pasta `bin/` ou um arquivo marcador. Rejeitada: mais uma regra para o jogador lembrar.

### 2. A feature não entrega nada novo na p1
O binário continua só no SYSTEM; o `ClassiCube-pc` é inteiramente do jogador. Isso resolve a pergunta "a imagem também entrega o binário na p1?": não, porque entregar criaria exatamente o cenário de binário velho na p1 depois de um `--keep-roms`. O `classicube-sync` não muda.

### 3. Ordem de tentativa por código de saída, dentro do próprio lançador
```
se existe ClassiCube-pc:
    rc=0; "$P1_BIN" --singleplayer || rc=$?          # tentativa 1: direto da p1
    se rc é 126 ou 127: copia para $TMP_DIR, chmod 0755, roda   # tentativa 2
    se rc é 126 ou 127 de novo: cai no SYSTEM          # tentativa 3
senão: SYSTEM
```
Só 126 (arquivo existe mas não executa: sem permissão, `noexec`, formato inválido) e 127 (interpretador ELF ausente) disparam a próxima tentativa. Qualquer outro código significa que o jogo rodou e saiu (inclusive crash), e o lançador não abre o jogo de novo. Isso evita testar `noexec` lendo `/proc/mounts`, que não cobre o caso de `fmask` sem bit x e duplicaria a lógica do kernel.
- *Alternativa:* sempre copiar para `/tmp`, sem tentar direto. Mais simples e robusta, mas o log nunca diria se a execução direta funciona, que é a pergunta aberta. Fica como evolução se o log mostrar que direto nunca funciona.
- *Alternativa:* testar `[ -x arquivo ]`. Rejeitada: numa montagem `noexec` ele diz que sim e a execução falha.

### 4. A cópia para a RAM usa `$TMP_DIR`, removida ao sair
`TMP_DIR="${R36_TMP:-/tmp}"`, cópia em `$TMP_DIR/ClassiCube-pc` (nunca `/tmp/classicube`, que o teste existente proíbe), `chmod 0755`, execução e `rm -f` depois. Cerca de 800 KiB de RAM e uma cópia por abertura, sem escrever na FAT32. Se a cópia ou o `chmod` falharem (por exemplo `/tmp` cheio), o lançador registra e vai ao SYSTEM.

### 5. `log.txt` reescrito inteiro a cada ponto de decisão
O lançador acumula as linhas numa variável e regrava o arquivo inteiro (`printf > log.txt`) antes de cada execução e depois de cada código de saída conhecido. Se o ES matar o jogo, o log já traz a tentativa que estava rodando. Conteúdo: caminho escolhido, código de saída de cada tentativa, `grep ' /storage/roms ' /proc/mounts`, `grep ' /tmp ' /proc/mounts` (ou "não é ponto de montagem") e o sha256 do SYSTEM e do `ClassiCube-pc`. O `sha256sum` é opcional: sem ele a linha diz "indisponível". Falha ao gravar o log (FAT cheia ou protegida) nunca derruba a abertura do jogo (`|| true`).
- *Alternativa:* append com rotação. Rejeitada: o arquivo cresceria na FAT32 e o spec pede só a última abertura.

### 6. Ganchos de teste no mesmo estilo do `classicube-sync`
`ROOT="${R36_ROOT:-}"` como prefixo de `PORT_DIR`, `SHARE_DIR` e `DB_FILE`, e `R36_TMP` para a RAM. No aparelho as duas variáveis ficam vazias e nada muda. Os testes montam um `R36_ROOT` temporário com "binários" que são scripts de shell (um que sai com 0, um que não tem permissão de execução, o do SYSTEM), o que cobre as quatro tentativas sem precisar de ARM. A parte de `/proc/mounts` lê o arquivo real; num `R36_ROOT` temporário o `grep` não casa e o log diz "não é ponto de montagem".

### 7. Um `ClassiCube-pc` diferente do SYSTEM não é rejeitado, só exposto
O lançador não compara versão nem data (a FAT32 do aparelho pode não ter relógio e o mtime não diz qual é o mais novo). O que protege o jogador é o log com os dois sha256 e o aviso no README.

## Risks / Trade-offs

- [Nem a execução direta nem a cópia para `/tmp` funcionam] → Cai no SYSTEM e o log mostra os dois códigos 126/127 e as linhas de montagem; o jogo abre mesmo assim.
- [O binário do jogador não é compatível (glibc nova demais)] → O loader sai com código 1, que não dispara a reserva (o lançador não distingue de crash). O log mostra `rc=1` nessa tentativa; a regra de ABI do `CLAUDE.md` (glibc ≤ 2.36) vale para o `ClassiCube-pc` também. Capturar o stderr fica fora do escopo.
- [`ClassiCube-pc` esquecido depois de uma imagem nova] → O jogo abre com o binário velho. Mitigado pelo log com os dois sha256 e pelo README, que manda apagar o `ClassiCube-pc` ao regravar o SYSTEM.
- [Mudar o `ClassiCube.sh` exige regravar o SYSTEM uma vez] → O sync só restaura o lançador a partir do SYSTEM, então o primeiro uso precisa de `--part system`. Depois disso o ciclo é só copiar pelo PC.
- [Regravar a FAT32 do `log.txt` a cada abertura] → Algumas centenas de bytes, uma ou três gravações por abertura; aceitável para o ganho de diagnóstico.
- [As duas changes mexem no `ClassiCube.sh`] → `corrige-classicube-controles` já está implementada no working tree (regra de sensibilidade); esta parte do estado atual do arquivo e mantém aquela regra intacta.

## Migration Plan

1. Implementar e gerar a imagem de teste (sem sudo, `--target-file`).
2. O usuário grava uma vez `./flash.sh --device /dev/sdX --part system` para levar o lançador novo.
3. Depois, para cada teste: copiar o binário compilado para `R36-ROMS/ports/classicube/ClassiCube-pc`, abrir o jogo e ler `log.txt` no PC.
4. Rollback: apagar o `ClassiCube-pc` da p1 (volta ao SYSTEM) ou reverter o commit e regravar o SYSTEM.

## Open Questions

- Depois do primeiro `log.txt` real, simplificar para "sempre copiar para `/tmp`" se a execução direta nunca funcionar, ou remover a cópia se a direta sempre funcionar. Não muda os specs atuais nem as tarefas; o resultado vai para o `CLAUDE.md` como fato do aparelho.
