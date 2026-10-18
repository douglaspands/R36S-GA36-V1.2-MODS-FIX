# CLAUDE.md

Fábrica de imagens de cartão SD para o clone do R36S (GA36-MB V1.2, Allwinner A33).
O `README.md` explica o uso; este arquivo guarda as regras de trabalho e os fatos
do aparelho que não se deduzem do código.

## Regras de trabalho

- **Shell:** comandos com caminhos relativos à raiz do projeto, um por chamada,
  sem `cd` e sem encadear com `&&` ou `;`. Lógica longa vai num script temporário
  rodado numa chamada só.
- **Sem sudo**, em nenhuma forma, nem indireta (`./flash.sh --device` chama
  `sudo dd`). Para validar uma gravação, use `./flash.sh --target-file`. O que
  precisar de root ou do cartão real vira instrução para o usuário rodar.
- **Python via uv:** `uv run`, `uv add`, `uv sync`. Nada de `pip`, venv manual ou
  `python3` direto. Testes: `uv run python -I -m unittest discover -s tests`.
- **Uma branch por change:** cada change OpenSpec ganha uma branch própria criada
  a partir da `main` no início do `/opsx:apply`, com o nome da change. Merge e
  push só a pedido.
- **Onde registrar:** regras e fatos duráveis vão neste `CLAUDE.md`; decisões de
  uma change vão nos artefatos OpenSpec dela (proposal, design, specs).

## O aparelho

- **Acesso só pelo cartão SD.** Não há rede, SSH nem Wi-Fi. Tudo que entra ou
  sai do aparelho (cores, perfis de PGO, logs) passa pelo cartão lido no PC. A
  p1 (`R36-ROMS`, FAT32) é gravável no PC sem root; a p8 (`R36-STORAGE`, ext4)
  tem arquivos do root. Nunca propor passos por SSH.
- **Sistema:** EmuELEC 4.7 "Nexus" de fábrica, kernel sunxi 3.4.39. O fonte do
  fork não é público, então só se trocam arquivos das partições.
- **ABI da base**, que todo binário novo precisa respeitar: armhf (ARMv7-A,
  VFPv4 + NEON, hard-float), **glibc 2.36** (`GLIBC_` até 2.36) e **libstdc++
  6.0.29** (GCC 11, `GLIBCXX_` até 3.4.29). Um core C++ compilado com GCC mais
  novo precisa de `-static-libstdc++` ou de GCC 11.
- **Cores libretro:** `/tmp/cores` é um overlay (`tmp-cores.mount`) com lowerdir
  `/usr/lib/libretro` (SYSTEM) e upperdir `/storage/cores` (p8). O
  `emuelecRunEmu.sh` carrega `/tmp/cores/<core>_libretro.so`. A lista de cores
  de cada sistema vem do `es_systems.cfg`: o ES lê a cópia em
  `/storage/.config/emulationstation/`, e o SYSTEM tem outra em
  `/usr/config/emulationstation/`.
- **Imagem base:** `base/R36S GA36-MB V1.2-20260416 - Emuelec - No ROMS.img`
  (sha256 em `config/base.toml`), do post
  <https://www.reddit.com/r/R36S/comments/1w2i8em/r36s_ga36mb_v1220260416_emuelec_no_roms/>.
  Nunca é modificada.
