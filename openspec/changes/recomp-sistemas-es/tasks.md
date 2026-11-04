# Tasks

## 1. Branch e ELF de teste

- [x] 1.1 Criar a branch `recomp-sistemas-es` a partir da `main` (regra do projeto) e conferir com `git branch --show-current`
- [x] 1.2 Criar um ELF armhf de teste em `tools/` (fonte em C mais receita de cross-compile contra glibc 2.36, sem recompilador): abre a tela em GLES2/fbdev, toca um tom por ALSA e espera `SIGTERM`; conferir com `readelf -A` (ARMv7, hard-float) e `readelf -V` (`GLIBC_` até 2.36). Se não houver toolchain no PC, registrar o bloqueio e seguir com os testes por script de shell
  - Bloqueio registrado: sem toolchain armhf/sysroot glibc 2.36 no PC. Entregues `tools/recomp_teste/teste.c` (SDL2 + GLES2 + tom + espera `SIGTERM`) e `LEIAME.md` com a receita, **sem compilar**; os testes seguem com ELFs falsos (assinatura `\x7fELF`) e scripts de shell. O `Teste.recomp` real fica para quem tiver a toolchain (tarefa 6.4)

## 2. Serviço de cópia dos executáveis (`58-ports-exec`)

- [x] 2.1 Em `tests/test_ports_exec.py`, escrever os testes que falham: ELF em `roms/gba-recomp/` vira cópia `0755` e montagem; pasta `snes-recomp/` inventada funciona sem alterar o serviço; `recomp.log` e `recomp.log.1` não são tratados como executáveis; cartão sem pasta `*-recomp` só trata os ports; recomp removido apaga a cópia; erro de montagem em um recomp não impede ports nem outros recomps; log lista o recomp com sha256
- [x] 2.2 Alterar `features/58-ports-exec/system/usr/lib/r36/ports-exec` para varrer `roms/ports` e `roms/*-recomp` (primeiro nível, por padrão de nome) com o mesmo cache, a mesma limpeza e o mesmo log; verificar com `uv run python -I -m unittest tests.test_ports_exec`
- [x] 2.3 Atualizar `description` e o comentário do `features/58-ports-exec/feature.toml` para citar as pastas `*-recomp`; verificar com `uv run python -I -m unittest tests.test_ports_exec` (teste do `feature.toml`)

## 3. Lançador e saída pelo FN (`66-recomp`)

- [x] 3.1 Criar `features/66-recomp/feature.toml` (`order = 66`) com `[[override]]` do `es_systems.cfg` nas camadas `system` e `storage`, apontando para a feature `64-love2d`; verificar que `./build.sh --features 66-recomp --dry-run` (ou o equivalente do projeto) não acusa conflito
- [x] 3.2 Escrever `tests/test_recomp.py` com os cenários de `recomp-systems`: permissão e sintaxe do `recomp.sh`; comando do sistema sem `emuelecRunEmu.sh` nem `--core`; ELF executado direto; arquivo não-ELF registra erro e sai limpo; áudio antes e depois; idioma exportado; rotação do log a 100 KB; `ldd` no log; `gptokeyb` iniciado com `-killsignal 15` e perfil sem teclas de ação; `es_input.cfg` sem `id="10"` do `micro_gamepad`
- [x] 3.3 Implementar `features/66-recomp/system/usr/bin/recomp.sh` derivado do `love.sh` (D2): execução por symlink `/tmp/r36-recomp-game` (D3), `gptokeyb`, áudio, idioma, splash neutro, `trap` de limpeza e log em `roms/<sistema>/recomp.log`; verificar com `uv run python -I -m unittest tests.test_recomp`
- [x] 3.4 Criar `features/66-recomp/system/usr/config/gptokeyb/recomp.gptk` (`hotkey = guide`, `start = enter`, `back = esc`, `guide = esc`, zonas mortas iguais às do LÖVE); verificar pelo teste do perfil
- [x] 3.5 Acrescentar o sistema `gba-recomp` (extensões `.recomp`/`.RECOMP`, pasta `/storage/roms/gba-recomp`, `<theme>gba-recomp</theme>`, comando `/usr/bin/recomp.sh "%ROM%" "%SYSTEM%"`) às duas cópias do `es_systems.cfg` da feature; verificar com `uv run python -I -m unittest tests.test_es_systems` (duas cópias iguais, nenhum outro `*-recomp`)
- [x] 3.6 Criar a pasta `features/66-recomp/roms/gba-recomp/` com um `LEIAME.txt` curto em três idiomas (como copiar um `.recomp`, FN + Start para sair); verificar que a pasta aparece no `build` e que o arquivo não é listado pelo ES (extensão não coincide)

## 4. Tema Epic Cody ML

- [x] 4.1 Conferir de onde o tema tira a arte do GBA (a pasta `gba/` só traz `theme.xml`) e registrar a origem no `design.md`; verificar com o caminho dos arquivos de imagem encontrados
- [x] 4.2 Em `tests/test_tema_epic_cody_ml.py`, escrever os testes que falham: `gba-recomp/` com `theme.xml`, `logo.png`, `poster.png`, `system.png`; as cinco variáveis `gba-recomp.*` nos três `_languages`; `sys_line1` e `sys_line2` sem reticências no limite de caracteres do tema
- [x] 4.3 Escrever `tools/` script Python (via `uv run`) que deriva `logo.png`, `poster.png` e `system.png` da arte do GBA e compõe o selo RECOMP; gerar os três arquivos em `features/50-temas-extras/storage/.config/emulationstation/themes/Epic Cody ML/gba-recomp/` e conferir as imagens visualmente
- [x] 4.4 Criar `gba-recomp/theme.xml` (mesma estrutura do `gba/theme.xml`, variáveis `${gba-recomp.*}`) e declarar as variáveis nos `_languages` `pt-br.xml`, `es-latam.xml` e `en.xml`; verificar com `uv run python -I -m unittest tests.test_tema_epic_cody_ml tests.test_localizacao_ui`
- [x] 4.5 Conferir que o tema continua dentro do orçamento de 300 MiB da p8 (`tests.test_temas_extras`)

## 5. Documentação (três idiomas)

- [x] 5.1 Atualizar `docs/DEVELOPMENT.md`, `docs/DESENVOLVIMENTO.md` e `docs/DESARROLLO.md` com a feature `66-recomp`: pasta, extensão `.recomp`, contrato de ABI do ELF, FN + Start e como acrescentar um console; verificar que os três têm as mesmas seções
- [x] 5.2 Atualizar os três READMEs (`README.md`, `README.pt-BR.md`, `README.es.md`) só se a lista de recursos deles menciona consoles ou o LÖVE; verificar com a mesma estrutura nos três
- [x] 5.3 Registrar no `CLAUDE.md`, na seção "O aparelho", os fatos duráveis: recomp = ELF armhf em `roms/*-recomp`, execução por cópia da p8, symlink `r36-recomp-game` e FN + Start; verificar relendo o texto contra a spec

## 6. Integração e validação

- [x] 6.1 Rodar a suíte completa com `uv run python -I -m unittest discover -s tests` e confirmar que passa
- [x] 6.2 Rodar `openspec validate recomp-sistemas-es --strict` e corrigir o que acusar
- [x] 6.3 Gerar uma imagem de teste (`./build.sh --lang pt_BR`) e conferir, sem montar nada com `sudo`, o `es_systems.cfg`, o `recomp.sh`, o `ports-exec` e o tema, por `mcopy` e `unsquashfs -cat` (regra do projeto)
- [ ] 6.4 Instrução para o usuário (você não roda `sudo`): gravar a imagem com `./flash.sh --device ... --part system`, copiar o pacote de teste (`Teste.sh` e a pasta `Teste/`, de `tools/recomp_teste/pacote/`) para `gba-recomp/`, e conferir no aparelho: sistema aparece, jogo abre, som sai, FN + Start encerra, Select chega ao jogo, `r36-ports-exec.log` lista o ELF, sistema vazio some do menu, nome do processo no `recomp.log` é `r36-recomp-game`. Registrar o resultado no `design.md` (D3 e D9 confirmados ou plano B)

## Workflow follow-up

- Arquivar a change depois da conferência no aparelho.
- A change `recompilador-gba` (ROM → ELF armhf, glibc 2.36, GLES2) parte desta e fica fora daqui.
