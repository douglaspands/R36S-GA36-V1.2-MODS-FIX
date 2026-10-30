# Tasks

Os prompts dos agentes e do revisor estão em `orquestracao.md`; as regras (write-set, portões, ordem de merge) estão no `design.md`.

## 1. Preparar o terreno

- [x] 1.1 Rodar a suíte completa na `main` antes de qualquer coisa (`uv run python -I -m unittest discover -s tests`): precisa estar verde, para que toda falha futura seja atribuível a uma change. Verificar pela saída `OK`.
- [x] 1.2 Commitar a pasta de cada change, só ela, na branch com o nome da change criada a partir da `main` (`limita-consumo-e-miniaturas-savestate`, `retroarch-idioma-do-emuelec`, `shaders-gb-gbc-r36s`, `brilho-fn-direcional`), e voltar à `main`. Verificar com `git ls-tree -r --name-only <branch> openspec/changes/<change>` listando os artefatos de cada uma e `git status --short` na `main` sem as quatro pastas (esta change segue não versionada até o passo 4).

## 2. Fase paralela (um agente por change, worktree isolado)

- [x] 2.1 Disparar **na mesma mensagem** os quatro agentes de `orquestracao.md` (A, B, C, D) com `isolation: "worktree"` e `model: "opus"`, cada um com preâmbulo comum + prompt próprio. Verificar: quatro agentes em execução e, ao fim, quatro relatórios com a saída dos portões.
- [x] 2.2 Receber o relatório de A e conferir na branch: suíte verde, `openspec validate limita-consumo-e-miniaturas-savestate --strict`, tasks 1.x a 3.x marcadas. Verificar com os comandos rodados por mim no worktree, sem confiar só no relatório.
- [x] 2.3 Idem para B (padrão `en_US` refletido em proposal, design, specs, tasks e testes; `idioma-aplica` 0755) e para C (task 3.3 reescrita com a decisão; shaders 0644; pranchas geradas). Verificar com `grep -rn "pt_BR" openspec/changes/retroarch-idioma-do-emuelec` conferindo que "padrão pt_BR" não sobrou, e `grep -n "3.3" openspec/changes/shaders-gb-gbc-r36s/tasks.md`.
- [x] 2.3b Idem para D (`brilho-fn-direcional`): tasks dos grupos 1 a 5 marcadas, suíte verde, `openspec validate brilho-fn-direcional --strict`, `brilho-aplica` e `brilho-leitor` 0755, `git diff main...brilho-fn-direcional -- features/46-audio` com **uma** linha de código nova (a chamada do `brilho-aplica`), e o achado da task 1.1 de D registrado no `design.md` dela. Verificar com os comandos rodados por mim no worktree. **Parcial (verificado em D: suíte 590 OK, validate, 0755, achado no `design.md`; reset por FN + L3 por decisão do usuário):** a linha do `udt_pwr_events.sh` e a entrada dela em `tests/test_audio.py` foram adiadas para a integração (task 4.1b), porque `test_audio.py` é só leitura para D; marcar esta task depois dela.
- [x] 2.4 Conferir o write-set de cada branch: `git diff --name-only main...<branch>` contra a matriz D2 do `design.md`. Verificar: nenhum caminho fora da matriz; `README.md` e `CLAUDE.md` intocados. Qualquer desvio volta ao agente (`SendMessage`) antes de seguir.

## 3. Revisão independente

- [x] 3.1 Disparar quatro revisores novos (um por branch, prompt do revisor em `orquestracao.md`), em paralelo. Verificar: quatro listas de achados com arquivo:linha.
- [x] 3.2 Mandar os achados ao implementador correspondente (`SendMessage`), repetir portões e revisão até zero achado aberto. Verificar: relatório final de cada revisor sem achado e suíte verde em cada branch.

## 3b. Fase paralela 2: E e F com modelo Flash 3.8

- [x] 3b.1 Criar branches `emuelec-localizacao-ui` (E) e `tema-epic-cody-ml` (F) a partir da `main`, commitar os artefatos de cada change e disparar os sub-agentes com o modelo **Flash 3.8** (`Model: "flash"`), em paralelo via `invoke_subagent`. Verificar: ambos os agentes em execução simultânea.
- [x] 3b.2 Receber relatórios de E e F: suíte verde, `openspec validate <change> --strict`, conferência do write-set (D2) via `git diff --name-only main...<branch>`.
- [x] 3b.3 Revisão independente de E e F e ajustes pontuais até zero achados.
- [x] 3b.4 Fazer o merge `--no-ff` de E e F na branch de integração `integra-limite-idioma-shaders-gb`.

## 4. Integração

- [x] 4.1 Criar a branch `integra-limite-idioma-shaders-gb` a partir da `main`, commitar nela a pasta desta change e fazer o merge `--no-ff` na ordem A, C, B, D. Verificar com `git log --oneline --graph -16` mostrando os quatro merges e `git status` limpo; conflito fora da zona do D2 → parar e relatar.
- [x] 4.2 Recalcular a contagem de linhas novas do `emuelecRunEmu.sh` em `tests/test_ptbr_controle.py` (soma de A e B) e conferir que a ordem da chamada do `idioma-aplica` continua antes do `eval ${RUNTHIS}`. Verificar com `uv run python -I -m unittest tests.test_ptbr_controle` e `bash -n features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`.
- [x] 4.3 Consolidar `README.md` e `CLAUDE.md` a partir dos quatro `docs-*.md` (FN + ↑/↓ muda o brilho, passo, piso, reset por FN + ↑ + ↓ e por `r36-brilho-original`, `r36-brilho.log` na lista de logs sob chave, o `lcdbl` e o arquivo de nível na p8; padrão `en_US` do `--idioma` no topo da seção do build, `r36-idioma` e `r36-idioma.log` na lista de logs sob chave, shaders de GB/GBC ligados por padrão e as chaves `r36-gb-sem-shader`/`r36-gbc-sem-shader`, savestates sem subpasta de core, `sort_savestates_enable`, serviços removidos) e apagar os quatro `docs-*.md`. Verificar com `grep -n "r36-idioma\|\-\-idioma\|r36-gb-sem-shader\|sort_savestates\|r36-brilho" README.md CLAUDE.md` e `ls openspec/changes/*/docs-*.md` sem resultado.
- [x] 4.4 Escrever em `tests/test_integracao_3_changes.py` o teste de interação: sobre um mesmo `R36_ROOT` temporário com `retroarch.cfg` e p8 de fábrica, rodar em sequência `retroarch-prepara`, `shaderset-aplica`, `idioma-aplica`, `shader-gba-prepara`, `shader-gb-gbc-prepara` e `brilho-aplica aplica`, duas vezes, e conferir que o resultado é o esperado e idempotente (chaves de A, `user_language` de B, presets de GBA e de GB/GBC sem colisão, `lcdbl` e `r36-brilho.level` de D sem tocar no `retroarch.cfg`, nenhuma escrita na segunda rodada). Verificar com `uv run python -I -m unittest tests.test_integracao_3_changes`.
- [x] 4.5 Rodar a suíte completa e `openspec validate` (`--strict`) de todas as changes (A a F) e desta integração. Verificar: tudo `OK`/válido.

## 5. Build único e inspeção sem montar

- [x] 5.1 Gerar `./build.sh --idioma pt_BR`. Verificar: imagem `*_pt-br_build_<timestamp>.img.xz`, `manifest.json` com `"language"` `pt_BR` e `R36-BUILD.txt` com `idioma:`.
- [x] 5.2 Inspecionar a imagem do build sem montar (`mcopy`, `unsquashfs -cat/-lls` no `parts/system.img` e `parts/storage.img`): (A) links de `systemd-timesyncd*` e `pulseaudio` ausentes e units presentes, `emuelec.conf` com as chaves `=0`, `retroarch.cfg` com `sort_savestates_enable = "false"`, drivers `null` e menus ocultos, RunEmu com `mkdir -p` e guarda do netplay; (B) `system.language`, `Language` e `user_language` em português do Brasil e a chamada do `idioma-aplica` antes do `eval`; (C) `gb-modern-dmg.*`, `gbc-modern-remaster.*`, `shader-gb-gbc-prepara` e o serviço, com dono `0:0` e permissões certas; (D) `brilho-aplica` e `brilho-leitor` 0755, as duas units e os links em `emuelec.target.wants`, e a chamada do `brilho-aplica` no `udt_pwr_events.sh`, depois do restore do `lcdbl`; (E) arquivos `.mo` e `.po` de `pt_BR` e `es_MX` presentes em `usr/config/emuelec/configs/locale/` com dono `0:0`; (F) tema `Epic Cody ML` presente em `.config/emulationstation/themes/`, tema original removido e `ThemeSet = "Epic Cody ML"` em `es_settings.cfg`.
- [x] 5.3 Gerar `./build.sh --idioma en_US --test` e conferir que o nome tem `en-us`, que as três chaves de idioma estão em inglês e que o `-test` não substitui o build principal. Verificar com `ls` do diretório de saída e `unsquashfs -cat`.
- [x] 5.4 Validar a gravação sem root: `./flash.sh --target-file work/alvo-teste.img --all --wipe-roms --wipe-storage --build <timestamp>` do build principal (o arquivo precisa existir; o `--help` mostra o exemplo). Verificar: verificação pós-gravação sem erro.
- [x] 5.5 Copiar as pranchas de `var/exemplos-gb-gbc/` do worktree de C para o `var/` da árvore principal. Verificar com `ls var/exemplos-gb-gbc`.

## 6. Conferência no aparelho (instruções para o usuário)

- [x] 6.1 Entregar ao usuário o comando de gravação, no zsh e fora do agente: `./flash.sh --device /dev/sdc --all --keep-roms --wipe-storage --build 20261029-174922` (decisão do usuário: a p1 com as ROMs nunca é apagada; a p8 pode ser, o que faz as chaves novas do `emuelec.conf` de A, o idioma, o brilho e o tema entrarem de fábrica; os saves da p8 se perdem, então lembrar o backup em `/mnt/backup/games/r36-storage/` antes; confirmar a letra do dispositivo com `lsblk -o NAME,SIZE,LABEL,FSTYPE,MOUNTPOINT`). Rodar antes `--dry-run` para ver o plano. Só se o usuário mudar de ideia: `--part system` e `--keep-storage` preservam os saves, mas a p8 vence o SYSTEM e as chaves do `emuelec.conf` não chegam. Verificar: comando copiável, um por linha.
- [x] 6.2 Lista de testes para o usuário (A): abrir um jogo, criar um save state pelo RetroArch e ver a miniatura no Save State Manager do ES; conferir que `/storage/roms/savestates/<sistema>/` não tem subpasta de core; menu do RetroArch sem Rewind/Netplay/Streaming/Gravação.
- [x] 6.3 Idem (B): trocar o idioma do EmuELEC para English e abrir um jogo (menu do RetroArch em inglês), voltar a português e conferir; trocar pelo menu do RetroArch e abrir outro jogo sem mexer no EmuELEC. Registrar na `design.md` de B qual chave o ES grava (task 1.1 de B).
- [x] 6.4 Idem (C): abrir um jogo de GB e outro de GBC e ver os shaders ligados (comparar com as pranchas); medir fluidez; conferir "SHADER SET" no ES; testar `r36-gb-sem-shader` e `r36-gbc-sem-shader`. Se o usuário mudar de ideia sobre o padrão, abrir uma change pequena.
- [x] 6.5 Idem (D): FN + ↑ e FN + ↓ em jogo e no ES (sobe e desce; segurar repete); o brilho persiste ao reiniciar e ao dormir e acordar; FN + ↑ + ↓ volta a 80; `r36-brilho-original` na p1 volta a 80 no boot; ↑/↓ sem o FN seguem normais; o FN sozinho no ES não faz nada; o brilho do RetroArch em jogo (limite conhecido do `screen_brightness`). Com `r36-diagnostico`, enviar o `r36-brilho.log` (tipo de evento do D-pad). Verificar: lista copiável entregue no relatório.
- [x] 6.6 Aviso ao usuário: para os logs de diagnóstico (`r36-idioma.log`, `r36-shader-gb-gbc.log`, `r36-brilho.log`), criar `r36-diagnostico` na raiz da p1 e religar antes de reproduzir.
- [x] 6.7 Idem (E - Localização UI): navegar pelos menus e scrapers em português e espanhol; validar ausência de textos em inglês nas opções secundárias; conferir que termos técnicos (*Save State*, *Core*, *Shader*, *Scraper*) permanecem em inglês em pt_BR.
- [x] 6.8 Idem (F - Tema Epic Cody ML): verificar que o tema padrão sobe em português; testar alteração para Espanhol Latino e Inglês no menu de opções do tema; validar legibilidade e ausência de textos cortados na tela de 3.5".

## Workflow follow-up

- Depois dos testes no aparelho: o usuário decide o merge na `main` (sem push sem pedido) e o arquivamento na ordem A, C, B, D, integração (`/opsx:archive`), com `/opsx:sync` um por vez porque A e C alteram specs de capabilities vizinhas.
- Worktrees e branches dos agentes podem ser removidos depois do merge.
