# Design

## Context

- A feature `52-psp-desempenho` já leva o `ppsspp.ini` global inteiro nas duas camadas (SYSTEM e STORAGE). O teste `tests/test_psp.py` compara as duas cópias com o ini da base e só aceita as chaves do dicionário `NOVOS`.
- As 4 chaves novas aparecem uma única vez no ini (`EnableCheats` em `[General]`, `TextureFiltering` e `ReplaceTextures` em `[Graphics]`, `AchievementsEnable` em `[Achievements]`). Por isso o teste de valores, que exige uma ocorrência por chave, continua valendo sem ajuste.

## Goals / Non-Goals

**Goals:**
- Somar as 4 chaves ao global com o menor diff possível.

**Non-Goals:**
- Mudar `FrameSkipType`. Ele não traz ganho de desempenho com `FrameSkip = 1`, e a semântica do modo percentual não foi confirmada.
- O ini por jogo do GTA (`ULUS10041`).
- Mexer nos inis por jogo de fábrica.

## Decisions

1. **Alterar a própria feature 52 em vez de criar uma feature nova.** O carregador acusa conflito quando duas features gravam o mesmo caminho, e uma feature 54 teria que levar o mesmo `ppsspp.ini` inteiro. Com uma feature só, o arquivo continua tendo um dono e um teste.
   - Descartado: uma feature 54 que substitui a 52. Duplicaria o arquivo e deixaria a 52 sem efeito.

2. **Valores escolhidos:**

   | Chave | Fábrica | Novo | Motivo |
   |---|---|---|---|
   | `TextureFiltering` | 3 | 2 | nearest gasta menos banda na Mali-400. Com resolução 1x numa tela de 3,5", a diferença visual é pequena |
   | `ReplaceTextures` | True | False | não há pacotes de textura na imagem |
   | `AchievementsEnable` | True | False | sem conta, só faria trabalho em vão. Também evita que o `ChallengeMode` bloqueie savestates se alguém logar |
   | `EnableCheats` | True | False | o PPSSPP deixa de processar cheats a cada ciclo de atualização |

3. **O teste muda só no dicionário `NOVOS`**, que passa de 6 para 10 entradas. A lógica de comparação com a base continua a mesma.

## Risks / Trade-offs

- [Nearest deixa as texturas mais serrilhadas em alguns jogos] → é reversível pelo menu do PPSSPP (Gráficos > Filtragem de textura), sem regravar o cartão.
- [Quem usa cheats estranha que eles não funcionam] → o README explica como religar pelo menu.
- [O ganho de cada chave é pequeno e não foi medido] → as chaves foram escolhidas por não terem custo visual relevante. A medição acontece nos testes do GTA, na próxima change.
- [`--keep-storage` não leva a mudança] → igual à feature 52, já documentado no README.
