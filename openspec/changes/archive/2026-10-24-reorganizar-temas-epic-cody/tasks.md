# Tasks

## 1. Remoção do NES-BOX-V2

- [x] 1.1 Remover a pasta `features/51-tema-nes-box-v2/` e todos os seus arquivos (descritor, scripts, SVGs e arte).
- [x] 1.2 Remover o arquivo de teste `tests/test_tema_nes_box_v2.py`.
- [x] 1.3 Rodar a suíte de testes (`uv run python -I -m unittest discover -s tests`) para garantir que os demais testes passam sem referências residuais à feature 51.

## 2. Obtenção e validação do tema Epic Cody

- [x] 2.1 Identificar o commit fixo mais recente da branch `main` do repositório `CodyV59/es-theme-epic-cody-RG351V`.
- [x] 2.2 Baixar o tarball correspondente, calcular o sha256 e salvar em `work/cache/external/`.
- [x] 2.3 Inspecionar o tarball para certificar que não contém links simbólicos incompatíveis com o sistema de arquivos FAT32 (`tar -tzf ... | grep "^l"`).

## 3. Reorganização dos temas em `features/50-temas-extras`

- [x] 3.1 Atualizar `features/50-temas-extras/feature.toml`:
  - Definir `budget_mib = 700` para acomodar os temas extras.
  - Atualizar a entrada do `Switch` para `layer = "roms"` e `dest = "themes/Switch"`.
  - Atualizar a entrada do `Crystal` para `layer = "roms"` e `dest = "themes/Crystal"`.
  - Adicionar a entrada do `Epic Cody` com `layer = "roms"` e `dest = "themes/Epic Cody"`, apontando para a URL de commit fixo e sha256.
  - Manter `Minimal EmuELEC` e `Graphite OGA` em `layer = "storage"`.
- [x] 3.2 Criar ou atualizar teste automatizado para garantir que os temas da camada `roms` utilizam caminhos iniciados por `themes/` e não geram links simbólicos.

## 4. Validação de Build

- [x] 4.1 Rodar a suíte completa de testes (`uv run python -I -m unittest discover -s tests`).
- [x] 4.2 Executar o build com a feature de temas (`./build.sh --features 50-temas-extras`) e verificar o `changes.txt`:
  - Conferir que `themes/Crystal`, `themes/Switch` e `themes/Epic Cody` aparecem na camada `roms`.
  - Conferir que apenas `Minimal EmuELEC` e `Graphite OGA` aparecem na camada `storage`.
  - Verificar que o orçamento de download (`budget_mib`) é respeitado.

## 5. Documentação

- [x] 5.1 Atualizar o `README.md`:
  - Remover a seção da feature `51-tema-nes-box-v2`.
  - Atualizar a descrição da feature `50-temas-extras`, explicando onde os temas ficam instalados (`storage` para temas leves, `roms/themes/` para temas ricos em mídia como Crystal, Switch e Epic Cody).
  - Mencionar que o usuário pode adicionar novos temas diretamente na partição FAT32 `R36-ROMS/themes/` ao plugar o cartão no PC.
