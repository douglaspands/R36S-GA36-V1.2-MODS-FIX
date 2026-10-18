# es-themes Specification

## Purpose
Definir quais temas do EmulationStation a imagem gerada traz, onde eles ficam e qual é o padrão, para o usuário escolher entre vários temas sem precisar de rede no aparelho.

## Requirements

### Requirement: Temas extras disponíveis no menu
A imagem gerada SHALL trazer, além do NES-BOX, os temas extras declarados pela feature de temas. Todos SHALL aparecer na lista de temas das configurações de interface do EmulationStation.

#### Scenario: Escolher um tema
- **WHEN** o cartão é gravado com `--wipe-storage` e o usuário abre a lista de temas do EmulationStation
- **THEN** a lista mostra o NES-BOX e cada tema extra, e escolher um deles aplica o tema depois do reinício do EmulationStation

### Requirement: Temas legíveis na tela do aparelho
Cada tema extra SHALL mostrar a lista de sistemas e a lista de jogos na tela de 640x480 sem texto cortado a ponto de impedir a navegação. Um tema que falhar nessa validação SHALL sair do conjunto.

#### Scenario: Navegação com um tema extra
- **WHEN** o usuário seleciona um tema extra e navega até a lista de jogos de um sistema
- **THEN** os nomes dos sistemas e dos jogos são legíveis e a seleção atual é visível

### Requirement: NES-BOX continua padrão
O tema ativo no primeiro boot SHALL continuar sendo o NES-BOX.

#### Scenario: Primeiro boot
- **WHEN** o aparelho inicia pela primeira vez com o storage gravado pela imagem
- **THEN** o EmulationStation abre com o tema NES-BOX

### Requirement: Espaço dos temas limitado
Os temas extras juntos SHALL ocupar no máximo 400 MiB na p8, e o build SHALL falhar se o limite for ultrapassado.

#### Scenario: Orçamento respeitado
- **WHEN** o build aplica a feature de temas
- **THEN** o relatório do build mostra o tamanho total dos temas extras, e ele é de no máximo 400 MiB

#### Scenario: Orçamento estourado
- **WHEN** a lista de temas extraídos soma mais de 400 MiB
- **THEN** o build falha antes de gerar a imagem, mostrando o tamanho de cada tema

### Requirement: Tema NES-BOX-V2 disponível
A imagem gerada SHALL trazer o tema NES-BOX-V2 na p8, ao lado do NES-BOX, e ele SHALL aparecer na lista de temas do EmulationStation. O V2 SHALL conter tudo que o NES-BOX contém. O NES-BOX SHALL permanecer inalterado.

#### Scenario: Escolher o V2
- **WHEN** o cartão é gravado com `--wipe-storage` e o usuário abre a lista de temas do EmulationStation
- **THEN** a lista mostra o NES-BOX e o NES-BOX-V2, e escolher o V2 aplica o tema depois do reinício do EmulationStation

#### Scenario: NES-BOX preservado
- **WHEN** o build aplica a feature
- **THEN** os arquivos do NES-BOX ficam byte a byte iguais aos da base, e o relatório de diferenças mostra só adições, todas sob o NES-BOX-V2

### Requirement: NES-BOX-V2 cobre todos os sistemas da imagem
O NES-BOX-V2 SHALL ter uma pasta própria para cada nome de tema declarado no `es_systems.cfg` da imagem, com um `theme.xml` cujo logo (`system.png`) e arte de personagem (`background_icon.png`) existam, na própria pasta ou na pasta de um sistema equivalente do V2.

#### Scenario: Sistema antes sem pasta de tema
- **WHEN** o usuário escolhe o NES-BOX-V2 e o EmulationStation lista um sistema que o NES-BOX não cobria (por exemplo `wii` ou `pgm2`)
- **THEN** o sistema aparece com logo e arte de personagem do tema, e não com o visual genérico

#### Scenario: Verificação de cobertura
- **WHEN** a verificação automatizada do repositório cruza o `es_systems.cfg` da imagem com o NES-BOX-V2 da p8 gerada
- **THEN** cada nome de tema tem uma pasta com `theme.xml`, e todo logo e arte que ele referencia existe, e a verificação falha se algum faltar, listando o sistema e o arquivo

### Requirement: Arte oficial primeiro, criada quando não existir
Para cada sistema que o NES-BOX não cobre, o logo e a arte de personagem SHALL vir de material oficial da internet (do sistema, do fabricante ou do projeto) quando existir. Quando não existir material oficial, a imagem SHALL ser criada com base no assunto do sistema, no estilo do tema. Sistemas que só diferem de um existente no nome SHALL reaproveitar a arte desse existente por referência, sem duplicar o arquivo.

#### Scenario: Logo oficial disponível
- **WHEN** o sistema tem logo oficial publicado (por exemplo `wii`)
- **THEN** o `system.png` é esse logo, convertido para PNG com fundo transparente

#### Scenario: Nada na internet
- **WHEN** não há logo nem arte para o sistema (por exemplo `karaoke` ou `imageviewer`)
- **THEN** a feature traz uma imagem criada com base no assunto do sistema, e o registro de origem marca o arquivo como criado

#### Scenario: Diferença só de nome
- **WHEN** o nome de tema do `es_systems.cfg` é uma variação de um existente (por exemplo `pce-cd` e `pcenginecd`)
- **THEN** a pasta nova não tem PNGs próprios, e o `theme.xml` dela aponta para o logo e a arte da pasta equivalente, que aparecem no sistema

### Requirement: Origem da arte registrada
Cada arquivo de arte acrescentado SHALL ter a origem registrada na feature: URL e sha256 do arquivo baixado quando for material da internet, ou a marca "criado". Cada pasta por referência SHALL registrar a pasta equivalente a que aponta. O build SHALL NOT baixar nada para aplicar essa arte.

#### Scenario: Consulta da origem
- **WHEN** o usuário abre o registro de origem da feature
- **THEN** cada sistema acrescentado aparece com a origem do logo e da arte de personagem

#### Scenario: Build sem rede
- **WHEN** o build roda sem acesso à rede
- **THEN** a feature é aplicada normalmente, porque a arte já está no repositório ou extraída da base

### Requirement: Formato da arte acrescentada
O `system.png` acrescentado SHALL ser PNG com fundo transparente, de largura entre 400 e 600 px. O `background_icon.png` SHALL ser PNG de 960x540 com fundo transparente. O `theme.xml` de cada pasta nova SHALL seguir o formato das pastas existentes e incluir o `theme.xml` do tema.

#### Scenario: Dimensões conferidas
- **WHEN** a verificação automatizada confere os arquivos da feature
- **THEN** os PNGs acrescentados têm fundo transparente e as dimensões exigidas, e a verificação falha, listando o arquivo, se algum não tiver

#### Scenario: Legibilidade na tela do aparelho
- **WHEN** o usuário navega até um sistema acrescentado na tela de 640x480
- **THEN** o logo aparece inteiro, sem cortar, e a arte de personagem não cobre a lista de jogos
