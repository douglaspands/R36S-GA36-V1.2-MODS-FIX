# Spec Delta

## MODIFIED Requirements

### Requirement: Artefatos de saída versionados
Cada build SHALL ser identificado por um timestamp no formato `AAAAMMDD-HHMMSS`. O build SHALL aceitar a opção opcional `--timestamp <TIMESTAMP>` para fixar o timestamp explicitamente; se omitido, o timestamp SHALL ser gerado a partir do horário local atual. A imagem completa SHALL se chamar `<prefixo>_<idioma>_build_<timestamp>.img.xz`, com prefixo configurado (`r36s_ga36-mb_v1.2-20260416`) e `<idioma>` o código do idioma do build em minúsculas com `-` no lugar de `_` (`en-us` no padrão `en_US`, `pt-br` com `--idioma pt_BR`); um build sem features, que não tem idioma, SHALL se chamar `<prefixo>_build_<timestamp>.img.xz`. O diretório `<timestamp>`, sem o idioma, SHALL conter a imagem, uma imagem por partição gravável e um manifest (timestamp, idioma, tamanho do cartão, sha256, offsets e features). O manifest SHALL registrar `"language"` com o código original (`en_US`) e o `R36-BUILD.txt` a linha `idioma: en_US`. Um diretório existente SHALL NOT ser sobrescrito.

O build SHALL aceitar a opção `--test`, que o marca como imagem de teste (intermediária). Num build de teste, o diretório SHALL se chamar `<timestamp>-test` e a imagem completa SHALL se chamar `<prefixo>_<idioma>_build_<timestamp>-test.img.xz`. O timestamp registrado no manifest SHALL continuar sendo apenas `AAAAMMDD-HHMMSS`, o manifest SHALL conter `"test": true`, e o `R36-BUILD.txt` SHALL conter a linha `teste: sim`. Num build sem `--test`, o nome, o manifest e o `R36-BUILD.txt` SHALL ficar exatamente como se a opção não existisse. A opção `--test` SHALL NOT alterar o conteúdo das partições, o conjunto de features nem o tamanho do cartão.

#### Scenario: Timestamp explícito informado
- **WHEN** o build é executado com `--timestamp 20261030-120000`
- **THEN** o diretório de saída é `20261030-120000`, a imagem gerada usa o timestamp `20261030-120000` no nome e no manifest, mesmo que o relógio do sistema avance durante a compilação

#### Scenario: Timestamp inválido
- **WHEN** o build é executado com `--timestamp` em formato diferente de `AAAAMMDD-HHMMSS`
- **THEN** o build falha antes de criar arquivos, informando formato inválido

#### Scenario: Saída completa
- **WHEN** um build termina com sucesso
- **THEN** o diretório do build contém a imagem completa comprimida, as quatro imagens de partição (boot, system, storage, roms) e o manifest, e o sha256 de cada arquivo confere com o manifest

#### Scenario: Nome da imagem
- **WHEN** um build é gerado em 13/10/2026 às 15:30:45, hora local
- **THEN** a imagem completa se chama `r36s_ga36-mb_v1.2-20260416_en-us_build_20261013-153045.img.xz`, o diretório se chama `20261013-153045`, o manifest registra o timestamp `20261013-153045` e `"language": "en_US"`, e o `R36-BUILD.txt` registra o nome da imagem e `idioma: en_US`, sem uma linha separada de timestamp

#### Scenario: Build no mesmo segundo
- **WHEN** um build é iniciado no mesmo segundo de outro, cujo diretório de saída já existe
- **THEN** o build falha sem alterar o diretório existente

#### Scenario: Build de teste
- **WHEN** um build é gerado com `--test` em 13/10/2026 às 15:30:45, hora local
- **THEN** o diretório se chama `20261013-153045-test`, a imagem completa se chama `r36s_ga36-mb_v1.2-20260416_en-us_build_20261013-153045-test.img.xz`, o manifest registra o timestamp `20261013-153045` e `"test": true`, e o `R36-BUILD.txt` contém `teste: sim`

#### Scenario: Build normal inalterado
- **WHEN** um build é gerado sem `--test`
- **THEN** o nome do diretório e da imagem não têm o sufixo `-test`, o manifest não tem o campo `test`, e o `R36-BUILD.txt` não tem a linha `teste:`

#### Scenario: Outro idioma no nome
- **WHEN** um build é gerado com `--idioma pt_BR`
- **THEN** a imagem completa tem `_pt-br_` no nome, o diretório continua só com o timestamp, e o manifest e o `R36-BUILD.txt` registram `pt_BR`

#### Scenario: Build sem features
- **WHEN** um build é gerado com `--no-features`
- **THEN** a imagem completa se chama `<prefixo>_build_<timestamp>.img.xz`, sem idioma, e o manifest e o `R36-BUILD.txt` não registram idioma
