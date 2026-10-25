# Design

## Context

O console R36S clone (GA36-MB V1.2) é equipado com o SoC Allwinner A33 (CPU Quad-Core ARM Cortex-A7 @ 1.2 GHz, 32-bit armhf com VFPv4 e NEON). O sistema roda EmuELEC 4.7 com glibc 2.36 e kernel sunxi 3.4.39.
O repositório já possui uma infraestrutura de compilação em container (`cores/toolchain` e `./cores.sh`) que garante build reprodutível, sem privilégios de root no host e com verificação automática de conformidade de ABI (`glibc <= 2.36`, `libstdc++ <= 6.0.29`).

Veja `proposal.md` para a motivação e `specs/gba-emulation/spec.md` para os requisitos de sistema.

## Goals / Non-Goals

**Goals:**
- Criar a receita `cores/mgba/receita.toml` para compilação do core libretro do mGBA a partir de um commit fixado.
- Compilar a variante otimizada `o2` (`mgba_a33`) usando flags específicas do A33 (`-O2`, `-mcpu=cortex-a7`, `-mfpu=neon-vfpv4`, `-mfloat-abi=hard`, `-flto`).
- Garantir compatibilidade total de ABI com o userland da imagem base.
- Integrar `mgba_a33` como core selecionável no menu do EmulationStation (`es_systems.cfg`).
- Manter compatibilidade de saves de bateria (.srm) e opções de core com o mGBA original.

**Non-Goals:**
- Não alterar o core padrão do GBA (o `gpSP` permanece o padrão global).
- Não reescrever código do mGBA em Rust ou Assembly ARM, nem implementar Dynarec do zero.
- Não executar múltiplas rodadas exaustivas de treino PGO neste momento: a variante `-O2` é a meta direta para o teste de fumaça.

## Decisions

### Decisão 1: Otimização `-O2` com LTO em vez de `-O3`
- **Escolha:** Utilizar `-O2 -flto=auto -fuse-linker-plugin` em conjunto com seções de dados/funções (`-ffunction-sections -fdata-sections`) e remoção de seções mortas (`-Wl,--gc-sections`).
- **Racional:** O Cortex-A7 possui pipeline in-order e cache L1 de instrução restrita a 32 KB. Como observado na experiência do `snes9x2005_plus`, a agressividade de inlining e unrolling do `-O3` infla o código e provoca *cache thrashing*, tornando o desempenho inferior ao `-O2`.
- **Alternativas consideradas:** `-O3` (descartado pelo risco de saturação da cache L1); PGO imediato (descartado temporariamente pela complexidade de coleta no cartão físico).

### Decisão 2: Identificador `mgba_a33` e preservação do `.info`
- **Escolha:** Nomear o binário como `mgba_a33_libretro.so` e gerar seu correspondente `mgba_a33_libretro.info`. O campo `corename` ou `display_name` no `.info` identifica a variante, mas a biblioteca mantém compatibilidade com opções e saves do mGBA original.
- **Racional:** Permite manter o `mgba_libretro.so` original da fábrica intacto na imagem base. O usuário pode comparar os dois diretamente no menu do EmulationStation.
- **Alternativas consideradas:** Sobrescrever diretamente o `mgba_libretro.so` da fábrica (rejeitado para não violar o princípio de imutabilidade e permitir fallback).

### Decisão 3: Integração no EmulationStation via `features/`
- **Escolha:** Adicionar a entrada `<core>mgba_a33</core>` no arquivo `es_systems.cfg` sob o sistema `gba`, preservando `<core default="true">gpsp</core>`.
- **Racional:** Segue o mesmo padrão implementado com sucesso para o `snes9x2005_plus_a33` no sistema SNES.

## Risks / Trade-offs

- **[Risco] Jogos com polígonos 3D ou scaling pesado (Golden Sun, F-Zero) ainda apresentarem queda de FPS**  
  → *Mitigação:* O gpSP permanece configurado como padrão global. O mGBA A33 é recomendado para títulos 2D, jogos que utilizam RTC (Pokémon) ou que possuem falhas gráficas no gpSP.
- **[Risco] Dependências dinâmicas ausentes na base durante o linking**  
  → *Mitigação:* O Makefile do mGBA libretro permite compilar sem dependências externas pesadas ou utilizar implementações embutidas (`HAVE_STATIC_LIBPNG=1`, etc.). O script de ABI (`./cores.sh abi`) validará os símbolos antes do empacotamento.
