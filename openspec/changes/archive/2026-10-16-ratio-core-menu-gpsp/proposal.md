# Proposal

## Why

Três padrões de fábrica do EmuELEC não agradam ao uso diário do R36S: a proporção de tela dos jogos é forçada em 4:3, os menus do RetroArch vêm com OK e Cancel invertidos em relação ao controle posicional da feature 20, e o GBA abre no mGBA, mais pesado que o gpSP para o A33 (4x Cortex-A7). As três correções são valores em arquivos da p8, sem tocar no SYSTEM.

## What Changes

- **Proporção:** `global.ratio` passa de `4/3` para `core` no `emuelec.conf`. O EmulationStation grava `aspect_ratio_index = "22"` ("Core provided") no `retroarch.cfg` ao lançar cada jogo, então cada core usa a proporção que ele mesmo informa.
- **OK/Cancel nos menus do RetroArch:** `menu_swap_ok_cancel_buttons` passa de `"true"` para `"false"` no `retroarch.cfg`. Com a feature 20, OK fica no botão da direita (A do RetroPad) e Cancel no de baixo (B).
- **GBA:** o `emuelec.conf` ganha `gba.emulator=libretro` e `gba.core=gpsp`, e o gpSP vira o core padrão do Game Boy Advance. O mGBA, o vbam e o vba_next continuam instalados e selecionáveis pelo menu do ES.
- Os três ajustes entram na feature `10-ptbr-sao-paulo`, que já é dona dos dois arquivos (o build proíbe duas features no mesmo caminho sem `[[override]]`, e um override obrigaria a duplicar o `retroarch.cfg` de 3000 linhas). O `name` e a `description` da feature passam a citar os novos padrões.
- **No cartão:** os dois arquivos ficam na p8, então a mudança só chega com `--wipe-storage`. Quem já tem cartão gravado muda os três pontos pelo menu do ES e do RetroArch.
- Fora do escopo: instalar `gba_bios.bin` (o gpSP roda sem ele, com BIOS HLE interno), mexer no SYSTEM, `es_systems.cfg` ou `setsettings.sh`, e mudar a proporção por sistema (`<sistema>.ratio`).

## Capabilities

### New Capabilities
- `display-aspect-ratio`: proporção de tela padrão dos jogos (core provided) e como o EmuELEC a aplica.
- `gba-emulation`: emulador e core padrão do Game Boy Advance na imagem gerada.

### Modified Capabilities
- `retroarch-controls`: ganha o requisito de que OK e Cancel dos menus do RetroArch não ficam invertidos.

## Impact

- `features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf`: `global.ratio`, `gba.emulator`, `gba.core`.
- `features/10-ptbr-sao-paulo/storage/.config/retroarch/retroarch.cfg`: `menu_swap_ok_cancel_buttons`.
- `features/10-ptbr-sao-paulo/feature.toml`: `name` e `description`.
- `tests/test_ptbr_controle.py`: conferências das quatro chaves; README: seção da feature 10.
- O `joy2key.py` do SYSTEM lê `menu_swap_ok_cancel_buttons`, então os diálogos de ferramentas lançados pelo ES também deixam de trocar A e B.
- O registro térmico (`thermal-control`) passa a gravar `gpsp` no lugar de `mgba` para GBA; o exemplo no spec é só ilustrativo e não muda.
