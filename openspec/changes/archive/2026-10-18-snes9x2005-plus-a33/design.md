# Design

## Context

O SYSTEM da base traz em `/usr/lib/libretro/` o `snes9x2005_plus_libretro.so` (524 KB, stripped). Inspeção com `readelf`: ELF 32-bit ARM hard-float, ARMv7-A, VFPv4 com NEON e FMA, modo ARM (os `retro_*` estão em endereços pares), GCC 11.3.0, versão `v1.36 d4e2b9a`, e só `libc.so.6` com `GLIBC_2.4`/`2.7` como dependência. O pacote do EmuELEC compila com `USE_BLARGG_APU=1 platform=armv8-hardfloat-neon`, que no Makefile do upstream cai no ramo genérico `armv` (`-O2`, sem LTO).

**O `d4e2b9a` não é um commit do `libretro/snes9x2005`** (descoberto na tarefa 2.1). O Makefile monta a versão com `git rev-parse --short HEAD`, e o EmuELEC extrai o tarball do core dentro da própria árvore de build, então o hash é o do repositório (privado) do fork. O fonte é o `fd45b0e055bce6cff3acde77414558784e93e7d0` que o EmuELEC v4.7 fixa no `package.mk` (`PKG_SHA256` `a400aa12…f05`, igual ao do tarball baixado). Entre 2022-04-01 e 2026-03-31 o upstream só mudou CI e Makefile, então qualquer commit que o fork tenha usado nesse período tem o mesmo fonte C. As strings do binário da base (opções do core, mensagens, `Snes9x 2005 Plus`) estão todas no `libretro.c`/`libretro_core_options.h` desse commit. Userland: EmuELEC 4.7 Nexus, glibc 2.36, libstdc++ 6.0.29 (GCC 11).

O `/tmp/cores` é um overlay (`tmp-cores.mount`): a lowerdir é `/usr/lib/libretro` (SYSTEM) e a upperdir é `/storage/cores` (p8). O `emuelecRunEmu.sh` monta `EMU="${CORE}_libretro"` e carrega `/tmp/cores/${EMU}.so`, sem caso especial para nomes de SNES. Nenhum script de `/usr/bin` do SYSTEM cita `snes9x`. A lista de cores do sistema `snes` vem do `es_systems.cfg`: o ES lê a cópia em `/storage/.config/emulationstation/`, e o SYSTEM tem outra em `/usr/config/emulationstation/`. O `r36-thermal-log` grava a coluna `core` a partir do `--core=` do `emuelecRunEmu.sh` em execução.

O aparelho não tem rede: tudo entra e sai pelo cartão no PC. A p1 (FAT32) é gravável no PC sem root. A p8 (ext4) tem arquivos do root. O host tem podman e docker, mas nenhum cross-compiler para ARM. O `readelf` do host lê ELF ARM.

## Goals / Non-Goals

**Goals:**
- Um processo de compilação de cores que qualquer core futuro reaproveita trocando só a receita.
- As quatro variantes do `snes9x2005_plus` na imagem, ao lado do original, com o registro do que foi compilado e de como cada uma se saiu no Yoshi's Island.

**Non-Goals:**
- Trocar o core padrão de outros sistemas. (Trocar o do SNES era non-goal no plano original; o usuário decidiu promover o vencedor nesta change, veja "Promoção".)
- Atualizar o fonte para o master do upstream. Ele continua em `fd45b0e`, o mesmo da base, para isolar o efeito das flags.
- Benchmark automático (por exemplo um script no sistema Ports). Fica registrado como opção para cores futuros.
- Fazer o `./build.sh` compilar cores ou depender do podman.

## Decisions

### Estrutura no repositório

```
cores.sh                               wrapper uv (como build.sh/flash.sh)
tools/r36img/cores.py                  compilar, verificar, perfil, resumo
cores/toolchain/Containerfile          FROM debian:bookworm@sha256:<digest>
cores/toolchain/a33-cc                 wrapper do compilador (abaixo)
cores/snes9x2005_plus/receita.toml     fonte, make, variantes
cores/snes9x2005_plus/pgo/*.gcda       perfil do treino (binário)
cores/snes9x2005_plus/builds.jsonl     uma linha por compilação aceita
cores/snes9x2005_plus/RESULTADOS.md    protocolo e resultado das sessões
features/53-cores-a33/feature.toml
features/53-cores-a33/system/usr/lib/libretro/snes9x2005_plus_a33_<v>_libretro.{so,info}
features/53-cores-a33/system/usr/config/emulationstation/es_systems.cfg
features/53-cores-a33/storage/.config/emulationstation/es_systems.cfg
```

- **Uma feature para todos os cores recompilados (`53-cores-a33`)**, e não uma por core. Os próximos cores acrescentam arquivos e linhas no mesmo `es_systems.cfg`, e não há conflito de caminho entre features. Alternativa descartada: uma feature por core, porque cada uma traria a própria cópia do `es_systems.cfg` e o build falharia por conflito de caminho, exigindo uma cadeia de `[[override]]`.
- **Os binários são commitados na feature**, com `*.so binary` e `*.gcda binary` no `.gitattributes`. São poucos e pequenos (cerca de 0,5 a 2 MB cada). O `./build.sh` continua sem podman e sem rede para cores. Alternativas descartadas: `[[external]]`, que exige uma URL pública para hospedar os binários; e compilar dentro do `./build.sh`, que tornaria o build da imagem dependente de podman, rede e minutos de compilação.
- **`.info` e `es_systems.cfg` commitados como arquivos derivados da base**, como o `ppsspp.ini` da `52-psp-desempenho`. Os testes `@needs_base` conferem que a diferença para a base é só a esperada: `display_name`/`display_version` no `.info` e as quatro linhas `<core>` no `es_systems.cfg`. O `es_systems.cfg` vai nas duas camadas, idênticas, também como no PSP: a do `/storage` é a que o ES lê, e a do SYSTEM cobre um `/storage` recriado.

### Toolchain

- **Debian bookworm em podman rootless**, com `gcc-arm-linux-gnueabihf` (GCC 12.2) e `libc6-dev-armhf-cross` (glibc 2.36, a mesma da base). A imagem de origem é fixada por digest no `Containerfile`. O build roda com `--userns=keep-id`, montagens com `:Z` (SELinux no Fedora) e o fonte sempre em `/build/src`. Alternativas descartadas: Ubuntu 22.04 (glibc 2.35 e GCC 11, mas o libstdc++ cross de lá não é garantidamente o 6.0.29, então não resolve o C++ e só troca uma diferença por outra) e toolchain no host (o Fedora não empacota uma glibc armhf para cross).
- Os pacotes do apt podem andar entre point releases do bookworm. Em vez de fixá-los por `snapshot.debian.org`, a versão do compilador vai no `builds.jsonl` em toda compilação. Se o binário de uma recompilação mudar, o registro mostra o porquê.
- **GCC 12 contra o 11.3 da base:** para um core em C que só depende da libc, a diferença não importa. A checagem de `GLIBCXX_` (máximo `3.4.29`) já impede um core C++ futuro de sair incompatível. Como resolver isso para C++ (`-static-libstdc++` ou GCC 11) fica para a change desse core.

### Como as flags entram: wrapper do compilador

O Makefile do upstream monta `CFLAGS` por plataforma, com `+=` e o próprio `-O2`. Passar `CFLAGS=...` na linha de comando do `make` substituiria tudo, inclusive defines de que o core precisa. Por isso o `make` roda com `platform=armv8-hardfloat-neon CC=a33-cc`, e o `a33-cc` chama `arm-linux-gnueabihf-gcc "$@" $A33_FLAGS`. As flags da variante entram **por último**, e no GCC o último `-O`/`-mcpu` vale. O wrapper também registra cada linha de comando efetiva num log, que vai resumido para o `builds.jsonl`. `AR` aponta para `arm-linux-gnueabihf-gcc-ar`, para o LTO funcionar com arquivos `.a` intermediários, se houver (no `snes9x2005` não há: ele só liga os `.o`).

- **`platform=armv8-hardfloat-neon`, o mesmo da base, e não `platform=unix`** (decidido na tarefa 2.1). O ramo `unix` acrescenta `-fno-builtin`, que a base não tem e que impede o GCC de expandir `memcpy`/`memset` em linha; isso misturaria uma flag a mais na comparação. O ramo `armv` acrescenta `-marm -mfloat-abi=hard -mfpu=neon -DARM` (o fonte não usa `ARM`, e o `-mfpu` do wrapper vem depois). O `CC = gcc` desse ramo não atrapalha, porque o `CC` da linha de comando do `make` vale sobre o do Makefile, e o `LD` é `$(CC)`.

- Flags comuns: `-marm -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -DNDEBUG -flto=auto -fuse-linker-plugin -ffunction-sections -fdata-sections` na compilação; mais `-Wl,--gc-sections -Wl,-O1 -s` na ligação. Elas vão em todas as chamadas, porque com LTO o nível de otimização também conta na ligação.
- Variantes na receita: `o2` = `-O2`; `o3` = `-O3`; `pgo_treino` = nível de `base` + `-fprofile-generate=/storage/roms/pgo/snes9x2005_plus -fprofile-update=single`; `pgo` = nível de `base` + `-fprofile-use=/storage/roms/pgo/snes9x2005_plus -fprofile-partial-training -Werror=missing-profile -Werror=coverage-mismatch`. O campo `base` das duas variantes de PGO é preenchido com o vencedor depois das sessões 1–3.
- Versão: `GIT_VERSION=" fd45b0e a33-<variante>"` na linha do `make`, com as aspas fazendo parte do valor (o Makefile faz `-DGIT_VERSION=\"$(GIT_VERSION)\"`). A variável da linha de comando vale sobre o `GIT_VERSION :=` do Makefile, então não precisa de patch. O `libretro.c` monta `"v1.36" GIT_VERSION`.
- Descartadas e registradas na receita com o motivo: `-Ofast`/`-ffast-math` (o core é quase todo inteiro, então o ganho fica perto de zero e há risco no áudio), `-mthumb` (fica para uma variante futura), unroll e align manuais (o PGO cuida deles), Graphite e `-fipa-pta` (ganho marginal, risco de bug do compilador), `-fno-plt` (só afeta chamadas à libc).

### PGO

- **Mesmo caminho no gerar e no usar.** O instrumentado grava em `/storage/roms/pgo/snes9x2005_plus/` (p1), com nomes derivados do caminho de cada objeto (`#build#src#...gcda`). No build com perfil, o container monta `cores/snes9x2005_plus/pgo/` exatamente nesse caminho, e o fonte continua em `/build/src`. Assim os nomes batem sem `-fprofile-prefix-map`.
- **`-fprofile-partial-training`:** o código que o treino não exercitou, como SA-1, Cx4 e DSP-1, continua com otimização normal, em vez de ser tratado como frio e otimizado só para tamanho. Os jogos de fumaça fora do treino conferem isso.
- **Importar o perfil:** `./cores.sh perfil snes9x2005_plus <R36-ROMS montada>/pgo/snes9x2005_plus` copia os `.gcda` para o repositório, confere que há um por objeto do instrumentado e registra os hashes. O build `pgo` falha se faltar perfil ou se ele não corresponder ao fonte (`-Werror=missing-profile`, `-Werror=coverage-mismatch`).
- **Sair pelo menu do RetroArch** (*Quit*): o libgcov grava ao fim do processo ou quando a biblioteca é descarregada. Se o processo for morto, nada é gravado. O `RESULTADOS.md` traz esse passo, e a primeira sessão de treino confere que os arquivos apareceram.

### Checagem de ABI

`./cores.sh verificar` lê `readelf -A -d -V --dyn-syms -W` de cada `.so` e falha quando:

- algum `NEEDED` não existe no `/usr/lib` da base;
- há um `GLIBC_` acima de 2.36 ou um `GLIBCXX_` acima de 3.4.29;
- falta `Tag_ABI_VFP_args: VFP registers`, ou não é ARMv7 com VFPv4;
- algum `retro_*` exportado está em endereço ímpar (Thumb);
- há seções `.debug_*`.

A lista de bibliotecas e os limites saem da base pela própria `r36img`, quando a base está disponível, e senão de constantes no código. A checagem roda no fim de `compilar`, antes de copiar para a feature, e também num teste sobre os binários commitados.

### Nomes e identidade do core

O arquivo, a entrada no ES e o `display_name` do `.info` (`Nintendo - SNES / SFC (Snes9x 2005 Plus A33 O3)`) mudam por variante. O `library_name` interno continua `Snes9x 2005 Plus`, então as opções do core, os overrides e os saves são os mesmos do original. Isso deixa a comparação justa (mesmas opções) e o save do Yoshi passa de uma variante para outra. Os savestates também devem funcionar, porque o fonte é o mesmo. A variante carregada aparece na versão (`a33-o3`) e na coluna `core` do CSV térmico.

### snes9x2010 (acrescentado depois da primeira rodada)

Na primeira rodada, o defeito de som num ponto do Yoshi's Island apareceu no original e nas duas variantes do 2005_plus. Como o fonte é o mesmo nos três, o defeito é da emulação, não das flags. O usuário pediu para comparar com o `snes9x2010` (Snes9x 1.52, mais preciso e mais pesado), que já vem na base.

- **Fonte:** `d8b10c4cd7606ed58f9c562864c986bc960faaaf`, o `PKG_VERSION` do EmuELEC v4.7 (`PKG_SHA256` `7faf4243…302`, igual ao do tarball). A versão do `.so` da base é `1.52.4 d4e2b9a`: o mesmo hash do fork do 2005_plus, o que confirma que ele vem da árvore de build. Até 2026-03-31 o upstream só mudou CI e o `Makefile.libretro`, e as chaves de opção do binário da base são as do `libretro.c` desse commit.
- **Make:** o EmuELEC roda `make -f Makefile.libretro` sem `platform`, que no Linux cai em `unix`: `-O2`, `-flto` e `-fPIC` no próprio Makefile, sem `-fno-builtin`. A receita passa `platform=unix` explícito. O core é só C e depende de `libc.so.6` e `libm.so.6`.
- **Variantes:** só `o2` e `o3`. O original da base já tem LTO, então o `_o2` mede quase só a troca de compilador e de `-mcpu`. O PGO do 2010 entra depois, se o 2010 for o caminho.
- **Escolha entre 2005_plus e 2010:** o mesmo critério dos 5%, mais o defeito de som. Se o 2010 corrige o som e roda liso, ele vira o candidato mesmo usando mais CPU.
- O upstream do 2010 voltou a ter commits em 2026 (thread de renderização, SIMD na PPU). Atualizar o fonte continua fora desta change, mas fica como opção para o 2010 numa change futura.

### Avaliação

O protocolo fica no `RESULTADOS.md`:

- **Antes de cada sessão:** aparelho frio, bateria acima de 50% e `maxperf` ligado só no Yoshi (opção por jogo no ES, que vale para qualquer core). Ligar o FPS na tela do RetroArch (*On-Screen Display > Notifications > Display Framerate*).
- **Sessão:** jogar 1-1 e 1-2 inteiras e sair pelo menu do RetroArch.
- **Ordem:**
  1. original, `_o2`, `_o3`: escolhe o vencedor;
  2. `_pgo_treino`: Yoshi 1-1 e 1-2, e opcionalmente DKC e Kirby Super Star por cerca de 3 min;
  3. `_pgo`;
  4. fumaça (Star Fox, Mega Man X2, Super Mario Kart e Kirby Super Star, 2–3 min cada no `_pgo` ou no candidato).
- **Critério:** se um core engasga e o outro não, ganha o que não engasga. Se os dois rodam lisos, ganha o de menor ocupação média de CPU no resumo térmico. Diferença abaixo de 5% conta como empate, e o empate favorece o `-O2` (menor e mais perto da base). O `_pgo` só ganha se superar o vencedor sem perfil por esse mesmo critério.
- **`./cores.sh resumo <r36-thermal.csv> [--roms <R36-ROMS montada>]`** separa as sessões por (`boot`, `core`, `rom`) contíguos e imprime uma tabela Markdown para colar no `RESULTADOS.md`. Cada linha tem duração, ocupação média e máxima (média de `cpu0`–`cpu3` online), `cpu_mhz` médio, `cpu_max_mhz` e temperatura no início e no fim. Com `--roms`, mapeia `/storage/roms/...` para o ponto de montagem e calcula CRC32 e SHA1 de cada ROM.

### Gravações

| # | Gravação | O que chega | Sessões |
|---|---|---|---|
| 1 | imagem com `--keep-roms --wipe-storage` | `_o2`, `_o3` e o `es_systems.cfg` já com as quatro entradas | original, `_o2`, `_o3` |
| 2 | `--part system` | `_pgo_treino` | treino |
| 3 | `--part system` | `_pgo` final | `_pgo` e fumaça |

Até a gravação 2, o `_pgo_treino` e o `_pgo` aparecem no menu sem binário, e escolher um deles falha ao abrir. O `RESULTADOS.md` avisa disso. Essa é a troca por ter um único `--wipe-storage`.

### Documentação

- **`CLAUDE.md` novo na raiz:** regras de trabalho (shell sem `cd` e sem encadeamento, sem sudo, Python via uv, branch por change, regras duráveis no `CLAUDE.md` e decisões nos artefatos OpenSpec), fatos do aparelho (acesso só pelo cartão SD, ABI da base, overlay de cores) e a origem da imagem base.
- **`README.md`:**
  - acrescentar a regra "sem rede, SSH nem Wi-Fi" em "O aparelho e por que só esta base funciona";
  - trocar "por SSH ou no terminal do aparelho" da seção do swap por um caminho que funcione sem rede, ou pelo terminal do aparelho;
  - incluir um item para a feature `53-cores-a33`;
  - incluir uma subseção "Compilar um core" em "Para desenvolvedores".

### Promoção (decidida depois da avaliação)

- **Nome:** `snes9x2005_plus_a33`. O arquivo é o mesmo binário do `_o2` (mesmo sha256), copiado com o nome novo; a versão interna continua `v1.36 fd45b0e a33-o2`, que diz de onde ele veio. Na receita, a variante `o2` passa a ter `nome = "snes9x2005_plus_a33"`, e o `builds.jsonl` continua casando pela variante e pelo sha256.
- **O que fica na imagem:** só o `snes9x2005_plus_a33` (`.so` e `.info` com `display_name` "Snes9x 2005 Plus A33") e uma linha `<core>snes9x2005_plus_a33</core>` no fim do bloco `snes` do `es_systems.cfg`. O `_o3`, o `_pgo_treino`, o `_pgo` e as duas variantes do `snes9x2010` saem da feature. As receitas, os registros, o perfil e o `RESULTADOS.md` ficam em `cores/`, e as variantes continuam compiláveis. No `./cores.sh verificar`, variante sem binário na feature aparece como "fora da feature".
- **Padrão:** `snes.core=snes9x2005_plus_a33` na `emuelec.conf` da `10-ptbr-sao-paulo`, onde o `snes.core` já está. Copiar a `emuelec.conf` inteira para a 53 exigiria um `[[override]]` e duplicaria o arquivo. A troca é que a 10 passa a depender da 53, e um teste falha se a 53 estiver desligada e o `snes.core` apontar para o core dela.
- **Por que promover sem ganho perceptível:** 10% menos CPU significa menos calor e mais folga quando o aparelho esquenta e cai para 1104 MHz; e o original continua um clique de distância no menu do ES.

## Risks / Trade-offs

- [O `make` do upstream ignora o `CC` em algum alvo, ou acrescenta flags depois das nossas na ligação] → o log do wrapper mostra cada linha efetiva. Um teste no `builds.jsonl` confere que o último `-O` é o da variante, e a checagem de atributos ELF pega uma ISA errada.
- [O perfil não casa por diferença de caminho ou de nome de objeto sob LTO] → mesmo caminho fixo no gerar e no usar, conferência de um `.gcda` por objeto na importação e `-Werror=coverage-mismatch`/`-Werror=missing-profile` no build `pgo`.
- [O RetroArch é morto ao sair e o perfil não é gravado] → sair pelo menu do RetroArch, e conferir os arquivos na p1 logo depois da primeira sessão de treino.
- [O instrumentado roda lento demais para jogar] → é esperado. O perfil conta proporções, não tempo. Se ficar injogável, encurtar o treino para 1-1.
- [Avaliação jogando é ruidosa] → mesmo trecho, aparelho frio e clock fixo, limiar de 5% para empate, e registro da temperatura inicial para descartar sessões fora do padrão.
- [Mudança de GCC 11.3 para 12.2 confunde o efeito das flags] → a variante `_o2` mede justamente "mesmo nível, outro compilador mais LTO". Se ela empatar com o original, o ganho do `_o3`/`_pgo` é das flags.
- [`--wipe-storage` apaga o estado do `/storage` (configurações, ES)] → mesmo procedimento das changes anteriores, com `--keep-roms`. As ROMs e o que está na p1 ficam.
- [Entradas do ES sem binário entre as gravações 1 e 3] → aviso no `RESULTADOS.md`. Na pior hipótese, o jogo não abre e volta ao menu.
- [Binários no git crescem a cada recompilação] → só a versão atual de cada variante fica na feature. O histórico de sha256 fica no `builds.jsonl`.

## Migration Plan

- Para voltar atrás num cartão gravado: escolher o `snes9x2005_plus` nas opções do sistema SNES no ES (vale para todos os jogos) ou por jogo.
- Para voltar atrás na imagem: `snes.core=snes9x2005_plus` na `emuelec.conf` da `10-ptbr-sao-paulo` e, se quiser, `enabled = false` na `53-cores-a33`; novo build e gravação com `--wipe-storage`. O original nunca foi tocado.
