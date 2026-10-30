# Tasks

Convenções do repositório (ver `CLAUDE.md`): testes em `tests/test_brilho_fn.py`, no estilo de `tests/test_fn.py` e `tests/test_audio.py` (`R36_ROOT` temporário, `UnitCase`, `diretivas`); escrever cada teste antes do código e vê-lo falhar. Suíte: `uv run python -I -m unittest discover -s tests`.

## 1. Descobertas na base (sem montar)

- [x] 1.1 Achar na imagem base, com `mcopy`/`unsquashfs -cat` (sem montar), quem grava o `lcdbl` no boot (autostart, scripts do SYSTEM, `get_ee_setting brightness.level`) e em que ordem frente ao `emuelec.target`. Registrar o achado na seção D5 do `design.md`. Verificar: o `design.md` cita o script e a linha, ou diz "nenhum script grava no boot" com a busca feita.
- [x] 1.2 Conferir no SYSTEM que o `evtest` existe e o formato de linha dele (`type 1 (EV_KEY), code 316 (BTN_MODE), value 1`), e como o `udt_joystick` nomeia o dispositivo em `/proc/bus/input/devices`. Verificar: o formato e o nome vão para o `design.md` (D3) e servem de fixture dos testes.

## 2. O script `brilho-aplica`

- [x] 2.1 Escrever em `tests/test_brilho_fn.py` os testes do `brilho-aplica` com `R36_ROOT` temporário (`lcdbl` falso, `r36-brilho.level`, `emuelec.conf`): sem arquivo usa o `emuelec.conf` e depois 80; arquivo válido aplica `(nível*255+50)/100`; valor vazio, texto, negativo, acima de 100 ou abaixo do piso cai no padrão; `ajusta +` e `ajusta -` andam 5 pontos e param em 10 e em 100; `salva` grava só o arquivo; `padrao` apaga o arquivo e aplica 80; `lcdbl` ausente sai com 0 sem erro; segunda rodada de `aplica` sem mudança não regrava o arquivo. Verificar: os testes existem e falham (script ainda não existe).
- [x] 2.2 Criar `features/62-brilho-fn/system/usr/lib/r36/brilho-aplica` (sh do BusyBox, 0755, comentário de cabeçalho no estilo do `audio-ganho`) e `features/62-brilho-fn/feature.toml` (`order = 62`, descrição). Verificar: `uv run python -I -m unittest tests.test_brilho_fn` passa e `sh -n` no script sai 0.

## 3. O leitor de eventos

- [x] 3.1 Escrever os testes do parser e da máquina de estado com linhas reais do `evtest` (fixture da 1.2): FN apertado + `KEY_UP`/`BTN_DPAD_UP`/`ABS_HAT0Y -1` sobe; o mesmo para descer; D-pad sem FN não age; soltar a seta para a repetição; FN + L3 (`BTN_THUMBL` ou código 317) chama `padrao` uma vez por clique, só com o FN apertado, com o D-pad como botão ou como eixo; soltar o FN no meio interrompe; `salva` chamado só ao soltar. Usar um `brilho-aplica` falso que registra as chamadas. Verificar: os testes existem e falham.
- [x] 3.2 Criar `features/62-brilho-fn/system/usr/lib/r36/brilho-leitor` (bash, 0755): acha o dispositivo `micro_gamepad` por nome, lê o `evtest`, trata as três formas de D-pad, repete a 0,2 s (padrão do `repeat_volume_ctrl`), e sai com 0 se não achar o dispositivo depois da espera (`R36_BRILHO_ESPERA` nos testes). Verificar: os testes da 3.1 passam e `bash -n` sai 0.
- [x] 3.3 Registrar em `r36-brilho.log` (p1) o dispositivo, o tipo de evento do D-pad visto e os níveis aplicados, só com `r36-diagnostico` na raiz da p1. Verificar: teste com e sem a chave (sem chave, o arquivo não existe depois de um ajuste).

## 4. Units, boot, chave e acordar

- [x] 4.1 Escrever os testes das units e do boot: `r36-brilho.service` (oneshot, sem `After=emuelec-autostart.service`, `TimeoutStartSec` com folga para os 20 s da p1), `r36-brilho-leitor.service` (simple, `Nice=10`), links em `emuelec.target.wants`; `aplica` no boot com `r36-brilho-original` descarta o nível e fica em 80; sem p1 em 20 s trata a chave como ausente (`R36_BRILHO_ESPERA_P1`). Verificar: falham primeiro.
- [x] 4.2 Criar as duas units, os links e o tratamento da chave no `brilho-aplica boot` (ou subcomando equivalente). Aplicar o ponto de ordem achado na 1.1. Verificar: os testes da 4.1 passam e `uv run python -I -m unittest tests.test_ptbr_controle` continua verde.
- [x] 4.3 (feita na integração `integra-limite-idioma-shaders-gb`: linha no `udt_pwr_events.sh`, entrada em `tests/test_audio.py` e `skip` removido) Escrever o teste do `udt_pwr_events.sh` (só lê o arquivo): contém uma única chamada ao `brilho-aplica aplica` no ramo de acordar, **depois** do `echo $scaled_value > .../lcdbl` e com guarda `[ -x ]`. Depois acrescentar a linha com o marcador `# R36:`. Verificar: o teste falha antes e passa depois, `bash -n features/46-audio/system/usr/bin/udt_pwr_events.sh` sai 0 e `git diff` do arquivo mostra só essa linha (e o comentário).
  - **Bloqueada (agente de D):** o `tests/test_audio.py::ScriptsDaBase::test_udt_pwr_events_so_acrescenta_a_reaplicacao` compara o `udt_pwr_events.sh` com a base e exige a lista **exata** de linhas acrescentadas (só as duas do `audio-ganho`); qualquer linha nova o quebra, e o `test_audio.py` é só leitura para D (matriz D2 da integração). O teste da 4.3 já está em `tests/test_brilho_fn.py` (`BrilhoAoAcordar`, com `@unittest.skip`) e foi conferido numa cópia do arquivo (falha sem a linha, passa com ela, `bash -n` 0). Para destravar, a integração aplica as duas mudanças juntas e tira o `skip`:
    - `features/46-audio/system/usr/bin/udt_pwr_events.sh`, logo depois da l.37 (`echo $scaled_value  > /sys/devices/virtual/disp/disp/attr/lcdbl`), com a mesma indentação (3 tabs): `[ -x /usr/lib/r36/brilho-aplica ] && /usr/lib/r36/brilho-aplica aplica  # R36: brilho salvo (feature 62)`
    - `tests/test_audio.py`, na lista de `acrescentadas` do `test_udt_pwr_events_so_acrescenta_a_reaplicacao`, antes das duas linhas do `audio-ganho`: `"[ -x /usr/lib/r36/brilho-aplica ] && /usr/lib/r36/brilho-aplica aplica  # R36: brilho salvo (feature 62)",`
    - Até lá, ao acordar o brilho volta ao `brightness.level` do `emuelec.conf` (80), não ao nível salvo; o boot e o atalho não dependem disso.
- [x] 4.4 Conferir que nenhum teste existente foi quebrado e que o FN segue sem função no ES: `uv run python -I -m unittest tests.test_fn tests.test_audio` e a suíte completa. Verificar: tudo `OK`; `git diff --name-only main...HEAD` só tem caminhos do write-set (feature 62, `udt_pwr_events.sh`, `tests/test_brilho_fn.py`, esta change).

- [x] 4.5 Revisão independente: `Restart=always` e `RestartSec=5` no `r36-brilho-leitor.service` (teste das units), teste de que `ajusta` repetido não escreve o `r36-brilho.log` mesmo com `r36-diagnostico`. O ramo `mountpoint -q` do `p1_montada` só roda com `R36_ROOT` vazio, que exigiria o `lcdbl` real: não testado, para não fragilizar o teste.

## 5. Spec, documentação e portões

- [x] 5.1 Escrever `docs-brilho-fn-direcional.md` nesta pasta, com os trechos prontos para `README.md` (atalho, passo, piso, reset por FN + L3 e por `r36-brilho-original`, lista de logs sob chave com o `r36-brilho.log`) e para `CLAUDE.md` (fatos do aparelho: `lcdbl`, arquivo de nível na p8 e por que não o `emuelec.conf`, o D-pad no `micro_gamepad`, a chamada em `udt_pwr_events.sh`). Verificar: o arquivo tem um bloco por documento com a seção onde entra.
- [x] 5.2 Portões: `uv run python -I -m unittest discover -s tests` verde, `openspec validate brilho-fn-direcional --strict` sem erro, `sh -n`/`bash -n` nos scripts, permissões (0755 nos executáveis, 0644 nos demais). Verificar: a saída de cada comando colada no relatório.

## 6. Conferência no aparelho (instruções para o usuário, fora do alcance do agente)

- [x] 6.1 Entregar ao usuário a lista de testes: FN + ↑/↓ sobe e desce em jogo e no ES; segurar repete; o brilho persiste ao reiniciar e ao dormir e acordar; FN + clique do L3 volta a 80; `r36-brilho-original` na p1 volta a 80 no boot; ↑/↓ sem o FN seguem normais; FN sozinho no ES não faz nada. Com `r36-diagnostico` na p1, enviar o `r36-brilho.log` para confirmar o tipo de evento do D-pad e o código que o L3 emite (`BTN_THUMBL`/317 é hipótese). Reduzir o brilho, abrir um jogo, sair e conferir se o nível se mantém (o `emuelecRunEmu.sh` copia o `brightness.level` para o `screen_brightness`). Verificar: lista copiável entregue no relatório da integração.

## Workflow follow-up

- Depois dos testes no aparelho, a change é arquivada dentro da integração (`/opsx:archive`, depois de A, C e B), com `/opsx:sync` um por vez.
