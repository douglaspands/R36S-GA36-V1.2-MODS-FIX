# Design

## Context

O build gera `out/<ts>/` e a imagem `<prefixo>_build_<ts>.img.xz` (`build.py`). O `flash.sh` descobre builds em `out/` com `TS_RE = ^\d{8}-\d{6}$` (`flash.py`), valida `--build` com a mesma regex e escolhe o mais recente pelo maior nome. Só o `flash.py` lê o nome do diretório; o manifest e o `R36-BUILD.txt` repetem o timestamp puro. Por isso um diretório `<ts>-test` seria ignorado pelo `flash.sh` hoje, e o marcador precisa ser ensinado aos dois lados. Motivação e escopo estão em `proposal.md`; os requisitos estão em `specs/`.

## Goals / Non-Goals

**Goals:**
- Distinguir builds de teste olhando `out/`, o `--list-builds` ou o `R36-BUILD.txt` no cartão.
- Não alterar o conteúdo da imagem: `--test` muda só os nomes e os registros.

**Non-Goals:**
- Qualquer comportamento diferente do `flash.sh` para builds de teste (sem proteção, sem filtro, sem confirmação extra).
- Rótulos livres, variantes de configuração ou mudanças no registro térmico.

## Decisions

1. **Sufixo `-test` no nome, timestamp puro nos registros.** O nome do diretório e da imagem usam um identificador `dirname = ts + "-test"` (ou só `ts`). O campo `timestamp` do manifest, o `volume_id` do FAT (derivado do `ts`) e o `ts` do log continuam puros. Alternativa descartada: pôr `-test` no próprio timestamp. Isso quebraria o `int(ts.replace("-", ""))` do volume id e a regra de que o timestamp é sempre `AAAAMMDD-HHMMSS`.
2. **Sufixo em inglês e fixo (`-test`).** Foi o pedido do usuário. Sem rótulo livre: uma única palavra reconhecível basta para o objetivo (saber que é intermediário).
3. **Marcador também dentro dos registros.** `manifest.json` ganha `"test": true` e o `R36-BUILD.txt` ganha `teste: sim`, só em builds de teste. O motivo é o marcador sobreviver a uma pasta renomeada e aparecer no aparelho (`/flash/R36-BUILD.txt`). Em builds normais o manifest e o `R36-BUILD.txt` ficam byte a byte como hoje (campo e linha ausentes, não `false`).
4. **`flash.py` aceita o sufixo.** `TS_RE` passa a `^\d{8}-\d{6}(-test)?$`. O sufixo mantém a ordenação por nome (`<ts>` ordena antes de `<ts>-test`), então "o mais recente" continua sendo o maior nome. A mensagem de erro de `--build` cita o formato com `-test` opcional.
5. **A linha do build mostra o marcador a partir do manifest.** `build_line` acrescenta `test` quando `manifest.get("test")` é verdadeiro. Se o manifest não puder ser lido, a linha continua como "manifest ilegível" (comportamento atual).
6. **Diretório de trabalho com o mesmo identificador do diretório de saída.** `work/<dirname>` em vez de `work/<ts>`, para dois builds no mesmo segundo (um normal e um de teste) não disputarem o mesmo diretório temporário.

## Risks / Trade-offs

- [Um `flash.sh` sem `--build` pode gravar um build de teste como "o mais recente"] → Aceito: o usuário pediu explicitamente que não haja tratamento especial. O marcador aparece no plano antes da confirmação, e a confirmação continua exigindo digitar o dispositivo.
- [Código externo que assuma `^\d{8}-\d{6}$` para nomes em `out/`] → Só `flash.py` e os testes usam a regex; os testes de nome (`tests/test_image.py`) passam a cobrir o sufixo opcional.
- [`README.md` e `--help` ficarem desatualizados] → Entram nas tarefas.

## Migration Plan

Não há migração: builds antigos em `out/` continuam válidos e sem marcador. Rollback é reverter a branch.
