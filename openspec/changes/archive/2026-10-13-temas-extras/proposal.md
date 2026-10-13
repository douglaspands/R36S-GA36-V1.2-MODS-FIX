# Proposal

## Why

O EmulationStation da imagem só tem o tema NES-BOX. O downloader de temas embutido precisa de Wi-Fi, que o aparelho não tem ativo. O usuário quer vários temas para escolher no menu, incluindo temas com personagens de jogos infantis.

## What Changes

- Nova feature `50-temas-extras`, que instala um conjunto de temas na p8, em `/storage/.config/emulationstation/themes/`, ao lado do NES-BOX. O NES-BOX continua sendo o tema padrão, e o usuário escolhe outro em "Configurações da interface → Tema".
- Conjunto inicial de candidatos. Cada um precisa caber no orçamento de espaço e funcionar em 640x480; os que falharem saem da lista:
  - **Gerais:** Crystal (dm2912, padrão do downloader do EmuELEC, com modo 4:3 640x480), es-theme-switch (Jetup13), Graphite-OGA (mtoensing, feito para a tela pequena do Odroid Go Advance) e minimal-EmuELEC.
  - **Infantis, 4:3:** GPi_Mario, GPi_Sonic e GPi_Crash (RetroHursty69, feitos para a tela 4:3 do GPi Case).
  - **Infantis, 16:9 (a validar em 4:3):** PokemonUno, KirbyUno e YoshiUno (RetroHursty69).
- Os temas não entram no git. O build baixa cada tema de uma URL fixada (tarball de um commit específico), confere o sha256, guarda em cache em `work/` e extrai para a camada `storage`.
- O orçamento de espaço dos temas extraídos é de **400 MiB**. Se for ultrapassado, o build falha antes de gerar a imagem.
- **No cartão:** os temas ficam na p8 e só chegam com `--wipe-storage`. Com `--keep-storage`, podem ser copiados pelo PC para `/storage/.config/emulationstation/themes/` (ext4, label `R36-STORAGE`).

## Capabilities

### New Capabilities
- `es-themes`: quais temas do EmulationStation a imagem traz, onde ficam e o tema padrão.

### Modified Capabilities
- `feature-layers`: uma feature passa a poder declarar conteúdo externo (arquivo remoto fixado por sha256) que o build baixa, extrai e aplica numa camada, como se estivesse no diretório da feature.

## Impact

- `tools/r36img/features.py` (descritor e plano) e um módulo novo de download e cache (`urllib`, `hashlib` e `tarfile` da biblioteca padrão). Testes em `tests/`.
- `./build.sh` passa a precisar de rede na primeira vez que uma feature com conteúdo externo é usada. Depois disso, o cache em `work/cache/` basta. Uma opção `--offline` usa só o cache e falha se faltar algo.
- `features/50-temas-extras/feature.toml` com as entradas fixadas (URL, sha256, destino).
- A p8 perde até 400 MiB de espaço livre. Hoje há cerca de 660 MiB livres; o change `otimizacoes-sistema` libera mais 300 MB (swapfile).
- README: seções de features e de criação de features (conteúdo externo).
- Licenças: cada tema mantém o arquivo de licença do repositório de origem, quando houver.
