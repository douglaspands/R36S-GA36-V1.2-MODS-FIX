# Tasks

## 1. Informações e listagem de builds

- [x] 1.1 Em `tools/r36img/flash.py`, criar a formatação da linha de um build a partir do manifest (timestamp, `card_size_mib` em MiB, ids das features ou "sem features", "manifest ilegível" quando o JSON não abre). Verificar com testes em `tests/test_flash.py` para build com features, sem features e com manifest corrompido.
- [x] 1.2 Adicionar `--list-builds`: dispensa `--device`/`--target-file` e `--all`/`--part`, lista do mais recente para o mais antigo e sai com 0; com `out/` vazio, informa e sugere `./build.sh`. Verificar com testes de `parse_args`/`flash` usando um `out/` temporário, e com `./flash.sh --list-builds` no repositório (sem sudo).

## 2. Menu interativo

- [x] 2.1 Implementar a escolha: sem `--build`, com `interactive` verdadeiro (padrão `sys.stdin.isatty()`) e 2 ou mais builds, mostrar o menu numerado (1 = mais recente), aceitar Enter (padrão 1), repetir em resposta inválida e cancelar em EOF sem escrever. A escolha acontece antes de `deps.check_flash()` e `inspect_device()`. Verificar com testes que simulam `input_fn` para: escolha `2`, Enter, `9` seguido de `1`, EOF, um só build (sem menu) e `--build` explícito (sem menu).
- [x] 2.2 Garantir que, com `interactive` falso, o comportamento continua o de hoje (mais recente, sem perguntar). Verificar que a suíte rápida existente passa sem alteração nos testes antigos: `uv run python -I -m unittest discover -s tests`.
- [x] 2.3 Incluir no plano mostrado antes da confirmação (`show_plan`) a linha do build (features e tamanho do cartão). Verificar com um teste que captura a saída de `--dry-run` com `--target-file`.

## 3. Documentação

- [x] 3.1 Atualizar o README ("Gravar o cartão"): menu de escolha, `--list-builds` e o `--build` continuando a valer, e o texto de ajuda/epílogo do `./flash.sh`. Verificar que os comandos citados aparecem em `./flash.sh --help` e que `./flash.sh --list-builds` roda como documentado.

## 4. Integração

- [x] 4.1 Com os dois builds existentes em `out/`, rodar num terminal `./flash.sh --target-file work/cartao-teste.img --all --keep-roms --keep-storage --dry-run`, escolher o build mais antigo no menu e verificar que o plano mostra esse timestamp e as features dele.
- [x] 4.2 Rodar a suíte completa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`) e verificar que ela passa.

## Workflow follow-up

- Fazer commit na branch `feat/flash-escolher-build` quando o usuário pedir e arquivar o change com `/opsx:archive`.
