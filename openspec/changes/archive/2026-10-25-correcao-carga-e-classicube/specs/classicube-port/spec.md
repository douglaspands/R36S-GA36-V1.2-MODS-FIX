# Spec Delta: classicube-port

## MODIFIED Requirements

### Requirement: Lançador integrado aos Ports do EmulationStation
A imagem SHALL disponibilizar um script inicializador em `/storage/roms/ports_scripts/ClassiCube.sh` (visível na lista "Ports" da interface), acompanhado de metadados e imagem de capa em `gamelist.xml`, responsável por configurar o ambiente de execução e iniciar o binário.

#### Scenario: Inicialização pelo menu
- **WHEN** o usuário seleciona o ClassiCube no menu de Ports do EmulationStation
- **THEN** o script define as variáveis de ambiente necessárias (`SDL_VIDEO_GL_DRIVER`, `SDL_VIDEO_EGL_DRIVER`), muda o diretório de trabalho para `/storage/roms/ports/classicube` e dispara o executável no modo local com `--singleplayer` sem repassar argumentos externos do EmulationStation que possam corromper a inicialização

#### Scenario: Exibição da capa na lista
- **WHEN** o usuário navega pelo menu "Ports" do EmulationStation
- **THEN** a lista exibe o nome do jogo e a imagem da capa (boxart/screenshot) correspondente definida no `gamelist.xml`

#### Scenario: Retorno limpo ao EmulationStation
- **WHEN** o jogador pressiona o botão de sair do jogo (ou combinação de atalho)
- **THEN** o processo encerra sem travar o framebuffer e retorna o foco à interface do EmulationStation
