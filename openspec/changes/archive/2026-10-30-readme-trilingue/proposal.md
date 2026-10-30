# Proposal

## Why

O `README.md` atual é um manual de desenvolvedor de 1094 linhas, só em português, e diz
"criança de 7 anos". Quem chega ao repositório não encontra a história do projeto (um
aparelho para o filho de 6 anos do mantenedor), de onde vem a imagem, o que é o clone
nem o que foi corrigido. Falta também uma apresentação nos três idiomas que o tema
`Epic Cody ML` já oferece (`pt-br`, `es-latam`, `en`).

## What Changes

- Três READMEs de apresentação, um por idioma, com seletor de idioma no topo:
  `README.md` (inglês, padrão no GitHub), `README.pt-BR.md` e `README.es.md`.
- Cada um traz: motivação (filho de 6 anos), origem da imagem base, o que é o clone e
  como difere do R36S original, especificações de hardware, features e correções de
  bugs, atalhos, melhorias com imagens e a seção do desenvolvedor no fim.
- O manual técnico atual passa para `docs/DESENVOLVIMENTO.md`, com o conteúdo
  preservado (só os links relativos e a menção "7 anos" mudam), e cada README linka
  para ele.
- Imagens versionadas em `docs/img/`: a foto do R36S enviada pelo usuário e cópias
  selecionadas de `var/` (telas do tema e comparativos de shader).
- Desenvolvedor: Douglas Panhota, `douglaspands@gmail.com` (do `git config`).

## Capabilities

### New Capabilities

Nenhuma. É mudança só de documentação, sem comportamento novo (`skip_specs: true`).

### Modified Capabilities

Nenhuma.

## Impact

- Arquivos: `README.md` (reescrito), `README.pt-BR.md` e `README.es.md` (novos),
  `docs/DESENVOLVIMENTO.md` (movido do README atual), `docs/img/*` (novas).
- Referências ao README: conferir `CLAUDE.md`, `tests/` e `openspec/` por menções a
  seções do `README.md` que passam a viver em `docs/DESENVOLVIMENTO.md`.
- Nenhum efeito no build, na imagem ou no aparelho.
