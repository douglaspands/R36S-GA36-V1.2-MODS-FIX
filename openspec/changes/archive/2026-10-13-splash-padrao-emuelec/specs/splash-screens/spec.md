# Spec Delta

## Purpose

Definir quais imagens o aparelho mostra no boot, antes do EmulationStation, e ao abrir um jogo, e garantir que sejam a tela da distribuição EmuELEC e um símbolo neutro, não artes de terceiros.

## ADDED Requirements

### Requirement: Tela de boot da distribuição EmuELEC
A imagem gerada SHALL mostrar no boot, antes do EmulationStation, a tela de splash da distribuição EmuELEC (logo com o controle e a palavra EMUELEC), em 640x480, ocupando a tela inteira sem distorção.

#### Scenario: Ligar o aparelho
- **WHEN** o aparelho liga com o SYSTEM gravado pelo build
- **THEN** a tela mostrada antes do EmulationStation é o logo da distribuição EmuELEC em tela cheia, sem barras pretas, e não a arte do God of War

### Requirement: Tela de carregamento de jogo com símbolo
Ao abrir um jogo sem tela personalizada em `/storage/roms/splash`, a imagem gerada SHALL mostrar um ícone de controle centralizado num fundo escuro, sem texto, em 640x480.

#### Scenario: Abrir um jogo
- **WHEN** o cartão é gravado com `--wipe-storage` e o usuário abre um jogo de NES sem tela personalizada
- **THEN** o aparelho mostra o ícone de controle sem texto, e não a arte do God of War

#### Scenario: Tela personalizada continua prioritária
- **WHEN** existe `/storage/roms/splash/nes.png`
- **THEN** essa imagem é mostrada no lugar do ícone

### Requirement: Telas na resolução do aparelho
Todos os PNGs de tela da feature SHALL ter 640x480 pixels, RGB de 8 bits e sem transparência. O arquivo de boot cru SHALL ter exatamente 921600 bytes (640x480 em RGB24) e o mesmo conteúdo do PNG de boot.

#### Scenario: Conferência dos arquivos
- **WHEN** os arquivos de tela da feature são inspecionados
- **THEN** cada PNG tem 640x480 em RGB de 8 bits, e o `.raw` tem 921600 bytes, com pixels iguais aos do PNG de boot

### Requirement: Nenhuma cópia da arte de terceiros
Nenhum arquivo de tela no SYSTEM nem no STORAGE da imagem gerada SHALL conter a arte do God of War. As telas fora deste escopo (logo do U-Boot, bateria e vídeo de introdução) SHALL permanecer como na base.

#### Scenario: Inspeção pelo PC
- **WHEN** os diretórios de telas do SYSTEM e do STORAGE gerados são comparados com a base
- **THEN** nenhum arquivo tem o sha256 da arte de fábrica, e os arquivos fora do escopo são idênticos aos da base

### Requirement: Origem das telas registrada e reproduzível
A feature SHALL registrar a origem de cada tela (repositório e commit do EmuELEC para o boot; pacote e versão do ícone para o jogo), as licenças e os sha256 dos arquivos gerados. O script versionado na feature SHALL regerar arquivos idênticos a partir das fontes registradas.

#### Scenario: Regerar as telas
- **WHEN** o script de geração da feature é executado a partir das fontes registradas
- **THEN** os arquivos gerados têm os mesmos sha256 registrados
