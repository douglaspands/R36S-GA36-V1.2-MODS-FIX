## ADDED Requirements

### Requirement: Interframe blending ligado por padrão no gpSP, com chave para desligar
O gpSP SHALL abrir os jogos de GBA com `gpsp_frame_mixing` (Interframe Blending, o ghosting do LCD) em `enabled`, pela opção gravada em `/storage/.config/retroarch/config/gpSP/gpSP.opt`. O sistema SHALL criar o arquivo, ou acrescentar a chave, no boot, somente se a chave não existir, e SHALL NOT alterar um valor existente nem outras linhas.

#### Scenario: Padrão de fábrica
- **WHEN** o usuário abre um jogo de GBA no gpSP depois de gravar a imagem e ligar o aparelho, sem ter mexido na opção
- **THEN** o gpSP roda com o Interframe Blending ligado, e o menu de opções do core mostra "Interframe Blending: enabled"

#### Scenario: Cartão gravado com --keep-storage
- **WHEN** o cartão recebe só o SYSTEM novo e a p8 não tem `gpSP.opt`
- **THEN** o boot seguinte cria `gpSP.opt` com `gpsp_frame_mixing = "enabled"`

#### Scenario: Arquivo existente sem a chave
- **WHEN** `gpSP.opt` já existe com outras opções e sem `gpsp_frame_mixing`
- **THEN** o boot acrescenta só a linha `gpsp_frame_mixing = "enabled"` e preserva as demais, inclusive se o arquivo não termina com quebra de linha

#### Scenario: Escolha do usuário preservada
- **WHEN** `gpSP.opt` já tem `gpsp_frame_mixing = "disabled"`, por exemplo salvo pelo usuário no menu
- **THEN** o boot não o altera

### Requirement: Chave para desligar o interframe blending
O usuário SHALL poder desligar o padrão criando o arquivo vazio `r36-gpsp-sem-ghost` na raiz da R36-ROMS pelo PC.

#### Scenario: Chave para desligar
- **WHEN** o usuário cria `r36-gpsp-sem-ghost` na raiz da R36-ROMS e liga o aparelho
- **THEN** a linha `gpsp_frame_mixing = "enabled"` é removida de `gpSP.opt` (e só ela), o gpSP abre sem o efeito, e a linha não volta enquanto o arquivo existir

#### Scenario: Outros cores de GBA
- **WHEN** o usuário abre um jogo no mGBA, VBA-M ou VBA Next
- **THEN** nada muda nesses cores

### Requirement: gpSP inicia pela BIOS por padrão
O gpSP SHALL abrir os jogos de GBA com `gpsp_boot_mode` em `bios` ("Boot mode: Boot to BIOS"), pela opção gravada em `/storage/.config/retroarch/config/gpSP/gpSP.opt`. O sistema SHALL criar o arquivo, ou acrescentar a chave, no boot, somente se a chave não existir, e SHALL NOT alterar um valor existente nem outras linhas.

#### Scenario: Padrão de fábrica
- **WHEN** o usuário abre um jogo de GBA no gpSP depois de gravar a imagem com a p8 nova e ligar o aparelho, sem ter mexido na opção
- **THEN** o menu de opções do core mostra "Boot mode: Boot to BIOS"

#### Scenario: Arquivo existente sem a chave
- **WHEN** `gpSP.opt` já existe com outras opções e sem `gpsp_boot_mode`
- **THEN** o boot acrescenta só a linha `gpsp_boot_mode = "bios"` e preserva as demais, inclusive se o arquivo não termina com quebra de linha

#### Scenario: Escolha do usuário preservada
- **WHEN** `gpSP.opt` já tem `gpsp_boot_mode = "game"`, por exemplo salvo pelo usuário no menu
- **THEN** o boot não o altera

#### Scenario: A chave do blending não afeta o boot mode
- **WHEN** o usuário cria `r36-gpsp-sem-ghost` na raiz da R36-ROMS e liga o aparelho
- **THEN** só a linha `gpsp_frame_mixing = "enabled"` é removida, e `gpsp_boot_mode` continua como está
