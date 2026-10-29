# Proposal

## Why

Os logs de áudio, bateria e shader foram criados para investigar problemas que já foram resolvidos (chiado, percentual da bateria, tearing e bind do shader). Hoje eles gravam na p1 a cada boot, mesmo sem ninguém olhar, e deixam arquivos soltos na raiz da R36-ROMS. Remover o código perderia a ferramenta se o problema voltar e obrigaria a mexer em scripts que também fazem trabalho útil; desativar por uma chave mantém a ferramenta a um arquivo de distância.

## What Changes

- Novo arquivo vazio `r36-diagnostico` na raiz da p1 (R36-ROMS). Sem ele, os logs de áudio, bateria e shader **não são gravados**; com ele, voltam a ser gravados como hoje.
- `r36-audio.log` (`audio-prepara`): sem a chave, não grava o log e não faz as leituras de diagnóstico (`amixer contents`, dumps do `audio_reg*`, antes e depois do `Speaker Function`). Os passos úteis continuam: modo corrigido/original, chaves do `retroarch.cfg`, `Speaker Function` e `audio-ganho aplica`.
- `r36-audio-dac.log` (`audio-amostra`): sem a chave, o amostrador termina logo depois de a p1 montar, sem ler nada nem criar o arquivo.
- `r36-bateria.log` (`bateria-percentual`): sem a chave, não copia o log do boot para a p1. O cálculo, o bind do `capacity`, a curva e a chave `r36-bateria-original` não mudam; o log interno em `/run` e o `logger` continuam.
- `r36-shader-gba.log` (`shader-gba-prepara`): sem a chave, não grava o log. O shader por padrão, os presets e a chave `r36-gba-sem-shader` não mudam.
- O registro térmico (`r36-thermal.csv`, `r36-sysinfo.txt`) **não** entra na chave e segue sempre ligado.
- Os logs que já estão no cartão não são apagados pelo aparelho; quem apaga é o usuário, pelo PC.
- `README.md` e `CLAUDE.md` passam a documentar a chave; os testes das três features ganham os dois cenários (com e sem a chave).

## Capabilities

### New Capabilities
- `diagnostic-logs`: a chave `r36-diagnostico` na p1 e a regra de que os logs de diagnóstico de áudio, bateria e shader só existem com ela (e que o registro térmico fica fora).

### Modified Capabilities
- `audio-output`: os requisitos "Diagnóstico de áudio na p1" e "Amostragem do codec com áudio tocando" passam a valer só com a chave.
- `retroarch-shaders`: o requisito "Chave para desligar e log na p1" mantém a chave `r36-<sistema>-sem-shader` e passa a gravar o log só com `r36-diagnostico`.

## Impact

- `features/46-audio/system/usr/lib/r36/audio-prepara`, `audio-amostra`, `feature.toml`.
- `features/48-bateria-percentual/system/usr/lib/r36/bateria-percentual`, `feature.toml`.
- `features/54-shaders-gba/system/usr/lib/r36/shader-gba-prepara`.
- `tests/test_audio.py`, `tests/test_bateria_percentual.py`, `tests/test_shaders_gba.py`.
- `README.md` e `CLAUDE.md`.
- Sem mudança de ABI, de partições nem de `flash.sh`. A p1 passa a receber menos escrita por boot.
- As changes seguintes que gravarem log de diagnóstico (por exemplo, o do botão FN) devem usar a mesma chave.
