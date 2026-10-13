# psp-emulation Specification

## Purpose

Definir a configuração padrão do emulador de PSP (PPSSPP standalone) na imagem gerada, priorizando a velocidade de jogo no hardware do A33.

## Requirements

### Requirement: Renderização na resolução nativa do PSP
A configuração global do PPSSPP SHALL renderizar os jogos na resolução nativa do PSP (480x272, fator 1x), e não em resolução maior para depois reduzir.

#### Scenario: Conferência no PC
- **WHEN** o `ppsspp.ini` global da p8 e o do SYSTEM gerados são inspecionados
- **THEN** ambos declaram `InternalResolution = 1`

### Requirement: CPU emulada na frequência do jogo
A configuração global SHALL deixar o jogo escolher a frequência da CPU emulada (sem overclock fixo).

#### Scenario: Conferência no PC
- **WHEN** o `ppsspp.ini` global é inspecionado
- **THEN** ele declara `CPUSpeed = 0`

### Requirement: Threads e leituras de GPU adequadas ao A33
A configuração global SHALL usar 4 threads de trabalho, uma por núcleo do A33, e SHALL pular as leituras de volta da GPU.

#### Scenario: Conferência no PC
- **WHEN** o `ppsspp.ini` global é inspecionado
- **THEN** ele declara `NumWorkerThreads = 4` e `SkipGPUReadbackMode = 1`

### Requirement: Curvas em qualidade baixa e sem contador de FPS
A configuração global SHALL usar a qualidade baixa para curvas spline e bézier e SHALL esconder o contador de FPS.

#### Scenario: Conferência no PC
- **WHEN** o `ppsspp.ini` global é inspecionado
- **THEN** ele declara `SplineBezierQuality = 0` e `ShowFPSCounter = 0`

### Requirement: Demais configurações iguais às de fábrica
Fora das chaves desta capability, o `ppsspp.ini` global SHALL ser idêntico ao de fábrica, incluindo controles, áudio, pular quadros automático e efeitos de buffer. Os inis por jogo de fábrica SHALL continuar na imagem sem alteração.

#### Scenario: Comparação com a base
- **WHEN** o `ppsspp.ini` global gerado é comparado com o da base
- **THEN** as únicas linhas diferentes são as das chaves `InternalResolution`, `CPUSpeed`, `NumWorkerThreads`, `SkipGPUReadbackMode`, `SplineBezierQuality` e `ShowFPSCounter`

#### Scenario: Inis por jogo
- **WHEN** os arquivos `*_ppsspp.ini` gerados são comparados com os da base
- **THEN** todos são idênticos

### Requirement: Configuração aplicada ao abrir um jogo
Com o cartão gravado com `--wipe-storage`, o PPSSPP SHALL abrir os jogos sem ini próprio já com a configuração global desta capability.

#### Scenario: Abrir um jogo de PSP sem ini próprio
- **WHEN** o usuário abre um jogo de PSP que não tem ini por jogo e entra no menu de gráficos do PPSSPP
- **THEN** o menu mostra resolução 1x, sem contador de FPS e pular quadros automático ligado
