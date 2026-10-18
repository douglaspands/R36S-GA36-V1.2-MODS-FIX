# Tasks

## 1. Preparação e documentação do projeto

- [x] 1.1 Criar a branch `snes9x2005-plus-a33` a partir da `main` e verificar com `git branch --show-current` e `git status` que ela está limpa
- [x] 1.2 Criar o `CLAUDE.md` na raiz com as regras de trabalho, os fatos do aparelho (acesso só pelo cartão SD, ABI da base, overlay `/tmp/cores`) e a origem da imagem base, conforme o design; verificar que cita sudo, uv, a branch por change, o cartão SD, glibc 2.36 e libstdc++ 6.0.29
- [x] 1.3 No `README.md`, acrescentar a regra "sem rede, SSH nem Wi-Fi: tudo pelo cartão SD" em "O aparelho e por que só esta base funciona" e trocar o "por SSH ou no terminal do aparelho" da seção do swap; verificar com `grep -n SSH README.md` que não sobra instrução de acesso por SSH
- [x] 1.4 Acrescentar `*.so binary` e `*.gcda binary` ao `.gitattributes` e verificar com `git check-attr binary -- x.so x.gcda`

## 2. Toolchain e receita

- [x] 2.1 Resolver o hash completo do commit `d4e2b9a` do `libretro/snes9x2005`, baixar o `.tar.gz` do commit, anotar o sha256 e conferir no Makefile desse commit o uso de `GIT_VERSION`, `CC`, `AR` e `platform=unix`; verificar anotando os achados na descrição do commit (e um patch de versão se `GIT_VERSION` não existir) — o `d4e2b9a` é do repositório do fork, e o fonte é o `fd45b0e` do EmuELEC v4.7; `platform=armv8-hardfloat-neon` em vez de `unix` (ver design)
- [x] 2.2 Criar `cores/toolchain/Containerfile` (bookworm fixado por digest, `gcc-arm-linux-gnueabihf`, `libc6-dev-armhf-cross`, `make`) e `cores/toolchain/a33-cc`, que acrescenta `$A33_FLAGS` ao fim e registra cada linha de comando; verificar com `podman build` rootless e `arm-linux-gnueabihf-gcc --version` dentro do container
- [x] 2.3 Criar `cores/snes9x2005_plus/receita.toml` com fonte (URL, commit, sha256), `make` (`USE_BLARGG_APU=1`, `platform=armv8-hardfloat-neon`), flags comuns, variantes `o2`/`o3`/`pgo_treino`/`pgo` (com `base` a definir) e a lista de flags descartadas com o motivo; verificar com o teste de leitura da receita (tarefa 3.1)

## 3. Comando `./cores.sh`

- [x] 3.1 Implementar em `tools/r36img/cores.py` a leitura e validação da receita (variante desconhecida lista as válidas; `base` vazio nas variantes PGO dá erro claro) e a montagem das flags por variante; cobrir em `tests/test_cores.py` e verificar com `uv run pytest tests/test_cores.py`
- [x] 3.2 Implementar o download do fonte com conferência de sha256 e cache em `work/cache/cores/`, sem rede quando já está no cache; cobrir com teste de sha256 divergente e de cache e verificar com `uv run pytest tests/test_cores.py`
- [x] 3.3 Implementar a checagem de ABI (`NEEDED` existente na base, `GLIBC_` ≤ 2.36, `GLIBCXX_` ≤ 3.4.29, ARMv7 + VFPv4 + VFP args, `retro_*` em endereço par, sem `.debug_*`) usando `readelf`; testar contra o `snes9x2005_plus_libretro.so` da base (`@needs_base`, passa) e contra casos sintéticos de saída do `readelf` (falha), e verificar com `uv run pytest tests/test_cores.py`
- [x] 3.4 Implementar `compilar <core> <variante>`: podman rootless com `--userns=keep-id`, `:Z`, fonte em `/build/src` e, no `pgo`, o perfil montado em `/storage/roms/pgo/<core>`; checagem de ABI; cópia do `.so` para a `53-cores-a33`; e linha no `builds.jsonl` (data, variante, core, commit, flags efetivas do log do wrapper, `gcc --version`, digest, tamanho, sha256); verificar com `./cores.sh compilar snes9x2005_plus o2` gerando o binário e a linha
- [x] 3.5 Implementar `verificar [<core>]` (ABI dos binários commitados e sha256 igual ao último registro de cada variante) e `perfil <core> <dir>` (copia os `.gcda`, confere um por objeto do instrumentado, registra hashes); cobrir em `tests/test_cores.py` e verificar com `uv run pytest tests/test_cores.py`
- [x] 3.6 Implementar `resumo <csv> [--roms <ponto>]`: sessões por (`boot`, `core`, `rom`) contíguos, tabela Markdown com duração, ocupação média e máxima, `cpu_mhz` médio, `cpu_max_mhz`, temperatura inicial e final, e CRC32/SHA1 das ROMs; cobrir com um CSV fixture de duas sessões em cores diferentes e verificar com `uv run pytest tests/test_cores.py`
- [x] 3.7 Criar o wrapper `cores.sh` no molde do `build.sh` e documentar em "Para desenvolvedores" do `README.md` a subseção "Compilar um core" (pré-requisitos sem sudo, os quatro subcomandos e como acrescentar um core novo); verificar que `./cores.sh --help` lista os subcomandos citados no README

## 4. Variantes `o2` e `o3` na feature

- [x] 4.1 Compilar `o2` e `o3` com `./cores.sh compilar`; verificar com `./cores.sh verificar snes9x2005_plus`, com o último `-O` do log igual ao da variante, e com `strings` mostrando `a33-o2`/`a33-o3` na versão
- [x] 4.2 Criar `features/53-cores-a33/feature.toml` (order 53, habilitada, descrição), os `.info` das quatro variantes derivados do original (só `display_name` e `display_version` mudam) e o `es_systems.cfg` nas camadas system e storage, com as quatro `<core>` depois de `snes9x2005_plus` no bloco `snes`; verificar com o teste da tarefa 4.3
- [x] 4.3 Criar `tests/test_cores_a33.py`: descritor; camadas do `es_systems.cfg` idênticas; diferença para a base só nas quatro linhas (`@needs_base`) e sem mudar `default="true"`, `snesh` nem `snesmsu1`; `.info` diferentes do original só em `display_name`/`display_version` (`@needs_base`); cada `.so` presente com registro e sha256 iguais; verificar com `uv run pytest tests/test_cores_a33.py`
- [x] 4.4 Criar `cores/snes9x2005_plus/RESULTADOS.md` com o protocolo (preparo, sessão, ordem, critério de 5%, aviso das entradas sem binário até a gravação 3, sair pelo menu) e a tabela de sessões vazia, e acrescentar o item da `53-cores-a33` em "Features habilitadas" do `README.md`; verificar que o README cita as quatro variantes, que o original fica intocado e o `--wipe-storage` único
- [x] 4.5 Rodar `uv run pytest` e `./build.sh --test`; verificar sem sudo, no SYSTEM gerado, os `.so`/`.info` novos em `/usr/lib/libretro`, o `snes9x2005_plus_libretro.so` com o mesmo sha256 da base, e na p8 o `es_systems.cfg` com as quatro entradas

## 4b. snes9x2010 (acrescentado depois da primeira rodada de sessões)

- [x] 4b.1 Resolver o fonte do snes9x2010 da base (`PKG_VERSION` do EmuELEC v4.7, `d8b10c4`, sha256 do tarball igual ao `PKG_SHA256`), conferir que o upstream não mudou o fonte C até a data da imagem e que as chaves de opção batem com o binário da base; verificar anotando na descrição do commit
- [x] 4b.2 Criar `cores/snes9x2010/receita.toml` (`-f Makefile.libretro platform=unix`, como a base, variantes `o2` e `o3`) e compilar as duas; verificar com `./cores.sh verificar` e com `strings` mostrando `1.52.4 d8b10c4 a33-o2`/`a33-o3`
- [x] 4b.3 Acrescentar os `.info` das duas variantes e as duas `<core>` no fim do bloco `snes` do `es_systems.cfg` (camadas system e storage), e generalizar `tests/test_cores_a33.py` para os dois cores; verificar com `uv run python -I -m unittest discover -s tests`
- [x] 4b.4 Documentar o snes9x2010 no `README.md` e no protocolo do `RESULTADOS.md` e gerar a imagem com `./build.sh --test`; verificar no SYSTEM gerado os `.so`/`.info` do 2010, o `snes9x2010_libretro.so` original com o mesmo sha256 da base e na p8 as seis entradas

## 5. Sessões no aparelho: original, `o2` e `o3`

- [x] 5.1 Usuário grava a imagem da tarefa 4b.4 com `--keep-roms --wipe-storage`, confere no ES que as seis variantes aparecem no Yoshi's Island e liga o `maxperf` **pelo ES** (opções do jogo) e o FPS na tela; com o cartão no PC, conferir que a `emuelec.conf` tem a chave `maxperf=1` do jogo; verificar com o usuário
- [x] 5.2 Usuário joga 1-1 e 1-2 no `snes9x2005_plus` original, no `_o2` e no `_o3`, e no `snes9x2010` original, no `_o2` e no `_o3`, com o aparelho frio e a bateria acima de 50% antes de cada sessão, e anota se o defeito de som do Yoshi aparece em cada um; com o cartão no PC, rodar `./cores.sh resumo` sobre o `r36-thermal.csv` com `--roms` e registrar no `RESULTADOS.md` as sessões, a percepção e o FPS informados pelo usuário, o governor `performance` em todas e o vencedor pelo critério; verificar que o registro tem as seis linhas e a decisão (inclusive entre 2005_plus e 2010)

## 6. PGO

- [x] 6.1 Preencher `base` das variantes PGO com o nível vencedor, compilar `pgo_treino` e gerar a imagem com `./build.sh --test`; verificar com `./cores.sh verificar` e com `strings` mostrando `a33-pgo-treino`
- [x] 6.2 Usuário grava com `--part system`, joga 1-1 e 1-2 no `_pgo_treino` (e opcionalmente DKC e Kirby Super Star) e sai pelo menu do RetroArch; com o cartão no PC, rodar `./cores.sh perfil snes9x2005_plus <R36-ROMS>/pgo/snes9x2005_plus`; verificar que os `.gcda` foram importados, um por objeto, e registrar a sessão no `RESULTADOS.md`
- [x] 6.3 Compilar `pgo` com o perfil importado e gerar a imagem com `./build.sh --test`; verificar que a compilação não emite aviso de perfil ausente ou incompatível, que `./cores.sh verificar` passa e que `uv run pytest` passa
- [x] 6.4 Usuário grava com `--part system` e joga 1-1 e 1-2 no `_pgo`, e faz a fumaça (Star Fox, Mega Man X2, Super Mario Kart e Kirby Super Star, 2–3 min cada); com o cartão no PC, rodar `./cores.sh resumo` e registrar no `RESULTADOS.md` o `_pgo` contra o vencedor e contra o original, a fumaça e o candidato final para a promoção; verificar que o registro tem a decisão, mesmo que o PGO não tenha ganhado

## 7. Fechamento

- [x] 7.1 Rodar `uv run pytest` e `./cores.sh verificar`, e conferir que `builds.jsonl`, `pgo/`, `RESULTADOS.md`, os binários e o `README.md` estão commitados na branch; verificar com `git status` limpo

## 8. Promoção do vencedor (decidida depois da avaliação)

- [x] 8.1 Na receita do `snes9x2005_plus`, dar à variante `o2` o nome `snes9x2005_plus_a33`; na feature `53-cores-a33`, deixar só o `snes9x2005_plus_a33_libretro.so` (o mesmo binário do `_o2`) e o `.info` dele, tirar os `.so`/`.info` do `_o3`, `_pgo_treino`, `_pgo` e do `snes9x2010`, e deixar só a linha `snes9x2005_plus_a33` no `es_systems.cfg` das duas camadas; verificar com `./cores.sh verificar` (sha256 igual ao registro do `o2`)
- [x] 8.2 Trocar `snes.core` para `snes9x2005_plus_a33` na `emuelec.conf` da `10-ptbr-sao-paulo` e ajustar os testes (`test_cores_a33.py`, `test_ptbr_controle.py` e um teste que falha se a 53 estiver desligada com o `snes.core` apontando para ela); verificar com `uv run python -I -m unittest discover -s tests`
- [x] 8.3 Atualizar o `README.md` (itens da 10 e da 53), o `RESULTADOS.md` (decisão de promover) e gerar a imagem com `./build.sh --test`; verificar no SYSTEM gerado só o `snes9x2005_plus_a33` novo, o original com o sha256 da base, e na p8 o `snes.core` novo e a única entrada nova no `es_systems.cfg`

## Workflow follow-up

- Arquivar a change depois de registrado o resultado das sessões.
- Investigar o limite de clock (1104 MHz a partir de ~56 °C, 912 MHz com bateria fraca descarregando) e o defeito de tela que pisca a parte de cima embaixo.
