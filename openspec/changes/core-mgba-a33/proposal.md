# Proposal

## Why

O emulador mGBA original da base EmuELEC roda no Allwinner A33 como interpretador genérico sem otimizações específicas para o microcórtex ARM Cortex-A7 (VFPv4 e NEON). Embora o gpSP continue sendo o core padrão ideal para manter 60 FPS com Dynarec na maioria dos jogos, o mGBA é preferido para jogos com relógio em tempo real (RTC), recursos especiais e maior acurácia de emulação. Recompilar o mGBA com flags específicas para a arquitetura do A33 (`-O2`, `-mcpu=cortex-a7`, `-mfpu=neon-vfpv4`, `-flto`) e adicioná-lo como variante selecionável (`mgba_a33`) reduz o consumo de CPU em títulos 2D e oferece melhor estabilidade térmica sem quebrar a compatibilidade da imagem base.

## What Changes

- Adiciona a receita versionada `cores/mgba/receita.toml` no pipeline de build `./cores.sh`.
- Define a variante `o2` do mGBA com otimizações para ARMv7-A Cortex-A7, NEON VFPv4, LTO e seções de lixo eliminadas (`--gc-sections`).
- Gera o binário `mgba_a33_libretro.so` e seu arquivo `.info`, testado e validado contra a ABI da base (`glibc 2.36`, ARM hard-float).
- Registra o core compilado em `cores/mgba/builds.jsonl` e documenta o resultado da fumaça em `cores/mgba/RESULTADOS.md`.
- Disponibiliza o core `mgba_a33` no EmulationStation (`es_systems.cfg`) para o sistema GBA como opção selecionável por jogo ou sistema.
- Mantém o core original `mgba` e o padrão `gpsp` inalterados.

## Capabilities

### New Capabilities

*(Nenhuma nova capability necessária)*

### Modified Capabilities

- `gba-emulation`: Adiciona o requisito para inclusão do core `mgba_a33` (mGBA recompilado para o A33) selecionável no EmulationStation, mantendo o original intacto e o gpSP como padrão.

## Impact

- **Build / Toolchain:** Utiliza o container existente em `cores/toolchain` via `./cores.sh` sem alterações de infraestrutura.
- **Imagem e Partições:** Novo arquivo em `/usr/lib/libretro/mgba_a33_libretro.so` (partição SYSTEM / p8) e entrada adicional na lista de cores do GBA em `es_systems.cfg`.
- **Compatibilidade:** Totalmente compatível com saves e savestates existentes do mGBA, mantendo o gpSP como padrão intocado.
