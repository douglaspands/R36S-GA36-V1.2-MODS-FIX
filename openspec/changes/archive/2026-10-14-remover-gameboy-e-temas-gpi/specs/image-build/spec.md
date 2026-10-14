## MODIFIED Requirements

### Requirement: Artefatos de saída versionados
Cada build SHALL ser identificado pelo timestamp local da geração, no formato `AAAAMMDD-HHMMSS`. A imagem completa SHALL se chamar `<prefixo>_build_<timestamp>.img.xz`, com prefixo configurado (`r36s_ga36-mb_v1.2-20260416`). O diretório `<timestamp>` SHALL conter a imagem, uma imagem por partição gravável e um manifest (timestamp, tamanho do cartão, sha256, offsets e features). Um diretório existente SHALL NOT ser sobrescrito.

#### Scenario: Saída completa
- **WHEN** um build termina com sucesso
- **THEN** o diretório do build contém a imagem completa comprimida, as quatro imagens de partição (boot, system, storage, roms) e o manifest, e o sha256 de cada arquivo confere com o manifest

#### Scenario: Nome da imagem
- **WHEN** um build é gerado em 13/10/2026 às 15:30:45, hora local
- **THEN** a imagem completa se chama `r36s_ga36-mb_v1.2-20260416_build_20261013-153045.img.xz`, o diretório se chama `20261013-153045`, o manifest registra o timestamp `20261013-153045`, e o `R36-BUILD.txt` registra o nome da imagem, sem uma linha separada de timestamp

#### Scenario: Build no mesmo segundo
- **WHEN** um build é iniciado no mesmo segundo de outro, cujo diretório de saída já existe
- **THEN** o build falha sem alterar o diretório existente
