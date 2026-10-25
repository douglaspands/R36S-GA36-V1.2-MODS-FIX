# Proposal

## Why

A emulação do Sega 32X no clone do R36S (GA36-MB V1.2) apresenta gargalos de desempenho perceptíveis em comparação com outros consoles portáteis de entrada. O SoC Allwinner A33 conta com quatro núcleos ARM Cortex-A7 (32-bit in-order) operando a até 1.2 GHz, sujeitos a throttling térmico para 1104 MHz ou 912 MHz sob carga contínua. Emular o 32X exige sincronizar simultaneamente dois processadores Hitachi SH-2 (23 MHz cada), um Motorola 68000, um Z80 e dois VDPs com blend de vídeo.

O core `picodrive_libretro.so` presente de fábrica na imagem base é um binário genérico (`ARMv7-VE`) de um snapshot antigo. Recompilar o PicoDrive a partir do upstream fixado do libretro, com otimizações específicas para o microcórtex Cortex-A7 (`-O2`, `-mcpu=cortex-a7`, `-mfpu=neon-vfpv4`, `-mfloat-abi=hard`, `-flto`) e Dynarec SH-2 ativado, permite reduzir o consumo de CPU em 5% a 15%, diminuindo perda de quadros e engasgos de áudio em jogos chave de 32X e Mega Drive.

## What Changes

- Criação da receita versionada `cores/picodrive/receita.toml` no pipeline de compilação `./cores.sh`.
- Configuração do make e flags de compilação direcionadas ao SoC A33, garantindo o uso do Dynarec ARM para os processadores SH-2 (`use_sh2drc=1`), otimização `-O2`, LTO e eliminação de seções não utilizadas (`--gc-sections`).
- Geração dos binários `picodrive_a33_libretro.so` e `picodrive_a33_libretro.info`, com validação estrita de conformidade da ABI da base (`GLIBC_ <= 2.36`, `libstdc++ <= 6.0.29`, ARM hard-float).
- Registro dos metadados de compilação em `cores/picodrive/builds.jsonl`.
- Integração do core `picodrive_a33` como opção selecionável no EmulationStation (`es_systems.cfg`) para o sistema `sega32x` (e secundariamente `megadrive`).
- Criação do documento `cores/picodrive/RESULTADOS.md` com protocolo de testes práticos no aparelho (medição de FPS, ocupação de CPU e dados térmicos via `r36-thermal.csv`).
- Preservação integral do `picodrive` original da imagem base para fallback e compatibilidade.

## Capabilities

### New Capabilities

- `sega32x-emulation`: Requisitos de emulação para a plataforma Sega 32X, incluindo a disponibilização do core `picodrive_a33` otimizado para o A33, coexistindo com o core de fábrica e compartilhando saves e configurações.

### Modified Capabilities

- *(Nenhuma capability existente modificada)*

## Impact

- **Build / Toolchain:** Execução em container isolado via `./cores.sh` sem dependências novas no host e sem necessidade de permissões de root.
- **Imagem e Partições:** Adição de `picodrive_a33_libretro.so` e `.info` na partição SYSTEM (`/usr/lib/libretro`) e atualização dos arquivos `es_systems.cfg` em `features/53-cores-a33`.
- **Compatibilidade:** Mantém total compatibilidade com saves (`.srm`), savestates e opções de core já existentes do PicoDrive.
