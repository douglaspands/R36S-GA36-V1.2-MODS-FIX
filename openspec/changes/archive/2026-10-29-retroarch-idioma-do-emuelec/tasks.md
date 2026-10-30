# Tasks

## 1. Verificação do que o aparelho grava (instruções para o usuário)

- [x] 1.1 Com o cartão da `main` mesclada com a change `es-shader-config-gpsp-ghost`: no ES, trocar o idioma pelo menu (por exemplo para English), desligar e ler na p8 `system.language` do `.config/emuelec/configs/emuelec.conf` e `Language` do `.config/emulationstation/es_settings.cfg` (`udisksctl mount -b /dev/sdc8`). Registrar na `design.md` (D2) qual dos dois muda e se o caminho do `es_settings.cfg` do script (`/storage/.config/emulationstation/`) é o mesmo que o `emuelecRunEmu.sh` lê (`/storage/.emulationstation/`); o script já lê os dois arquivos (usa o que difere do guardado), então só o caminho muda, se for o caso.
- [x] 1.2 Conferir no binário do RetroArch do SYSTEM (`unsquashfs -cat ... usr/bin/retroarch`, `strings`) as cadeias dos idiomas e confirmar os números do D3 (`pt_BR`=7, `pt_PT`=8, `en_US`=0, `es_ES`=3, `fr_FR`=2, `de_DE`=4, `it_IT`=5). Registrar o resultado na `design.md`.

## 2. Idioma do RetroArch segue o do EmuELEC

- [x] 2.1 Criar `features/56-retroarch-ajustes/system/usr/lib/r36/idioma-aplica` (modo 0755, `R36_ROOT` para os testes): lê o idioma do EmuELEC (D2), traduz pela tabela do D3, grava `user_language` no `retroarch.cfg` só quando o idioma difere do guardado em `/storage/.config/retroarch/r36-idioma` (D4), grava esse arquivo e sai com 0 em qualquer caso. Verificar com `ls -l features/56-retroarch-ajustes/system/usr/lib/r36` e `sh -n` no script.
- [x] 2.2 Chamar `/usr/lib/r36/idioma-aplica` no `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`, ao lado da chamada do `shaderset-aplica`, protegido por `[ -x ]` e com comentário `# R36:`. Verificar com `git diff` (só essas linhas) e `bash -n`; atualizar a contagem de linhas novas em `tests/test_ptbr_controle.py` e a ordem (antes do `eval ${RUNTHIS}`).
- [x] 2.3 Escrever `tests/test_idioma_aplica.py` num `R36_ROOT` temporário: troca de `pt_BR` para `en_US` e de volta; cada código da tabela; primeiro jogo (sem `r36-idioma`) acerta um cartão com `user_language = "0"`; escolha manual no RetroArch dura enquanto o idioma do EmuELEC não muda; idioma fora da tabela e arquivo ausente não mudam nada e saem com 0; `retroarch.cfg` sem a linha ganha a linha; sem `r36-diagnostico` nenhum log, com ele uma linha por jogo em `r36-idioma.log`. Verificar com `uv run python -I -m unittest discover -s tests -p "test_idioma_aplica.py"`.
- [x] 2.4 Documentar no `CLAUDE.md` (o `r36-idioma`, a regra de só ajustar quando o idioma do EmuELEC muda e o `r36-idioma.log` na lista de logs sob chave) e no `README.md` (o RetroArch acompanha o idioma do EmuELEC a cada jogo). Os trechos ficam prontos em `docs-retroarch-idioma-do-emuelec.md` desta pasta e entram no `README.md` e no `CLAUDE.md` na integração (`integra-limite-idioma-shaders-gb`, D2). Verificar com `grep -n "r36-idioma\|idioma-aplica" openspec/changes/retroarch-idioma-do-emuelec/docs-retroarch-idioma-do-emuelec.md` (e, depois da integração, `CLAUDE.md README.md`).

## 3. Idioma padrão escolhido no build e no nome da imagem

- [x] 3.1 Em `tools/r36img/build.py`, aceitar `--idioma <código>` (padrão `en_US`, decisão do usuário; códigos do D3; erro com a lista para código inválido; erro com `--no-features`). Verificar com `./build.sh --help` e `uv run python -I -m unittest discover -s tests -p "test_cli.py"`.
- [x] 3.2 Depois do planejamento, gerar em `work/` cópias do `emuelec.conf`, do `es_settings.cfg` e do `retroarch.cfg` com `system.language`, `Language` e `user_language` trocados (D6), e apontar as entradas do plano para elas; falhar com erro claro se uma chave não existir; não alterar `features/`. Verificar com `uv run python -I -m unittest discover -s tests -p "test_idioma_build.py"` (com `R36_SLOW=1`: `R36_SLOW=1 uv run python -I -m unittest tests.test_idioma_build`; sem a variável a suíte pula estes testes; arquivo novo: build de teste no padrão `en_US` e com `--idioma pt_BR` confere os três valores na imagem e `git status` limpo em `features/`).
- [x] 3.3 Nomear a imagem `<prefixo>_<idioma>_build_<timestamp>[-test].img.xz` (código em minúsculas com `-`), manter o diretório `<timestamp>`, registrar `"language"` no manifest e `idioma:` no `R36-BUILD.txt`; build sem features sem idioma (D7). Atualizar `NAME_RE` e os nomes esperados em `tests/test_image.py` e acrescentar os cenários do padrão `en_US`, de `--idioma pt_BR` e de `--no-features`. Verificar com `R36_SLOW=1 uv run python -I -m unittest tests.test_image` (sem `R36_SLOW=1` a suíte pula os testes de build).
- [x] 3.4 Documentar `--idioma` e o novo nome da imagem no `README.md` (uso do `build.sh`, exemplos e o motivo: imagem pronta no idioma de quem vai usar; no topo da seção do build, que o padrão é inglês e que português pede `--idioma pt_BR`) e no `./build.sh --help`. O trecho do `README.md` fica em `docs-retroarch-idioma-do-emuelec.md` até a integração. Verificar com `grep -n "\-\-idioma" openspec/changes/retroarch-idioma-do-emuelec/docs-retroarch-idioma-do-emuelec.md` e `./build.sh --help`.

## 4. Integração

- [x] 4.1 Rodar a suíte inteira (`uv run python -I -m unittest discover -s tests`) e `openspec validate retroarch-idioma-do-emuelec --strict`; ambos sem erro.
- [x] 4.2 Gerar `./build.sh --idioma pt_BR` e `./build.sh --test` (padrão `en_US`); conferir, sem montar (`mcopy`, `unsquashfs -cat`), os nomes das imagens, os três valores de idioma de cada build e a chamada ao `idioma-aplica` no `emuelecRunEmu.sh`.

## 5. Conferência no aparelho (instruções para o usuário)

- [x] 5.1 Gravar o `system` do build (`./flash.sh --device /dev/sdc --part system --build <ts>`), trocar o idioma do EmuELEC para English pelo menu, abrir um jogo e ver o menu do RetroArch em inglês; voltar para Português (Brasil) e conferir de novo. Com `r36-diagnostico` na p1, o `r36-idioma.log` mostra o idioma lido e o gravado.
- [x] 5.2 Trocar o idioma pelo menu do RetroArch e abrir outro jogo sem mexer no EmuELEC: o idioma escolhido no RetroArch continua.
- [x] 5.3 Gravar uma imagem do padrão (`en_US`, sem `--idioma`) numa p8 nova (`--wipe-storage`) e conferir ES e RetroArch em inglês no primeiro boot.

## Workflow follow-up

- Criar a branch `retroarch-idioma-do-emuelec` a partir da `main` no início do `/opsx:apply`, só depois da change `es-shader-config-gpsp-ghost` estar mesclada na `main` (esta change usa a feature `56-retroarch-ajustes` e o ponto de chamada do `shaderset-aplica`).
- Arquivar a change depois da conferência no aparelho.
