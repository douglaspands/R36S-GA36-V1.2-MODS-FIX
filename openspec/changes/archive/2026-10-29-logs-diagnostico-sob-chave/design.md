# Design

## Context

Motivação e escopo: veja `proposal.md`. Estado atual dos quatro logs, todos na raiz da p1:

| Log | Script | Como grava hoje |
|---|---|---|
| `r36-audio.log` | `46-audio/.../audio-prepara` | acumula num `TMPLOG` e faz `cat "$TMPLOG" > "$LOG"` no fim |
| `r36-audio-dac.log` | `46-audio/.../audio-amostra` | laço de 10 min; cria o arquivo na primeira mudança de estado |
| `r36-bateria.log` | `48-bateria-percentual/.../bateria-percentual` | `registra()` escreve em `$RUN/log` e `grava_p1` copia para a p1 depois que ela monta |
| `r36-shader-gba.log` | `54-shaders-gba/.../shader-gba-prepara` | `registro()` acrescenta em `$LOG` quando `MONTADA` |

Fatos que moldam a solução:

- Os scripts rodam cedo no boot e a p1 monta dentro do `emuelec-autostart`. Os três serviços que já leem chaves da p1 (`r36-audio-original`, `r36-bateria-original`, `r36-gba-sem-shader`) esperam a montagem em vez de ordenar o unit depois do autostart, que travaria o boot (veja o CLAUDE.md). A chave nova segue o mesmo padrão.
- O `audio-prepara` mistura diagnóstico com trabalho útil: o `amixer cset name='Speaker Function'` fica entre as leituras de antes e depois, e o `audio-ganho aplica` vem logo em seguida. A chave não pode pular esses comandos.
- Os testes rodam os scripts com `R36_ROOT` apontando para um diretório temporário e conferem o conteúdo dos logs.

## Goals / Non-Goals

**Goals:**
- Sem `r36-diagnostico` na p1, nenhum dos quatro logs é criado nem tocado, e as leituras que só servem ao log não rodam.
- Com a chave, o conteúdo dos logs é o de hoje.
- Uma checagem única, com o mesmo nome de arquivo e o mesmo critério de "p1 montada", nas três features.

**Non-Goals:**
- Não apagar logs que já estão na p1.
- Não mexer no registro térmico.
- Não mudar o formato nem o conteúdo dos logs, nem o `logger`/journal da bateria.
- Não criar um comando ou serviço central de diagnóstico: são três `if` pequenos.

## Decisions

### 1. Uma chave só, `r36-diagnostico`, na raiz da p1

Um arquivo vazio, criado e apagado pelo PC sem root, como as demais chaves do projeto.

Alternativas: uma chave por feature (`r36-diagnostico-audio` e assim por diante) dá controle fino, mas quatro arquivos para lembrar. Uma variável em `emuelec.conf` exigiria root para editar a p8 e não é legível como arquivo na p1. Fica uma chave só; separar depois é barato.

### 2. A checagem acontece onde cada script já espera a p1

Cada script ganha `DIAG="$ROOT/storage/roms/r36-diagnostico"` (ou `$ROMS/...` na bateria) e a variável `LOGA`, preenchida só quando a p1 está montada e o arquivo existe.

- `audio-prepara`: na etapa 1, junto de `MONTADA` e do teste de `$OFF`. `registro()` e `secao()` viram no-ops sem `LOGA`; o `cat "$TMPLOG" > "$LOG"` final exige `LOGA`. As leituras caras (`amixer contents`, os dumps do `audio_reg*`, o teste do `devmem`, as leituras de antes e depois do `Speaker Function`) ficam dentro de `if [ -n "$LOGA" ]`. `troca_chave`, o `amixer cset name='Speaker Function'` e o `audio-ganho aplica` ficam fora do `if`.
- `audio-amostra`: dentro do `if montada`, antes da primeira leitura, `[ -e "$ROMS/r36-diagnostico" ] || exit 0`. Como o laço já espera a p1 montar, não há espera nova. Não se usa `ConditionPathExists` no unit: o serviço sobe antes de a p1 existir e a condição daria falso para sempre.
- `bateria-percentual`: em `pos_montagem`, quando a p1 monta, `LOGA=sim` se a chave existir; `grava_p1` passa a exigir `LOGA` além de `ROMS_OK`. O log em `$RUN/log` e o `logger` continuam, porque custam só RAM e dão o diagnóstico pelo journal.
- `shader-gba-prepara`: `registro()` e o `: > "$LOG"` passam a usar `LOGA` em vez de `MONTADA`. A chave `$OFF` (`r36-gba-sem-shader`) continua usando `MONTADA`. Os blocos de diagnóstico de framebuffer (`for fb in ...`) ficam dentro de `if [ -n "$LOGA" ]`.

Alternativa descartada: apontar `TMPLOG` para `/dev/null` sem a chave. É curto, mas o `trap 'rm -f "$TMPLOG"'` do `audio-prepara` apagaria `/dev/null` quando rodar como root.

### 3. Logs antigos ficam

Apagar a p1 a cada boot sem a chave seria uma escrita extra e o oposto do objetivo. O CLAUDE.md e o README dizem que o usuário apaga pelo PC.

### 4. Documentação como parte da entrega

O `CLAUDE.md` ganha uma frase na seção do aparelho: os logs de diagnóstico só existem com `r36-diagnostico` na p1, e uma sessão que pedir um log ao usuário deve lembrá-lo da chave. O README troca os trechos das linhas citadas por uma subseção "Diagnóstico" única, com os quatro logs.

## Risks / Trade-offs

- [Alguém pede um log e o usuário esquece a chave] → o `CLAUDE.md` manda lembrar da chave, e a spec `diagnostic-logs` a descreve.
- [O `if` do `audio-prepara` deixar um comando útil dentro do bloco de diagnóstico e quebrar o áudio sem a chave] → os testes rodam o script sem a chave e conferem `Speaker Function`, `retroarch.cfg` e `audio-ganho aplica`, os mesmos efeitos de antes.
- [A leitura da chave atrasar o boot] → ela é um `[ -e ]` depois de a p1 já montada; nenhuma espera nova.
- [A p1 monta tarde e a chave é tratada como ausente] → aceito. É o mesmo comportamento das outras três chaves, e a spec o declara.

## Migration Plan

1. Implementar as três features e os testes.
2. Gravar um build e, no aparelho, conferir sem a chave: nenhum log novo, som, bateria e shader como antes.
3. Criar `r36-diagnostico` na p1 e religar: os quatro logs aparecem.
4. Rollback: reverter a branch. Não há migração de dados.
