# Tasks

## 1. Feature e serviço de boot (etapa 1)

- [x] 1.1 Criar a branch `audio-menos-chiado` a partir da `main` e a feature `features/46-audio/feature.toml` (schema 1, order 46, enabled). Verificar com `./build.sh --list` (ou o comando de listagem do projeto), que deve mostrar a feature.
- [x] 1.2 Criar `system/usr/lib/r36/audio-prepara` com:
  - o `R36_ROOT` dos testes;
  - a espera da p1 por até 20 s;
  - a decisão do modo (`r36-audio-original`) gravada em `/run/r36-audio.modo`;
  - a troca exata das linhas `audio_latency`/`audio_resampler_quality` do `retroarch.cfg` da p8 nos dois sentidos (Decisão 7).

  Verificar com testes em `tests/test_audio.py`:
  - valores de fábrica viram 96/1;
  - valor do usuário (128) fica como está;
  - modo original volta 96/1 para 64/2;
  - `video_threaded` e as demais linhas ficam idênticas;
  - sem p1 o script termina com código 0.
- [x] 1.3 Acrescentar ao `audio-prepara` o diagnóstico (Decisão 2, etapa 1). O log `r36-audio.log` na p1, escrito de uma vez no fim, deve trazer:
  - `amixer contents`;
  - o caminho encontrado da `audio_reg_debug` (busca em `/sys`) e o seu conteúdo;
  - o dump antes e depois de reaplicar o `Speaker Function` conforme o `h2w/state`, com o `speaker volume control` e o `headphone volume control` antes e depois;
  - se o `busybox` tem `devmem`;
  - o modo e as chaves do RetroArch aplicadas.

  Nenhuma escrita em registrador. Verificar com um teste que usa `amixer`, `busybox` e `mountpoint` simulados no `PATH` e uma árvore `/sys` falsa: o log tem todas as seções, e a ausência da interface aparece no log sem erro.
- [x] 1.4 Criar `system/usr/lib/systemd/system/r36-audio.service` (oneshot, `Before=emustation.service`, `After=sound.target`, sem `After=emuelec-autostart.service`, `TimeoutStartSec=60`, `WantedBy=emuelec.target`). Verificar com um teste que lê a unit e recusa `After=emuelec-autostart.service`, e confirmar que o build a habilita como as outras units das features 43 e 54.

## 2. Ponto único de ganho e substituição dos scripts da base (etapa 1)

- [x] 2.1 Criar `system/usr/lib/r36/audio-ganho` com os subcomandos `aplica` e `volume <v>`:
  - escala de fábrica `(v*43+50)/100 + 20`;
  - modo `original` quando `/run/r36-audio.modo` falta;
  - (a escala corrigida, as constantes `REG_IFACE`/`DAC_REG`/`DESLOC` e a ordem analógico → DAC foram feitas aqui e removidas na task 5.1, depois que o log mostrou o DAC em 0 dB).

  Verificar com testes (com `amixer` simulado que grava as chamadas):
  - a escala de fábrica bate com a fórmula da base para 0, 3, 29 e 100;
  - `volume` limita a 0..100 e grava `audio.volume`.
- [x] 2.2 Definir o mudo de `audio.volume` = 0 a partir do log (Open Question 1), ou deixar pronto com `speaker volume control` = 0 e confirmar na task 4.2. Verificar com um teste: `volume 0` produz o comando de mudo, e `volume 3` depois dele devolve o ganho e religa a saída.
- [x] 2.3 Copiar `usr/bin/udt_events.sh` e `usr/bin/udt_pwr_events.sh` do SYSTEM da base (`mcopy` + `unsquashfs -cat`) para `features/46-audio/system/usr/bin/`, trocando:
  - no `udt_events.sh`, a escala e o `amixer` por `/usr/lib/r36/audio-ganho volume`;
  - no `udt_pwr_events.sh`, acrescentar `audio-ganho aplica` depois do `Speaker Function` do retorno.

  As duas chamadas ficam protegidas por `[ -x ]`. Verificar com um teste que extrai os originais da imagem base e aceita só essas diferenças (Decisão 9), e conferir que os modos 0755 herdados da base aparecem no manifest do build.
- [x] 2.4 No `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`, chamar `audio-ganho aplica` (protegido por `[ -x ]`) depois do bloco de `Speaker Function` da abertura e do da saída do jogo. O `audio-prepara` também chama `aplica` no fim. Verificar com um teste que acha as duas chamadas logo após cada `case "$current_state"`, e confirmar que `tests/test_ptbr_controle.py` continua passando.

## 3. Documentação e build da etapa 1

- [x] 3.1 Documentar a feature 46 no `README.md`:
  - o que muda;
  - o `r36-audio.log`;
  - a chave `r36-audio-original`;
  - que tudo vale com `--part system`;
  - os 96 ms e como voltar pelo menu do RetroArch.

  Atualizar o `CLAUDE.md`:
  - corrigir "sem controle de taxa" (a base tem `audio_rate_control = "true"`);
  - registrar a cadeia de ganho (botões no `speaker volume control`, `Speaker Function` com nomes trocados) e o `audio-ganho` como ponto único. (O texto de DAC `0x8d8d` escrito aqui é corrigido na task 5.2.)

  Verificar relendo as duas seções contra o design.
- [x] 3.2 Rodar `uv run python -I -m unittest discover -s tests` (tudo verde) e gerar o build. Validar com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage`, e conferir na imagem:
  - os dois scripts substituídos;
  - a unit habilitada;
  - `audio-prepara` e `audio-ganho` com modo 0755.
- [x] 3.3 Passar ao usuário a gravação do build `20261026-163416` e a leitura do `r36-audio.log` (feito: o log foi lido do cartão, achados no fim do `design.md`). A verificação do pipoco passou para a task 5.4.

## 3b. Diagnóstico com áudio tocando (etapa 1b, a partir do log da etapa 1)

O `r36-audio.log` do build `20261026-163416` não mostrou nenhum registrador de volume digital do DAC (ver o fim do `design.md`). Esta etapa descobriu o estado do codec com som tocando antes de qualquer escrita.

- [x] 3.4 Criar `system/usr/lib/r36/audio-amostra` e `r36-audio-amostra.service` (simple, sem `Before`/`After`, `WantedBy=emuelec.target`): nos primeiros 10 minutos, lê o `audio_reg_debug/audio_reg` a cada 3 s e grava em `r36-audio-dac.log` (p1) o dump completo e os controles do mixer quando o estado muda. Só leitura, com limite de 64 KiB. Verificar com testes: grava só quando o estado muda, ignora contadores, não escreve no codec, sai sem erro sem a interface ou sem a p1, respeita o limite.
- [x] 3.5 Gerar o build `20261026-170324`, validar com `--target-file` e ler o `r36-audio-dac.log` gravado pelo aparelho. Resultado: DAC em 0 dB com som tocando, sem `0x8d8d` em registrador algum; a premissa do ajuste de DAC caiu e o escopo foi reduzido (seção 5).

## 5. Escopo reduzido (a partir do log da etapa 1b)

- [x] 5.1 Tirar do `audio-ganho` tudo que é de DAC: as constantes `REG_IFACE`, `DAC_REG`, `DESLOC`, `DAC_FEX`, `DAC_0DB`, as funções `dac_le`/`dac_escreve`, a `escala_corrigida` e o recuo. Fica a escala de fábrica, o mudo do volume 0 (`speaker volume control` = 0) fora do modo original, o volume salvo (padrão 29) e os comandos `aplica` e `volume <v>`. Ajustar os comentários do script e a linha de resultado que ele imprime. Verificar com `tests/test_audio.py`: remover os testes de DAC (interface ausente, escrita recusada, constantes vazias) e manter escala de fábrica, mudo e volta de 0 para 3, modo original, limite 0..100, volume padrão e `audio.volume` acrescentado sem quebra de linha. O `audio-prepara` e o `audio-amostra` seguem sem escrita em registrador.
- [x] 5.2 Corrigir a documentação: no `README.md`, a seção da feature 46 sem o DAC, a escala compensada e o "duas gravações" (fica mudo, volume salvo, buffer, chave `r36-audio-original`, `r36-audio.log` e `r36-audio-dac.log`); no `CLAUDE.md`, o item "Cadeia de ganho do som" sem o DAC `0x8d8d` (registrar que o DAC toca em 0 dB, que o ganho é um só, analógico, que o driver zera o volume ao fechar o stream e a interface `audio_reg_debug/audio_reg`). Verificar relendo as duas seções contra o `design.md`.
- [x] 5.3 Rodar `uv run python -I -m unittest discover -s tests` (tudo verde), gerar o build e validar com `./flash.sh --target-file work/cartao-teste.img --part system --build <ts>`, conferindo na imagem os scripts e as duas units.
- [x] 5.4 Passar ao usuário a gravação `./flash.sh --device /dev/sdc --part system --build <ts>` (rodada por ele). Verificar com o usuário no aparelho:
  - os pipocos sumiram ou diminuíram nas telas em que apareciam;
  - com o volume em 0 não sai som nem chiado (e com `r36-audio-original` na p1 o 0 volta ao de fábrica, para comparar);
  - o volume salvo vale já no menu depois do boot;
  - o `r36-audio.log` mostra o `speaker volume control` aplicado.
  Se o 0 não calar por completo, registrar no `design.md` (Open Questions) e propor outra change.
  Resultado (build `20261026-183653`): sem pipocos; o volume salvo vale já no menu depois do boot (precisou da Decisão 8, `r36-audio.volume`, porque o ES regravava o `emuelec.conf` ao reiniciar pelo menu); com o volume 0 ainda sai um chiado baixo, registrado no `design.md` (Open Questions) para outra change. O `speaker volume control` aplicado aparece no `r36-audio.log` do build anterior (32 para o volume 29).

## Workflow follow-up

- Merge na `main` e arquivamento da change só a pedido do usuário.
