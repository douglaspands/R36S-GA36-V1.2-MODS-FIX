# Design

## Context

Motivação e escopo: veja `proposal.md`. Fatos verificados no SYSTEM da build `20261026-215833` (só leitura, com `mcopy` e `unsquashfs`):

- O módulo `udt_joystick.ko` cria o dispositivo `micro_gamepad` e expõe `fn_key`, `power_key` e `wake_lock` em `/sys/devices/platform/micro_gamepad/`. Há `fn_key_show` e `setkeycode` nas strings do módulo, então ler e trocar o código do FN é suportado.
- O `emuelecRunEmu.sh` da base traz, comentados, `echo "318" > .../fn_key` (`#BTN_THUMBR`, no ramo do `nds`) e `echo "464" > .../fn_key` (`# key_fn`, depois do jogo). O fabricante trocava o código do FN para um botão de gamepad ao abrir o Drastic e o devolvia a 464 (`KEY_FN`). Isso é a evidência de que o driver aceita um código de botão.
- `udt_events.sh` lê só `KEY_VOLUMEUP` e `KEY_VOLUMEDOWN` em `/dev/input/event1` com `evtest`; nada trata o FN.
- No `micro_gamepad.cfg` (feature 20), o Select é o botão 8 e era o hotkey (`input_enable_hotkey_btn = "8"`); o menu é `input_menu_toggle_btn = "2"` (X). A numeração segue a ordem dos códigos do evdev: Select (314) = 8, Start (315) = 9, L3 (317) = 11, R3 (318) = 12. O botão 10 não tem bind e corresponde ao `BTN_MODE` (316).
- O RetroArch tem um só botão modificador de hotkey (`input_enable_hotkey_btn`) e um só botão de menu (`input_menu_toggle_btn`).
- O autoconfig é lido de `joypad_autoconfig_dir = ~/joypads` (`/storage/joypads`, p8). O `micro_gamepad.cfg` da feature vai para lá, e um arquivo que já existe na p8 não é atualizado por gravar só o `system`.

**Primeiro teste no aparelho** (build `20261029-105539`): o `r36-fn.log` registrou `fn_key ausente` e o `/proc/bus/input/devices` não tinha `micro_gamepad`: o `udt_joystick` carrega depois do início dos serviços do `emuelec.target`. A espera de até 60 s pelo `fn_key` resolveu isso.

**Segundo teste** (build `20261029-114403`, FN como Select, 314): **o FN funcionou** no RetroArch. O usuário achou o boot um pouco lento; não foi medido. As suspeitas são a espera do `fn_key` num serviço do `emuelec.target` e, com `r36-diagnostico`, o `evtest` do `fn-registro`; a medição (Decisão 5) separa o atraso real do que é só percepção.

**Terceiro teste** (build `20261029-124925`, FN em 316): o `r36-fn.log` mostra `Event code 316 (BTN_MODE)` anunciado pelo `micro_gamepad` e um evento `code 316` por aperto do FN, então o remapeamento valeu. O `fn_key` apareceu 6 s depois do início do serviço (`uptime_inicio=11`, `uptime_fn_key=17`, `uptime_fim=17`): o serviço não atrasa o boot, e o usuário notou o boot mais rápido. Mas o `fn_key` lido, antes e depois da escrita, é `-1088990680`, sem relação com o código, então a condição `depois=316` nunca valeu, o cfg da p8 ficou com `8` e o FN não fez nada no jogo (o Select continuou hotkey). A leitura de `fn_key` não serve de prova; o evento é a prova.

Não confirmado: se o SDL numera o `BTN_MODE` (316) como botão 10 (o driver o anuncia, confirmado no terceiro teste). Antes: se o driver anuncia o `BTN_MODE` (316) entre os botões do `micro_gamepad` (sem isso o SDL ignora o evento) e se o SDL o numera como botão 10. O `r36-fn.log` existe para isso.

## Goals / Non-Goals

**Goals:**
- O FN é o único modificador dos atalhos do RetroArch: FN + botão dispara os atalhos de fábrica, e o Select passa a ser só o botão Select do jogo.
- Nenhum risco de perder o acesso ao menu: o hotkey só vai para o FN se o remapeamento valeu; senão o Select continua o hotkey.
- A chave `r36-fn-original` devolve o FN de fábrica e o hotkey ao Select.
- Medir o tempo do boot que esta feature gasta, pelo log opcional.

**Non-Goals:**
- O FN como menu de um toque só, sem outro botão (disputaria o botão com o modificador dos atalhos).
- Mexer no `emuelecRunEmu.sh`, no `udt_events.sh` ou na lógica de energia e volume.
- Dar ao FN uma função no EmulationStation: ele fica reservado ali para funções futuras (por exemplo o controle de brilho da tela), e não precisa imitar o Select (Decisão 7).

## Decisions

### 1. O FN emite `BTN_MODE` (316) e vira o hotkey

O RetroArch só aceita um modificador de hotkey. Na primeira etapa o FN emitia o código do Select (314), e os dois eram o mesmo botão 8. Para o Select deixar de ser hotkey, o FN precisa de um botão próprio: o `fn-remapeia` grava `316` (`BTN_MODE`) em `fn_key`, e o `micro_gamepad.cfg` passa `input_enable_hotkey_btn` para o botão 10, o que a numeração do autoconfig indica para o 316. O `input_select_btn` continua 8: o Select chega ao jogo como Select.

Alternativas: (a) um serviço que lê o evento do FN e injeta teclas é mais código e mais latência; (b) outro código livre de gamepad: o 316 é o que sobra entre os binds atuais e o que o fabricante já tratava como botão (o ramo do `nds` usa 318, que é o R3, já em uso). Se o `r36-fn.log` mostrar que o driver não anuncia o 316, ou que o botão não é o 10, o número e o código são ajustados antes de gravar.

### 2. Um serviço oneshot no boot, na feature 20

`fn-remapeia` roda no `emuelec.target`, como os `r36-audio*`. O FN é parte do controle embutido, então fica na feature 20 (`20-controle-posicional`), onde está o autoconfig do `micro_gamepad`.

O script espera a p1 montar por até 20 s (padrão do `audio-prepara`, sem ordenar o unit depois do autostart, porque isso travaria o boot, como diz o CLAUDE.md) para ler a chave `r36-fn-original`. Passados os 20 s sem p1, grava o código mesmo assim: o padrão é o FN ligado.

O `fn_key` só existe depois que o `udt_joystick` carrega, depois do início do serviço. O script espera o `fn_key` aparecer por até 60 s (`R36_FN_ESPERA_FN` nos testes), a cada segundo, e só então espera a p1 (até 20 s) e lê a chave. Com o `fn_key` presente, lê o valor antes, escreve o código, lê depois e deixa os valores para o log. Se o `fn_key` não aparecer em 60 s, sai com 0 sem erro e grava `modo=sem-fn_key` em `/run/r36-fn.estado`. O unit tem `TimeoutStartSec=120` e continua sem `After`/`Before` do autostart ou do ES, então a espera não segura o boot.

### 3. O hotkey do autoconfig acompanha o resultado do remapeamento

O `micro_gamepad.cfg` está na p8 e um arquivo estático não obedece à chave `r36-fn-original` nem ao caso em que o `fn_key` não aparece. O `fn-remapeia` por isso também escreve `input_enable_hotkey_btn` no `/storage/joypads/micro_gamepad.cfg` da p8, no fim do serviço, com `sed` só nessa linha:

- `modo=remapeado` e a escrita do 316 em `fn_key` com código de saída 0: `input_enable_hotkey_btn = "10"`. A decisão não usa a leitura de volta do `fn_key`: no aparelho ela devolve um valor sem relação com o código (terceiro teste), enquanto o evento 316 chega.
- `modo=original`, `modo=sem-fn_key` ou escrita recusada: `input_enable_hotkey_btn = "8"`. O Select volta a ser o hotkey e o acesso ao menu não depende do FN.

O arquivo da feature (`features/20-controle-posicional/storage/joypads/micro_gamepad.cfg`) traz `8`, o valor seguro: um cartão em que o serviço não roda continua com o Select como hotkey. Sem o arquivo na p8, o script não cria nada. O RetroArch lê o autoconfig ao abrir o jogo; o serviço termina no máximo cerca de 80 s depois do início do boot, antes de o usuário abrir um jogo. 

Alternativa: gravar `10` direto no arquivo da feature, o que exigiria gravar a p8 a cada mudança, não obedeceria a `r36-fn-original` e deixaria o aparelho sem menu se o FN falhar.

### 4. Estado em `/run`, sem log na p1

O `fn-remapeia` grava em `/run/r36-fn.estado` o `fn_key` antes e depois (só registro) e o uptime (de `/proc/uptime`) no início, quando o `fn_key` apareceu e no fim. Um `fn_key` que aparece em poucos segundos descartou o serviço como causa do boot lento (terceiro teste: `uptime_inicio=11`, `uptime_fn_key=17`). Um log de diagnóstico na p1 (`r36-fn.log`, sob `r36-diagnostico`, com `evtest` em cada `/dev/input/event*`) serviu aos três testes no aparelho e foi removido ao fim da change, junto do `fn-registro` e do seu unit.

### 5. (removida) Medição do boot

Feita com o estado da Decisão 4; a ordem do unit não mudou.

### 6. Chave `r36-fn-original` para desfazer

Mesmo padrão das outras chaves do projeto. Sem escrita no `fn_key`, o valor de fábrica (464) vale e o hotkey do cfg volta a 8 (Decisão 3): o FN deixa de chegar ao RetroArch e o Select é o hotkey, como na base.

### 7. FN reservado no EmulationStation

No `es_input.cfg` do SYSTEM, o `micro_gamepad` liga `select` e `hotkeyenable` só ao botão 8; o botão 10 (o 316) não tem bind. Com o FN em 316, ele não faz nada no ES, e isso é o desejado: o FN fica livre para funções futuras, como o controle de brilho da tela, sem herdar o comportamento do Select. Esta change não cria bind do botão 10 no ES e não mexe no `es_input.cfg`. Uma change futura que dê função ao FN no ES (por exemplo FN + direcional para o brilho) trata do `es_input.cfg` ou de um serviço próprio.

## Risks / Trade-offs

- [O FN do clone não está ligado ao driver] → verificado: o FN funcionou no segundo teste.
- [O driver não anuncia o 316, ou o SDL não o numera como 10] → o FN não aciona o hotkey e, como o cfg da p8 é gravado a partir do sucesso da escrita no driver, e não do botão que o SDL vê, o hotkey iria para um botão que não chega. O `r36-fn.log` (cabeçalho do `evtest`) e a tela de remap do RetroArch mostram isso no teste; sem o menu, a chave `r36-fn-original` na p1 devolve o Select como hotkey, e o código e o número são ajustados antes de arquivar.
- [O `fn_key` não aparece em 60 s] → o serviço sai com 0, o FN fica em 464, o hotkey fica em 8 e o log mostra `modo=sem-fn_key`; o Select abre o menu como na base.
- [O cfg da p8 não existe ou não é gravável] → o script não cria o arquivo e termina com 0; o hotkey fica como estiver, e o arquivo da feature traz 8.
- [Select físico livre no jogo] → Select + X deixa de abrir o menu: o Select chega ao jogo. É a intenção; o usuário passa a usar FN + X.
- [Um jogo ou script futuro escreve outro valor em `fn_key`, como o ramo comentado do `nds`] → hoje essas linhas estão comentadas; o CLAUDE.md registra o fato.
- [O FN muda de função no EmulationStation] → intencional (Decisão 7): na primeira etapa o FN agia como Select nos menus; com o 316 o ES não tem bind para ele, então o FN não faz nada ali e o Select continua servindo. Conferir no teste.
- [Boot lento] → a Decisão 5 mede; sem o dado, não há causa confirmada.

## Migration Plan

1. Implementar o código novo, o ajuste do cfg, o uptime no estado e os testes; gerar o build.
2. Gravar o cartão (só o `system` basta: o cfg da p8 é ajustado pelo serviço), testar no aparelho: FN + X abre o menu, FN + R salva estado, Select + X não abre o menu e o jogo recebe o Select.
3. Se o FN não funcionar como hotkey, criar `r36-fn-original` na p1 (o Select volta a ser o hotkey).
4. Decidir o que fazer com o boot lento a partir dos uptimes, em tarefa própria.

## Open Questions

- O `BTN_MODE` (316) é anunciado pelo driver e numerado como botão 10 pelo SDL? Respondida pelo teste no aparelho (o FN abre o menu).
- Quanto do atraso do boot é a espera do `fn_key`? Respondida pelos uptimes do estado.
