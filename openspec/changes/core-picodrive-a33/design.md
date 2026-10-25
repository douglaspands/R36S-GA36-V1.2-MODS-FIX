# Design

## Context

O console portátil R36S clone (placa GA36-MB V1.2) é equipado com o SoC Allwinner A33 (CPU Quad-Core ARM Cortex-A7 @ 1.2 GHz, 32-bit armhf com VFPv4 e NEON). O sistema operacional é o EmuELEC 4.7 "Nexus" (kernel sunxi 3.4.39, glibc 2.36).

O sistema Sega 32X é um dos alvos de emulação mais exigentes para este hardware, pois depende de múltiplos coprocessadores e processamento de vídeo em camadas. O core de fábrica `picodrive_libretro.so` é um binário antigo compilado de forma genérica.

O repositório já dispõe de um ambiente hermético de compilação em container (`cores/toolchain` e `./cores.sh`) capaz de compilar variantes otimizadas de cores libretro, garantindo conformidade de ABI e rastreabilidade total.

## Goals / Non-Goals

**Goals:**
- Criar a receita `cores/picodrive/receita.toml` para compilação reproduzível do PicoDrive a partir de um commit fixado do libretro.
- Configurar o build com o Dynarec ARM para SH-2 ativado (`use_sh2drc=1`) e flags de microrquitetura Cortex-A7 (`-O2`, `-mcpu=cortex-a7`, `-mfpu=neon-vfpv4`, `-mfloat-abi=hard`, `-flto`).
- Assegurar compatibilidade rigorosa de ABI com a imagem base (`GLIBC_ <= 2.36`, ARM hard-float).
- Disponibilizar `picodrive_a33` como core selecionável no menu do EmulationStation (`es_systems.cfg`) para o sistema `sega32x` (e opcionalmente `megadrive`).
- Definir protocolo de avaliação no console com medição de FPS, ocupação de núcleos de CPU e temperatura.

**Non-Goals:**
- Não substituir ou deletar o binário `picodrive_libretro.so` da imagem base (imutabilidade e fallback seguro).
- Não reescrever módulos do PicoDrive ou do renderizador em código assembly customizado do zero.
- Não alterar as opções de outros emuladores de Mega Drive (como Genesis Plus GX).

## Decisions

### Decisão 1: Otimização `-O2` e LTO vs `-O3`
- **Escolha:** Adotar `-O2 -flto=auto -fuse-linker-plugin -ffunction-sections -fdata-sections -Wl,--gc-sections`.
- **Racional:** O Cortex-A7 possui pipeline in-order e cache L1 de instrução restrita a 32 KB. Como comprovado empiricamente na avaliação do `snes9x2005_plus` neste mesmo aparelho, `-O3` provoca expansão excessiva de laços e funções (*code bloat*), gerando *cache thrashing* e resultando em maior ocupação de CPU e maior aquecimento.
- **Alternativas consideradas:** `-O3` (descartado pelo risco de saturação da L1I); PGO imediato (mantido como possível evolução após validação da variante base `-O2`).

### Decisão 2: Dynarec SH-2 e Assembler ARM
- **Escolha:** Forçar a ativação do Dynarec ARM do SH-2 (`use_sh2drc=1`) e otimizações em assembly ARM (`ARM_ASM=1`) no Makefile.
- **Racional:** A emulação dos dois núcleos SH-2 via interpretador em C é inviável no A33 a 1.2 GHz. O recompilador dinâmico em assembly ARM é fundamental para que qualquer jogo de 32X atinja taxas jogáveis de quadros.

### Decisão 3: Nomeação e coexistence de cores
- **Escolha:** Nomear o binário gerado como `picodrive_a33_libretro.so` com o `.info` correspondente `picodrive_a33_libretro.info`.
- **Racional:** Permite manter o core original da fábrica totalmente intacto. No EmulationStation, o usuário pode selecionar tanto o `picodrive` padrão quanto o `picodrive_a33` por jogo ou globalmente para o sistema 32X, permitindo testes A/B diretos.

### Decisão 4: Integração via camada de features
- **Escolha:** Registrar o binário na partição SYSTEM e adicionar a entrada `<core>picodrive_a33</core>` no `es_systems.cfg` dentro de `features/53-cores-a33`.
- **Racional:** Mantém a separação declarativa da infraestrutura de montagem de imagem já adotada no projeto.

## Risks / Trade-offs

- **[Risco] Jogos com polígonos 3D pesados (Virtua Racing Deluxe, Star Wars Arcade) ainda oscilarem abaixo de 60 FPS**  
  → *Mitigação:* A recompilação alivia a carga de CPU, mas títulos 3D exigem ajustes complementares de core (ex: `picodrive_renderer = "fast"` e `picodrive_frameskip = "auto"` ou limiar 1). O protocolo de teste em `RESULTADOS.md` instruirá claramente o usuário sobre essas opções.
- **[Risco] Variação de clock por throttling térmico durante os testes**  
  → *Mitigação:* As sessões de teste no aparelho devem utilizar a opção `maxperf=1` do EmulationStation para fixar o clock da CPU e isolar o ganho real de instruções da variante.
