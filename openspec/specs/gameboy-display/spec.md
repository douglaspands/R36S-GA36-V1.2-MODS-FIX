# gameboy-display Specification

## Purpose

Definir como os jogos de Game Boy e Game Boy Color aparecem na tela do aparelho (tamanho, moldura do console, cor e textura do LCD), para que jogar pareça jogar no console original.

## Requirements

### Requirement: Tela do jogo na altura total
Nos sistemas GB e GBC, a imagem do jogo (160x144) SHALL ocupar a altura toda da tela, em 534x480 pixels, centrada na horizontal (de x=53 a x=586), na proporção 10:9, sem cortes e sem distorção.

#### Scenario: Abrir um jogo de GB
- **WHEN** o cartão é gravado com `--wipe-storage` e o usuário abre um jogo da pasta `gb`
- **THEN** o jogo ocupa o retângulo de 534x480 pixels de x=53 a x=586, de cima a baixo, e nenhuma parte do jogo fica coberta pela moldura

#### Scenario: Abrir um jogo de GBC
- **WHEN** o usuário abre um jogo da pasta `gbc`
- **THEN** o jogo ocupa o mesmo retângulo de 534x480 pixels, entre as laterais da moldura do GBC

### Requirement: Laterais do Game Boy original
Nos jogos de GB, as duas faixas laterais que sobram ao lado do jogo SHALL mostrar a lente do DMG na cor cinza-azulada escura. A esquerda SHALL ter o LED vermelho com o texto "BATTERY", e a direita SHALL ser lisa, sem texto.

#### Scenario: Elementos das laterais do DMG
- **WHEN** um jogo de GB está rodando
- **THEN** a lateral esquerda mostra o LED "BATTERY", a direita mostra só a cor da lente, sem texto, e nenhuma das duas fica preta

### Requirement: Laterais do Game Boy Color Atomic Purple
Nos jogos de GBC, as duas faixas laterais que sobram ao lado do jogo SHALL mostrar o GBC na cor Atomic Purple: roxo translúcido. A esquerda SHALL ter o LED com o texto "POWER", e a direita SHALL ser lisa, sem texto.

#### Scenario: Elementos das laterais do GBC
- **WHEN** um jogo de GBC está rodando
- **THEN** a lateral esquerda mostra o LED "POWER", a direita mostra só o roxo translúcido, sem texto, e nenhuma das duas fica preta

### Requirement: Paleta verde do DMG nos jogos de GB
Os jogos de GB sem cor SHALL ser exibidos nos quatro tons verdes do LCD do DMG original, do mais claro (fundo) ao mais escuro.

#### Scenario: Jogo monocromático
- **WHEN** o usuário abre um jogo de GB monocromático
- **THEN** o fundo e os sprites aparecem em tons de verde do DMG, e não em cinza nem nas paletas coloridas do GBC

### Requirement: Textura de LCD visível
Nos jogos de GB e GBC, cada pixel do jogo SHALL aparecer separado dos vizinhos por uma grade fina, como no LCD do console, sem borrar a imagem.

#### Scenario: Olhar a tela de perto
- **WHEN** um jogo de GB ou GBC está rodando
- **THEN** a grade entre os pixels do jogo é visível, e as bordas dos sprites continuam nítidas

### Requirement: Cor do GBC corrigida para o LCD
Os jogos de GBC SHALL ser exibidos com a correção de cor que imita o LCD do GBC, com cores menos saturadas que os valores crus do jogo.

#### Scenario: Jogo colorido
- **WHEN** o usuário abre um jogo de GBC
- **THEN** as cores aparecem com a correção de LCD do GBC, e não com a saturação crua

### Requirement: Velocidade cheia com moldura e shader
Os jogos de GB e GBC SHALL rodar a 60 quadros por segundo com a moldura e o shader ativos.

#### Scenario: Medição no aparelho
- **WHEN** um jogo de GB e um de GBC rodam com o contador de FPS do RetroArch ligado
- **THEN** o contador fica em 60 fps (59,7 no GB) durante a jogabilidade normal

### Requirement: Outros sistemas inalterados
A configuração de GB e GBC SHALL valer só para jogos das pastas `gb` e `gbc`. Os outros sistemas e cores SHALL continuar com a apresentação de antes.

#### Scenario: Jogo de outro sistema
- **WHEN** o usuário abre um jogo de NES depois de jogar GB
- **THEN** o jogo de NES aparece sem moldura e sem o shader do LCD, como antes

### Requirement: Artes geradas de forma reproduzível
As molduras SHALL ser geradas por um script versionado na feature, a partir de fontes cuja origem, licença e sha256 ficam registrados. Os PNGs SHALL ter 640x480 com canal alfa e ser totalmente transparentes na área da tela do jogo.

#### Scenario: Regerar as molduras
- **WHEN** o script de geração é executado a partir das fontes registradas
- **THEN** os PNGs gerados têm os mesmos sha256 registrados

#### Scenario: Conferir o recorte da tela
- **WHEN** um PNG de moldura é inspecionado
- **THEN** ele tem 640x480 com alfa, todos os pixels do retângulo de 534x480 do jogo (x=53 a 586) são totalmente transparentes e as faixas laterais são opacas
