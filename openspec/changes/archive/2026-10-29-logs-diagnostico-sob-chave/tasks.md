# Tasks

## 1. Áudio (46-audio)

- [x] 1.1 Em `audio-prepara`, ler `r36-diagnostico` na etapa 1 (junto de `MONTADA`) para definir `LOGA`; tornar `registro()` e `secao()` no-ops sem `LOGA`, pôr `amixer contents`, os dumps do `audio_reg*`, o `devmem` e as leituras de antes e depois do `Speaker Function` dentro de `if [ -n "$LOGA" ]`, e exigir `LOGA` no `cat "$TMPLOG" > "$LOG"`. Verificar que `troca_chave`, o `amixer cset name='Speaker Function'` e o `audio-ganho aplica` ficam fora do `if`, lendo o diff.
- [x] 1.2 Em `audio-amostra`, sair com `exit 0` quando a p1 está montada e `r36-diagnostico` não existe. Verificar que o unit não ganhou `ConditionPathExists`.
- [x] 1.3 Em `tests/test_audio.py`, criar `r36-diagnostico` no `setUp` dos testes que conferem o log (`test_log_traz_todas_as_secoes`, `test_log_substitui_o_anterior`, `test_fone_conectado_vira_spk`, `test_sem_interface_aparece_no_log_sem_erro` e os de `AudioAmostra`) e acrescentar: sem a chave o `audio-prepara` não cria `r36-audio.log` mas aplica `retroarch.cfg`, `Speaker Function` e volume; sem a chave o `audio-amostra` não cria `r36-audio-dac.log` nem lê o codec; log antigo na p1 sem a chave fica intacto. Verificar com `uv run python -I -m unittest tests.test_audio`.
- [x] 1.4 Atualizar o comentário e a `description` de `features/46-audio/feature.toml` e o cabeçalho dos dois scripts para citar a chave. Verificar com `grep -n "r36-diagnostico" features/46-audio -r`.

## 2. Bateria (48-bateria-percentual)

- [x] 2.1 Em `bateria-percentual`, definir `LOGA` em `pos_montagem` quando `$ROMS/r36-diagnostico` existe e exigir `LOGA` em `grava_p1`. Verificar que o log em `$RUN/log` e o `logger` continuam sem a chave.
- [x] 2.2 Em `tests/test_bateria_percentual.py`, criar a chave nos testes que leem `r36-bateria.log` (linhas 212, 320, 345) e acrescentar: sem a chave `r36-bateria.log` não é criado e o `capacity` publicado é o mesmo; a chave `r36-bateria-original` continua devolvendo o valor do kernel. Verificar com `uv run python -I -m unittest tests.test_bateria_percentual`.
- [x] 2.3 Atualizar o comentário e a `description` de `features/48-bateria-percentual/feature.toml` e o cabeçalho do script. Verificar com `grep -rn "r36-bateria.log" features/48-bateria-percentual` e conferir que todo trecho cita a chave.

## 3. Shader (54-shaders-gba)

- [x] 3.1 Em `shader-gba-prepara`, definir `LOGA` quando a p1 está montada e `r36-diagnostico` existe; usar `LOGA` em `registro()` e no `: > "$LOG"`, manter `MONTADA` para a chave `r36-gba-sem-shader`, e pôr o bloco de diagnóstico do framebuffer dentro de `if [ -n "$LOGA" ]`. Verificar lendo o diff que a lógica de presets e `emuelec.conf` não mudou.
- [x] 3.2 Em `tests/test_shaders_gba.py`, criar a chave nos testes das linhas 298 e 319 e acrescentar: sem a chave `r36-shader-gba.log` não é criado, o `gba.shaderset` e os presets de core são criados como antes e `r36-gba-sem-shader` ainda os desfaz. Verificar com `uv run python -I -m unittest tests.test_shaders_gba`.

## 4. Spec, documentação e integração

- [x] 4.1 No `CLAUDE.md`, acrescentar na seção do aparelho que os logs de áudio, bateria e shader só existem com `r36-diagnostico` na p1 e que é preciso lembrar o usuário da chave ao pedir um log; ajustar as menções às linhas dos logs de áudio e de shader. Verificar com `grep -n "r36-diagnostico" CLAUDE.md`.
- [x] 4.2 No `README.md`, criar uma subseção "Diagnóstico" que descreve a chave e os quatro logs, e ajustar os trechos dos logs de áudio, bateria e shader para apontar para ela. Verificar que todo comando do trecho roda como escrito e que `grep -n "r36-diagnostico" README.md` cobre as quatro features.
- [x] 4.3 Rodar a suíte inteira com `uv run python -I -m unittest discover -s tests` e verificar que passa sem falhas novas.
- [x] 4.4 Rodar `openspec validate logs-diagnostico-sob-chave --strict` e verificar que não há erro.
- [x] 4.5 Gerar um build (`./build.sh`) e verificar nos arquivos dele (`mcopy` e `unsquashfs -cat` na imagem, sem montar) que os três scripts contêm a checagem. A conferência no aparelho (sem a chave nenhum log novo; com a chave os quatro logs) é instrução para o usuário rodar.

## Workflow follow-up

- Criar a branch `logs-diagnostico-sob-chave` a partir da `main` no início do `/opsx:apply`.
- Arquivar a change depois da conferência no aparelho.
