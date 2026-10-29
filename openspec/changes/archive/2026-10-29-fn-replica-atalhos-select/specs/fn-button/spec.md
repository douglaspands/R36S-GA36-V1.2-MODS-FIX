# Spec Delta

## Purpose

Definir como o botão FN do R36S chega ao RetroArch como o hotkey, como o hotkey acompanha o resultado do remapeamento, como desfazer e como diagnosticá-lo pelo cartão.

## ADDED Requirements

### Requirement: FN como botão próprio
No boot, o sistema SHALL trocar o código que o FN emite para o do botão `BTN_MODE` (316), para que o RetroArch receba o FN como um botão do `micro_gamepad` diferente do Select (botão 10 do autoconfig, contra o 8 do Select).

#### Scenario: FN chega ao RetroArch
- **WHEN** o aparelho está ligado e o usuário aperta o FN
- **THEN** o RetroArch recebe o botão 10 do `micro_gamepad`, e o Select físico continua sendo o botão 8

#### Scenario: Evento do FN depois do boot
- **WHEN** o aparelho terminou de ligar e o usuário aperta o FN
- **THEN** o `micro_gamepad` emite `code 316 (BTN_MODE)` e não emite mais `KEY_FN` (464); a leitura de `fn_key` não prova o remapeamento, porque o driver devolve nela um valor sem relação com o código

#### Scenario: Driver do gamepad carrega depois do serviço
- **WHEN** o `fn_key` só passa a existir alguns segundos depois do início do serviço, dentro de 60 s
- **THEN** o serviço espera, escreve o 316 e o FN passa a emitir `BTN_MODE`

#### Scenario: fn_key nunca aparece
- **WHEN** o `fn_key` não existe 60 s depois do início do serviço
- **THEN** o serviço sai com código 0, o boot segue sem travar e o estado registra `modo=sem-fn_key`

#### Scenario: Select físico intacto
- **WHEN** o usuário aperta o Select físico
- **THEN** o RetroArch o recebe como o botão 8, o Select do jogo, como antes da troca

### Requirement: Hotkey acompanha o remapeamento
O serviço SHALL gravar `input_enable_hotkey_btn` no `micro_gamepad.cfg` da p8: `10` apenas quando a escrita do 316 em `fn_key` tiver sucesso (código de saída 0), e `8` em qualquer outro caso (chave `r36-fn-original`, `fn_key` ausente ou escrita recusada). O serviço SHALL NOT decidir pela leitura de `fn_key`, que no aparelho não devolve o código escrito. O arquivo da imagem SHALL trazer `8`. O serviço SHALL NOT criar o arquivo na p8 se ele não existir, e SHALL alterar só essa linha.

#### Scenario: Remapeamento valeu
- **WHEN** a escrita do 316 em `fn_key` tem sucesso, seja qual for o valor lido de volta
- **THEN** o `micro_gamepad.cfg` da p8 tem `input_enable_hotkey_btn = "10"` e as outras linhas intactas

#### Scenario: fn_key ausente
- **WHEN** o `fn_key` não aparece em 60 s
- **THEN** o `micro_gamepad.cfg` da p8 tem `input_enable_hotkey_btn = "8"` e o Select abre o menu como na base

#### Scenario: Driver recusa a escrita
- **WHEN** a escrita do 316 em `fn_key` falha (código de saída diferente de 0)
- **THEN** o `micro_gamepad.cfg` da p8 tem `input_enable_hotkey_btn = "8"`

#### Scenario: Cartão que já tinha o cfg
- **WHEN** a p8 já tem um `micro_gamepad.cfg` de uma gravação anterior e só o `system` é regravado
- **THEN** o serviço atualiza a linha do hotkey no boot, sem exigir regravar a p8

### Requirement: Chave para devolver o FN de fábrica
Quando a raiz da p1 tiver o arquivo vazio `r36-fn-original`, o sistema SHALL NOT trocar o código do FN, que fica no valor de fábrica (464), e SHALL deixar o hotkey no Select (`input_enable_hotkey_btn = "8"`).

#### Scenario: Desligar pelo PC
- **WHEN** o usuário cria `r36-fn-original` na raiz da p1 e religa o aparelho
- **THEN** a leitura de `fn_key` mostra 464, o FN não aciona nenhum botão do RetroPad e o Select + X abre o menu

#### Scenario: p1 indisponível
- **WHEN** `/storage/roms` não monta em até 20 s
- **THEN** o serviço trata a chave como ausente, troca o código e o boot segue sem travar

### Requirement: FN reservado no EmulationStation
No EmulationStation, o FN SHALL NOT ter o comportamento do Select nem de outro botão: o `es_input.cfg` da imagem SHALL NOT trazer bind do botão 10 do `micro_gamepad`, para que o FN fique livre para funções futuras (por exemplo o controle de brilho da tela).

#### Scenario: FN nas listas do EmulationStation
- **WHEN** o FN está remapeado e o usuário o aperta nas telas do EmulationStation
- **THEN** nada é selecionado, navegado nem aberto, e o Select continua servindo como antes

#### Scenario: Sem bind do botão 10 no ES
- **WHEN** o `es_input.cfg` da imagem gerada é inspecionado
- **THEN** o `micro_gamepad` não tem entrada com `id="10"`
