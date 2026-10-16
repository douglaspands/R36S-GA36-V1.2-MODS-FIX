## MODIFIED Requirements

### Requirement: Artefatos de saída versionados
Cada build SHALL ser identificado pelo timestamp local da geração, no formato `AAAAMMDD-HHMMSS`. A imagem completa SHALL se chamar `<prefixo>_build_<timestamp>.img.xz`, com prefixo configurado (`r36s_ga36-mb_v1.2-20260416`). O diretório `<timestamp>` SHALL conter a imagem, uma imagem por partição gravável e um manifest (timestamp, tamanho do cartão, sha256, offsets e features). Um diretório existente SHALL NOT ser sobrescrito.

O build SHALL aceitar a opção `--test`, que o marca como imagem de teste (intermediária). Num build de teste, o diretório SHALL se chamar `<timestamp>-test` e a imagem completa SHALL se chamar `<prefixo>_build_<timestamp>-test.img.xz`. O timestamp registrado no manifest SHALL continuar sendo apenas `AAAAMMDD-HHMMSS`, o manifest SHALL conter `"test": true`, e o `R36-BUILD.txt` SHALL conter a linha `teste: sim`. Num build sem `--test`, o nome, o manifest e o `R36-BUILD.txt` SHALL ficar exatamente como se a opção não existisse. A opção `--test` SHALL NOT alterar o conteúdo das partições, o conjunto de features nem o tamanho do cartão.

#### Scenario: Saída completa
- **WHEN** um build termina com sucesso
- **THEN** o diretório do build contém a imagem completa comprimida, as quatro imagens de partição (boot, system, storage, roms) e o manifest, e o sha256 de cada arquivo confere com o manifest

#### Scenario: Nome da imagem
- **WHEN** um build é gerado em 13/10/2026 às 15:30:45, hora local
- **THEN** a imagem completa se chama `r36s_ga36-mb_v1.2-20260416_build_20261013-153045.img.xz`, o diretório se chama `20261013-153045`, o manifest registra o timestamp `20261013-153045`, e o `R36-BUILD.txt` registra o nome da imagem, sem uma linha separada de timestamp

#### Scenario: Build no mesmo segundo
- **WHEN** um build é iniciado no mesmo segundo de outro, cujo diretório de saída já existe
- **THEN** o build falha sem alterar o diretório existente

#### Scenario: Build de teste
- **WHEN** um build é gerado com `--test` em 13/10/2026 às 15:30:45, hora local
- **THEN** o diretório se chama `20261013-153045-test`, a imagem completa se chama `r36s_ga36-mb_v1.2-20260416_build_20261013-153045-test.img.xz`, o manifest registra o timestamp `20261013-153045` e `"test": true`, e o `R36-BUILD.txt` contém `teste: sim`

#### Scenario: Build normal inalterado
- **WHEN** um build é gerado sem `--test`
- **THEN** o nome do diretório e da imagem não têm sufixo, o manifest não tem o campo `test`, e o `R36-BUILD.txt` não tem a linha `teste:`
