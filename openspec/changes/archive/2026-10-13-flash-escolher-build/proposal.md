# Proposal

## Why

A pasta `out/` acumula vários builds, e o `./flash.sh` grava o mais recente quando não recebe `--build`. Para gravar outro, o usuário precisa saber o timestamp exato de cabeça ou errar de propósito para ver a lista. Sem ver as features e o tamanho de cartão de cada build, é fácil gravar o build errado.

## What Changes

- Sem `--build`, num terminal interativo e com mais de um build em `out/`, o `./flash.sh` mostra um menu numerado com os builds. Cada linha traz timestamp, tamanho do cartão e features, lidos do `manifest.json`. O mais recente é o padrão, escolhido com Enter.
- Fora de um terminal interativo (testes, scripts, pipe), o comportamento atual continua: usa o build mais recente sem perguntar.
- Nova opção `--list-builds`, que só lista os builds com as mesmas informações e termina. Ela não exige `--device`, `--target-file`, `--all` nem `--part`.
- `--build <timestamp>` continua funcionando como hoje e pula o menu.
- O plano mostrado antes da confirmação passa a exibir também as features e o tamanho do cartão do build escolhido.

## Capabilities

### New Capabilities
(nenhuma)

### Modified Capabilities
- `sd-flashing`: o requisito "Modos de gravação" passa a prever a escolha interativa do build e a listagem de builds.

## Impact

- `tools/r36img/flash.py`: argumentos (`--list-builds` e validação condicional), escolha do build e exibição do plano.
- `tests/test_flash.py`: casos do menu (entrada simulada), do modo não interativo e do `--list-builds`.
- README: seção "Gravar o cartão".
- Nenhuma mudança no build, nas features ou na imagem.
