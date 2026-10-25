# Tasks

## 1. Obtenção do Código Fonte e Compilação do Binário

- [x] 1.1 Definir o commit estável upstream do ClassiCube e obter o código fonte em C99 verificado por sha256.
- [x] 1.2 Compilar o binário `ClassiCube` no container isolado (`cores/toolchain`) com flags de arquitetura para o Allwinner A33 (`-O2 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard`), ativando `-DCC_BUILD_SDL2` e `-DCC_BUILD_GLES`.
- [x] 1.3 Executar checagem de ABI no binário gerado, validando ausência de símbolos de glibc superiores a `GLIBC_2.36` e garantindo conformidade com as bibliotecas da base (`libSDL2-2.0.so.0`, `libGLESv2.so.2`, `libEGL.so.1`, etc.).

## 2. Preparação de Ativos Offline e Scripts de Integração

- [x] 2.1 Preparar e empacotar o pacote de texturas clássicas em `texpacks/default.zip` e a biblioteca de áudio em `audio/` para operação 100% offline.
- [x] 2.2 Gerar o arquivo de configuração pré-definido `options.txt` com resolução nativa de 640x480, tela cheia, sensibilidade de controle calibrada e configurações de vídeo otimizadas.
- [x] 2.3 Criar o script inicializador `ClassiCube.sh` em `ports_scripts/`, com exportação de bibliotecas, tratamento de permissão em FAT32 e inicialização do jogo.
- [x] 2.4 Estruturar a camada de feature no pipeline de imagem para instalar os arquivos em `/storage/roms/ports/classicube/` e o lançador em `/storage/roms/ports_scripts/`.

## 3. Testes Automatizados e Validação

- [x] 3.1 Escrever teste unitário em `tests/` para verificar a conformidade de ABI do binário do ClassiCube e a sintaxe do script de inicialização.
- [x] 3.2 Executar a suíte completa de testes com `uv run python -I -m unittest discover -s tests` e confirmar 100% de aprovação.
- [x] 3.3 Validar a geração da imagem com `./build.sh` e inspecionar a partição de ROMs/Ports confirmando a inclusão de todos os arquivos.
