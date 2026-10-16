# Spec Delta

## ADDED Requirements

### Requirement: Filtragem de textura nearest
A configuração global SHALL usar a filtragem de textura nearest, que gasta menos banda de memória na GPU do A33 do que a linear.

#### Scenario: Conferência no PC
- **WHEN** o `ppsspp.ini` global da p8 e o do SYSTEM gerados são inspecionados
- **THEN** ambos declaram `TextureFiltering = 2`

### Requirement: Recursos extras desligados
A configuração global SHALL desligar a busca por texturas de substituição, as conquistas e os cheats. O usuário pode religar os cheats pelo menu do PPSSPP.

#### Scenario: Conferência no PC
- **WHEN** o `ppsspp.ini` global é inspecionado
- **THEN** ele declara `ReplaceTextures = False`, `AchievementsEnable = False` e `EnableCheats = False`

## MODIFIED Requirements

### Requirement: Demais configurações iguais às de fábrica
Fora das chaves desta capability, o `ppsspp.ini` global SHALL ser idêntico ao de fábrica, incluindo controles, áudio, pular quadros automático, frequência da CPU escolhida pelo jogo e efeitos de buffer. Os inis por jogo de fábrica SHALL continuar na imagem sem alteração.

#### Scenario: Comparação com a base
- **WHEN** o `ppsspp.ini` global gerado é comparado com o da base
- **THEN** as únicas linhas diferentes são as das chaves `InternalResolution`, `CPUSpeed`, `NumWorkerThreads`, `SkipGPUReadbackMode`, `SplineBezierQuality`, `ShowFPSCounter`, `TextureFiltering`, `ReplaceTextures`, `AchievementsEnable` e `EnableCheats`

#### Scenario: Inis por jogo
- **WHEN** os arquivos `*_ppsspp.ini` gerados são comparados com os da base
- **THEN** todos são idênticos
