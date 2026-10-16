# Tasks

## 1. Configuração, teste e documentação

- [x] 1.1 Em `features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf`, trocar `global.maxperf=1` por `global.maxperf=0` (linha 9) e ajustar o comentário da linha 8 para dizer que a imagem sai com a opção desligada e que dá para ligá-la por sistema ou jogo no menu do ES. Não adicionar nenhuma outra chave `*.maxperf`. Verificar com `grep -n maxperf` no arquivo: só a linha do comentário e `global.maxperf=0`.
- [x] 1.2 Em `tests/test_ptbr_controle.py` (`test_emuelec_conf`), afirmar `c["global.maxperf"] == "0"` e que nenhuma outra chave do arquivo termina em `.maxperf`. Verificar com `uv run python -I -m unittest tests.test_ptbr_controle`, primeiro vendo o teste falhar com o valor antigo e depois passar.
- [x] 1.3 No `README.md`, na feature `10-ptbr-sao-paulo`, trocar "três padrões" por "quatro" e acrescentar o item do máximo desempenho desligado (`global.maxperf=0`): menos calor, menos desempenho nos sistemas pesados (GBA, PSP, N64), como ligar por sistema ou jogo no ES, e que só imagem nova ou regravada recebe o padrão. Na feature `43-registro-termico`, trocar "o `maxperf` e o `normperf` agem como sempre" por texto que não afirme isso. Verificar relendo as duas seções e conferindo que os nomes de chave batem com a conf.
- [x] 1.4 Em `openspec/specs/thermal-control/spec.md`, nada a editar à mão: o delta desta change entra no arquivamento. Verificar com `openspec validate maxperf-desligado-por-padrao --strict`.

## 2. Integração (build e verificação no aparelho)

- [x] 2.1 Rodar `./build.sh` com todas as features e verificar que o `changes.txt` mostra a `emuelec.conf` alterada apenas pela feature 10, sem conflito com as outras features.
- [x] 2.2 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms`, verificar que termina com "verificado", e conferir `global.maxperf=0` na conf da p8 gravada. Rodar a suíte completa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`) e verificar que ela passa.
- [ ] 2.3 No aparelho com a imagem nova: jogar uns 5 minutos num sistema sem ajuste (GBA ou SNES), e ler o `r36-thermal.csv` do cartão. Verificar que `governor` fica `ondemand` e `dram_scene` fica `1` nas linhas com o jogo. Se continuarem `performance` e `0`, registrar o fato e abrir uma change para o `emuelecRunEmu.sh`, conforme o design.

## Workflow follow-up

- Arquivar a change depois da verificação no aparelho (2.3).
