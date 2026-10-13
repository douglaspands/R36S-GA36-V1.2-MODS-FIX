# Design

## Context

- `tools/r36img/flash.py` já tem `available_builds()` (lista os diretórios `out/AAAAMMDD-HHMMSS` com `manifest.json`) e `resolve_build()` (escolhe pelo timestamp ou pega o último).
- `flash(args, *, out_root, input_fn, lsblk)` já recebe `input_fn` para simular a digitação do nome do dispositivo nos testes. O menu pode usar o mesmo mecanismo.
- O `manifest.json` de cada build traz `timestamp`, `card_size_mib` e `features` (lista com `id`, `name` e `order`).
- `parse_args()` exige `--device`/`--target-file` e `--all`/`--part`. `--list-builds` precisa ser exceção a essas regras.

## Goals / Non-Goals

**Goals:**
- Escolher o build sem decorar timestamps, sem mudar nada para quem já usa `--build`.
- Testes e scripts continuam sem interação (o padrão segue sendo o mais recente).

**Non-Goals:**
- Apagar builds antigos de `out/`.
- Comparar builds entre si ou mostrar o `changes.txt` no menu.

## Decisions

1. **O menu só aparece com `sys.stdin.isatty()` verdadeiro, sem `--build` e com 2 ou mais builds.** Fora de um TTY, o resultado continua o de hoje, e os testes atuais seguem válidos. Nos testes, a detecção de TTY é injetada por parâmetro (`interactive=`), igual ao `input_fn`. Alternativa descartada: uma opção `--choose` explícita. O pedido do usuário é que a escolha seja o caminho natural.

2. **A escolha acontece antes de qualquer acesso ao cartão.** O menu roda logo depois de `resolve_build` e antes de `deps.check_flash()` e `inspect_device()`, para o usuário não esperar o sudo nem a leitura do cartão antes de decidir. O plano mostrado depois (`show_plan`) passa a incluir as features e o tamanho do cartão, para conferência antes de digitar o nome do dispositivo.

3. **Uma função só formata a linha de um build.** O mesmo texto (`timestamp  NNNNN MiB  feature-a, feature-b` ou `sem features`) é usado no menu, no `--list-builds` e no plano. Um manifest ilegível não derruba a listagem: a linha mostra `manifest ilegível`, e o build não pode ser escolhido.

4. **Ordem do mais recente para o mais antigo, com o número 1 no mais recente.** Assim o padrão (Enter) é sempre a opção 1.

5. **`--list-builds` dispensa as validações de alvo e modo.** Em `validate_args`, com `--list-builds`, as outras opções são ignoradas e o script lista e sai com código 0. Combinar com `--device` não é erro, mas nada é gravado.

## Risks / Trade-offs

- [O usuário escolhe um build gerado para outro tamanho de cartão] → O tamanho aparece no menu e no plano, e a verificação de capacidade existente continua recusando cartão menor que a imagem.
- [`input()` recebe EOF (Ctrl+D)] → Tratado como cancelamento: o script sai sem escrever, com código 1.
