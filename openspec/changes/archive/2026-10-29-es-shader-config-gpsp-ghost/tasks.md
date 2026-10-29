# Tasks

## 1. Feature `56-retroarch-ajustes` e shader do ES

- [x] 1.1 Criar `features/56-retroarch-ajustes/feature.toml` (schema 1, order 56, enabled) e `system/usr/lib/r36/shaderset-aplica` (executável): lê `emuelec.conf` na ordem jogo, sistema, global (`<sistema>["<rom>"]...shaderset=`, `<sistema>.shaderset=`, `global...shaderset=`), apaga `video_shader` e `video_shader_enable` do `retroarch.cfg` e grava `video_shader = "/tmp/shaders/<valor>"` e `video_shader_enable = "true"` para um valor que não seja `true`, `1`, `none`, `false`, `0` nem vazio; para `none`, `false`, `0` e vazio só apaga as duas linhas; para `true` e `1` não faz nada. `R36_ROOT` para os testes. Verificar com `ls -l features/56-retroarch-ajustes/system/usr/lib/r36` (modo 0755) e `sh -n` no script.
- [x] 1.2 Em `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`, chamar `/usr/lib/r36/shaderset-aplica "${PLATFORM}" "${ROMNAME_SHADER}"` logo depois da linha do `SHADERSET=$(setsettings.sh ...)`, protegido por `[ -x ]`, com um comentário `# R36:` como as demais. Verificar com `git diff features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh` (só essas linhas) e `bash -n`.
- [x] 1.3 Criar `tests/test_retroarch_ajustes.py` com os casos do `shaderset-aplica` num `R36_ROOT` temporário: preset por sistema grava `video_shader` e `video_shader_enable`; escolha por jogo vence a do sistema e a do sistema vence a global; `none`, `false`, `0` e ausência apagam as linhas e não deixam shader do jogo anterior; `true` e `1` não gravam; nome com espaço; o padrão `gba.shaderset=gba/gba-modern-remaster.glslp` vira `video_shader`; sem a chave `r36-diagnostico` nenhum log, com ela uma linha por jogo em `r36-shader-gba.log`. Verificar com `uv run python -I -m unittest tests.test_retroarch_ajustes`.
- [x] 1.4 Registrar no teste da feature 10 (`tests/test_ptbr_controle.py`) que o `emuelecRunEmu.sh` chama o `shaderset-aplica` depois do `setsettings.sh` e antes do `RUNTHIS`. Verificar com `uv run python -I -m unittest tests.test_ptbr_controle`.

## 2. Caminhos do RetroArch e gpSP com ghosting

- [x] 2.1 Criar `system/usr/lib/r36/retroarch-prepara` na feature 56: troca no `retroarch.cfg` da p8, só quando a linha é a de fábrica, `rgui_config_directory` (`/config`), `savefile_directory` (`/saves`), `log_dir` (`/logs`) e `osk_overlay_directory` (`/overlays/keyboards`) pelos valores da spec; escreve no mesmo arquivo, sai sem erro se o arquivo não existe, e é idempotente. Verificar com os testes de 2.4.
- [x] 2.2 No mesmo script, cuidar do `config/gpSP/gpSP.opt`: cria `gpsp_frame_mixing = "enabled"` ou acrescenta só a linha (com quebra de linha antes se faltar) quando a chave não existe; não altera um valor existente; com `r36-gpsp-sem-ghost` na p1 remove só a linha `enabled`. A espera pela p1 (até 20 s, `mountpoint -q /storage/roms`) segue o `54-shaders-gba`. Verificar com os testes de 2.4.
- [x] 2.3 Criar `system/usr/lib/systemd/system/r36-retroarch-prepara.service` (oneshot, `Before=emustation.service`, sem `After=emuelec-autostart.service`, `TimeoutStartSec=60`, `WantedBy=emuelec.target`) e o link em `emuelec.target.wants`, e gravar `r36-retroarch.log` só com `r36-diagnostico`. Verificar com `uv run python -I -m unittest tests.test_retroarch_ajustes` (o teste confere o unit e o link) e `grep -n "emuelec-autostart" features/56-retroarch-ajustes -r`.
- [x] 2.4 Em `tests/test_retroarch_ajustes.py`, cobrir: os quatro valores trocados em `--keep-storage` simulado; valor diferente do de fábrica intocado; segunda execução sem mudança; sem `retroarch.cfg` sem erro; `gpSP.opt` criado, acrescentado (com e sem quebra de linha no fim), preservado com `disabled`, desfeito pela chave `r36-gpsp-sem-ghost` e sem a linha voltar; sem `r36-diagnostico` nenhum `r36-retroarch.log`. Verificar com `uv run python -I -m unittest tests.test_retroarch_ajustes`.
- [x] 2.5 Em `features/10-ptbr-sao-paulo/storage/.config/retroarch/retroarch.cfg`, trocar os quatro valores pelos da spec e acrescentar em `tests/test_ptbr_controle.py` um teste que lê o arquivo e confere que nenhuma chave `*_directory`/`*_dir` aponta para `/config`, `/saves`, `/logs` ou `/overlays` e que cada valor começa por `~`, `/usr`, `/tmp` ou `/storage` (exceto `recording_config_directory`). Verificar com `uv run python -I -m unittest tests.test_ptbr_controle`.

## 3. Documentação e integração

- [x] 3.1 No `CLAUDE.md`, corrigir a frase de que o binário do ES escreve `video_shader` (o `shaderset-aplica` é quem grava), registrar o `rgui_config_directory` corrigido e a razão (raiz somente leitura), incluir `r36-retroarch.log` na lista de logs sob chave e a chave `r36-gpsp-sem-ghost`. Verificar com `grep -n "shaderset-aplica\|rgui_config_directory\|r36-gpsp-sem-ghost\|r36-retroarch.log" CLAUDE.md`.
- [x] 3.2 No `README.md`, descrever a feature 56 (shader do ES, caminhos corrigidos, blending do gpSP e as chaves `r36-gpsp-sem-ghost` e `r36-diagnostico`) e que o gpSP.opt chega com `--part system` ou `--keep-storage`. Verificar com `grep -n "r36-gpsp-sem-ghost\|56-retroarch-ajustes" README.md`.
- [x] 3.3 Rodar a suíte inteira com `uv run python -I -m unittest discover -s tests` e verificar que passa sem falhas novas.
- [x] 3.4 Rodar `openspec validate es-shader-config-gpsp-ghost --strict` e verificar que não há erro.
- [x] 3.5 Gerar um build (`./build.sh`) e verificar, na imagem do build (`mcopy` e `unsquashfs -cat`, sem montar), que o SYSTEM tem os dois scripts, o serviço e o link, e que o `emuelecRunEmu.sh` chama o `shaderset-aplica`; e, na p8 da imagem, o `retroarch.cfg` com os valores novos. Verificar com `./flash.sh --target-file work/cartao-teste.img` quando o `CLAUDE.md` pedir gravação de teste.

## 4. Correções depois do primeiro teste no aparelho

- [x] 4.1 `shaderset-aplica`: imprimir `--set-shader "/tmp/shaders/<valor>"` só para um caminho (D6); `emuelecRunEmu.sh` atribui a saída a `SHADERSET` antes do `sed` do `--config`. Verificar com `uv run python -I -m unittest discover -s tests -p "test_retroarch_ajustes.py"` e `test_ptbr_controle.py` (a contagem de linhas novas do `emuelecRunEmu.sh` passa a 27).
- [x] 4.2 `retroarch-prepara`: `gpsp_boot_mode = "bios"` pela mesma regra do blending (D7), com testes de criação, acréscimo, preservação de `game` e independência da chave `r36-gpsp-sem-ghost`.
- [x] 4.3 `retroarch.cfg` da feature 10: viewport 768x672, `rgui_aspect_ratio = "11"`, `menu_show_load_content_animation = "false"`, `notification_show_autoconfig = "false"` e `user_language = "7"` (D8); atualizar `test_retroarch_cfg` em `tests/test_ptbr_controle.py` e acrescentar o teste dos cinco valores. Verificar com `uv run python -I -m unittest discover -s tests -p "test_ptbr_controle.py"`.
- [x] 4.4 `README.md` e `CLAUDE.md`: menu do RetroArch em português do Brasil (troca a frase que diz inglês por padrão), os padrões de aparência, o `--set-shader` e o `gpsp_boot_mode`. Verificar com `grep -n "user_language\|set-shader\|gpsp_boot_mode" README.md CLAUDE.md`.
- [x] 4.5 Rodar a suíte inteira, `openspec validate es-shader-config-gpsp-ghost --strict` e `./build.sh`; conferir na imagem do build (`mcopy`, `unsquashfs -cat`, sem montar) o `retroarch.cfg` da p8 e o `emuelecRunEmu.sh`.

## 5. Conferência no aparelho (instruções para o usuário)

- [x] 5.1 Gravar o `system` do build (`./flash.sh --device /dev/sdc --part system --build <ts>`), criar `r36-diagnostico` na R36-ROMS e ligar. Verificar em `r36-retroarch.log` que os quatro caminhos foram trocados e conferir o `ls -R` de `.config/retroarch/config` da p8 antes de gravar (D4 da `design.md`).
- [x] 5.2 No aparelho: escolher um shader em "SHADER SET" do ES para um sistema sem preset automático (por exemplo `rpi/zfast_crt_standard.glslp` no SNES) e abrir um jogo; o `emuelec.log` traz `--set-shader` na linha de comando; o `r36-shader-gba.log` traz a linha do jogo e a imagem muda. Abrir um jogo de GBA sem escolher nada: o `gba-modern-remaster` entra.
- [x] 5.3 No aparelho: mudar uma opção do core no RetroArch e salvar as opções do core, sem erro; reabrir o jogo e confirmar que a opção ficou. Se ainda der erro, copiar o `retroarch.log` da p8 (`udisksctl mount -b /dev/sdc8`) para análise.
- [x] 5.4 No aparelho: abrir um jogo no gpSP e ver em "Core Options" que "Interframe Blending" está `enabled` e "Boot mode" está "Boot to BIOS"; criar `r36-gpsp-sem-ghost` na R36-ROMS, ligar e conferir que passou a `disabled`.

- [x] 5.5 No aparelho, com a p8 nova: o menu do RetroArch aparece em português do Brasil (conferir os acentos do RGUI), o viewport e a proporção do RGUI são os novos, e não há animação de carregamento nem aviso de autoconfig ao abrir um jogo.

## Workflow follow-up

- Criar a branch `es-shader-config-gpsp-ghost` a partir da `main` no início do `/opsx:apply`. A chave `r36-diagnostico` usada pelos logs vem da change `logs-diagnostico-sob-chave`; se ela ainda não estiver na `main`, mesclar ou rebasear antes.
- Arquivar a change depois da conferência no aparelho.
