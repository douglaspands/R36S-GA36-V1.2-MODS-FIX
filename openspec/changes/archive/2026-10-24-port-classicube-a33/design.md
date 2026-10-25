# Design

## Context

O console R36S clone (placa GA36-MB V1.2) utiliza o SoC Allwinner A33 com quatro núcleos ARM Cortex-A7 @ 1.2 GHz (32-bit `armhf`), GPU ARM Mali-400 MP2 (OpenGL ES 1.1 / 2.0), 512 MB de RAM e sistema EmuELEC 4.7 "Nexus" (kernel sunxi 3.4.39, glibc 2.36). O console não possui Wi-Fi nem rede.

O ClassiCube é uma reimplementação em C puro (C99) do Minecraft Classic, amplamente portada para dispositivos embarcados e consoles retro. Ele é construído modularmente e suporta compilação direta com SDL2 e OpenGL ES 2.0 nativo.

O EmuELEC gerencia ports nativos via EmulationStation lendo scripts `.sh` em `/storage/roms/ports_scripts` e dados em `/storage/roms/ports/<jogo>`. A partição de ROMs (`p1`, FAT32) é acessível e gravável em qualquer computador comum sem privilégios de root.

## Goals / Non-Goals

**Goals:**
- Compilar o binário `ClassiCube` para ARMv7-A hard-float com otimização `-O2` e flags de microrquitetura Cortex-A7 (`-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard`).
- Vincular o executável aos backends nativos SDL2 (`CC_BUILD_SDL2`) e OpenGL ES 2.0 (`CC_BUILD_GLES`).
- Garantir compatibilidade estrita com a ABI da base (`GLIBC_ <= 2.36`, bibliotecas dinâmicas `/usr/lib/libSDL2-2.0.so.0`, `/usr/lib/libGLESv2.so.2` e `/usr/lib/libEGL.so.1`).
- Incluir previamente todos os arquivos de dados necessários para execução offline (pacote de texturas clássicas em `texpacks/default.zip`, sons em `audio/` e configuração pré-definida em `options.txt` para 640x480).
- Fornecer o script inicializador `ClassiCube.sh` em `ports_scripts/` para integração transparente com o menu "Ports" do EmulationStation.
- Configurar o mapeamento dos botões físicos e analógicos do console para jogabilidade imediata.

**Non-Goals:**
- Não suportar modo multiplayer online (o console não possui hardware de rede).
- Não emular versões recentes do Minecraft Java (1.12+ ou 1.20+) ou Minecraft Bedrock, que extrapolam a memória e a GPU do A33.
- Não alterar bibliotecas do sistema ou a integridade de emuladores existentes.

## Decisions

### Decisão 1: Toolchain isolada em container (cores/toolchain)
- **Escolha:** Compilar o código fonte do ClassiCube dentro do mesmo container Debian Bookworm utilizado para os cores libretro do projeto (`arm-linux-gnueabihf-gcc`).
- **Racional:** O container Debian Bookworm possui `glibc 2.36`, exatamente a mesma versão da imagem base do EmuELEC 4.7. Isso assegura que nenhum símbolo de glibc mais novo (como 2.37 ou 2.38) contamine o binário.

### Decisão 2: Backend de Renderização Direto OpenGL ES 2.0
- **Escolha:** Utilizar `-DCC_BUILD_GLES` (OpenGL ES 2.0) em conjunto com `-DCC_BUILD_SDL2`.
- **Racional:** A GPU Mali-400 MP2 não suporta OpenGL desktop nativo. Wrappers como GL4ES adicionam sobrecarga de tradução de chamadas e incompatibilidades com shaders. O ClassiCube possui pipeline GLES 2.0 nativo e leve, conectando-se diretamente às bibliotecas `libGLESv2.so.2` e `libEGL.so.1` do driver Mali da Allwinner.

### Decisão 3: Localização dos Arquivos na Partição de ROMs (p1)
- **Escolha:** Estruturar o jogo dentro de `/storage/roms/ports/classicube/` e o lançador em `/storage/roms/ports_scripts/ClassiCube.sh`.
- **Racional:** Como a `p1` é FAT32, o usuário pode adicionar novos mapas (`.cw`), trocar pacotes de textura (`texpacks/`) ou fazer backup de suas criações diretamente pelo leitor de cartão SD do PC, sem necessidade de ferramentas de ext4 ou privilégios de root.

### Decisão 4: Empacotamento de Ativos Offline
- **Escolha:** Fornecer o arquivo `default.zip` e a estrutura de pastas `audio/` no momento do build da imagem.
- **Racional:** Na versão desktop para PC, o ClassiCube baixa as texturas clássicas do servidor da Mojang/ClassiCube na primeira execução. Em um aparelho offline, isso causaria tela preta ou blocos sem textura.

### Decisão 5: Mapeamento de Controles
- **Escolha:** Pré-configurar `options.txt` e disponibilizar as definições de controle do SDL2 para o joystick embutido do clone.
- **Racional:** O ClassiCube lê gamepads via subsistema SDL2 Joystick/GameController. Caso o driver do kernel exponha o controle como teclado/eventos brutos, o script inicializador pode acionar o `gptokeyb` (já presente em `/usr/bin/gptokeyb` e `/storage/.config/emuelec/configs/gptokeyb/`) como camada de compatibilidade transparente.

## Risks / Trade-offs

- **[Risco] Permissão de Execução em Partição FAT32 (p1)**  
  → *Mitigação:* O EmulationStation invoca o script através de `/usr/bin/bash %ROM%`, contornando a necessidade de bit `+x` no script em si. Se a montagem da FAT32 impedir a execução direta do binário `ClassiCube`, o script inicializador pode copiá-lo temporariamente para a memória RAM (`/tmp/classicube`, montada com permissão de execução) e executá-lo de lá, retornando os saves para a `p1`.
- **[Risco] Calibração de Deadzone do Analógico**  
  → *Mitigação:* Os analógicos do clone do R36S utilizam leitura ADC. A sensibilidade do analógico e a zona morta (deadzone) podem ser ajustadas previamente no arquivo `options.txt` do ClassiCube para evitar "drift" de câmera.
