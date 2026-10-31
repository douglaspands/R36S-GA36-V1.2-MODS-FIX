# Proposal: console-love2d-standalone

## Why

O clone do R36S (GA36-MB V1.2, Allwinner A33, 1 GB RAM) atualmente não possui uma forma dedicada e otimizada de executar jogos desenvolvidos com o framework LÖVE (Love2D). O core `love_libretro` disponível para RetroArch é incompleto e incompatível com a maior parte dos jogos modernos em Lua, enquanto a execução como script isolado no menu "Ports" não proporciona a experiência visual de um console clássico com catálogo, capas e metadados. Integrar o LÖVE 11.x standalone compilado sob medida para o Cortex-A7/NEON com suporte a OpenGL ES 2.0 no Mali-400 e adicioná-lo como um sistema de primeira classe no EmulationStation transforma o aparelho em uma plataforma nativa para jogos indie em Lua com máxima fidelidade e desempenho.

## What Changes

- **Compilação hermética do LÖVE 11.x standalone:** Receita de compilação em container Debian Bookworm (`ports/love2d/`) otimizada para Allwinner A33 (`-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -O3`), com LuaJIT 2.1, SDL2 e suporte nativo a OpenGL ES 2.0 (`libGLESv2.so.2`), garantindo a disponibilidade das bibliotecas compartilhadas necessárias.
- **Lançador dedicado com gerenciamento de saída e log rotativo (`/usr/bin/love.sh`):** Script de inicialização que injeta variáveis de renderização GLES2 (`LOVE_GRAPHICS_USE_OPENGLES=1`), configura o gamepad integrado (`micro_gamepad`), detecta e propaga o idioma do console para o ambiente de execução (`CONSOLE_LANG`, `LANG`, `LANGUAGE`), instancia o `gptokeyb` em segundo plano para capturar o atalho de encerramento (`Select + Start`), devolvendo o controle suavemente ao EmulationStation com restauração da cadeia de áudio. Na fase de testes, implementa registro rotativo em `/storage/roms/love/love.log` (teto de 100 KB com histórico `love.log.1`) com flag de ativação (`ENABLE_LOG=1`), pronto para desativação futura sem remoção de código.
- **Console LÖVE no EmulationStation (`es_systems.cfg`):** Declaração do sistema `love` reconhecendo extensões `.love` e `.zip` na partição acessível pelo PC (`/storage/roms/love/` na FAT32 `R36-ROMS`).
- **Suporte visual e curadoria exclusiva no tema Epic Cody ML:**
  - Entrada visual do LÖVE no tema padrão `Epic Cody ML` com logotipo oficial e descrições localizadas em português (`pt-br`), inglês (`en`) e espanhol (`es-latam`).
  - Arte de poster em 640x480 para o LÖVE inspirada na identidade oficial do site https://love2d.org/.
  - Correção de diagramação com alinhamento à esquerda de `nameLabel` para eliminar colisão do título do console com o ícone da bateria e relógio no topo direito.
  - Inclusão do elemento `<text name="md_name">` abaixo da imagem da capa (`md_image`) nas visualizações detalhadas para exibição integral do nome do jogo.
  - Remoção dos temas secundários (`NES-BOX`, `Minimal EmuELEC`, `Graphite OGA`, `Switch` e `Crystal`) para evitar manutenção excessiva, concentrando o sistema 100% no tema curado `Epic Cody ML`.
- **Jogo de demonstração e validação (*Mr. Rescue*):** Inclusão do jogo livre e open-source *Mr. Rescue* (desenvolvido por Simon Larsen / Tangram Games) pré-instalado em `/storage/roms/love/` acompanhado de metadados (`gamelist.xml`) e capa (`images/mrrescue.png`), servindo como teste de aceitação de áudio, gráficos, física e entrada de controle.
- **Documentação e Guia para Desenvolvedores:** Seção dedicada sobre o LÖVE nos três idiomas dos READMEs (`README.md`, `README.pt-BR.md`, `README.es.md`) e em `docs/DESENVOLVIMENTO.md`, ilustrando formatos suportados, como jogar e exemplo de código em Lua demonstrando como jogos podem ler o idioma do console com fallback automático.

## Capabilities

### New Capabilities
- `love2d-engine`: Requisitos de compilação, ABI glibc 2.36, inicialização em framebuffer `mali-fbdev`, integração de controle via SDL2/gptokeyb, logging rotativo com toggle para diagnóstico de execução, empacotamento do lançador e configuração do sistema LÖVE no EmulationStation e partição de ROMs.

### Modified Capabilities
- `es-themes`: Requisitos de suporte visual no tema Epic Cody ML para o sistema `love2d`, arte de poster 640x480 inspirada em love2d.org, alinhamento à esquerda de `nameLabel`, renderização do nome completo do jogo via `md_name` abaixo da capa, e exclusividade temática com remoção dos temas extras secundários.

## Impact

- **Imagens e Partições:** Adiciona a nova feature `64-love2d` (ou arquivos correspondentes no SYSTEM e ROMS); não afeta negativamente o tamanho do SYSTEM. A remoção dos temas extras poupa centenas de megabytes no build e na partição de ROMs.
- **EmulationStation:** `es_systems.cfg` passa a ter a entrada do console LÖVE. Quando a pasta `roms/love` contiver jogos, o carrossel exibe o novo console automaticamente sob o tema único `Epic Cody ML`.
- **Hardware & Compatibilidade:** Execução direta no framebuffer `/dev/fb0` usando a GPU Mali-400 MP2 via EGL e GLES 2.0; aproveita o 1 GB de memória RAM para caches e texturas.
