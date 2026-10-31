# Design: console-love2d-standalone

## Context

O console R36S clone deste repositório (GA36-MB V1.2) é equipado com SoC Allwinner A33 (4x Cortex-A7), 1 GB de memória RAM, GPU ARM Mali-400 MP2 e display LCD de 640x480 (4:3). O sistema operacional é o EmuELEC 4.7 sobre kernel Linux sunxi 3.4.39, operando diretamente sobre o framebuffer legacy (`/dev/fb0`) via driver de vídeo `mali-fbdev`, sem nenhum servidor gráfico (X11 ou Wayland). A biblioteca C do sistema é a glibc 2.36 e o GCC da base é a versão 11 (`GLIBCXX_3.4.29`).

Veja a motivação completa no `proposal.md`.

## Goals / Non-Goals

**Goals:**
- Compilar o binário oficial do LÖVE 11.5 hermeticamente em container Podman rootless (Debian Bookworm) com flags dedicadas ao Cortex-A7 e VFPv4/NEON, compatível com glibc <= 2.36, incluindo as bibliotecas compartilhadas necessárias.
- Executar jogos `.love` e `.zip` nativamente em tela cheia no framebuffer da GPU Mali-400 MP2 via EGL e OpenGL ES 2.0.
- Implementar o script lançador `/usr/bin/love.sh` com suporte a captura de atalho de saída (`Select + Start`) via `gptokeyb`, sem congelamento de processos e restaurando o ganho de áudio no encerramento.
- Implementar logging rotativo e checagem de dependências dinâmicas no lançador com chave de controle (`ENABLE_LOG=1` nos testes, desativável com `0`).
- Integrar o LÖVE como um videogame de primeira classe no carrossel do EmulationStation (`es_systems.cfg`), suportando lista de jogos, boxart/capturas e metadados na partição FAT32 (`/storage/roms/love/`).
- Adicionar visual completo para o LÖVE no tema padrão `Epic Cody ML` e catálogo em três idiomas (`pt-br`, `en`, `es-latam`), além de poster oficial 640x480 inspirado no love2d.org.
- Corrigir o alinhamento de `nameLabel` à esquerda e adicionar `md_name` abaixo da capa no `Epic Cody ML`.
- Remover temas adicionais (`NES-BOX`, `Minimal EmuELEC`, `Graphite OGA`, `Switch`, `Crystal`), unificando a manutenção exclusivamente no `Epic Cody ML`.
- Disponibilizar o jogo open-source *Mr. Rescue* pronto para execução no primeiro boot como validação técnica de aceitação.

**Non-Goals:**
- Executar o LÖVE através do RetroArch ou de cores `love_libretro` (a arquitetura é 100% standalone).
- Suportar jogos que exijam recursos de desktop OpenGL ou GLSL 3.0 indisponíveis no hardware do Mali-400 MP2.
- Adicionar suporte a emulação de teclado/mouse via teclado virtual na tela (jogos suportam gamepad nativo ou atalhos direcionais do D-pad).
- Manter temas secundários de terceiros ativos na imagem base.

## Decisions

### Decisão 1: LÖVE versão 11.5 como alvo do runtime
**Decisão:** Adotar a versão 11.5 do upstream LÖVE como motor padrão.
**Racional:** A versão 11.5 é o padrão consolidado em portáteis retrô (ArkOS, AmberELEC e PortMaster), suporta a vasta maioria dos jogos homebrew recentes e possui compatibilidade nativa com OpenGL ES 2.0 e LuaJIT 2.1.
**Alternativas consideradas:** LÖVE 0.10.2 (descartada por ser legado e não rodar jogos desenvolvidos após 2018); `love_libretro` (descartada pelo usuário e por ter compatibilidade deficiente).

### Decisão 2: Compilação hermética via Podman com Debian Bookworm
**Decisão:** Utilizar o ambiente de compilação já estabelecido no projeto (`cores/toolchain` e `ports/classicube`), baseado em `debian:bookworm` com cross-GCC `arm-linux-gnueabihf`.
**Racional:** Garante estrita conformidade com a ABI da imagem de fábrica (`GLIBC_2.36`), dispensando instalação de compiladores no host e executando sem `sudo`.
**Flags adotadas:**
`-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -O3 -fno-math-errno` combinadas com `-DLOVE_GRAPHICS_USE_OPENGLES=1`.

### Decisão 3: Lançador `/usr/bin/love.sh` com gptokeyb e restauração de áudio
**Decisão:** Criar um script wrapper dedicado para orquestrar a execução e saída do jogo.
**Racional:** Jogos standalone em fbdev não possuem o menu do RetroArch. Para que o jogador possa sair do jogo a qualquer momento com a convenção do console (`Select + Start`), o `gptokeyb` roda em background monitorando o `/dev/input/event*` do `micro_gamepad`. Ao detectar a combinação, ele emite `SIGTERM` no processo `love`. Em seguida, o lançador chama `/usr/lib/r36/audio-ganho aplica` para reativar o ganho analógico do codec de áudio (sunxi-pcm-codec), prevenindo problemas de volume baixo ao retornar ao menu.

### Decisão 4: Mapeamento de controle SDL2 nativo
**Decisão:** Injetar a variável de ambiente `SDL_GAMECONTROLLERCONFIG` com a string GUID exata do `micro_gamepad`.
**Racional:** Permite que jogos desenvolvidos com o subsistema `love.joystick` reconheçam os botões físicos, analógicos e D-pad nativamente como botões de controle de videogame, sem necessidade de tradução de teclas pelo gptokeyb.

### Decisão 5: Estrutura da pasta de ROMs e catálogo
**Decisão:** Mapear a pasta `/storage/roms/love/` na partição `R36-ROMS` (FAT32, p1).
**Racional:** Como a partição p1 é gravável diretamente no PC pelo jogador (sem root), o usuário pode copiar novos jogos `.love` e imagens de capa na pasta `images/`. O EmulationStation processa o `gamelist.xml` local e renderiza as capas na lista detalhada.

### Decisão 6: Identidade visual no tema Epic Cody ML
**Decisão:** Criar o diretório `Epic Cody ML/love2d/theme.xml` e inserir chaves no `_languages/` para os três idiomas suportados.
**Racional:** O tema Epic Cody ML gerencia dinamicamente as legendas de console através de variáveis `${love2d.sys_line1}` e `${love2d.sys_line2}`. Configuramos "Motor de Jogos" e "LÖVE" em português, e a arte utiliza o logotipo padrão do framework estilizado para a interface de 640x480.

### Decisão 7: Propagação de Idioma do Console para Jogos LÖVE
**Decisão:** Extrair o idioma configurado no EmuELEC no lançador `/usr/bin/love.sh` e exportá-lo via variáveis de ambiente (`CONSOLE_LANG`, `CONSOLE_LANG_SHORT`, `LANG`, `LANGUAGE`) e arquivo temporário `/tmp/console_lang`.
**Racional:** O idioma do sistema fica registrado em `/storage/.config/emuelec/configs/emuelec.conf` (`system.language`) ou `es_settings.cfg` (`Language`), com fallback para `en_US`. Jogos LÖVE em Lua podem ler `os.getenv("CONSOLE_LANG")` ou `os.getenv("LANG")` para selecionar sua tabela de localização (ex: `pt_BR`, `en_US`, `es_ES`). Caso o jogo não reconheça a variável ou não ofereça tradução para aquele código, deve reverter para seu idioma padrão (fallback) sem quebrar.

### Decisão 8: Log rotativo em partição acessível com chave de desativação configurável
**Decisão:** Implementar logging rotativo no `/usr/bin/love.sh` gravando em `/storage/roms/love/love.log` (partição FAT32 `R36-ROMS`, p1), controlado pela variável `ENABLE_LOG=1`.
**Racional:** Durante a fase de testes, diagnósticos detalhados de inicialização (como carregamento de bibliotecas dinâmicas e saída de console) são fundamentais para solucionar falhas silenciosas. O log em FAT32 é legível diretamente no PC pelo usuário sem root. A rotação em 100 KB (com histórico `love.log.1`) impõe teto rígido de 200 KB, protegendo o SD. A flag `ENABLE_LOG` permite que, concluída a validação ou em changes futuras, o logging seja desativado instantaneamente mudando `ENABLE_LOG=0`, sem deletar o código e preservando a infraestrutura para futuras manutenções.

### Decisão 9: Correção do alinhamento do `nameLabel` no tema Epic Cody ML
**Decisão:** Alterar o alinhamento de `nameLabel` de `right` para `left` em `theme.xml`.
**Racional:** Com `alignment` à direita e largura `0.65`, o texto colidia diretamente com o relógio e o indicador de bateria no canto superior direito (x > 0.85). Alinhado à esquerda a partir de x=0.33, o nome do console fica legível e visualmente limpo sem colidir com os elementos de status do sistema.

### Decisão 10: Inclusão do elemento `md_name` abaixo da capa do jogo
**Decisão:** Adicionar `<text name="md_name">` abaixo de `<image name="md_image">` na view `basic, detailed` e `video`.
**Racional:** A coluna de lista de jogos (`textlist`) ocupa apenas ~32% da largura da tela de 640x480 (`size 0.319`), fazendo com que jogos com nomes mais longos fiquem cortados. Adicionar o `md_name` abaixo da capa do jogo permite ao jogador ler imediatamente o nome completo do jogo selecionado.

### Decisão 11: Poster do console LÖVE inspirado no love2d.org
**Decisão:** Criar imagem de poster 640x480 para o console LÖVE baseada nos motivos e paleta oficial de https://love2d.org/.
**Racional:** Para manter a consistência visual com os demais consoles do tema `Epic Cody ML` e valorizar o sistema de jogos LÖVE, a imagem de fundo de 640x480 adota a identidade oficial (balões de coração, paleta rosa/azul/branco suave) alinhada à direita da composição, permitindo que a metade esquerda exiba as informações tipográficas sem conflito de contraste.

### Decisão 12: Unificação e foco exclusivo no tema Epic Cody ML
**Decisão:** Remover as entradas e arquivos dos temas secundários (`NES-BOX`, `Minimal EmuELEC`, `Graphite OGA`, `Switch` e `Crystal`) em `features/50-temas-extras/`.
**Racional:** Manter múltiplos temas acarreta carga de manutenção contínua toda vez que um console novo é adicionado ou ajustado. Focar 100% no tema curado `Epic Cody ML` simplifica o ecossistema, economiza espaço substancial no build e garante uma experiência visual uniforme no aparelho. Os temas podem ser reintroduzidos no futuro se solicitado.

## Risks / Trade-offs

- **[Mali-400 GLES 2.0 e limitações de shaders]** → *Risco:* Jogos que tentem compilar shaders com instruções de OpenGL moderno ou GLSL 3.0 falharão. *Mitigação:* A variável `LOVE_GRAPHICS_USE_OPENGLES=1` é exportada antes da inicialização, instruindo a engine a utilizar o pipeline de compatibilidade móvel.
- **[Resoluções fixas de janela definidas no conf.lua]** → *Risco:* Alguns jogos são programados para 800x600 ou 1280x720. *Mitigação:* O driver SDL2 em `mali-fbdev` cria uma janela fullscreen do tamanho físico do display (640x480) e o subsistema de escala interna do LÖVE redimensiona a imagem proporcionalmente.
- **[Persistência de saves na partição FAT32]** → *Risco:* LÖVE por padrão tenta gravar dados em `~/.local/share/love/<game>`. *Mitigação:* No lançador ou na configuração do sistema, garantimos que `HOME=/storage` para que as gravações fiquem seguras na partição p8 ou montadas adequadamente.
