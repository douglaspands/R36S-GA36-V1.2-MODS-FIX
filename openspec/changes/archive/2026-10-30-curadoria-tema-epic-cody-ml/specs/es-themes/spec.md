# Spec Delta

## MODIFIED Requirements

### Requirement: Calibração visual e terminologia no tema
As descrições, títulos e elementos de interface no tema Epic Cody ML SHALL respeitar os limites espaciais da resolução 640x480, alinhando a coluna de informações em margem segura à esquerda (mínimo 2% de deslocamento horizontal) sem corte próximo à moldura física do aparelho, e SHALL manter nomenclaturas técnicas e de gêneros clássicos (*16-bit*, *Arcade*, *RPGs*, *Shmups*) inalteradas no catálogo em português.

#### Scenario: Leitura de descrição de console
- **WHEN** o usuário visualiza qualquer sistema no carrossel do tema Epic Cody ML em português
- **THEN** os textos de `shortdescription` e `longdescription` cabem confortavelmente dentro dos limites visuais da tela de 3.5 polegadas respeitando a margem esquerda de segurança

## ADDED Requirements

### Requirement: Hierarquia visual e ausência de truncamento nos títulos de consoles
O tema Epic Cody ML SHALL distribuir a titulação dos sistemas em duas linhas estruturadas (`sys_line1` para fabricante/família e `sys_line2` para modelo/identificador) com dimensionamento de caixa e tipografia calibrados para a resolução de 640x480, de modo que nenhum nome de console ou coleção gere truncamento com reticências (`...`) na tela do aparelho.

#### Scenario: Visualização de consoles com nomes longos no carrossel
- **WHEN** o usuário navega por consoles de nomes extensos como GameBoy Color, PlayStation, Nintendo 64, Nintendo DS ou coleções como Todos os Jogos
- **THEN** a linha hero (`sys_line2`) e o subtítulo (`sys_line1`) são exibidos inteiramente sem reticências ou cortes

### Requirement: Estilização harmônica do rodapé e proteção contra sobreposição
A visualização de sistemas (`system`) do tema Epic Cody ML SHALL estilizar explicitamente o elemento `<helpsystem name="help">` com tipografia discreta, proporções compactas e cores harmônicas com a paleta do tema, e a arte do console (`controller`) SHALL ser dimensionada e posicionada de modo a garantir espaçamento livre de sobreposição em relação à barra de navegação inferior.

#### Scenario: Navegação na tela inicial sem colisão visual
- **WHEN** o usuário visualiza a tela principal de um sistema
- **THEN** a imagem representativa do videogame não sobrepõe os textos e ícones da barra de comandos inferior, e as legendas de botões utilizam fonte proporcional sem ocupar agressivamente a tela

### Requirement: Localização integral de elementos visuais e badges de ação
O tema Epic Cody ML SHALL exibir o badge do botão de ação principal (botão A) e todos os metadados de sistema e categorias traduzidos de acordo com o idioma ativo do tema (`pt-br`, `es-latam` ou `en`), sem manter termos em inglês na interface configurada em português ou espanhol.

#### Scenario: Botão de ação e metadados em português
- **WHEN** o tema Epic Cody ML está ativo no idioma Português (Brasil)
- **THEN** o badge do botão principal indica `(A) ENTRAR` e rótulos de configurações, emuladores e categorias especiais não exibem termos em inglês órfãos
