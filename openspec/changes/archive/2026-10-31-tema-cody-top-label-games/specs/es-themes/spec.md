# es-themes Specification Delta

## Requirements

### Requirement: Localização dinâmica do cabeçalho da lista de jogos no tema Epic Cody ML
O tema Epic Cody ML SHALL exibir o cabeçalho superior esquerdo da lista de jogos dinamicamente a partir da variável `${top_label}`, refletindo o idioma selecionado no tema sem texto em inglês embutido estaticamente na imagem de fundo.

#### Scenario: Visualização da lista de jogos em português
- **WHEN** o idioma do tema Epic Cody ML está definido como Português (Brasil)
- **THEN** o cabeçalho da lista de jogos no canto superior esquerdo exibe o texto "GAMES" e o título do console (`nameLabel`) em escala tipográfica uniforme (`0.050`), ambos rigorosamente nivelados na mesma baseline e centro vertical (16px de respiro superior e 16px de respiro até a linha amarela reta contínua em `y=53`)

### Requirement: Design System da Lista de Jogos (Gamelist)
Na visualização de lista de jogos (`basic`, `detailed`, `video`) do tema Epic Cody ML na resolução de 640x480 (display 3.5"), os elementos estruturais de interface SHALL seguir rigorosamente as métricas do Design System:
1. **Linha Divisória de Cabeçalho**: A linha divisória horizontal amarela/âmbar (`#FFAE00`) da imagem de fundo SHALL se estender contínua e reta por toda a largura da tela (`x = 0..639`) na coordenada exata `y = 53`.
2. **Faixa Superior do Cabeçalho**: A faixa de cabeçalho (`y = 0..52`) SHALL abrigar em alinhamento vertical idêntico o rótulo da coluna (`top_label`) e o título do console (`nameLabel`), ambos em fonte Bebas Neue com escala uniforme `fontSize = 0.050` (altura de glifo de 21px), com respiro simétrico de 16.0px em relação à borda superior da tela e 16.0px em relação à linha amarela inferior, resultando em 0px de desnível vertical entre eles.
3. **Alinhamento Horizontal por Colunas**: O rótulo `top_label` SHALL iniciar em `pos: 0.025 0.025` (`x = 16px`), e o título do console `nameLabel` SHALL iniciar em `pos: 0.339 0.025` (`x = 217px`) com `alignment = left`, mantendo livre a área superior direita (`x > 0.85`) para os ícones de status de bateria e relógio.
4. **Legenda Inferior do Jogo (`md_name`)**: O título completo da ROM selecionada (`md_name`) SHALL ser posicionado como legenda inferior em `pos: 0.339 0.81` (Opção 1 do Design System), mantendo livre a área central (`y = 75..370`) para a renderização sem obstrução de capas (`md_image`) e vídeos (`md_video`), e finalizando antes da barra de comandos do rodapé (`helpsystem`).

#### Scenario: Visualização do cabeçalho da lista sem colisão com bateria e relógio
- **WHEN** o usuário acessa a lista de jogos de qualquer console no tema Epic Cody ML
- **THEN** o cabeçalho exibe `GAMES` e o nome do console nivelados no centro vertical (`y=26.5px`) entre o topo da tela e a linha amarela em `y=53`, o título do console inicia à esquerda em `x=0.339` mantendo livre a área de bateria e relógio, e o título do jogo é exibido como legenda inferior em `y=0.81` abaixo da capa do jogo sem cobrir a arte

#### Scenario: Visualização da lista de jogos em espanhol
- **WHEN** o idioma do tema Epic Cody ML está definido como Español (Latino)
- **THEN** o cabeçalho da lista de jogos no canto superior esquerdo exibe o texto "JUEGOS" renderizado pelo EmulationStation

#### Scenario: Visualização da lista de jogos em inglês
- **WHEN** o idioma do tema Epic Cody ML está definido como English
- **THEN** o cabeçalho da lista de jogos no canto superior esquerdo exibe o texto "GAMES"
