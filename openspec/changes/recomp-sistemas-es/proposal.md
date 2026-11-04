# Proposal

## Why

O projeto quer jogos recompilados estaticamente: uma ROM vira um ELF nativo armhf, sem core nem RetroArch. O recompilador em massa ainda não existe (será a change futura `recompilador-gba`), mas a parte do aparelho já pode ser pronta e validada antes dele: uma lista no EmulationStation, um lançador que executa o ELF e uma saída do jogo pelo FN. Sem isso o recompilador não teria onde entregar o resultado, e o FN, que no resto da imagem só vale no RetroArch, deixaria o jogador sem saída.

## What Changes

- Novo sistema do EmulationStation `gba-recomp` (pasta `/storage/roms/gba-recomp`, extensão `.recomp`), com comando `/usr/bin/recomp.sh "%ROM%" "%SYSTEM%"`. Só o GBA entra agora; outros consoles entram depois acrescentando uma linha numa tabela, sem lançador novo.
- Novo lançador genérico `/usr/bin/recomp.sh`, no molde do `love.sh`: executa o ELF direto (sem core), ajusta rota e ganho de áudio, propaga idioma, mostra as telas neutras de carga e saída e grava log rotativo.
- **FN + Start encerra o jogo**: o lançador sobe o `gptokeyb` com `guide` (FN, botão 10) como hotkey e `-killsignal 15`, tendo como alvo o nome do processo (`basename` do ELF). O Select continua livre para o jogo.
- O serviço `r36-ports-exec` (feature `58-ports-exec`) passa a varrer também `roms/*-recomp/`: cada ELF ganha uma cópia `0755` na p8 montada por cima do arquivo da p1 (FAT32 não guarda bit de execução). O log passa a listar também esses executáveis.
- Tema Epic Cody ML ganha a pasta `gba-recomp/` (`theme.xml`, logo, poster, `system.png` derivados da arte do GBA com selo RECOMP) e as variáveis `${gba-recomp.*}` nos três `_languages` (`pt-br`, `es-latam`, `en`).
- Validação com um ELF armhf de teste (sem depender do recompilador): testes automáticos do lançador, do serviço e do tema, mais conferência no aparelho.

Fora do escopo: o recompilador ROM→ELF (change `recompilador-gba`), os demais consoles (`snes-recomp`, `genesis-recomp`...), shaders e save states para recomps.

## Capabilities

### New Capabilities
- `recomp-systems`: sistemas `<console>-recomp` no EmulationStation, o lançador genérico `recomp.sh` que executa o ELF sem core, a saída do jogo por FN + Start e o contrato de formato do jogo (`.recomp` = ELF armhf).

### Modified Capabilities
- `ports-executables`: o serviço de cópia `0755` passa a cobrir também `roms/*-recomp/`, além de `roms/ports/`.
- `es-themes`: o tema Epic Cody ML passa a trazer o sistema `gba-recomp`, localizado nos três idiomas e legível em 640x480.

## Impact

- Features: nova `66-recomp` (`es_systems.cfg` nas camadas `system` e `storage` sobrepondo o da `64-love2d`, `recomp.sh`, perfil `recomp.gptk`, pasta `roms/gba-recomp`); alterações em `58-ports-exec` (`ports-exec`) e `50-temas-extras` (tema e `_languages`).
- Testes novos e alterados em `tests/` (`test_recomp.py`, `test_ports_exec.py`, `test_tema_epic_cody_ml.py`, `test_es_systems.py`).
- Documentação: manual em três idiomas (`docs/DEVELOPMENT.md`, `docs/DESENVOLVIMENTO.md`, `docs/DESARROLLO.md`) com a lista de features e o `CLAUDE.md` com os fatos do aparelho.
- Sem dependência nova de build e sem rede; o FN segue reservado no ES, sem `es_input.cfg` novo.
