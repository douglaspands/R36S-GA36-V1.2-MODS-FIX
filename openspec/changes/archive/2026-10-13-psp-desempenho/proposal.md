# Proposal

## Why

O `ppsspp.ini` global de fábrica é pesado demais para o A33 (4x Cortex-A7, Mali-400 MP2):
- renderiza em 2x (960x544) para depois reduzir para a tela de 640x480;
- emula a CPU do PSP a 666 MHz;
- usa 8 threads de trabalho em 4 núcleos.

O usuário quer o máximo de desempenho no PSP para jogar GTA e PES, sem saber ainda quais versões. Por isso esta change ajusta só a configuração global, de forma razoável para todos os jogos.

## What Changes

- Nova feature `52-psp-desempenho`, que troca o `ppsspp.ini` global (SYSTEM e STORAGE) por uma cópia do de fábrica com estas chaves alteradas:
  - `InternalResolution` de 2 para **1** (resolução nativa do PSP, 480x272);
  - `CPUSpeed` de 666 para **0** (o jogo escolhe a frequência, como no PSP real);
  - `NumWorkerThreads` de 8 para **4** (um por núcleo);
  - `SkipGPUReadbackMode` de 0 para **1** (pula as leituras de volta da GPU, caras na Mali-400);
  - `SplineBezierQuality` de 1 para **0** (curvas em qualidade baixa);
  - `ShowFPSCounter` de 2 para **0** (sem contador na tela).
- Ficam como estão, por já favorecerem o desempenho:
  - pular quadros automático (`AutoFrameSkip = True`, `FrameSkip = 1`);
  - transformação por hardware e skinning por software;
  - sem escala de textura, sem anisotropia e sem MSAA;
  - backend OpenGL e `InflightFrames = 3`;
  - `SkipBufferEffects = False`, para não quebrar o visual de nenhum jogo.
- Os inis por jogo que vêm de fábrica (God of War, Ridge Racer e outros) ficam intactos, e seus valores continuam valendo sobre o global.
- **No cartão:** o PPSSPP lê a cópia do `/storage`, então a mudança só chega com `--wipe-storage`.

## Capabilities

### New Capabilities
- `psp-emulation`: configuração padrão do emulador de PSP (PPSSPP standalone) na imagem gerada, voltada para desempenho no A33.

### Modified Capabilities
<!-- nenhuma -->

## Impact

- Novo diretório `features/52-psp-desempenho/` com `system/usr/config/ppsspp/PSP/SYSTEM/ppsspp.ini` e `storage/.config/ppsspp/PSP/SYSTEM/ppsspp.ini`.
- Novo teste em `tests/` que compara os dois arquivos com os da base e só aceita as diferenças listadas.
- O README ganha a seção da feature.
- Fica para uma change futura: configurações por jogo para GTA e PES, quando as versões (IDs) forem conhecidas.
