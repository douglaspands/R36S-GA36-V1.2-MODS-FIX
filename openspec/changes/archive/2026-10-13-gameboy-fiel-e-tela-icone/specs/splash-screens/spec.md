# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Tela de boot da distribuição EmuELEC`
- TO: `### Requirement: Tela de boot com o ícone de controle`

## MODIFIED Requirements

### Requirement: Tela de boot com o ícone de controle
A imagem gerada SHALL mostrar no boot, antes do EmulationStation, a mesma imagem da tela de carregamento de jogo: o ícone de controle centralizado num fundo escuro, sem texto, em 640x480, ocupando a tela inteira sem distorção.

#### Scenario: Ligar o aparelho
- **WHEN** o aparelho liga com o SYSTEM gravado pelo build
- **THEN** a tela mostrada antes do EmulationStation é o ícone de controle em tela cheia, sem barras pretas, e não a arte do God of War nem o logo do EmuELEC

### Requirement: Nenhuma cópia da arte de terceiros
Nenhum arquivo do SYSTEM nem do STORAGE da imagem gerada SHALL conter a arte do God of War, incluindo as imagens de recursos do EmulationStation. As telas fora deste escopo (logo do U-Boot, bateria e vídeo de introdução) SHALL permanecer como na base.

#### Scenario: Inspeção pelo PC
- **WHEN** todos os arquivos do SYSTEM e do STORAGE gerados são verificados
- **THEN** nenhum arquivo tem o sha256 da arte de fábrica, e os arquivos fora do escopo são idênticos aos da base

### Requirement: Origem das telas registrada e reproduzível
A feature SHALL registrar a origem do ícone de controle (pacote e versão), a licença e os sha256 dos arquivos gerados. O script versionado na feature SHALL regerar arquivos idênticos a partir das fontes registradas.

#### Scenario: Regerar as telas
- **WHEN** o script de geração da feature é executado a partir das fontes registradas
- **THEN** os arquivos gerados têm os mesmos sha256 registrados

## ADDED Requirements

### Requirement: Carregamento do EmulationStation só com o ícone
Enquanto o EmulationStation carrega, a imagem gerada SHALL mostrar o ícone de controle em tela cheia, sem texto de progresso nem lista de sistemas ou collections por cima.

#### Scenario: Boot até o menu
- **WHEN** o cartão é gravado com `--wipe-storage` e o aparelho liga
- **THEN** do fim do boot até o menu do EmulationStation, a tela mostra só o ícone de controle, sem a arte do God of War e sem texto de carregamento

### Requirement: Abertura de jogo sem a tela de boot
Entre escolher um jogo no EmulationStation e o jogo aparecer, a imagem gerada SHALL mostrar só o ícone de controle (ou a tela personalizada do jogo), sem nenhuma outra imagem no meio.

#### Scenario: Abrir um jogo
- **WHEN** o usuário abre um jogo de NES sem tela personalizada
- **THEN** a tela passa do menu para o ícone de controle e do ícone direto para o jogo, sem mostrar outra imagem no intervalo

#### Scenario: Voltar do jogo
- **WHEN** o usuário sai do jogo
- **THEN** a tela passa do jogo para o ícone de controle e depois para o menu, sem mostrar outra imagem
