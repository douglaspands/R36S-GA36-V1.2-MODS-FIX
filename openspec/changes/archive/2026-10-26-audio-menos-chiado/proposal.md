# Proposal

## Why

O som do aparelho tem dois defeitos que o usuário percebe:

- **Chiado** quando o jogo está em silêncio. Ele fica mais alto quando se aumenta o volume.
- **Pipocos** durante o jogo, em algumas telas ou jogos. A imagem não engasga.

O que se sabe de cada um:

- **Chiado:** a hipótese inicial era um DAC com volume digital de cerca de -14 dB no FEX (`DAC_VOL_CTRL_SPK = DAC_VOL_CTRL_HEADPHONE = 0x8d8d`), compensado no ganho analógico pelos botões de volume, que multiplica o ruído. **O log do aparelho refutou isso.** Com música e jogo tocando, o `DAC_Digital_Part_Control` vale `0x105` (campo de volume digital em 0, ou seja, 0 dB) e nenhum registrador do codec tem `0x8d8d`. O único ganho é o analógico (`Headphone_Volume_Control`, que acompanha o `speaker volume control`, de 0 a 63). Não há, portanto, ganho digital a redistribuir. O que a base faz de errado e a change corrige:
  - o volume 0 dá `speaker volume control` = 20 e não silencia;
  - o `audio.volume` salvo não é aplicado no boot (só no primeiro toque num botão de volume).
- **Pipoco:** é falta de áudio no buffer (underrun). O RetroArch roda com `audio_latency = 64` e `audio_resampler_quality = 2` (sinc "normal") num A33 que reduz a frequência da CPU quando esquenta. Basta uma cena mais pesada para o buffer esvaziar.

## What Changes

- **Feature nova `46-audio`**, ligada por padrão:
  - **Volume 0 mudo e volume salvo no boot:**
    - O volume 0 passa a silenciar de verdade (`speaker volume control` = 0).
    - O volume salvo em `audio.volume` é aplicado já no boot e depois de cada troca do caminho de saída (`Speaker Function`): ao abrir e fechar um jogo e ao acordar da suspensão.
    - A escala dos botões de volume é a de fábrica (20 + volume × 0,43) para qualquer volume acima de 0.
  - **Folga no buffer (pipoco):** no `retroarch.cfg` da p8, `audio_latency` passa de 64 para 96 e `audio_resampler_quality` de 2 para 1. As duas chaves só mudam enquanto estiverem no valor de fábrica, então um valor que o usuário escolheu no menu é respeitado.
  - **Diagnóstico:** a cada boot, grava `r36-audio.log` na raiz da p1 (controles do mixer, interface de registradores do driver, efeito de um `Speaker Function`, o que o serviço aplicou) e, nos primeiros minutos, `r36-audio-dac.log` com o dump do codec a cada mudança de estado, com som tocando. Os dois são só de leitura.
- **Chave de comparação:** um arquivo `r36-audio-original` na raiz da p1 volta o volume 0 para a escala de fábrica (sem mudo) e as duas chaves do RetroArch para os valores de fábrica. Isso permite comparar no mesmo cartão, sem regravar.
- O `emuelecRunEmu.sh` da feature `10-ptbr-sao-paulo` ganha a chamada ao ajuste depois de cada `Speaker Function`, protegida por `[ -x ... ]`, igual à do `cpu-ondemand-tune`.
- A feature substitui `usr/bin/udt_events.sh` (botões de volume) e `usr/bin/udt_pwr_events.sh` (suspensão) do SYSTEM. Os serviços `udt-hotkeys` e `udt_pwr` continuam os mesmos.
- **Fora do escopo:**
  - redistribuir o ganho entre o DAC e o analógico (não há ganho digital a mover, ver acima);
  - reduzir o chiado com som tocando, que depende do amplificador analógico e fica para outra change se o usuário ainda quiser;
  - trocar o `audio_driver` (`alsathread`), que fica para outra change se o pipoco continuar;
  - desligar o amplificador externo no silêncio;
  - alterar o FEX/`script.bin` na área do bootloader.

## Capabilities

### New Capabilities
- `audio-output`: como a saída de som do aparelho é configurada: volume 0 mudo, volume salvo aplicado no boot, folga do buffer de áudio do RetroArch, diagnóstico gravado na p1 e chave para voltar ao som de fábrica.

### Modified Capabilities

Nenhuma. O `system-services` já exige que `udt-hotkeys`, `udt_pwr` e o áudio continuem ativos, e eles continuam: só os scripts que esses serviços rodam são substituídos.

## Impact

- Arquivos novos em `features/46-audio/` (todos em `system/usr/`):
  - `feature.toml`;
  - `system/usr/lib/r36/audio-ganho`: aplica o volume salvo e o mudo, e serve também de ponto de reaplicação;
  - `system/usr/lib/r36/audio-prepara`: modo, chaves do RetroArch e `r36-audio.log` no boot;
  - `system/usr/lib/r36/audio-amostra`: `r36-audio-dac.log`;
  - `system/usr/lib/systemd/system/r36-audio.service` e `r36-audio-amostra.service`;
  - `system/usr/bin/udt_events.sh` e `system/usr/bin/udt_pwr_events.sh`, cópias da base com a chamada ao `audio-ganho`.
- `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`: duas chamadas protegidas ao `audio-ganho`.
- `tests/test_audio.py`: testes com uma árvore falsa e um `amixer` simulado no `PATH`, no padrão do `test_registro_termico.py`.
- `README.md` (seção da feature 46) e `CLAUDE.md`. O `CLAUDE.md` hoje diz "sem controle de taxa", mas o `retroarch.cfg` da base tem `audio_rate_control = "true"`; a seção do áudio é corrigida e registra a cadeia de ganho real (um ganho analógico só, DAC em 0 dB, driver que zera o volume ao fechar o stream).
- Efeito no aparelho:
  - o volume 0 cala o alto-falante;
  - o `audio.volume` vale desde o boot;
  - cerca de 32 ms a mais de atraso no som do RetroArch;
  - um pouco menos de CPU gasta no resampler.
  - Tudo vale com `--part system` ou `--keep-storage`, porque o ajuste da p8 é feito pelo serviço e não pela camada `storage`.
- Risco: mudanças pequenas e reversíveis. O `r36-audio-original` desfaz tudo sem regravar.
