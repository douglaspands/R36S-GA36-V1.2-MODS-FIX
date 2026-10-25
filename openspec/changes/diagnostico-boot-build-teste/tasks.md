# Tasks

## 1. Features só de teste no build

- [ ] 1.1 Em `tools/r36img/features.py`, aceitar `test_only` no `feature.toml` (booleano, padrão `false`, valor inválido falha indicando a feature) e guardar no `Feature`. Verificar com testes novos em `tests/` para o padrão, `true` e um valor inválido.
- [ ] 1.2 Estender `features.select` com `test`: o padrão exclui as `test_only` quando `test` é falso, e `names` com uma feature `test_only` sem `test` falha com mensagem que pede `--test`. No `build.py`, passar `test` para a seleção e trocar a ajuda do `--test` ("o conteúdo não muda" deixa de valer). Verificar com testes de seleção: build normal sem a feature de teste, build de teste com ela, `--features` sem `--test` falhando.
- [ ] 1.3 Documentar `test_only` e o novo efeito de `--test` no `README.md` (seção de build e de features). Verificar com `uv run python -I -m unittest discover -s tests`.

## 2. Log do boot no cartão (`91-boot-log-cartao`)

- [ ] 2.1 Criar `features/91-boot-log-cartao/feature.toml` (`order = 91`, `enabled = true`, `test_only = true`) e o script `system/usr/lib/r36/boot-log-cartao` (`0755`): 36 ciclos de 5 s, retrato com data, uptime, `systemctl list-jobs`, `systemctl --failed`, `journalctl -b` e `dmesg`, cada comando com `timeout 5`; destino `/storage/roms/r36-boot-log/` ou, depois de 60 s sem a p1, `/flash/r36-boot-log/` com remount de leitura e escrita só durante a cópia; `boot-<n>.txt` gravado por `.tmp` + `mv`, mantendo os 10 mais recentes. Usar uma raiz configurável por variável de ambiente, como o `classicube-sync`, para os testes. Verificar com `sh -n` e com testes que rodam o script num diretório temporário com `systemctl`, `journalctl`, `dmesg` e `mountpoint` falsos no `PATH`: destino na p1, fallback na p7, numeração e limite de 10.
- [ ] 2.2 Criar `r36-boot-log-cartao.service` (`Type=simple`, `Nice=10`, `WantedBy=emuelec.target`, sem `After=`/`Before=` envolvendo `emuelec-autostart` ou `emustation`) e o link em `emuelec.target.wants/`. Verificar nos testes as diretivas, a ausência dessas ordens e o link.
- [ ] 2.3 Documentar a feature no `README.md`: onde ler o log no PC, o que cada seção mostra e como reconhecer uma espera circular no `systemctl list-jobs`. Verificar que o README cita `r36-boot-log/` e `test_only`.

## 3. Log do boot na tela (`90-boot-log-tela`)

- [ ] 3.1 Criar `features/90-boot-log-tela/feature.toml` (`order = 90`, `enabled = true`, `test_only = true`) e o script `system/usr/lib/r36/boot-log-tela` (`0755`), que roda `fbterm` com fonte Liberation Mono pequena executando `journalctl -b -f -n 40 -o short-monotonic --no-hostname` e, ao receber `SIGTERM`, restaura o VT (`setterm --cursor on`). Verificar com `sh -n` e com teste que confere o comando do `fbterm` e do `journalctl`.
- [ ] 3.2 Criar `r36-boot-log-tela.service` (`Type=simple`, `DefaultDependencies=no`, `After=systemd-journald.service`, `TTYPath=/dev/tty1`, `StandardInput=tty`, `WantedBy=sysinit.target`, com link em `sysinit.target.wants/`) e o drop-in `emustation.service.d/r36-boot-log-tela.conf` com `ExecStartPre=-/usr/bin/systemctl stop r36-boot-log-tela.service` (sem `--no-block`). Verificar nos testes as diretivas, o link, o `-` e a ausência de `After=`/`Before=` com `emuelec-autostart` ou `emustation`.
- [ ] 3.3 Documentar a feature no `README.md` (o que aparece na tela, quando some, limitação: mensagens do kernel antes do systemd não aparecem) e registrar no `CLAUDE.md` o fato do aparelho: kernel sem console na tela, console na serial `ttyS2`, `fbterm` disponível no SYSTEM. Verificar com a suíte de testes.

## 4. Integração

- [ ] 4.1 Rodar `./build.sh --test --fast` e conferir no `changes.txt` e no `R36-BUILD.txt` as features 90 e 91; rodar `./build.sh --fast` e conferir que nenhum arquivo delas aparece no `changes.txt`. Gravar o build de teste num arquivo com `./flash.sh --target-file` para validar a gravação sem sudo.
- [ ] 4.2 Validação no aparelho (usuário): gravar o build de teste, ligar e conferir que o journal aparece na tela e some quando o ES abre, e que `R36-ROMS/r36-boot-log/boot-1.txt` tem as quatro seções. Se o `fbterm` não abrir, registrar o erro do retrato e decidir entre ajustar ou usar a reserva com `magick` (design, decisão 3).

## Workflow follow-up

- Arquivar a change depois da validação no aparelho.
