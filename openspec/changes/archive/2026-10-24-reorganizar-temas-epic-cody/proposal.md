# Proposal

## Why

A partição `storage` (p8, ext4) possui tamanho fixo de aproximadamente 1.5 GiB na imagem e precisa acomodar configurações de usuários, saves, estados e pacotes. Hoje, ela armazena temas do EmulationStation que ocupam centenas de megabytes (o tema Crystal sozinho tem ~250 MB compactado), além da feature `51-tema-nes-box-v2` que exigia manutenção complexa de dezenas de assets e scripts de geração local.

O usuário quer adicionar o tema **Epic Cody** (versão 4:3 640x480 do CodyV59, adaptada do Epic Noir para o RG351V), mas somar esse tema na p8 estouraria o espaço livre. Em contrapartida, a partição de ROMs (`R36-ROMS`, p1, FAT32) expande-se para ocupar toda a capacidade do cartão SD (tem gigabytes ou dezenas de gigabytes livres), é montada em `/storage/roms` e o EmulationStation do EmuELEC já possui suporte nativo para carregar temas em `/storage/roms/themes/`.

Portanto, reorganizamos os temas: removemos o `NES-BOX-V2`, preservamos o `NES-BOX` de fábrica como tema padrão imutável, mantemos temas leves na partição `storage` e movemos os temas pesados (`Crystal`, `Switch` e o novo `Epic Cody`) para a partição de ROMs (`roms`).

## What Changes

- **Remoção do NES-BOX-V2**: a feature `features/51-tema-nes-box-v2/` e seu teste associado `tests/test_tema_nes_box_v2.py` são removidos. O tema `NES-BOX` original de fábrica da imagem base permanece intacto e continua sendo o tema padrão no primeiro boot.
- **Migração de temas pesados para `roms`**:
  - `Crystal` e `Switch` passam a ser gravados na camada `roms`, no caminho `themes/Crystal` e `themes/Switch` (visíveis no sistema em `/storage/roms/themes/` e acessíveis diretamente pelo computador no PC/FAT32).
  - O tema **Epic Cody** (`CodyV59/es-theme-epic-cody-RG351V`) é adicionado como conteúdo externo (`[[external]]`) na camada `roms` em `themes/Epic Cody`, fixado por commit estável e conferido por sha256.
- **Temas leves mantidos em `storage`**:
  - `Minimal EmuELEC` e `Graphite OGA` permanecem na partição `storage` (ocupando apenas ~33 MB).
- **Orçamento de build atualizado**: o `budget_mib` da feature `50-temas-extras` é atualizado para refletir o novo total de downloads externos.

## Capabilities

### New Capabilities
Nenhuma.

### Modified Capabilities
- `es-themes`: remove os requisitos de existência e cobertura do NES-BOX-V2; atualiza os temas disponíveis (adicionando Epic Cody) e a distribuição dos temas entre a partição do sistema (`storage`) e a partição do cartão (`roms`).

## Impact

- **Armazenamento:** a partição `storage` (p8) recupera mais de 300 MiB livres, deixando mais de 850 MiB livres para configurações do usuário e RetroArch.
- **Partição de ROMs (p1):** ganha o diretório `themes/` na raiz FAT32 com `Crystal`, `Switch` e `Epic Cody`. Os arquivos são legíveis no PC diretamente.
- **Build:** remoção de scripts e dependências do `gerar.sh` (ImageMagick, debugfs para V2). O build passa a baixar e aplicar o tarball do Epic Cody via pipeline padrão de `[[external]]`.
- **Testes e Docs:** remoção do teste de cobertura do NES-BOX-V2 e atualização do `README.md`.
