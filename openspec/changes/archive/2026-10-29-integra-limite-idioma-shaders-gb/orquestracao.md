# Orquestração

Quem executa: a sessão principal (orquestrador), no `/opsx:apply` desta change. Sub-agentes em segundo plano, um por change, disparados em paralelo (`isolation: "worktree"` ou branch de trabalho). Changes A, B, C, D implementadas na fase 1; changes E (`emuelec-localizacao-ui`) e F (`tema-epic-cody-ml`) implementadas em paralelo na fase 2 com o modelo **Flash 3.8**. Cada prompt é autocontido.

```
main ── commit das changes nas branches A, B, C, D, E, F
  |
  +-- worktree A --+
  +-- worktree B --+
  +-- worktree C --+-- Fase 1 (A, B, C, D): implementadas e testadas
  +-- worktree D --+
  +-- subagente E -+-- Fase 2 (E, F): modelo Flash 3.8 em paralelo
  +-- subagente F -+
        |
        v  relatórios + docs-<change>.md
  revisão independente por branch --> correções
        |
        v
  branch integra-limite-idioma-shaders-gb: merge A, C, B, D, E, F
        |
        v
  suíte + validate --> ./build.sh --idioma pt_BR --> inspeção sem montar --> usuário
```

## Preâmbulo comum (vai no início dos quatro prompts)

> Você implementa UMA change OpenSpec do projeto R36S (A, B, C ou D, conforme o prompt), em um worktree isolado. Leia primeiro o `CLAUDE.md` da raiz e siga-o à risca: sem `sudo`; Python só com `uv run`; um comando de shell por chamada, caminhos relativos à raiz, sem `cd` e sem `&&`/`;`; lógica longa num script temporário em `$CLAUDE_JOB_DIR/tmp`.
> 1. Renomeie a branch do worktree para o nome da change: `git branch -m <change>`. Confirme que `openspec/changes/<change>/` existe; se não existir, pare e relate.
> 2. Crie `base` como symlink para `base/` da árvore principal (`ln -s <raiz-principal>/base base`); nunca escreva na imagem base.
> 3. Leia `proposal.md`, `design.md`, `tasks.md` e os specs da sua change, e os arquivos de `features/` e `tests/` que ela cita. Não confie em nenhum resumo: o código manda.
> 4. Escreva só dentro do seu write-set (matriz D2 do `design.md` de `openspec/changes/integra-limite-idioma-shaders-gb/`). Precisou de outro arquivo? Pare e relate; não edite. **Não edite `README.md` nem `CLAUDE.md`**: escreva os trechos prontos em `openspec/changes/<change>/docs-<change>.md` (um bloco por arquivo, com a seção onde entram).
> 5. Para cada task: escreva o teste antes do código, veja-o falhar, implemente, veja-o passar, rode a verificação descrita na task e só então marque `[x]`. Siga o estilo do código vizinho (comentários, nomes, idioma pt-BR, marcador `# R36:` nos trechos que entram em arquivo da base).
> 6. Não faça build de imagem completo (`./build.sh` sem `--test` é da integração), não grave cartão, não faça push nem merge. Faça commits pequenos na sua branch, um por grupo de tasks, mensagem em pt-BR.
> 7. Antes de relatar, rode e cole a saída final de: `uv run python -I -m unittest discover -s tests`, `openspec validate <change> --strict`, `sh -n`/`bash -n` nos scripts tocados, `git diff --name-only main...HEAD` (todos os caminhos dentro do write-set). Se algo falhar, conserte; se não der, diga qual teste, a saída e por quê.
> 8. Relatório final (curto): branch, commits, tasks feitas e não feitas (e por quê), saída dos portões, pontos que dependem do aparelho, riscos que você viu.

## Prompt A: `limita-consumo-e-miniaturas-savestate`

> Preâmbulo comum. Change: `limita-consumo-e-miniaturas-savestate`. Faça os grupos 1, 2 e 3 do `tasks.md`.
> Cuidados específicos:
> - `emuelecRunEmu.sh`: mexa **só** nos trechos de savestate (`mkdir`, parser de `-autosave`/`-state_slot`/`-state_file`) e na guarda do bloco de netplay. Outra change adicionará uma chamada do `idioma-aplica` perto da linha do `shaderset-aplica`: não toque ali.
> - `tests/test_ptbr_controle.py`: acrescente seus testes no fim do arquivo; a contagem de linhas novas do RunEmu (teste de diff contra a base) ajuste para a sua change isolada e anote o número e o diff no relatório; a integração recalcula.
> - Valide o parser com casos reais da ordem que o ES envia (`-autosave 1 -state_slot N`, `-autosave 1` sozinho, sem nenhum, com `--` e com `-state_file`) executando o trecho em `bash`, não só lendo.
> - Desempenho: a guarda do netplay precisa eliminar as 3 escritas `sed -Ei` por partida normal (mostre num teste que `set_ee_setting` não é chamado). Confira que as units removidas do systemd continuam existindo (só os links saem).
> - Migração de savestates no `retroarch-prepara`: idempotente, sem sobrescrever, sem erro com a p1 desmontada, com nomes com espaço e acentos. Teste com `R36_ROOT` temporário, inclusive um segundo run sem mudança.
> - Confirme que os `retroarch.cfg` da feature 10 e o `retroarch-prepara` dizem a mesma coisa para cada chave nova.

## Prompt B: `retroarch-idioma-do-emuelec`

> Preâmbulo comum. Change: `retroarch-idioma-do-emuelec`. Faça os grupos 2 e 3 do `tasks.md`; do grupo 1, faça a 1.2 (strings do binário no SYSTEM da imagem base, sem montar) e deixe a 1.1 (aparelho) como instrução para o usuário. Pule 4.2 e 5.x (build da integração e aparelho).
> **Decisão do usuário que sobrescreve a change:** o padrão do `--idioma` é **`en_US`** (e não `pt_BR`). Primeiro, atualize `proposal.md`, `design.md` (D3, D6, D7), os specs `build-language` e `image-build` e o `tasks.md` da sua change para refletir isso (um `./build.sh` sem argumento gera imagem em inglês, com `en-us` no nome; `--idioma pt_BR` gera português), rode `openspec validate retroarch-idioma-do-emuelec --strict` e só então implemente. Os arquivos das features no repositório continuam em `pt_BR`: o build é quem troca as três chaves nas cópias em `work/`.
> Cuidados específicos:
> - A chamada do `idioma-aplica` no `emuelecRunEmu.sh` é **uma só**, ao lado da do `shaderset-aplica`, protegida por `[ -x ]`. Mexa nada além disso. Em `tests/test_ptbr_controle.py` ajuste só a contagem de linhas novas (e a ordem) para a sua change isolada e anote o número e o diff no relatório.
> - `idioma-aplica`: `sh` do BusyBox, sai com 0 em qualquer caso, idempotente, e não escreve no SD quando o idioma não mudou (custo por jogo: no máximo duas leituras e nenhum `sed` no caminho comum). Teste com `R36_ROOT` temporário todos os cenários da spec, incluindo `retroarch.cfg` ausente e idioma fora da tabela.
> - Build: `--idioma` não pode alterar `features/` (confira `git status`), falha com erro claro para código inválido, para `--no-features` e para chave inexistente na cópia. Testes cobrem o padrão `en_US` e `--idioma pt_BR`, o nome `<prefixo>_<idioma>_build_<timestamp>[-test].img.xz`, o manifest e o `R36-BUILD.txt`. Para o build de teste dos testes use `--test`/`--fast` conforme os testes existentes, em `work/` do seu worktree.
> - O `retroarch.cfg` de entrada do build será o da feature 10 depois do merge com a change A (que mexe em outras chaves): não presuma nada além de `user_language` existir uma vez.

## Prompt C: `shaders-gb-gbc-r36s`

> Preâmbulo comum. Change: `shaders-gb-gbc-r36s`. Faça os grupos 1, 2 e 3 do `tasks.md`; pule 4.1/4.2 (build da integração).
> **Decisão do usuário que resolve a task 3.3:** os shaders `gb-modern-dmg` e `gbc-modern-remaster` ficam **ligados por padrão** no boot (`gb.shaderset`/`gbc.shaderset` e presets `<Core>/gb.glslp` e `<Core>/gbc.glslp`, chaves `r36-gb-sem-shader` e `r36-gbc-sem-shader`), como o GBA na feature 54. Reescreva a 3.3 no `tasks.md` (apresentar as pranchas em `var/exemplos-gb-gbc/` ao usuário depois dos testes, sem perguntar o padrão), ajuste `proposal.md`/`design.md`/specs se citarem a decisão em aberto, e rode `openspec validate shaders-gb-gbc-r36s --strict`.
> Cuidados específicos:
> - Leia a feature `54-shaders-gba` e seu serviço antes de escrever o `shader-gb-gbc-prepara`; reaproveite o padrão (mesmo inode, bind de `/tmp/shaders`, chaves, log sob `r36-diagnostico`). Os presets `<Core>/gb.glslp` e `<Core>/gbc.glslp` não podem colidir com `mGBA.glslp` do GBA nem com o `r36-shader-gba-prepara`, que apaga presets que referenciam shader antigo dele: teste os dois serviços sobre o mesmo `R36_ROOT`.
> - Ordem dos presets automáticos do RetroArch (jogo, pasta do conteúdo, core): o preset por pasta de conteúdo `<core>/gb.glslp` precisa vencer o do core quando o Gambatte serve GB e GBC. Confira o `CLAUDE.md` ("Ordem dos presets automáticos").
> - Os `.opt` do Gambatte não podem sobrescrever escolha existente do usuário; teste com `gb.opt` e `gbc.opt` já existentes.
> - Desempenho na Mali-400 é critério de aceite: passe único, uma leitura de textura, `mediump`, sem `pow()` e sem laços, e o teste confere isso por análise do GLSL. Calibre com a réplica numérica e as capturas do `~/AppImages/retroarch.appimage` com as ROMs de `/mnt/backup/PC/R36S/roms/{gb,gbc}`; todas as métricas da spec precisam passar. Se alguma ROM ou o AppImage faltar, relate sem inventar números.
> - As pranchas ficam em `var/exemplos-gb-gbc/` do SEU worktree (ignorado pelo git); informe o caminho no relatório para a integração copiar para `var/` da árvore principal.

## Prompt D: `brilho-fn-direcional`

> Preâmbulo comum. Change: `brilho-fn-direcional`. Faça os grupos 1 a 5 do `tasks.md`; o grupo 6 (aparelho) é instrução para o usuário.
> Cuidados específicos:
> - Write-set: `features/62-brilho-fn/**`, `tests/test_brilho_fn.py`, a pasta da sua change e **uma** linha em `features/46-audio/system/usr/bin/udt_pwr_events.sh` (a chamada do `brilho-aplica` depois do restore do `lcdbl`, no ramo de acordar, com guarda `[ -x ]` e marcador `# R36:`). **Não toque** no `emuelecRunEmu.sh` (nem no `screen_brightness`, l.67-70), que é de outras changes; `tests/test_fn.py` e `tests/test_audio.py` são só leitura. Se achar que precisa de outro arquivo, pare e relate.
> - Task 1.1: ache na imagem base (`base/`, sem montar: `mcopy`, `unsquashfs -cat/-lls`) quem grava o `lcdbl` no boot e decida a ordem do `r36-brilho.service` com isso. Nunca use `After=emuelec-autostart.service` com `Before=emustation.service` (trava o boot, ver `CLAUDE.md`).
> - Parser do leitor: alimente com linhas reais do formato do `evtest` (`type 1 (EV_KEY), code 316 (BTN_MODE), value 1`, `ABS_HAT0Y` com −1/0/1, `KEY_UP`, `BTN_DPAD_UP`), executando em `bash`, não só lendo. A repetição e o `kill` ao soltar seguem o `repeat_volume_ctrl` do `udt_events.sh`. O arquivo de nível só é gravado ao soltar a seta; `lcdbl` a cada passo.
> - O arquivo de nível `r36-brilho.level` fica em `/storage/.config/emuelec/configs/` (p8), valor validado (piso 10, passo 5, teto 100, padrão 80); o `emuelec.conf` só vale sem o arquivo. `lcdbl` ausente, FN não remapeado ou p1 indisponível: sai com 0, sem travar o boot.
> - Log `r36-brilho.log` só com `r36-diagnostico` na p1 (capability `diagnostic-logs`). Sem a chave, nada é escrito na p1.
> - Você não tem o aparelho: o que o D-pad emite com o FN apertado fica como instrução para o usuário (task 6.1) e como pergunta aberta no relatório. Não invente.

## Prompt E: `emuelec-localizacao-ui` (Sub-agente Flash 3.8)

> Preâmbulo comum. Change: `emuelec-localizacao-ui`. Modelo: Flash 3.8. Faça os grupos 1, 2 e 3 do `tasks.md`.
> Cuidados específicos:
> - Write-set: `features/10-ptbr-sao-paulo/system/usr/config/emuelec/configs/locale/**` (ou feature própria), `tests/test_localizacao_ui.py` e a pasta da change `openspec/changes/emuelec-localizacao-ui/**`. Não altere arquivos fora desse escopo.
> - Regra de terminologia gamer: mantenha termos consagrados em inglês no catálogo `pt_BR` (*Save State*, *Core*, *Shader*, *Overlay*, *RetroAchievements*, *Scraper*, *Hotkey*, *ROMs*, *BIOS*, *Netplay*, *Rewind*). Traduza apenas ações e diálogos de navegação.
> - Calibração para tela compacta 640x480: formule traduções curtas e diretas que não quebrem nem truncam botões e caixas de diálogo do EmulationStation.
> - Compilação de .po para .mo: gere os arquivos `.mo` válidos usando `msgfmt` ou ferramentas python `msgfmt.py`, garantindo cabeçalho UTF-8 limpo sem warnings. Commite ambos (.po e .mo).
> - Teste automatizado: crie `tests/test_localizacao_ui.py` garantindo ausência de `msgstr ""` vazias nos arquivos entregues e coerência estrutural dos catálogos.

## Prompt F: `tema-epic-cody-ml` (Sub-agente Flash 3.8)

> Preâmbulo comum. Change: `tema-epic-cody-ml`. Modelo: Flash 3.8. Faça os grupos 1, 2 e 3 do `tasks.md`.
> Cuidados específicos:
> - Write-set: `features/50-temas-extras/**`, `features/10-ptbr-sao-paulo/storage/.config/emulationstation/es_settings.cfg` (definindo `ThemeSet = "Epic Cody ML"`), `tools/refatora_epic_cody_ml.py`, `tests/test_tema_epic_cody_ml.py` e a pasta da change `openspec/changes/tema-epic-cody-ml/**`.
> - Script em Python: implemente `tools/refatora_epic_cody_ml.py` para desacoplar os textos dos nós `<text>` em variáveis `${sistema.*}` e gerar os catálogos `_languages/en.xml`, `_languages/pt-br.xml` e `_languages/es-latam.xml`.
> - Ordem do `<subset name="language">` no `theme.xml`: `pt-br`, seguido de `es-latam` e `en` para que português do Brasil seja o idioma ativo padrão.
> - Economia de espaço: remova o tema antigo `Epic Cody` da imagem/feature para economizar espaço e instale o novo tema sob `Epic Cody ML`.
> - Teste automatizado: implemente `tests/test_tema_epic_cody_ml.py` validando integridade do XML, presença dos 3 idiomas, ausência de tags não fechadas e consistência de variáveis.

## Prompt do revisor (um por branch, agente novo)

> Revise a branch `<change>` contra a `main` (`git diff main...<change>`), no worktree dela. Leia o `CLAUDE.md` da raiz e os artefatos de `openspec/changes/<change>/`. Procure: tasks marcadas sem a verificação feita; requisitos e cenários dos specs sem teste; teste que passaria mesmo com o código errado; `sh` não portátil para o BusyBox; falta de idempotência no boot; escrita desnecessária no SD; conflito com arquivo que a p8 já tem (a base nunca atualiza arquivo existente); custo de CPU/GPU no A33; na branch D, também o piso do brilho (a tela nunca apaga), a repetição que não vaza processo ao soltar o FN ou a seta e o `udt_pwr_events.sh` com uma linha só; arquivos fora do write-set (D2 do `design.md` de `integra-limite-idioma-shaders-gb`). Rode a suíte e o `openspec validate --strict`. Não edite nada. Relate achados ordenados por gravidade, cada um com arquivo:linha, cenário que falha e correção sugerida; diga também o que você conferiu e estava certo.
