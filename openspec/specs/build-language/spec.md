# build-language Specification

## Purpose
Permite gerar a imagem já no idioma de quem vai usar o aparelho, escolhendo o idioma no build em vez de editar arquivos, e igual no EmuELEC, no ES e no RetroArch.

## Requirements

### Requirement: Idioma padrão escolhido no build
O build SHALL aceitar a opção `--lang <código>` (e SHALL aceitar `--idioma <código>` como alias retrocompatível equivalente), com padrão `en_US`, e SHALL gravar esse idioma como padrão de fábrica do EmuELEC (`system.language`), do EmulationStation (`Language`) e do RetroArch (`user_language`). Os códigos aceitos SHALL ser `pt_BR`, `pt_PT`, `en_US`, `en_GB`, `es_ES`, `fr_FR`, `de_DE` e `it_IT`. O build SHALL trocar só essas três chaves, em cópias de trabalho dos arquivos, e SHALL NOT alterar os arquivos das features no repositório.

#### Scenario: Sem a opção
- **WHEN** o build roda sem `--lang` (ou sem `--idioma`)
- **THEN** o `emuelec.conf` da p8 tem `system.language=en_US`, o `es_settings.cfg` tem `Language` = `en_US` e o `retroarch.cfg` tem `user_language = "0"`: o EmuELEC, o ES e o RetroArch da imagem estão em inglês

#### Scenario: Português do Brasil
- **WHEN** o build roda com `--lang pt_BR` (ou `--idioma pt_BR`)
- **THEN** o `emuelec.conf` da p8 tem `system.language=pt_BR`, o `es_settings.cfg` tem `Language` = `pt_BR` e o `retroarch.cfg` tem `user_language = "7"`

#### Scenario: Código inválido
- **WHEN** o build roda com `--lang xx_YY` (ou `--idioma xx_YY`)
- **THEN** o build falha antes de gerar qualquer arquivo, com a lista dos códigos aceitos

#### Scenario: Arquivos do repositório intactos
- **WHEN** o build roda com `--lang fr_FR` (ou `--idioma fr_FR`)
- **THEN** os arquivos em `features/` do repositório não são alterados e um build seguinte sem a opção volta ao inglês

#### Scenario: Chave ausente
- **WHEN** um dos três arquivos de configuração das features não tem a chave de idioma
- **THEN** o build falha com uma mensagem que diz o arquivo e a chave, sem gerar a imagem

### Requirement: Idioma e build sem features
Um build sem features (`--no-features`) SHALL NOT aceitar `--lang` (nem `--idioma`) e SHALL continuar equivalente à base. Um build cujas features selecionadas não trazem os três arquivos de configuração SHALL sair sem idioma quando `--lang` (ou `--idioma`) não foi passado, e SHALL falhar dizendo qual arquivo falta quando `--lang` (ou `--idioma`) foi passado.

#### Scenario: Sem features e com idioma
- **WHEN** o build roda com `--no-features --lang en_US` (ou `--no-features --idioma en_US`)
- **THEN** o build falha explicando que o idioma exige as features

#### Scenario: Features sem os arquivos de idioma, sem a opção
- **WHEN** o build roda com `--features` que não inclui a feature que traz o `emuelec.conf`, o `es_settings.cfg` e o `retroarch.cfg`, sem `--lang` nem `--idioma`
- **THEN** o build termina sem idioma: o nome da imagem, o manifest e o `R36-BUILD.txt` não registram idioma

#### Scenario: Features sem os arquivos de idioma, com a opção
- **WHEN** o build roda com esse `--features` e `--lang pt_BR` (ou `--idioma pt_BR`)
- **THEN** o build falha dizendo qual arquivo de configuração falta para aplicar o idioma
