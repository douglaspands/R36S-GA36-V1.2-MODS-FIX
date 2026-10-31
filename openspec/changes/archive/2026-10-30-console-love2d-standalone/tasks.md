# Tasks

## 1. Receita e Compilação do LÖVE 11.5 para o A33

- [x] 1.1 Criar a receita de compilação `ports/love2d/receita.toml` com URLs do código-fonte upstream do LÖVE 11.5, sha256 e flags dedicadas para o Cortex-A7/NEON (`-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -O3`), e verificar a conformidade sintática do arquivo TOML.
- [x] 1.2 Criar o script hermético `ports/love2d/compilar.sh` orquestrando o container Podman Debian Bookworm, instalando bibliotecas de desenvolvimento armhf (`libsdl2-dev:armhf`, `libluajit-5.1-dev:armhf`, `libfreetype-dev:armhf`, `libopenal-dev:armhf`, `libmodplug-dev:armhf`, `libvorbis-dev:armhf`, `libphysfs-dev:armhf`), compilando com backend OpenGL ES 2.0 nativo e gerando o binário stripado.
- [x] 1.3 Executar a compilação do executável `love` e inspecionar os cabeçalhos ELF e a tabela de símbolos com `readelf`, verificando arquitetura ARMv7-A hard-float e símbolos da biblioteca C restritos a `GLIBC_` <= 2.36.

## 2. Lançador e Controle de Execução

- [x] 2.1 Criar o lançador `/usr/bin/love.sh` configurando as variáveis de ambiente de vídeo (`LOVE_GRAPHICS_USE_OPENGLES=1`), carregamento do mapeamento do `micro_gamepad` para SDL2, ativação do `gptokeyb` em segundo plano para capturar o atalho de encerramento (`Select + Start`), execução do processo e restauração do ganho de áudio com `/usr/lib/r36/audio-ganho aplica`.
- [x] 2.2 Criar o arquivo de configuração do mapeador de botões `love.gptk` garantindo que o atalho de saída funcione e que botões sejam traduzidos para jogos baseados em teclado.
- [x] 2.3 Implementar testes automatizados em `tests/test_love2d.py` validando permissões, sintaxe do script lançador, variáveis de ambiente exigidas e compatibilidade da ABI.
- [x] 2.4 Atualizar `/usr/bin/love.sh` para detectar o idioma configurado no EmuELEC (`system.language` / `Language`) com fallback para `en_US`, exportar `CONSOLE_LANG`, `CONSOLE_LANG_SHORT`, `LANG`, `LANGUAGE` e gravar `/tmp/console_lang`.
- [x] 2.5 Atualizar `tests/test_love2d.py` com testes para verificação da propagação de variáveis de ambiente de idioma e fallbacks.
- [x] 2.6 Implementar log com rotação automática em `/usr/bin/love.sh` direcionado para `/storage/roms/love/love.log` (teto de 100 KB, histórico `.1`, captura de stdout/stderr, verificação `ldd` de dependências e controle por `ENABLE_LOG=1`).
- [x] 2.7 Atualizar testes unitários em `tests/test_love2d.py` validando o mecanismo de rotação de log e a flag de ativação.

## 3. Integração com o EmulationStation e Estrutura de Feature

- [x] 3.1 Adicionar a declaração do sistema `love` em `features/53-cores-a33/system/usr/config/emulationstation/es_systems.cfg` e `features/53-cores-a33/storage/.config/emulationstation/es_systems.cfg`, mapeando o caminho `/storage/roms/love`, extensões `.love .zip .LOVE .ZIP` e o comando de inicialização `/usr/bin/love.sh "%ROM%"`.
- [x] 3.2 Criar a camada de feature `features/64-love2d` com seu respectivo `feature.toml`, organizando os arquivos do executável, script lançador, arquivos de mapeamento e diretório base de ROMs.
- [x] 3.3 Atualizar `tests/test_es_systems.py` para validar a presença da entrada do sistema `love` em ambos os arquivos `es_systems.cfg` e a coerência das extensões e caminhos declarados.

## 4. Visual e Curadoria do Tema Epic Cody ML

- [x] 4.1 Criar a pasta `love2d/` no tema padrão `features/50-temas-extras/storage/.config/emulationstation/themes/Epic Cody ML/` contendo `theme.xml` e arte gráfica do logotipo oficial do LÖVE.
- [x] 4.2 Inserir as variáveis descritivas e de título do console (`sys_line1`, `sys_line2`, `shortdescription`, `longdescription`) nos catálogos de idioma `pt-br.xml`, `en.xml` e `es-latam.xml` do tema `Epic Cody ML`.
- [x] 4.3 Validar que o tema `NES-BOX` em `features/50-temas-extras/roms/themes/NES-BOX/love2d/` é acionado corretamente pelo identificador do sistema.
- [x] 4.4 Adicionar testes automatizados em `tests/test_themes.py` conferindo a existência das chaves de tradução do LÖVE em todos os idiomas e ausência de truncamento de texto na resolução de 640x480.
- [x] 4.5 Ajustar o alinhamento de `nameLabel` para `left` em `features/50-temas-extras/storage/.config/emulationstation/themes/Epic Cody ML/theme.xml`, eliminando sobreposição com o ícone da bateria e relógio.
- [x] 4.6 Adicionar elemento `<text name="md_name">` abaixo da imagem (`md_image`) nas visualizações detalhadas do `theme.xml` para exibição integral do nome do jogo.
- [x] 4.7 Gerar a arte do poster do console LÖVE em 640x480 inspirada na estética e paleta de https://love2d.org/ e integrá-la ao tema `Epic Cody ML`.
- [x] 4.8 Remover os temas adicionais (`NES-BOX`, `Minimal EmuELEC`, `Graphite OGA`, `Switch` e `Crystal`) em `features/50-temas-extras/` e atualizar `feature.toml` para unificar o sistema exclusivamente no `Epic Cody ML`.
- [x] 4.9 Atualizar `tests/test_themes.py` com asserções para o alinhamento de `nameLabel`, presença de `md_name`, existência do poster do LÖVE e integridade do tema único.

## 5. Jogo de Demonstração Mr. Rescue e Validação da Imagem

- [x] 5.1 Integrar o pacote do jogo open-source *Mr. Rescue* (`mrrescue.love`) no diretório `roms/love/`, acompanhado de sua respectiva entrada no catálogo `gamelist.xml` e imagem de capa em `images/mrrescue.png`.
- [x] 5.2 Executar a suíte de testes automatizados do projeto (`uv run python -I -m unittest discover -s tests`) e verificar 100% de aprovação.
- [x] 5.3 Executar a geração da imagem de teste (`./build.sh --test --no-system-sha`) e inspecionar as partições `R36-SYSTEM` e `R36-ROMS`, assegurando a correta distribuição dos binários, scripts e ativos.
- [x] 5.4 Reexecutar os testes automatizados (`uv run python -I -m unittest discover -s tests`) para validar a nova suíte de testes unitários.

## 6. Documentação e Guia para Desenvolvedores

- [x] 6.1 Adicionar seção sobre o LÖVE nos três arquivos de apresentação (`README.pt-BR.md`, `README.md` e `README.es.md`), ilustrando formatos aceitos (`.love`, `.zip`), instruções de jogo e a subseção para desenvolvedores contendo exemplo prático de código em Lua para detecção do idioma do console com fallback.
- [x] 6.2 Atualizar o manual técnico `docs/DESENVOLVIMENTO.md` documentando a feature `64-love2d`, variáveis de ambiente de localização exportadas e atalhos de encerramento via gptokeyb.
