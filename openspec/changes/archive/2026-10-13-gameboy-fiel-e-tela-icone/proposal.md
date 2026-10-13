# Proposal

## Why

Hoje os jogos de Game Boy e Game Boy Color ocupam a tela inteira com pixels lisos e sem moldura. O usuário quer que pareça jogar no console original: jogo no maior tamanho que a tela permite, cor do LCD e a carcaça do aparelho nas laterais que hoje ficam pretas.

Além disso, a arte de fábrica do God of War ainda aparece no boot, com a lista de collections por cima. E, ao abrir um jogo, a tela de boot surge entre o ícone de carregamento e o jogo. O usuário quer uma única imagem, o ícone de controle (`3-icone-controle.png`, o mesmo da tela de carregamento atual), do boot até o jogo.

## What Changes

- **Nova feature de Game Boy fiel** (GB e GBC, core gambatte):
  - O jogo ocupa a altura toda da tela: 534x480, na proporção 10:9 do Game Boy, sem cortes nem distorção. As duas faixas laterais de 53 px, que hoje ficam pretas, recebem a moldura do console. Não há faixas em cima nem embaixo.
  - **GB:** laterais na cor da lente do DMG, com o LED vermelho e "BATTERY" à esquerda e a direita lisa, sem texto. O LCD fica na paleta verde do DMG original e um shader reproduz a grade de pixels.
  - **GBC:** laterais Atomic Purple (roxo translúcido), com o LED e "POWER" à esquerda e a direita lisa, sem texto. Usa a correção de cor do LCD do GBC e uma grade de pixels leve.
  - As molduras são geradas por um script versionado na feature, a partir de fontes registradas. Não foi encontrada moldura pronta nesse formato com licença clara.
- **Ajuste nas telas de boot (feature 30):**
  - Boot, carregamento do EmulationStation e carregamento de jogo passam a mostrar só o ícone de controle.
  - O `logo.png` do EmulationStation, que ainda era a arte de fábrica do God of War no SYSTEM e no STORAGE, é substituído pelo ícone, e o texto de progresso (a lista de collections) deixa de aparecer.
  - A tela de boot deixa de aparecer ao abrir um jogo, porque passa a ser a mesma imagem do ícone.
  - **BREAKING (visual):** a tela de boot da distribuição EmuELEC sai da imagem. O logo e a fonte dele deixam a feature, e o diretório da feature é renomeado, porque não usa mais o EmuELEC.
- **No cartão:** os overrides do RetroArch e a cópia do `logo.png` no `/storage` só chegam com `--wipe-storage`. Num cartão gravado com `--keep-storage`, o ES continua lendo a arte antiga do storage, e o GB continua sem moldura.

## Capabilities

### New Capabilities
- `gameboy-display`: como os jogos de GB e GBC são apresentados (tamanho, moldura, paleta e textura do LCD) e de onde vêm as artes.

### Modified Capabilities
- `splash-screens`: a tela de boot passa a ser o ícone de controle em vez do logo do EmuELEC. O carregamento do EmulationStation passa a ser coberto, com o ícone e sem texto de progresso. A abertura de jogo deixa de mostrar a tela de boot. A verificação da arte de fábrica passa a valer para todos os arquivos do SYSTEM e do STORAGE. A origem registrada perde o repositório do EmuELEC.

## Impact

- `features/30-splash-padrao-emuelec/` é renomeado (ver design), e o `gerar.sh`, o LEIA-ME e as camadas são refeitos. O EmuELEC sai dos créditos e licenças, e o Lucide continua.
- Nova feature em `features/` com o script de geração das molduras, a fonte tipográfica de "BATTERY" e "POWER" e as camadas `system` (PNGs das molduras e presets de shader) e `storage` (overrides do RetroArch).
- `tests/test_splash.py` passa a seguir o novo layout. Um teste novo confere as molduras: 640x480, buraco transparente na posição da tela e sha256 registrados.
- O README ganha seções das features.
- A geração das artes exige o ImageMagick 7, que já é usado pela feature 30. O build não muda e continua sem dependências Python.
- Desempenho: o shader do LCD roda numa área de 534x480 na Mali-400. A escolha entre o `gameboy.glslp` (5 passadas) e uma grade leve depende de medição no aparelho.
