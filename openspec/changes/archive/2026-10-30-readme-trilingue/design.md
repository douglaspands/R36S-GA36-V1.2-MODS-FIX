# Design

## Context

Veja a motivação em `proposal.md`. O `README.md` atual é o único documento de uso do
repositório e `CLAUDE.md` e testes podem citar suas seções. Fatos de hardware
confirmados: Allwinner A33 (4x Cortex-A7) remarcado como RK3326, 1 GB de RAM, Mali-400
MP2, tela de 3,5" a 640x480, EmuELEC 4.7 de fábrica (kernel 3.4.39), sem rede. A
capacidade nominal da bateria é desconhecida; só existe a descarga medida em 26/10
(264 min, 2640 mAh). O repositório não tem remote git.

## Goals / Non-Goals

**Goals:**
- Um texto curto, caloroso e fiel, nos três idiomas do tema, com o mesmo conteúdo.
- Preservar todo o manual técnico atual sem perda.

**Non-Goals:**
- Reescrever ou reorganizar o manual técnico.
- Mudar features, build ou imagem.
- Traduzir o manual técnico (fica em português).

## Decisions

1. **Um arquivo por idioma.** `README.md` em inglês (idioma padrão do GitHub e do
   `./build.sh`), mais `README.pt-BR.md` e `README.es.md`, ligados por uma linha de
   seletor no topo. Alternativa descartada: um arquivo com 3 seções em `<details>`,
   pesado e difícil de manter.
2. **Manual em `docs/DESENVOLVIMENTO.md`**, via cópia do `README.md` atual antes de
   reescrevê-lo, para não perder histórico. O título e a frase "7 anos" são ajustados
   (6 anos); os links relativos que passam a quebrar são corrigidos.
3. **Estrutura idêntica nos três**: motivação; foto e visão do aparelho; origem da
   imagem; o clone e hardware; features e bugs corrigidos; atalhos; melhorias com
   imagens; como gravar (resumo, link para o manual); desenvolvedor, créditos e
   licença/aviso. Espanhol em es-latam, como o tema.
4. **Hardware só com fatos verificados.** Bateria: sem capacidade nominal, cita só a
   medição de 26/10. Nada de especificação inventada para o clone (nem modelo de tela).
   O que o `CLAUDE.md` não cobre vira "não verificado" ou fica de fora.
5. **Atalhos** vêm da tabela do `20-controle-posicional`, do `62-brilho-fn` e do
   ClassiCube, sem inventar nada.
6. **Imagens em `docs/img/`**, com nomes ASCII e sem espaço. Escolhas de `var/`: 4 a 6
   telas do tema (`auto-allgames`, `gba`, `snes`, `megadrive`, `psx`, `retroarch`), 1
   comparativo de shader do GBA (`mario-kart_comparacao-1-2-3-4`), 1 do GB/GBC e 1 de
   TV. Foto do aparelho: a enviada pelo usuário, salva como `docs/img/r36s.jpg`. A
   autoria dela é desconhecida; o usuário confirmou que é só uma imagem ilustrativa,
   e os READMEs a legendam assim, sem crédito de autor.
7. **Desenvolvedor:** nome e e-mail do `git config`. Sem URL de GitHub (não há remote);
   o usuário pode acrescentar depois.
8. **Licença:** sem arquivo `LICENSE` por ora; os READMEs não afirmam licença. Os
   créditos citam EmuELEC, o tema Epic Cody, Libretro/RetroArch e ClassiCube, sem
   prometer termos de uso.
9. **Idade:** 6 anos nos três. Corrigir também o `CLAUDE.md` (que diz 7 anos no
   "Para quem é" copiado do README, se houver) é tarefa explícita.

## Risks / Trade-offs

- [Três textos fora de sincronia] → mesma estrutura e mesma lista de seções; tarefa de
  revisão cruzada no fim.
- [Links quebrados após mover o manual] → tarefa que procura referências a seções do
  README e confere os links relativos.
- [Foto de terceiros] → legenda "imagem ilustrativa" (confirmado pelo usuário).
- [Peso das imagens no git] → só PNG/JPG já existentes, poucas, redimensionadas se
  passarem de ~500 KB.
