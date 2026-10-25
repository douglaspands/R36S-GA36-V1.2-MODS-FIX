# Proposal

## Why

O clone do R36S (placa GA36-MB V1.2) possui recursos de hardware estritamente delimitados: processador Allwinner A33 (quad-core ARM Cortex-A7 @ 1.2 GHz, 32-bit armhf), GPU ARM Mali-400 MP2 (compatível apenas com OpenGL ES 1.1 / 2.0, sem OpenGL desktop e sem Vulkan), 512 MB de memória RAM compartilhada e ausência total de conectividade de rede (sem Wi-Fi nem porta Ethernet).

Neste cenário:
1. O **Minecraft Java Edition** é totalmente inviável: exige mais de 1 GB de RAM alocada para a JVM e suporte a OpenGL Desktop 2.1+, resultando em encerramento imediato pelo kernel por falta de memória (OOM) e ausência de aceleração gráfica.
2. O **Minecraft Bedrock Edition** moderno é incompatível por exigir binários ARM64 (AArch64) e OpenGL ES 3.0 / Vulkan.
3. O **ClassiCube** é uma recriação completa, leve e de código aberto em C puro (C99) da experiência clássica de blocos/voxel (Minecraft Classic / Alpha). Ele consome entre 20 e 40 MB de memória RAM, possui renderizador nativo em OpenGL ES 2.0 perfeitamente compatível com a Mali-400 e roda a 60 FPS cravados na resolução nativa de 640x480 do portátil.

Prover o ClassiCube pré-configurado e compilado nativamente para a arquitetura do A33 viabiliza uma experiência autêntica e fluida de Minecraft no console, integrada diretamente à biblioteca do EmulationStation sem sobrecarregar a memória do sistema.

## What Changes

- **Compilação hermética para ARMv7-A / A33:** Compilação do ClassiCube a partir do código fonte upstream em C99 utilizando a toolchain isolada (`cores/toolchain` com GCC armhf, glibc 2.36), flags de microrquitetura `-O2 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard` e backends nativos SDL2 (`CC_BUILD_SDL2`) e OpenGL ES 2.0 (`CC_BUILD_GLES`).
- **Conformidade de ABI:** Validação estrita das dependências dinâmicas contra as bibliotecas já fornecidas pela partição `SYSTEM` da base (`libc.so.6`, `libm.so.6`, `libpthread.so.0`, `libdl.so.2`, `libSDL2-2.0.so.0`, `libGLESv2.so.2` e `libEGL.so.1`).
- **Empacotamento offline de recursos:** Inclusão dos ativos indispensáveis para funcionamento sem internet (pacote de texturas `texpacks/default.zip`, arquivos de áudio e efeitos sonoros em `audio/` e configuração prévia de vídeo em `options.txt` para 640x480 em tela cheia).
- **Lançador nos Ports do EmuELEC:** Criação do script inicializador `ClassiCube.sh` (visível no menu "Ports" do EmulationStation em `/storage/roms/ports_scripts/`) que configura as variáveis de ambiente necessárias e invoca o binário em `/storage/roms/ports/classicube/ClassiCube`.
- **Mapeamento de Controles:** Configuração do gamepad embutido do R36S clone para movimentação analógica, seleção de blocos, pulo, quebra e colocação de blocos via gamepad nativo SDL2 ou perfil de mapeamento `gptokeyb`.
- **Testes e Validação:** Adição de testes unitários automatizados cobrindo a conformidade de ABI do executável gerado, a integridade do script inicializador e a presença dos recursos obrigatórios.

## Capabilities

### New Capabilities

- `classicube-port`: Requisitos para compilação, validação de ABI, empacotamento offline de ativos e inicialização do ClassiCube como port nativo no EmuELEC do Allwinner A33.

### Modified Capabilities

- *(Nenhuma capability existente modificada)*

## Impact

- **Desempenho e Memória:** Ocupação mínima de memória RAM (~35 MB de 512 MB), consumo suave de CPU sem disparar throttling térmico, estabilizando em 60 FPS na tela de 640x480.
- **Partições e Armazenamento:** Os arquivos do port são organizados na partição de ROMs (p1, FAT32), acessível e editável pelo usuário no PC sem permissões de root.
- **Isolamento e Segurança:** Não altera cores de emuladores nem o comportamento de outros sistemas; opera de maneira autônoma através do lançador de ports padrão do EmuELEC.
