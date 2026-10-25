# Design

## Context

- O EmulationStation do EmuELEC 4.7 procura temas nas seguintes ordens de caminhos:
  1. `/storage/.config/emulationstation/themes/` (camada `storage`, partição p8 ext4)
  2. `/usr/config/emulationstation/themes/` (camada `system`, somente leitura)
  3. `/etc/emulationstation/themes/`
  4. `/storage/roms/themes/` (camada `roms`, partição p1 FAT32)
- A partição p8 (`R36-STORAGE`, ext4) tem tamanho fixo de ~1.5 GiB na tabela de partição da base. Hoje ela tem cerca de 900 MiB livres, mas abrigava o Crystal (245 MB compactado, ~270 MB extraído), Switch (~14 MB) e NES-BOX-V2 (~25 MB).
- A partição p1 (`R36-ROMS`, FAT32) começa nos setores da base e é expandida para ocupar o restante de todo o cartão SD (tem mais de 12 GB livres num cartão de 16 GB e dezenas de GB em cartões maiores).
- A camada `roms` usa FAT32. O sistema de build (`tools/r36img/features.py`) proíbe expressamente links simbólicos na camada FAT (`FAT_LAYERS = ("roms", "boot")`). Os temas direcionados para `roms` precisam ser árvores limpas de arquivos regulares e diretórios.
- O tema `es-theme-epic-cody-RG351V` do CodyV59 foi desenvolvido para a tela de 640x480 (4:3), perfeitamente compatível com a resolução nativa do clone do R36S.

## Goals / Non-Goals

**Goals:**
- Aliviar a partição `storage` (p8), mantendo nela apenas temas muito leves (~33 MiB no total).
- Mover os temas pesados e ricos em multimídia (`Crystal`, `Switch` e `Epic Cody`) para a partição `roms` (p1), onde há espaço abundante.
- Remover completamente a complexidade da feature `51-tema-nes-box-v2` (gerador, dependências de ImageMagick, SVGs e testes de cobertura de arte faltante), mantendo o `NES-BOX` de fábrica como o padrão inalterado.
- Garantir que todos os 5 temas extras continuem aparecendo normalmente no menu do EmulationStation.
- Builds reproduzíveis e offline-friendly usando o mecanismo existente de `[[external]]`.

**Non-Goals:**
- Alterar o tema padrão no primeiro boot (continua sendo o NES-BOX de fábrica).
- Modificar o código do EmulationStation (o ES já busca em `/storage/roms/themes/` por padrão).

## Decisions

1. **Remoção total da feature `51-tema-nes-box-v2`:**
   A pasta `features/51-tema-nes-box-v2/` e o teste `tests/test_tema_nes_box_v2.py` são deletados. O NES-BOX original de fábrica já reside na partição da imagem base e continua 100% funcional.

2. **Reorganização de camadas em `features/50-temas-extras/feature.toml`:**
   - **Camada `storage` (p8 - ext4):**
     - `Minimal EmuELEC` -> `.config/emulationstation/themes/Minimal EmuELEC`
     - `Graphite OGA` -> `.config/emulationstation/themes/Graphite OGA`
     *(Carga na p8 reduzida para ~33 MiB)*
   - **Camada `roms` (p1 - FAT32):**
     - `Switch` -> `themes/Switch`
     - `Crystal` -> `themes/Crystal`
     - `Epic Cody` -> `themes/Epic Cody`
     *(Gravados na raiz FAT32 do cartão sob a pasta `themes/`, mapeada para `/storage/roms/themes/`)*

3. **Inclusão do tema Epic Cody do CodyV59:**
   Utilizar a URL do repositório `CodyV59/es-theme-epic-cody-RG351V` com commit fixo e conferência de `sha256`:
   ```toml
   [[external]]
   layer = "roms"
   dest = "themes/Epic Cody"
   url = "https://codeload.github.com/CodyV59/es-theme-epic-cody-RG351V/tar.gz/<commit>"
   sha256 = "<sha256>"
   strip = 1
   exclude = [".git*", "*.md"]
   ```

4. **Verificação de compatibilidade FAT32:**
   - Os arquivos do `Crystal` e `Switch` foram verificados e possuem 0 links simbólicos.
   - O tarball do `Epic Cody` será verificado durante o download para garantir ausência de symlinks antes da integração.

5. **Ajuste de orçamento (`budget_mib`):**
   O `budget_mib` na feature `50-temas-extras` é elevado para 700 MiB para permitir a soma de todos os downloads externos extraídos (já que Crystal ~270M + Epic Cody ~180M + Switch ~20M + Minimal/Graphite ~35M somam ~500 MiB no total de arquivos extraídos pelo build).

## Risks / Trade-offs

- **[Cartão SD sem partição de ROMs montada]:** se a partição `roms` não for montada por algum motivo, os temas no cartão não serão exibidos na lista (apenas NES-BOX, Minimal e Graphite aparecerão). Como os próprios jogos já exigem a partição `roms`, este comportamento é consistente e esperado.
- **[Tempo de gravação no cartão]:** a gravação dos temas na p1 aumenta ligeiramente o `write_sectors` da partição FAT32 se o cartão for regravado do zero (`--wipe-all`). No entanto, a gravação de updates com `--keep-roms` fica extremamente rápida porque a p8 não precisa mais gravar 300 MB de imagens e fontes de temas.
- **[Acesso via PC]:** os usuários ganham a facilidade de ver a pasta `themes/` diretamente ao plugar o cartão no computador (Windows/Mac/Linux), podendo inclusive inspecionar os arquivos sem drivers de ext4.
