# Spec Delta: es-themes

## ADDED Requirements

### Requirement: Suporte ao console LÖVE no tema Epic Cody ML
O tema padrão Epic Cody ML SHALL disponibilizar estrutura completa para o sistema `love2d`, definindo `love2d/theme.xml` compatível com a visão de sistema e de lista de jogos, incorporando o logotipo do LÖVE e fornecendo as descrições e títulos em duas linhas (`sys_line1` e `sys_line2`) nos dicionários `pt-br.xml`, `en.xml` e `es-latam.xml`, mantendo espaçamento seguro em 640x480 sem sobreposição à barra de rodapé.

#### Scenario: Visualização do console LÖVE no tema padrão em português
- **WHEN** o jogador navega até o console LÖVE com o tema Epic Cody ML ativo no idioma Português (Brasil)
- **THEN** o carrossel exibe o logotipo do LÖVE, o título "Motor de Jogos / LÖVE" e a descrição localizada sem truncamento de texto ou reticências

#### Scenario: Visualização da lista de jogos e capas
- **WHEN** o jogador entra no console LÖVE no tema Epic Cody ML
- **THEN** a lista exibe os títulos dos jogos e a área de visualização detalhada renderiza a capa do jogo sem distorção na tela de 3.5 polegadas

### Requirement: Alinhamento à Esquerda do Nome do Console na Lista de Jogos (Epic Cody ML)
Na visualização da lista de jogos (`basic`, `detailed`, `video`), o elemento `<text name="nameLabel">` do tema Epic Cody ML SHALL utilizar alinhamento à esquerda (`<alignment>left</alignment>`), posicionando o título do sistema à esquerda do painel superior e SHALL manter desobstruído o canto superior direito reservado aos indicadores de bateria e relógio.

#### Scenario: Visualização limpa da barra de status na lista de jogos
- **WHEN** o jogador abre a lista de jogos de qualquer console no tema Epic Cody ML
- **THEN** o nome do console é renderizado alinhado à esquerda e não se sobrepõe ao ícone da bateria ou ao relógio

### Requirement: Exibição do Nome Completo do Jogo Abaixo da Imagem (Epic Cody ML)
Nas visualizações detalhadas (`detailed`, `video`), o tema Epic Cody ML SHALL definir o elemento `<text name="md_name">` posicionado abaixo da imagem de capa (`md_image`), apresentando o título completo do jogo selecionado para leitura sem truncamento de títulos extensos.

#### Scenario: Exibição integral de título extenso
- **WHEN** o jogador navega sobre um jogo com título longo na lista
- **THEN** o painel direito exibe o nome completo do jogo abaixo da capa com tipografia legível

### Requirement: Poster do Console LÖVE Inspirado em love2d.org
O tema Epic Cody ML SHALL disponibilizar a arte de fundo/poster do console LÖVE (`_art/posters/love2d.png` ou `love2d/poster.png`) na resolução de 640x480, inspirada na identidade visual, elementos e paleta de cores do site oficial https://love2d.org/, com elementos visuais concentrados no terço direito da tela para harmonizar com os textos do carrossel posicionados à esquerda.

#### Scenario: Visualização do poster na tela do sistema
- **WHEN** o console LÖVE está em foco no carrossel do tema Epic Cody ML
- **THEN** a tela exibe o poster temático do LÖVE ao fundo com renderização nítida em 640x480

### Requirement: Exclusividade do Tema Epic Cody ML e Remoção de Temas Secundários
Para simplificação arquitetural e prevenção de sobrecarga de manutenção entre múltiplos temas, o sistema SHALL manter o tema `Epic Cody ML` como o único tema instalado, removendo temas adicionais (`NES-BOX`, `Minimal EmuELEC`, `Graphite OGA`, `Switch`, `Crystal`).

#### Scenario: Inicialização unificada no tema padrão
- **WHEN** o sistema inicializa o EmulationStation
- **THEN** o tema `Epic Cody ML` é carregado diretamente como único tema do console, sem referências quebradas a temas removidos
