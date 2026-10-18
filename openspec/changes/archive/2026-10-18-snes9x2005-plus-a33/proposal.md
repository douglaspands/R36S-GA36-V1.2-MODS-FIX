# Proposal

## Why

O `snes9x2005_plus`, core padrão do SNES, vem da base compilado pelo EmuELEC no alvo genérico `armv8-hardfloat-neon`: `-O2`, sem LTO e sem PGO. A ISA já é a do Cortex-A7 (ARM, VFPv4, NEON com FMA). Sobra ganho em nível de otimização, LTO e PGO, e no A33 esse ganho pode ser o que separa o Yoshi's Island (Super FX 2) de rodar liso ou engasgar. O usuário também vai recompilar outros cores depois, então o processo precisa ficar registrado e reproduzível desde este primeiro core.

## What Changes

- **Compilação de cores no repositório:** um container rootless (podman, Debian bookworm, glibc 2.36 igual à base) e um comando `./cores.sh` que compilam um core a partir de uma receita versionada. A receita fixa o repositório, o commit, o sha256 do fonte, as variáveis do `make` e as flags de cada variante. Cada binário passa por uma checagem de ABI contra a base, e cada build é registrado (sha256, versão do compilador, flags).
- **Quatro variantes experimentais do `snes9x2005_plus`**, ao lado do original e sem sobrescrevê-lo, todas no mesmo fonte da base (`fd45b0e` do upstream, o fixado pelo EmuELEC 4.7):
  - `snes9x2005_plus_a33_o2`: `-O2` + LTO
  - `snes9x2005_plus_a33_o3`: `-O3` + LTO
  - `snes9x2005_plus_a33_pgo_treino`: instrumentado, gera o perfil num diretório da p1
  - `snes9x2005_plus_a33_pgo`: o nível vencedor com o perfil
- **Duas variantes do `snes9x2010`** (acrescentadas depois da primeira rodada de sessões): o defeito de som do Yoshi's Island apareceu no mesmo ponto no original e nas variantes do 2005_plus, então é da emulação, não das flags. O `snes9x2010` (Snes9x 1.52, mais preciso e mais pesado) entra para comparar, no mesmo fonte da base (`d8b10c4`):
  - `snes9x2010_a33_o2`: `-O2` + LTO
  - `snes9x2010_a33_o3`: `-O3` + LTO
  - O PGO do 2010 fica para depois da comparação.
- **Feature nova `53-cores-a33`:** os `.so` e `.info` entram no SYSTEM, em `/usr/lib/libretro`. O `es_systems.cfg` ganha as quatro variantes no bloco `snes`, para escolher por jogo no EmulationStation.
- **Avaliação e PGO jogando:** o usuário joga as fases 1-1 e 1-2 do Yoshi's Island com o FPS na tela e o clock fixo. O resumo do `r36-thermal.csv` por core e o resultado de cada sessão ficam registrados junto da receita, assim como os `.gcda` do treino.
- **`CLAUDE.md`** na raiz, com as regras de trabalho e os fatos do aparelho: acesso só pelo cartão SD, ABI da base e overlay de cores.
- **`README.md`:** registra que o aparelho só é acessível pelo cartão SD, corrige a menção a SSH na seção do swap e documenta a feature e o `./cores.sh`.
- **Promoção do vencedor nesta mesma change** (decidida pelo usuário depois da avaliação): o `_o2` usou 10,2% menos CPU que o original no Yoshi, e o PGO, o `-O3` e o `snes9x2010` perderam. Ele vira o core `snes9x2005_plus_a33` (mesmo binário do `_o2`, só o nome muda) e o padrão do SNES (`snes.core=snes9x2005_plus_a33` na `emuelec.conf` da `10-ptbr-sao-paulo`). As variantes perdedoras saem da imagem; as receitas, os registros e o perfil ficam em `cores/`. O `snes9x2005_plus` original e os demais cores da base continuam instalados.

## Capabilities

### New Capabilities
- `core-builds`: como um core libretro é compilado para o A33 a partir de uma receita versionada (toolchain fixada, flags por variante, PGO com perfil guardado), verificado contra a ABI da base e registrado com os resultados de avaliação. É o molde para os próximos cores.

### Modified Capabilities
- `snes-emulation`: o core padrão do SNES passa a ser o `snes9x2005_plus_a33`, recompilado para o A33, e o `snes9x2005_plus` original continua instalado e selecionável.

## Impact

- Novos: `cores.sh`, `tools/r36img/cores.py`, `cores/toolchain/Containerfile`, `cores/snes9x2005_plus/` (receita, perfil `.gcda`, registro de builds e resultados), `features/53-cores-a33/` (binários, `.info`, `es_systems.cfg` nas camadas system e storage), testes e `CLAUDE.md`.
- Alterados: `README.md`, `.gitattributes` (`*.so` e `*.gcda` como binários) e a `emuelec.conf` da `10-ptbr-sao-paulo` (`snes.core`).
- Dependência nova só para compilar cores: podman rootless e a imagem `debian:bookworm` fixada por digest. O `./build.sh` não passa a depender do podman, porque usa os binários já commitados.
- Os binários e o `es_systems.cfg` da camada system chegam com `--part system`. A cópia do `es_systems.cfg` no `/storage`, que é a que o ES lê, chega com uma única gravação com `--wipe-storage`. O cartão só é acessível no PC, então cada iteração é uma gravação e uma leitura do cartão.
- O padrão do SNES (`snes.core`) e a lista de cores ficam no `/storage`, então só chegam com `--wipe-storage`. A `10-ptbr-sao-paulo` passa a depender da `53-cores-a33`: desligar a 53 exige voltar o `snes.core` para `snes9x2005_plus`, e um teste confere isso.
- Sem mudança em ROMs, boot, kernel, temas ou no core padrão de outros sistemas.
