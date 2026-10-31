# Spec Delta: love2d-engine

## Purpose

Define os requisitos de compilação, compatibilidade de ABI, inicialização standalone, gerenciamento de controle e integração com o EmulationStation para execução de jogos LÖVE 2D no Allwinner A33.

## ADDED Requirements

### Requirement: Executável LÖVE standalone otimizado para o Allwinner A33
O sistema SHALL disponibilizar o binário executável `love` compilado para arquitetura ARMv7-A hard-float (`-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -O3`), com backend nativo OpenGL ES 2.0 (`libGLESv2.so.2`), janela e contexto SDL2 no framebuffer `mali-fbdev` e runtime LuaJIT 2.1, sem depender de símbolos de glibc superiores a `GLIBC_2.36`.

#### Scenario: Execução em framebuffer sem servidor gráfico
- **WHEN** o executável `love` é chamado com um pacote de jogo válido em `/dev/fb0`
- **THEN** ele conecta-se diretamente aos drivers EGL e GLESv2 da Mali-400 e inicializa a superfície de renderização na resolução do display (640x480)

#### Scenario: Compatibilidade estrita de ABI
- **WHEN** as tabelas de símbolos do binário `love` são verificadas contra a biblioteca C do sistema
- **THEN** nenhuma dependência possui versão de símbolo `GLIBC_` superior a 2.36 nem requer bibliotecas ausentes na base

### Requirement: Lançador do LÖVE com controle de saída via gptokeyb
O sistema SHALL executar jogos através do lançador `/usr/bin/love.sh`, que SHALL exportar `LOVE_GRAPHICS_USE_OPENGLES=1`, configurar o mapa de botões do `micro_gamepad` para o SDL2 e carregar o daemon `gptokeyb` em segundo plano para encerrar o jogo ao detectar o atalho `Select + Start`, restaurando o volume do codec de áudio e o terminal ao finalizar.

#### Scenario: Encerramento de partida via combinação de botões
- **WHEN** o jogador pressiona simultaneamente os botões Select e Start durante a execução de qualquer jogo LÖVE
- **THEN** o `gptokeyb` envia sinal de finalização ao processo `love`, o lançador encerra o daemon e o EmulationStation retoma o foco imediatamente

#### Scenario: Restauração da cadeia de áudio na saída
- **WHEN** o jogo LÖVE é encerrado pelo jogador
- **THEN** o script chama `/usr/lib/r36/audio-ganho aplica` para reestabelecer os níveis de volume do sistema de som

### Requirement: Propagação de Localização e Idioma do Console para Jogos LÖVE
O lançador `/usr/bin/love.sh` SHALL resolver o idioma ativo do sistema a partir de `/storage/.config/emuelec/configs/emuelec.conf` (`system.language`) com fallback para `Language` em `/storage/.emulationstation/es_settings.cfg` e padrão `en_US`. O lançador SHALL exportar as variáveis de ambiente `CONSOLE_LANG`, `CONSOLE_LANG_SHORT`, `LANG` (`<código>.UTF-8`), `LANGUAGE` e gravar `/tmp/console_lang`, permitindo que scripts Lua consultem o idioma do console.

#### Scenario: Jogo em Lua adapta interface para o idioma do console
- **WHEN** o jogo LÖVE consulta `os.getenv("CONSOLE_LANG")` ou `os.getenv("LANG")` e encontra `pt_BR`
- **THEN** o jogo carrega sua tabela de tradução em português do Brasil e apresenta textos localizados

#### Scenario: Fallback para idioma padrão em jogos sem suporte
- **WHEN** o jogo LÖVE não possui tradução para o idioma informado pelo console ou não implementa localização
- **THEN** o jogo executa normalmente em seu idioma padrão de fábrica sem emitir erro de runtime ou travar a execução

### Requirement: Log de Execução Rotativo e Configurável no Lançador LÖVE
O script lançador `/usr/bin/love.sh` SHALL suportar registro de log de execução em `/storage/roms/love/love.log` na partição FAT32 `R36-ROMS`, capturando timestamp, argumentos, variáveis de ambiente, verificação de dependências dinâmicas via `ldd` e toda a saída padrão (stdout) e de erro (stderr) do binário `love`. O sistema SHALL gerenciar a ativação via variável de controle (`ENABLE_LOG=1` por padrão na fase de testes) e SHALL aplicar rotação automática com limite de tamanho de 100 KB mantendo no máximo 1 arquivo rotacionado (`love.log.1`), prevenindo exaustão de espaço no cartão SD e permitindo desativação sem exclusão do código de suporte.

#### Scenario: Diagnóstico detalhado de erro de inicialização
- **WHEN** o executável `love` não inicializa ou aborta prematuramente com `ENABLE_LOG=1`
- **THEN** a saída de erro do processo e a listagem de dependências dinâmicas não resolvidas são salvas em `/storage/roms/love/love.log`

#### Scenario: Rotação automática de log
- **WHEN** o arquivo `love.log` atinge ou supera 100 KB no início da execução
- **THEN** o arquivo é renomeado para `love.log.1` (sobrescrevendo versão anterior) e um novo `love.log` é iniciado

#### Scenario: Desativação transparente sem remoção de código
- **WHEN** a variável `ENABLE_LOG` é configurada como `0` no lançador
- **THEN** o processo `love` executa diretamente sem redirecionamento para o arquivo de log e sem impacto no tempo de inicialização

### Requirement: Console LÖVE integrado ao EmulationStation
O arquivo `es_systems.cfg` SHALL declarar o sistema `love` mapeando a pasta `/storage/roms/love` na partição FAT32 `R36-ROMS`, com suporte às extensões `.love` e `.zip`, associando o comando de execução ao lançador `/usr/bin/love.sh "%ROM%"`. O sistema SHALL exibir os títulos e capas descritos no catálogo `gamelist.xml` da pasta.

#### Scenario: Exibição condicional no carrossel do sistema
- **WHEN** o diretório `/storage/roms/love` contém pelo menos um arquivo com extensão `.love` ou `.zip`
- **THEN** o EmulationStation exibe o console LÖVE no carrossel principal com sua identidade visual e lista de jogos

#### Scenario: Visualização de capas e detalhes do jogo
- **WHEN** o jogador navega pela lista de jogos do console LÖVE
- **THEN** o EmulationStation exibe o nome, descrição e a imagem de capa indicada no `gamelist.xml`

### Requirement: Jogo de demonstração Mr. Rescue pré-instalado
A imagem do sistema SHALL fornecer o jogo livre e open-source *Mr. Rescue* (`mrrescue.love`) no diretório `/storage/roms/love/`, acompanhado de sua respectiva entrada no `gamelist.xml` e arquivo de imagem em `images/mrrescue.png`, permitindo validação imediata de vídeo, som, física e controles.

#### Scenario: Execução imediata no primeiro boot
- **WHEN** o console é iniciado pela primeira vez após a gravação completa
- **THEN** o jogo Mr. Rescue aparece listado com sua capa no menu LÖVE e inicia com som e jogabilidade operantes via micro_gamepad
