# Design

## Context

- **Script da base** (`/usr/bin/emuelecRunEmu.sh`, extraído do SYSTEM do cartão): a linha 7 faz `. /etc/profile` (que carrega `maxperf`, `normperf` e `get_ee_setting` de `/etc/profile.d/99-emuelec.conf`) e a linha 8 chama `maxperf` sem condição. `PLATFORM` é definido na linha 131 e `ROMNAME` na 140. O bloco que consulta a chave (linhas 475 a 484) está comentado, e o `normperf` da linha 558 roda ao fim do jogo.
- **`maxperf`/`normperf` no A33:** `performance` ou `ondemand` em `cpu0/cpufreq/scaling_governor`, e `0` ou `1` em `/sys/devices/platform/sunxi-ddrfreq/devfreq/sunxi-ddrfreq/dsm/scene`.
- **`get_ee_setting <chave> <plataforma> <rom>`** (do `profile.d`) consulta jogo, sistema, global e a chave solta, nessa ordem. Devolve vazio quando nada está definido.
- **Camada `system/`:** os arquivos de `features/*/system/` substituem os da base (o `changes.txt` mostra "substituído"). Nenhuma feature sobrescreve hoje um script da base.
- **Bugs do `thermal-log`:** a busca da DRAM tenta `platform/sunxi-ddrfreq/dsm/scene`, sem o trecho `devfreq/sunxi-ddrfreq`, que o `maxperf` usa; por isso `dram_scene` sai vazio. As linhas do log têm 15 campos contra 18 do cabeçalho: `cpu_busy` devolve vazio em vez de `a,b,c,d`. Causa confirmada com o busybox 1.32.1 da imagem (compilado do fonte): o `awk` dele lê `out = out (n ? "," : "") v` como chamada da função `out` e aborta com "Call to undefined function", então a função devolve vazio. O `awk` do host (gawk) e o busybox 1.37 aceitam, por isso os testes passavam.

## Goals / Non-Goals

**Goals:**
- O `maxperf` do menu do ES decide o governor de cada jogo.
- O log mostra a ocupação por núcleo e a cena da DRAM reais.

**Non-Goals:**
- Tetos de clock por sistema (spec futura, com base no log).
- Mexer em `profile.d/99-emuelec.conf`, no `emuelec_autostart.sh` ou em outros scripts da base.

## Decisions

- **Cópia do `emuelecRunEmu.sh` com duas alterações, na feature 10.** Remover o `maxperf` da linha 8 e inserir, logo depois de `ROMNAME` ser definido, `[ "$(get_ee_setting maxperf "${PLATFORM}" "${ROMNAME##*/}")" = "1" ] && maxperf || normperf`. O resto do arquivo fica idêntico à base, para a diferença ser pequena e conferível. Alternativas descartadas: (a) redefinir `maxperf()` num novo `profile.d`, que roda na linha 8 sem plataforma nem ROM; (b) descomentar o bloco das linhas 475 a 484, que exige `ee_oga_oc` e só decide depois do emulador montado, e deixaria a linha 8 ligar o modo antes. Aqui o modo é escolhido antes de qualquer trabalho pesado.
- **`1` liga, qualquer outro valor desliga.** Vazio (nenhuma chave) conta como desligado, coerente com o padrão `global.maxperf=0` da imagem.
- **Teste que guarda a diferença contra a base.** Um teste confere que o script da feature só difere da base nas linhas esperadas; assim, trocar a imagem base sem reconferir a cópia falha o teste. O teste usa a base quando ela está disponível no cache de testes e é pulado sem ela.
- **Correções no `thermal-log` na própria feature 43,** com um caminho extra para a DRAM (mantendo os atuais) e a leitura de `cpu_busy` reescrita para o `awk` que a imagem traz, validada com o mesmo `awk` nos testes.

## Risks / Trade-offs

- [Cópia de um script da base envelhece] → o teste de diferença contra a base e uma nota no README.
- [Regressão de desempenho em GBA, PSP, N64] → a opção continua ligável por sistema ou jogo; o README diz quais sistemas sofrem.
- [Os testes usam o `awk` do host, que aceita construções que o busybox 1.32.1 rejeita] → um teste estático proíbe `identificador (` dentro do `awk` do `cpu_busy`, e um teste roda a função com `busybox awk` quando houver `busybox` no PATH.
- [Licença] → o script é GPL-2.0-or-later e o cabeçalho de copyright da base é mantido.

## Migration Plan

Regravar a p7 (SYSTEM) e a p8 não é necessário para a conf; só a p7 muda (`--part system`). Para voltar, regravar com o build anterior.
