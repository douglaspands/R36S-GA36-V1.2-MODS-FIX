# Design

## Context

- O PSP abre no PPSSPP standalone (`PPSSPPSDL`, padrão no `es_systems.cfg`) pelo `ppsspp.sh`, que roda `PPSSPPSDL --fullscreen`. O backend é OpenGL.
- O `emuelecRunEmu.sh` chama `maxperf` em todo jogo: governor `performance` e DRAM na frequência máxima (`dsm/scene = 0`). Desse lado não há nada a ganhar.
- O `ppsspp.ini` global existe em `/usr/config/ppsspp/PSP/SYSTEM/` (SYSTEM) e em `/storage/.config/ppsspp/PSP/SYSTEM/` (p8). As duas cópias da base são idênticas. O PPSSPP lê e regrava a do storage.
- Há 9 inis por jogo de fábrica (God of War, Ridge Racer e outros) com valores próprios. No PPSSPP, um ini por jogo substitui as configurações por jogo do global.
- Padrão do projeto: uma feature que muda um arquivo de configuração leva a cópia inteira do arquivo (como o `retroarch.cfg` da feature 10), e um teste garante que só as linhas pretendidas diferem da base.

## Goals / Non-Goals

**Goals:**
- O máximo de ganho com o mínimo de risco visual, valendo para qualquer jogo.

**Non-Goals:**
- Inis por jogo para GTA e PES. Ficam para uma change futura, quando os IDs forem conhecidos.
- Mudar os inis por jogo de fábrica.
- Overclock do A33 pelo `script.bin`.
- Trocar o PPSSPP pelo core libretro.
- Ligar `SkipBufferEffects` no global, porque quebra efeitos em vários jogos. Pode entrar por jogo depois.

## Decisions

1. **Cópia integral do ini de fábrica com 6 chaves trocadas.** A mesma cópia vai para as duas camadas: a do SYSTEM serve ao reset de fábrica do storage, e a do STORAGE é a que o PPSSPP lê.
   - Descartado: um script de boot que edita o ini no `/storage`. Seria mais frágil e brigaria com o PPSSPP, que regrava o arquivo ao sair.

2. **Escolha das chaves, por custo e benefício na Mali-400 MP2:**

   | Chave | Fábrica | Novo | Motivo |
   |---|---|---|---|
   | `InternalResolution` | 2 | 1 | 4x menos pixels. É o maior ganho |
   | `CPUSpeed` | 666 | 0 | sem overclock, o jogo não gera trabalho extra no host |
   | `NumWorkerThreads` | 8 | 4 | menos disputa entre threads em 4 núcleos |
   | `SkipGPUReadbackMode` | 0 | 1 | evita esperas de sincronização com a GPU |
   | `SplineBezierQuality` | 1 | 0 | menos vértices nos jogos que usam curvas |
   | `ShowFPSCounter` | 2 | 0 | sem desenho extra. Pode ser religado pelo menu |

   O pular quadros automático com `FrameSkip = 1` já vem de fábrica e é o comportamento desejado para GTA e PES. Fica como está.

3. **Teste de diferença contra a base.** O teste lê o `ppsspp.ini` da base (no squashfs extraído pelo fixture existente) e o da feature. Ele exige que as únicas linhas diferentes sejam as 6 chaves, com os valores novos, e que as duas camadas tenham o mesmo conteúdo. No teste de integração, confere que os `*_ppsspp.ini` saem iguais aos da base.

## Risks / Trade-offs

- [`SkipGPUReadbackMode = 1` quebra algum efeito que dependa de leitura da GPU, como sombras ou miniaturas de save] → é um valor comum em aparelhos fracos. Se um jogo quebrar, um ini por jogo devolve o valor 0, sem mexer no global.
- [Um jogo depende do overclock para não ficar lento, como o God of War de fábrica com 666] → esses jogos já têm ini próprio e mantêm seus valores.
- [Os inis por jogo de fábrica com `InternalResolution = 2`] → ficam como estão, por escolha de escopo. Um ajuste por jogo futuro pode revisá-los.
- [`--keep-storage` não leva a mudança] → documentado no README. O usuário pode ajustar pelo menu do PPSSPP ou copiar o arquivo pelo PC (`R36-STORAGE`).
