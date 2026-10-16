# Proposal

## Why

A feature 52 deixou o `ppsspp.ini` global mais leve, mas ainda sobram quatro chaves de fábrica que custam desempenho no A33 sem trazer nada para quem joga. O usuário quer o máximo de desempenho no global sem quebrar o visual de nenhum jogo. Os cortes agressivos (`SkipBufferEffects` e mais pulo de quadros) ficam para um ini por jogo do GTA, depois dos testes no aparelho.

## What Changes

- A feature `52-psp-desempenho` passa a trocar mais 4 chaves no `ppsspp.ini` global (SYSTEM e STORAGE), além das 6 que já troca:
  - `TextureFiltering` de 3 (linear) para **2** (nearest), que usa menos banda da Mali-400;
  - `ReplaceTextures` de True para **False**, porque não há pacotes de textura para procurar;
  - `AchievementsEnable` de True para **False**, porque o aparelho não tem conta do RetroAchievements;
  - `EnableCheats` de True para **False**, para o PPSSPP não processar cheats.
- Ficam como estão, por decisão do usuário:
  - `CPUSpeed = 0`: o jogo escolhe a frequência, sem overclock;
  - pular quadros automático (`FrameSkip = 1`, `FrameSkipType = 1`, `AutoFrameSkip = True`);
  - `SkipBufferEffects = False`, para não quebrar efeitos.
- Os inis por jogo de fábrica continuam intactos.
- **No cartão:** como antes, a mudança só chega com `--wipe-storage`. Para usar cheats, o usuário religa a opção pelo menu do PPSSPP.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `psp-emulation`: o global ganha os requisitos de filtragem de textura nearest e de recursos extras desligados (texturas de substituição, conquistas e cheats). A comparação com a base passa a aceitar 10 chaves em vez de 6.

## Impact

- `features/52-psp-desempenho/`: as duas cópias do `ppsspp.ini` e a descrição no `feature.toml`.
- `tests/test_psp.py`: o `NOVOS` passa de 6 para 10 chaves.
- README: a seção da feature 52 lista as chaves novas e explica como religar os cheats.
- Fica para uma change futura: o ini por jogo do GTA Liberty City Stories (`ULUS10041`), com `SkipBufferEffects` e mais pulo de quadros, depois dos testes no aparelho.
