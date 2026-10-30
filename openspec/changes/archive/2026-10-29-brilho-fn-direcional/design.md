# Design

## Context

Ver `proposal.md` (Why). Estado atual, lido no repositório:

- Nenhuma feature ajusta o brilho. O `udt_pwr_events.sh` (feature 46) zera o `lcdbl` ao suspender e, ao acordar, lê `brightness.level` do `emuelec.conf` (`get_ee_setting`) e grava `(nível*255+50)/100` no `lcdbl`. O `emuelecRunEmu.sh` (l.67-70) copia o mesmo `brightness.level` para `screen_brightness` no `retroarch.cfg`. A feature 10 põe `brightness.level=80`.
- O `emuelec.conf` não é fonte confiável (o ES o regrava ao reiniciar). O modelo de persistência é o `audio-ganho` da feature 46: arquivo próprio na p8 (`r36-audio.volume`, em `/storage/.config/emuelec/configs/`), com chave de desfazer na p1.
- O FN chega como `BTN_MODE` (316) pelo `fn-remapeia` (feature 20). No `micro_gamepad.cfg` o D-pad são os botões 13 a 16 e nenhum hotkey do RetroArch os usa. O `evtest` existe na base e o `udt_events.sh` o usa em `/dev/input/event1` (teclas de volume); o `emuelecRunEmu.sh` liga o joystick a `/dev/input/event2`.
- Armadilha de `CLAUDE.md`: a p8 vence o SYSTEM (arquivo que já existe nunca é atualizado), e um serviço com `After=emuelec-autostart.service` + `Before=emustation.service` trava o boot.

## Goals / Non-Goals

**Goals:** atalho FN + ↑/↓ que funciona em jogo e no ES; nível persistente entre boots e sonos; custo de CPU e de escrita no SD desprezível; nenhum arquivo disputado com as changes A, B e C.

**Non-Goals:** brilho dentro do menu do ES ou do RetroArch; tratar o `screen_brightness` do `retroarch.cfg` (o RunEmu é de A e B); brilho automático; dar função ao FN no ES.

## Decisions

### D1. Feature `62-brilho-fn`, com três peças

- `usr/lib/r36/brilho-aplica` (sh do BusyBox, 0755): único ponto que lê e grava o nível. Subcomandos: `aplica` (lê o nível salvo, aplica no `lcdbl`), `ajusta +|-` (passo, piso e teto, grava o `lcdbl`) , `salva` (grava o arquivo do nível) e `padrao` (remove o arquivo e aplica 80). Sai sempre com 0.
- `usr/lib/r36/brilho-leitor` (bash, 0755): lê os eventos com `evtest` e chama o `brilho-aplica`.
- Units: `r36-brilho.service` (oneshot, aplica o nível e trata a chave `r36-brilho-original` no boot) e `r36-brilho-leitor.service` (simple, `Nice=10`), ambos em `emuelec.target.wants`, **sem** `After=emuelec-autostart.service`. O oneshot espera a p1 montar por dentro do script, como o `audio-prepara`.

*Alternativa descartada:* estender o `udt_events.sh` (feature 46). É arquivo de outra feature e já tem um laço de `evtest` em outro dispositivo; um serviço separado não mexe em nada existente.

### D2. Nível, passo, piso e persistência

- Arquivo `r36-brilho.level` em `/storage/.config/emuelec/configs/` (p8), uma linha, inteiro de 0 a 100. Escala para o `lcdbl`: `(nível*255+50)/100`, a mesma do `udt_pwr_events.sh`.
- Passo de **5** pontos, piso de **10** e teto de **100**. O valor de leitura inválido (vazio, texto, fora de 0 a 100, abaixo do piso) cai no padrão; sem arquivo, vale o `brightness.level` do `emuelec.conf` e, sem ele, 80.
- Durante a repetição o `lcdbl` é gravado a cada passo, mas o arquivo só é gravado **uma vez, quando a seta é solta** (e depois do reset por FN + L3), para não escrever no SD 5 vezes por segundo.
- *Na implementação:* o nível em uso fica em `/run/r36-brilho.atual` (tmpfs), gravado por `aplica`, `ajusta` e `padrao`; o `ajusta` parte dele (ou do nível salvo, sem ele). O `salva` só grava o arquivo se o nível em uso difere do que está nele (ou, sem o arquivo, do nível que valeria), então soltar a seta sem mudança, ou depois do reset com o `emuelec.conf` em 80, não escreve no SD; com o `emuelec.conf` em outro valor, o salva depois do reset grava 80, e o padrão persiste. Valor com zero à esquerda ou com mais de 3 algarismos também é inválido (evita a aritmética octal do `sh`).

### D3. Leitura dos eventos

- O dispositivo é achado pelo nome (`micro_gamepad`) em `/proc/bus/input/devices`, não por número fixo. Se não achar, o leitor tenta de novo por algum tempo e sai com 0.
- O FN é o evento `code 316 (BTN_MODE)`. O D-pad é aceito em três formas: `KEY_UP`/`KEY_DOWN`, `BTN_DPAD_UP`/`BTN_DPAD_DOWN` e `ABS_HAT0Y` (valor −1 sobe, +1 desce, 0 solta). Qual delas o aparelho emite só se descobre lá: o leitor registra o que viu no `r36-brilho.log` (sob a chave) e o tratamento das três cobre o caso sem nova gravação.
- Estado em variáveis do leitor: `fn`, `cima`, `baixo`. Reset: o L3 apertado (`value 1`) com `fn=1` faz o leitor parar a repetição e chamar `padrao` uma vez por clique; segurar o L3 não repete e o L3 sem o FN não faz nada. O laço de repetição segue o padrão do `repeat_volume_ctrl` (subshell em segundo plano, 0,2 s, `kill` ao soltar), com o cuidado de matar a repetição quando o FN é solto ou o combo dispara.
- O parser de uma linha de evento fica numa função que os testes alimentam com linhas reais do formato do `evtest`, sem precisar do aparelho.
- *Na implementação:* o primeiro passo roda na hora, no laço principal; só a repetição vai para o subshell, que tem `trap 'exit 0' TERM` para o `kill` esperar o passo (ou o `sleep`) em curso, e o `salva` sempre vem depois do último `ajusta`. Uma seta só age se for apertada com o FN já apertado; depois do reset, a seta que ficou apertada não volta a repetir até ser solta e apertada de novo. O reset por FN + L3 vale igual com o D-pad como botão, tecla ou eixo. Se o `evtest` acabar, a repetição para e o nível é salvo. O `value 2` (repetição automática do kernel) é ignorado. O script carregado com `.` só define as funções (os testes chamam o `interpreta` assim).

**Achado da task 1.2** (SYSTEM da imagem base, sem montar):

- `usr/bin/evtest` existe (0755). As cadeias do binário dão o formato da linha de evento: `Event: time %ld.%06ld, ` seguido de `type %d (%s), code %d (%s), value %d` (o `EV_MSC` sai em hexadecimal, `value %02x`), e as linhas de sincronismo `-------------- SYN_REPORT ------------`. O cabeçalho lista as capacidades como `    Event code 316 (BTN_MODE)`, sem `value`; o parser só aceita linhas que começam com `Event: time`. O binário conhece os nomes `BTN_MODE`, `BTN_DPAD_UP` e `ABS_HAT0Y`. Exemplos usados de fixture: `Event: time 1700000000.123456, type 1 (EV_KEY), code 316 (BTN_MODE), value 1`, `... type 1 (EV_KEY), code 544 (BTN_DPAD_UP), value 1`, `... type 1 (EV_KEY), code 103 (KEY_UP), value 0`, `... type 3 (EV_ABS), code 17 (ABS_HAT0Y), value -1`.
- `usr/lib/modules/udt_joystick.ko` registra o dispositivo de plataforma `micro_gamepad` (o mesmo nome do `input_device` do `micro_gamepad.cfg` do RetroArch) e um segundo dispositivo de entrada, `udt_keyboard`. O leitor procura o bloco com `N: Name="micro_gamepad"` em `/proc/bus/input/devices` e tira o `eventN` da linha `H: Handlers=`. O módulo é carregado pelo `emuelec_autostart.sh` na l.210, bem depois do início do serviço, por isso a espera.
- Hipótese sobre o D-pad (não confirmada): no `micro_gamepad.cfg` o FN (316) é o botão 10 e o D-pad são os botões 13 a 16, logo depois de 11 e 12 (`BTN_THUMBL`/`BTN_THUMBR`, 317 e 318). Na numeração do SDL isso aponta para `BTN_DPAD_UP`..`BTN_DPAD_RIGHT` (544 a 547). O leitor trata também `KEY_UP`/`KEY_DOWN` e `ABS_HAT0Y`; o que o aparelho emite só se vê no `r36-brilho.log` (task 6.1).

**Decisão do usuário (reset por FN + L3).** O usuário não consegue apertar ↑ e ↓ do D-pad ao mesmo tempo, então o reset ao padrão deixa de ser FN + ↑ + ↓ e passa a ser **FN + clique do analógico esquerdo (L3)**. Achado: o `micro_gamepad.cfg` da feature 20 mapeia `input_l3_btn = "11"` e `input_r3_btn = "12"`, e o FN (316, `BTN_MODE`) é o botão 10 (confirmado no aparelho: o FN abre o menu do RetroArch). Pela ordem do bloco `BTN_GAMEPAD` do kernel (`BTN_MODE` 316, `BTN_THUMBL` 317, `BTN_THUMBR` 318), o botão 11 é o **`BTN_THUMBL` (317)**; o `emuelecRunEmu.sh` cita o 318 (`BTN_THUMBR`) no ramo comentado do `nds`, coerente com o R3 = 12. É **hipótese** até o aparelho: o código que o L3 emite de fato só se vê no `r36-brilho.log` (com `r36-diagnostico`), que registra a primeira vez que cada código é visto. O leitor aceita `BTN_THUMBL` pelo nome e o código numérico 317 (a linha do `evtest` traz os dois: `code 317 (BTN_THUMBL)`), então um nome diferente com o mesmo código também serve. O reset só dispara com o FN apertado, na borda de subida do L3, uma vez por clique.

### D4. Reaplicar ao acordar, sem tocar no RunEmu

O `udt_pwr_events.sh` ganha **uma** chamada `[ -x /usr/lib/r36/brilho-aplica ] && /usr/lib/r36/brilho-aplica aplica`, logo depois do `echo $scaled_value > .../lcdbl` do ramo de acordar (a chamada vence a gravação do `emuelec.conf`). Marcador `# R36:` como as demais linhas da base. O `screen_brightness` do `retroarch.cfg` fica como está: só é lido pelo RetroArch para o brilho dele e é outro assunto (Non-Goal).

### D5. Boot

O `r36-brilho.service` precisa rodar **depois** de quem põe o brilho de fábrica no boot. Descobrir esse ponto (o `emuelec-autostart`, `udt_pwr_events`, o próprio driver) é a task 1.1, lendo os scripts do SYSTEM da imagem base sem montar. Se a base grava o `lcdbl` depois do nosso serviço, o script espera um tempo curto e reaplica; nada de `After=emuelec-autostart.service` (trava o boot).

**Achado da task 1.1** (SYSTEM da imagem base extraído com `mcopy` e lido com `unsquashfs`, sem montar; busca de `lcdbl` em todo `usr/bin`, `usr/lib/systemd`, `usr/lib/udev`, `usr/config` e `etc`, inclusive binários). Só dois pontos gravam o `lcdbl` no boot, os dois antes de a p1 montar:

1. `usr/bin/lsb_release`, l.18: `echo 204 > /sys/devices/virtual/disp/disp/attr/lcdbl` (80 %, fixo), depois do splash do `ffplay`. Quem o roda é o `show-version.service` (oneshot, `WantedBy=basic.target`), e todo serviço com dependências padrão (o nosso) já roda depois do `basic.target`.
2. `usr/bin/emuelec_autostart.sh`, l.54-56: `brightness=$(get_ee_setting brightness.level)` e `echo $scaled_value > .../lcdbl`, **antes** do `mount_romfs.sh` (l.89), que monta a p1, e do `insmod udt_joystick.ko` (l.210), que cria o `micro_gamepad`.

Os demais acham o `lcdbl` só em linhas comentadas (`headphone_sense.sh` l.59-61, `system-sleep/sleep` l.8 e l.20-22) ou fora do boot (`udt_pwr_events.sh`, ao suspender e acordar). O `emuelecRunEmu.sh` (l.64-67) só copia o `brightness.level` para o `screen_brightness` do `retroarch.cfg`, sem tocar no `lcdbl`. Nenhum binário do SYSTEM cita o `lcdbl`.

Decisão: o `brilho-aplica boot` espera `/storage/roms` virar ponto de montagem (até 20 s, como o `audio-prepara`). Como o autostart grava o `lcdbl` antes de chamar o `mount_romfs.sh`, a p1 montada garante que a gravação da base já passou, e o nível salvo é aplicado por cima, sem ordem do systemd. Sem a p1 nos 20 s, aplica assim mesmo: a l.56 é das primeiras do autostart. A unit não tem `After=` nem `Before=`.

### D6. Chave e log

- `r36-brilho-original` (arquivo vazio na raiz da p1) é lido pelo oneshot: com ela, o nível salvo é descartado e o brilho vai a 80 a cada boot. Sem p1 em 20 s, a chave conta como ausente.
- `r36-brilho.log` na p1 só com `r36-diagnostico`, a mesma regra dos outros logs (spec `diagnostic-logs`). Sem a chave não há escrita na p1.

## Risks / Trade-offs

- **O D-pad não chega com o FN apertado, ou chega por outro evento** → o parser trata botão e eixo, o log sob chave mostra o que foi visto, e a hipótese é confirmada no aparelho (tarefa do usuário na integração). Se nenhuma forma servir, a change volta ao planejamento.
- **O RetroArch também recebe o FN e o D-pad e abre o menu/age em jogo** → o FN já é hotkey do RetroArch e só age combinado com outro botão mapeado; ↑/↓ não estão mapeados como hotkey (`CLAUDE.md`, `micro_gamepad.cfg`). Conferir no aparelho que FN + ↑/↓ não faz nada no jogo além do brilho.
- **O D-pad também chega ao ES e ao jogo** → o leitor só observa (`evtest` sem `--grab`), então FN + ↑/↓ também move o cursor no ES e o personagem no jogo enquanto o brilho muda. Pegar o dispositivo com `--grab` tiraria o controle do ES e do RetroArch; fica como limite conhecido, conferido no aparelho (task 6.1).
- **A chamada ao acordar ficou fora do branch de D** → a linha no `udt_pwr_events.sh` quebra o `tests/test_audio.py::test_udt_pwr_events_so_acrescenta_a_reaplicacao` (lista exata de linhas acrescentadas à base), que é só leitura para D. A task 4.3 traz a linha e a mudança no teste para a integração aplicar; até lá, ao acordar vale o `brightness.level` do `emuelec.conf`.
- **O `evtest` terminar mata o atalho até o próximo boot** → o `r36-brilho-leitor.service` tem `Restart=always` e `RestartSec=5` (sem `After=emuelec-autostart.service`/`Before=emustation.service`). Se o leitor sair com 0 depois de esperar o dispositivo (até 120 s), o reinício vem 5 s depois e espera de novo: sem laço rápido; se o `evtest` morrer na hora, o ciclo é de 5 s, custo desprezível. O `VISTOS` zera a cada reinício, então o log sob chave repete a primeira vez de cada código.
- **Serviço lendo `evtest` sem parar gasta CPU** → bloqueia na leitura, `Nice=10`; o custo é o do `udt_events.sh` que já roda.
- **Arquivo de nível ruim na p8** → leitura validada (spec: Piso do brilho), cai no padrão.
- **A p8 vence o SYSTEM** → o arquivo de nível é criado pelo usuário em uso, nunca vem na imagem; a base não o atualiza e `--keep-storage` o preserva.
- **FN não remapeado (`r36-fn-original`)** → o atalho não age; o nível salvo ainda vale no boot.
- **Conflito de merge** → só o `udt_pwr_events.sh` é arquivo existente tocado, por uma linha, e nenhuma outra change da integração o edita.

## Migration Plan

Nada a migrar. Rollback: remover a feature `62-brilho-fn` e a linha do `udt_pwr_events.sh`; o arquivo de nível na p8 passa a ser ignorado e o brilho volta ao `brightness.level` do `emuelec.conf`. Para o usuário desfazer no aparelho sem regravar: `r36-brilho-original` na p1.

## Open Questions

- Em qual `/dev/input/eventN` e com qual tipo de evento o D-pad e o FN aparecem no aparelho (a descoberta por nome cobre o número; o tipo é visto no log).
