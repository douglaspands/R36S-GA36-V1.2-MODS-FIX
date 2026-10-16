# Tasks

## 1. Preparação

- [x] 1.1 Definir a base da branch com o usuário (a opção `--test` do build ainda está em `build-flag-test`), criar a branch da change e verificar com `git branch --show-current` e `./build.sh --help`, que deve listar `--test`
- [ ] 1.2 Antes de editar, conferir no aparelho `scaling_available_governors`, `ondemand/sampling_rate` e os tunables atuais, e registrar o resultado em um comentário do script; verificar que o caminho dos tunables (global ou por `policy*`) está anotado

## 2. CPS2 com fbalpha2012

- [x] 2.1 Adicionar `cps2.emulator=libretro` e `cps2.core=fbalpha2012` ao `emuelec.conf` da feature `10-ptbr-sao-paulo`, e verificar que não existe `cps1.core`, `cps3.core` nem `fbn.core` nesse arquivo
- [x] 2.2 Cobrir o requisito do CPS2 em `tests/test_ptbr_controle.py`, no mesmo estilo do teste de `gba.core`, e verificar com `uv run pytest tests/test_ptbr_controle.py`
- [x] 2.3 Documentar o CPS2 no `README.md`, junto da nota do gpSP, e verificar que o texto cita o `fbalpha2012` e a escolha de outro core pelo menu

## 3. Ondemand afinado

- [x] 3.1 Criar a feature `features/44-cpu-ondemand` com `feature.toml` (ordem 44, `enabled = true`) e verificar que `uv run pytest tests/test_features.py` continua passando
- [x] 3.2 Escrever `system/usr/lib/r36/cpu-ondemand-tune`: só age com governor `ondemand`, aplica `up_threshold` 30, `sampling_down_factor` 10 e `scaling_min_freq` 600000, cobre o tunable global e os `policy*`, e ignora o que não existe; verificar com um teste em `tests/` que roda o script contra uma árvore sysfs falsa, nos casos governor `ondemand`, governor `performance` e arquivo ausente
- [x] 3.3 Substituir `/usr/bin/cpufreq` na feature mantendo o `up_threshold=50` original e chamando o script de afinamento em seguida; verificar no teste que o script é chamado só quando o governor é `ondemand`
- [x] 3.4 Chamar o script de afinamento no `emuelecRunEmu.sh` logo após cada `normperf` (abertura e saída do jogo), protegido por `[ -x ]`; verificar com teste que o script é chamado nos dois pontos e que a ausência dele não quebra a abertura do jogo
- [x] 3.5 Testar o requisito de máximo desempenho não afetado: o teste verifica que `maxperf` continua escrevendo `performance` e cena `0`, e que o afinamento não escreve nesses caminhos
- [x] 3.6 Documentar a feature `44-cpu-ondemand` no `README.md`, com os valores, como desligar (`enabled = false`) e como conferir no log; verificar que o texto cita `up_threshold`, `sampling_down_factor` e o piso de 600 MHz

## 4. Imagem de teste

- [x] 4.1 Rodar a suíte inteira com `uv run pytest` e verificar que tudo passa
- [x] 4.2 Gerar a imagem com `./build.sh --test` e verificar que o diretório e a imagem terminam em `-test`, que `R36-BUILD.txt` traz `teste: sim` e as features incluem `44-cpu-ondemand`
- [x] 4.3 Conferir no SYSTEM da imagem gerada, sem sudo, que `usr/bin/cpufreq` e `usr/lib/r36/cpu-ondemand-tune` existem com modo `0755`, e na p8 que `cps2.core=fbalpha2012` está no `emuelec.conf`
- [ ] 4.4 No aparelho, rodar um jogo de CPS2, PSX e SNES em modo normal e comparar com o log de 13/05: verificar `cpu_mhz` sem valores abaixo de 600 em jogo, `%<1000MHz` e desvio de clock menores, `core` `fbalpha2012` no CPS2 e som sem picotar; abrir e fechar um jogo com o máximo desempenho ligado e verificar que o menu volta a `ondemand` com os mesmos valores

## Workflow follow-up

- Se o resultado do 4.4 não bastar, avaliar manter a cena da DRAM em `0` também no modo normal, em change à parte.
- Arquivar a change depois da validação no aparelho.
