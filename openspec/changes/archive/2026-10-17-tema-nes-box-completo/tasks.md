# Tasks

## 1. Feature, cópia do NES-BOX e sistemas por referência

- [x] 1.1 Criar `features/51-tema-nes-box-v2/` com `feature.toml` (ordem 51, camada `storage`) e um `gerar.sh` que extrai o NES-BOX da p8 da base para `storage/.config/emulationstation/themes/NES-BOX-V2/` (`debugfs rdump`, sem root) e escreve o `.gitignore` com os caminhos copiados. Verificar que, depois de rodar o `gerar.sh`, o diretório tem as mesmas pastas do NES-BOX e `git status` não lista nenhum arquivo copiado.
- [x] 1.2 Criar `tests/test_tema_nes_box_v2.py`: cruza os `<theme>` do `es_systems.cfg` da base com as pastas do NES-BOX-V2, confere que todo `<path>` dos `theme.xml` novos resolve e que cada pasta nova tem origem registrada. Verificar que o teste falha, listando os 15 sistemas faltantes, antes das pastas novas existirem.
- [x] 1.3 Criar as 7 pastas por referência (`pce-cd`→`pcenginecd`, `tic-80`→`tic80`, `sharpx1`→`x1`, `prboom`→`doom`, `ecwolf`→`wolf`, `megadrivemsu`→`megadrive`, `ggh`→`gamegear`), cada uma só com `theme.xml` apontando para `../<existente>/`. Verificar que o teste passa para esses 7 e falha só para os 8 restantes.
- [x] 1.4 Validar que o ES resolve `../` em `<path>` de imagem (ler o código do ES do EmuELEC ou testar no aparelho). Se não resolver, aplicar o fallback do design (o `gerar.sh` copia os 2 PNGs equivalentes para a pasta nova) e atualizar o design.md. Verificar com o resultado registrado no design.md.

## 2. Fontes da arte oficial

- [x] 2.1 Para cada um dos 8 sistemas (`wii`, `pgm2`, `fmtmarty`, `mplayer`, `freej2me`, `gmloader`, `karaoke`, `imageviewer`), buscar na internet o logo oficial e a arte de personagem oficial (ordem do design: projeto ou fabricante, Wikimedia Commons, Logopedia e wikis, arte promocional), baixar para `work/cache/` e conferir visualmente fundo, resolução e qualidade. Verificar com uma lista por sistema e por arquivo: URL, sha256 e decisão (`oficial` ou `criado`, com o motivo).
- [x] 2.2 Registrar essa decisão em `features/51-tema-nes-box-v2/fontes.toml` (sistema, arquivo, tipo, URL, sha256). Verificar que o arquivo tem entrada para os 16 arquivos (8 sistemas x 2) e que o teste de cobertura lê o arquivo e falha se faltar alguma.

## 3. Geração da arte

- [x] 3.1 Acrescentar ao `gerar.sh` (ImageMagick 7) o download dos itens `oficial` do `fontes.toml`, com conferência do sha256, e a conversão para PNG transparente (`system.png` entre 400 e 600 px de largura, `background_icon.png` 960x540 com o personagem na metade direita) em `NES-BOX-V2/<sistema>/`. Verificar rodando-o e conferindo dimensões e transparência com `identify`.
- [x] 3.2 Acrescentar ao `gerar.sh` a criação dos itens `criado`: logo com ícone temático (SVG do Lucide na pasta da feature) mais o nome do sistema em texto, e ilustração do assunto como arte de personagem. Verificar que `karaoke` e `imageviewer` saem completos e que a pré-visualização mostra logo e arte legíveis a 640x480.
- [x] 3.3 Gerar o `theme.xml` das 8 pastas novas a partir do formato existente (`./system.png`, `./background_icon.png`). Verificar que o teste de cobertura passa para os 15 sistemas, incluindo transparência e dimensões dos PNGs.
- [x] 3.4 Gerar o registro de origem no `LEIA-ME.txt` a partir do `fontes.toml` e do mapa de referências. Verificar que cada um dos 15 sistemas aparece com tipo e origem, e que o teste confere a presença.

## 4. Documentação

- [x] 4.1 Acrescentar ao README a seção da feature `51-tema-nes-box-v2` (o que faz, NES-BOX continua o padrão, como escolher o V2, só com `--wipe-storage`, cópia pelo PC para `--keep-storage`, como desligar com `enabled = false`, como regenerar com `gerar.sh`, e a nota de licença do NES-BOX). Verificar que os comandos da seção rodam como escritos.
- [x] 4.2 Conferir se o README e o `LEIA-ME.txt` da `50-temas-extras` dizem que o tema tem lacunas e atualizar. Verificar com `grep -n "NES-BOX" README.md`.

## 5. Integração

- [x] 5.1 Rodar a suíte rápida (`uv run python -I -m unittest discover -s tests`) e verificar que passa, incluindo o teste novo.
- [x] 5.2 Gerar uma imagem completa, sem `--test`, e conferir no `changes.txt` que só há adições sob o NES-BOX-V2, e que o build mostra o tamanho do tema dentro do orçamento. Verificar com `debugfs -R "ls /.config/emulationstation/themes" out/<timestamp>/parts/storage.img` (NES-BOX e NES-BOX-V2 presentes).
- [ ] 5.3 Gravar com `--wipe-storage` e conferir no aparelho que o NES-BOX continua o padrão, que o V2 aparece na lista de temas e que cada um dos 15 sistemas aparece com logo e arte no V2, na tela de 640x480, sem corte. Verificar com uma foto ou a descrição de cada sistema.

## Workflow follow-up

- Arquivar a change depois que a revisão da imagem no aparelho for aprovada, e conferir que o spec `es-themes` recebeu os requisitos novos.
