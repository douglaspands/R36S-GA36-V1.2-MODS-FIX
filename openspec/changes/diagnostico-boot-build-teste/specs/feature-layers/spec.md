# Spec Delta

## ADDED Requirements

### Requirement: Features só de teste
O descritor SHALL aceitar o campo opcional `test_only`, booleano e com padrão `false`. Uma feature com `test_only = true` SHALL entrar só em builds de teste (`--test`). Um valor que não seja booleano SHALL fazer o build falhar.

#### Scenario: Feature de teste num build normal
- **WHEN** uma feature habilitada tem `test_only = true` e o build roda sem `--test`
- **THEN** o build não a aplica, e ela não aparece no manifest nem no `R36-BUILD.txt`

#### Scenario: Feature de teste num build de teste
- **WHEN** uma feature habilitada tem `test_only = true` e o build roda com `--test`
- **THEN** o build a aplica na ordem declarada, e ela aparece no manifest, no `R36-BUILD.txt` e no `changes.txt`

#### Scenario: Valor inválido
- **WHEN** um descritor tem `test_only = "sim"`
- **THEN** o build falha, indicando a feature e que o campo deve ser true ou false

## MODIFIED Requirements

### Requirement: Seleção de features no build
Por padrão, o build SHALL aplicar todas as features habilitadas, exceto as `test_only`, que entram só em builds com `--test`. O build SHALL aceitar uma opção para aplicar só uma lista de features, ou nenhuma (a "feature vazia"). Uma feature desabilitada no descritor SHALL ser ignorada. Pedir pela lista uma feature `test_only` num build sem `--test` SHALL fazer o build falhar.

#### Scenario: Build sem features
- **WHEN** o build é executado com a opção de nenhuma feature
- **THEN** a imagem é gerada só a partir da base, e o manifest registra a lista de features vazia

#### Scenario: Feature desabilitada
- **WHEN** um descritor marca a feature como desabilitada
- **THEN** o build padrão não a aplica, e ela não aparece no manifest

#### Scenario: Feature de teste pedida pela lista sem --test
- **WHEN** o build é executado com `--features 90-boot-log-tela` e sem `--test`
- **THEN** o build falha antes de gerar saída, informando que a feature é só de teste e exige `--test`
