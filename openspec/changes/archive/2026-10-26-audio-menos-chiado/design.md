# Design

## Context

A motivação está na proposal ("Why"). Os fatos da base que definem o desenho foram lidos da imagem sem montar (o SYSTEM com `unsquashfs` e o kernel com `strings` na p6) e, depois, do `r36-audio.log` e do `r36-audio-dac.log` gravados pelo aparelho (seções "Resultado" no fim).

- **Codec:** é o driver `sunxi-pcm-codec`/`audiocodec` do kernel 3.4.39. Os controles do mixer são:
  - `speaker volume control`, `headphone volume control`, `Lineout volume control` e `earpiece volume control` (0 a 63, sem escala em dB);
  - `Audio speaker out` e `Audio headphone out` (ficam `off` mesmo tocando, não são o caminho do alto-falante);
  - `Speaker Function` (itens `headset` = 0, `spk` = 1; nomes trocados neste clone: com fone, `h2w/state` 1 ou 2, o sistema grava `spk`).

  O ganho de saída é um só, analógico: o `Headphone_Volume_Control` do codec acompanha o `speaker volume control`. O FEX traz `DAC_VOL_CTRL_SPK`/`_HEADPHONE` = `0x8d8d`, `pa_single_vol = 63`, `headphone_vol = 63`, `pa_double_used = 1`, `headphone_direct_used = 1` e o amplificador externo em `PH09` (`audio_pa_ctrl`), mas o `0x8d8d` não aparece em nenhum registrador do codec, e o DAC toca em 0 dB.
- **Quem mexe no áudio na base:**
  - `udt_events.sh` (serviço `udt-hotkeys`): botões de volume, `speaker volume control` = `(v*43+50)/100 + 20`, gravando `audio.volume`.
  - `udt_pwr_events.sh` (serviço `udt_pwr`): desliga e religa `Audio speaker out`/`Audio headphone out` na suspensão e troca o `Speaker Function` duas vezes ao acordar.
  - `emuelec_autostart.sh` (boot) e `emuelecRunEmu.sh` (abertura e saída de jogo): `Speaker Function` conforme `h2w/state`.

  Nenhum script aplica o `audio.volume` no boot. O `odroidgoa_utils.sh vol` do `emustation-config` mexe num controle `Playback`, que este codec não tem.
- **Driver ao fechar o stream:** o `speaker volume control` e o `headphone volume control` voltam a 0 e o `DAC_Analog_Enable` a `0x0`; ao abrir o stream o valor anterior volta. Um 0 lido com o aparelho parado é o estado ocioso, não um reset.
- **RetroArch** (`retroarch.cfg` da p8, igual ao da base): `sdl2` com `SDL_AUDIODRIVER=alsa`, `audio_latency = "64"`, `audio_resampler = "sinc"`, `audio_resampler_quality = "2"`, `audio_sync` e `audio_rate_control` ligados, `config_save_on_exit = "true"`. O ALSA `default` é `plug` em `hw:0,0`.
- **Restrições do projeto:** só se trocam arquivos das partições (sem kernel nem bootloader). Um serviço com `After=emuelec-autostart.service` e `Before=emustation.service` trava o boot. O `emuelecRunEmu.sh` já é da feature `10-ptbr-sao-paulo` e já chama scripts de `/usr/lib/r36` protegidos por `[ -x ]`.

## Goals / Non-Goals

**Goals:**
- Um único ponto que conhece a escala e o mudo (`audio-ganho`), chamado por todos os lugares que hoje mexem no volume ou no caminho de saída.
- Comparação A/B no mesmo cartão, sem regravar.
- Diagnóstico gravado na p1, porque o aparelho não tem SSH.

**Non-Goals:**
- Mudar o kernel, o FEX ou o driver de áudio do RetroArch.
- Escrever em registrador do codec (o diagnóstico só lê).
- Redistribuir ganho entre DAC e analógico (ver "Decisões descartadas").
- Detectar silêncio no fluxo de áudio e desligar o amplificador (noise gate).
- Tratar o caminho de HDMI (o aparelho não tem).

## Decisions

### 1. Reaplicação por chamada, não por um processo vigiando

Os scripts chamam `/usr/lib/r36/audio-ganho aplica`, sempre protegidos por `[ -x ]`:
- depois de cada `Speaker Function` no `emuelecRunEmu.sh` (abertura e saída de jogo);
- no `udt_pwr_events.sh` (retorno da suspensão);
- no `audio-prepara` (boot).

O `udt_events.sh` chama `audio-ganho volume <v>`, que grava o `audio.volume` e aplica.

- *Alternativa: um daemon que relê o ganho a cada segundo.* Descartada. Entre a troca e a próxima leitura, o som sai no ganho errado. O processo também acordaria a CPU a cada segundo, e o registro térmico já mostra que isso tem custo.

O ganho é reaplicado inteiro em cada chamada, a partir do `audio.volume` salvo.

### 2. Volume 0 mudo por `speaker volume control` = 0

Fora do modo original, `audio.volume` = 0 escreve `speaker volume control` = 0, que o registrador `Headphone_Volume_Control` reflete (`0x0`). Qualquer valor acima de 0 usa a escala de fábrica. No modo original, o 0 dá 20, como na base.

- *Alternativa: `Audio speaker out` = 0.* Descartada. Esse controle fica `off` mesmo com som tocando, então não é o caminho do alto-falante.

### 3. Modo decidido no boot e guardado em `/run`

O `audio-prepara` lê `r36-audio-original` na p1, esperando a montagem por até 20 s, como o `shader-gba-prepara`, e grava `corrigido` ou `original` em `/run/r36-audio.modo`.

O `audio-ganho` lê esse arquivo. Se ele não existir, por exemplo se o `udt-hotkeys` disparar antes do serviço, o modo é `original` (comportamento de fábrica).

- *Alternativa: o `audio-ganho` olhar a p1 a cada chamada.* Descartada. A p1 pode não estar montada, e a chave mudaria no meio da sessão.

### 4. Chaves do RetroArch alteradas só quando estão no valor de fábrica

Um `sed` troca apenas as linhas exatas `audio_latency = "64"` e `audio_resampler_quality = "2"`, e faz o inverso no modo original (`"96"` volta a `"64"`, `"1"` volta a `"2"`).

- Um valor que o usuário escolheu no menu não bate com nenhum dos dois e fica como está.
- Com `config_save_on_exit = "true"`, o RetroArch regrava o arquivo com os valores que leu, então a mudança se mantém.
- O `retroarch.cfg` da camada `storage` da feature 10 não muda. O serviço cobre cartões novos e cartões com `--keep-storage` pelo mesmo caminho.

- *Alternativa: um override por core.* Descartada. O pipoco aparece em vários sistemas, e o resampler mais leve ajuda todos os cores.
- *Valor 96, e não 128:* é o menor passo que dá 50% mais folga. Os 128 ficam para depois, se ainda houver pipoco, porque 64 ms a mais de atraso já se nota em jogo de ritmo.

### 5. Serviço `r36-audio.service`

O serviço é oneshot, com `Before=emustation.service` e `After=sound.target`, e sem `After=emuelec-autostart.service`. O script espera `/storage/roms` montar (até 20 s) antes de aplicar.

No `emuelec_autostart.sh` da base o `mount_romfs.sh` (linha 87) roda **antes** do `Speaker Function` (linha 229). Esperar a p1 não garante, portanto, que o `aplica` do serviço venha depois dele. O `r36-audio-dac.log` não mostrou nenhuma troca de `Speaker Function` alterando o ganho, e o driver devolve o último valor ao abrir o stream, então o valor gravado no boot vale até o primeiro `aplica` do lançador.

Fica `TimeoutStartSec=60` e `WantedBy=emuelec.target`, como o `r36-shader-gba-prepara`. O log é escrito de uma vez no fim (`> r36-audio.log`), substituindo o do boot anterior.

### 6. Amostrador `r36-audio-amostra.service`

Serviço `Type=simple`, sem `Before`/`After`, que roda o `audio-amostra` em paralelo ao boot por 10 minutos: lê o `audio_reg_debug/audio_reg` a cada 3 s e grava em `r36-audio-dac.log` o dump completo e os controles do mixer quando o estado muda. O estado comparado ignora os contadores e o FIFO, que mudam o tempo todo. O arquivo tem limite de 64 KiB e o script só lê.

### 7. Substituição de `udt_events.sh` e `udt_pwr_events.sh`

As duas cópias partem do arquivo da base, idêntico byte a byte. A mudança é só de linhas acrescentadas:
- no `udt_events.sh`, um bloco `if [ -x audio-ganho ]` chama `audio-ganho volume` e retorna antes da escala e do `amixer` originais, que continuam como reserva;
- no `udt_pwr_events.sh`, entra uma chamada ao `audio-ganho aplica` depois do `Speaker Function` do retorno.

O teste compara cada cópia com a da base extraída do SYSTEM e aceita só essas diferenças. Assim, uma base nova com scripts diferentes faz o teste falhar em vez de passar despercebida.

### 8. Volume num arquivo próprio, além do `emuelec.conf`

Com o build `20261026-172850`, o usuário baixou o volume pelos botões, reiniciou pelo menu do ES e o aparelho voltou ao padrão: no boot o `audio-ganho aplica` leu `audio.volume=29` do `emuelec.conf`. O binário do ES lê e grava esse arquivo (a chave `audio.volume` está nele), e a hipótese é que ele o regrava com o valor da memória ao reiniciar. O `audio-ganho volume` passa a gravar o volume também em `r36-audio.volume` (p8, `.config/emuelec/configs/`), que o `aplica` lê primeiro; se faltar ou for inválido, cai no `emuelec.conf` e depois no padrão. O `emuelec.conf` continua recebendo o valor, para o que o ES mostrar.

- *Alternativa: um serviço de desligamento que copia o volume.* Descartada. O aparelho é desligado pelo botão de energia, sem passar por um serviço de parada.
- Hipótese ainda por confirmar no aparelho; se o volume continuar voltando, o botão não está chamando o `audio-ganho` e é preciso um log nos botões.

## Decisões descartadas (refutadas pelo log da etapa 1b)

- **DAC ajustado em tempo de execução pela interface de registradores, com a escala dos botões compensada (`DESLOC`) e a ordem analógico → DAC → releitura.** Dependia de o DAC estar a -14 dB (`0x8d8d`). Com som tocando, o `DAC_Digital_Part_Control` vale `0x105` (volume digital em 0, 0 dB) e nenhum registrador tem `0x8d8d`. Não há ganho digital a mover.
- **Entrega em duas etapas** (diagnóstico primeiro, constantes `REG_IFACE`, `DAC_REG` e `DESLOC` depois). O diagnóstico cumpriu o papel: ele foi o que mostrou que a segunda etapa não existe.

## Risks / Trade-offs

- [96 ms de latência] → O som chega cerca de 32 ms mais tarde. É imperceptível na maioria dos jogos, e o valor fica no menu do RetroArch para quem quiser outro.
- [O pipoco continua] → O próximo passo é `alsathread` ou 128 ms, numa change própria, com o log térmico para ver se coincide com a redução de frequência por calor.
- [O chiado com som tocando continua] → Ele vem do ganho analógico do amplificador, que a change não altera. Fica fora do escopo; o mudo em volume 0 cobre o chiado em silêncio total.
- [`speaker volume control` = 0 não calar por completo] → O `r36-audio-original` desfaz; se o usuário ouvir chiado no 0, a alternativa é desligar o amplificador (fora do escopo).
- [`audio-amostra` gastar CPU] → Ele lê um arquivo do sysfs a cada 3 s por 10 minutos e termina sozinho.

## Migration Plan

1. Build e gravação com `--part system`. Nada muda na p8 além das duas chaves do RetroArch.
2. O usuário testa o pipoco, o volume 0 mudo e compara com `r36-audio-original` no mesmo cartão.
3. Para voltar atrás sem regravar, basta criar `r36-audio-original` na p1. Para remover de vez, desabilita-se a feature 46. As chaves do RetroArch voltam ligando o aparelho uma vez com `r36-audio-original` antes de regravar, ou pelo menu do RetroArch.

## Open Questions

- ~~O `speaker volume control` = 0 cala por completo?~~ **Respondida no aparelho (build `20261026-172850`): não.** Com `audio.volume` = 0 (`speaker volume control` = 0, registrador do codec em `0x0`) ainda sai um chiado baixo. O ganho analógico em 0 não desliga o amplificador externo (`PH09`, `audio_pa_ctrl`), que segue amplificando o próprio ruído. A saída é desligar o amplificador (ou o caminho `Audio speaker out`, que fica `off` mesmo tocando, então provavelmente não é o controle certo) quando o volume for 0 ou houver silêncio, o que está fora do escopo e fica para outra change. O mudo da change continua valendo como redução (de 20 para 0), não como silêncio total.

## Resultado da etapa 1 (r36-audio.log do build 20261026-163416)

Lido do cartão em `R36-ROMS/r36-audio.log`; o resto vem de `strings` no kernel da base (p6).

- **O que funcionou:** o log nasceu; as chaves do RetroArch viraram 96/1; o `aplica` pôs o `speaker volume control` em 32 (volume 29). Antes dele o controle estava em **0**, estado do aparelho parado (ver "Driver ao fechar o stream").
- **Interface de registradores:** `/sys/devices/platform/sunxi-pcm-codec/audio_reg_debug` é um **diretório**; a leitura do diretório dá erro de E/S e o arquivo útil é `audio_reg_debug/audio_reg` (`dump audio reg:`, grupo digital em `0xf1c22c00` e grupo analógico em `0x0`..`0xf`). No kernel, o `store_audio_reg` tem os formatos `%d,%d,0x%x,0x%x` e as mensagens `reg_group`, `reg_offset`, `reg_val`, `not rw_flag`, `not exist reg group`. Isto sugere `rw_flag,grupo,offset,valor`, **nunca testado**: a change não escreve em registrador.
- **Controle analógico:** `speaker volume control` vai de 0 a 63, `step=0`, **sem `dBscale`**.
- **Outros fatos:** `Audio speaker out` e `Audio headphone out` estavam `off`; `Speaker Function` tem o item 1 `spk` e o 0 `headset`; o `busybox` tem `devmem`; o `Speaker Function` do log não mudou nenhum valor lido.

## Resultado da etapa 1b (r36-audio-dac.log do build 20261026-170324)

Amostras com a música do menu e um jogo tocando (DAC ativo: `DAC_TX_DATA` com dados, `DAC_Analog_Enable_and_PA_Source_Control` = `0xcc`).

- **Sem atenuação digital visível.** Com o DAC ativo, `DAC_Digital_Part_Control` vale `0x105` e nenhum registrador do dump tem o `0x8d8d` do FEX. Os bits 17:12 (campo de volume digital, se o layout for o do A33) são 0, ou seja, 0 dB. O `DAC_VOL_CTRL_*` do FEX é lido pelo driver mas **não aparece em nenhum registrador do codec**. A premissa de "DAC em -14 dB" **não se sustenta**.
- **O ganho é um só, analógico:** `Headphone_Volume_Control` (analógico) acompanha o `speaker volume control` (`0x20` = 32 com o controle em 32, `0x0` com ele em 0).
- **O driver zera o volume ao fechar o stream:** ao parar o som o `speaker volume control` e o `headphone volume control` voltam a 0 e o `DAC_Analog_Enable` a `0x0`, e ao abrir o stream voltam a 32. Não se viu nenhuma troca do `Speaker Function` regravando o ganho.
- **`Audio speaker out`/`Audio headphone out` ficam `off` mesmo tocando.** O `PA_Enable_and_HP_Control` fica em `0xf4` o tempo todo.
