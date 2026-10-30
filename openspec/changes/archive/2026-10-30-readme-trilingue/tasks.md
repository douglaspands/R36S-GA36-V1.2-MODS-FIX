# Tasks

## 1. Manual técnico e imagens

- [x] 1.1 Copiar o `README.md` atual para `docs/DESENVOLVIMENTO.md`, trocar "7 anos" por "6 anos" e corrigir links relativos; verificar que o arquivo mantém todas as seções do original (mesma contagem de títulos `##`).
- [x] 1.2 Salvar a foto do R36S enviada pelo usuário como `docs/img/r36s.jpg` e copiar de `var/` as telas do tema e os comparativos de shader escolhidos (design, decisão 6) com nomes ASCII em `docs/img/`; verificar que os arquivos existem, abrem e cada um tem menos de ~500 KB (senão redimensionar).

## 2. READMEs de apresentação

- [x] 2.1 Escrever `README.md` em inglês com a estrutura da decisão 3, imagens de `docs/img/`, tabela de atalhos, seletor de idioma e seção do desenvolvedor (Douglas Panhota, `douglaspands@gmail.com`); verificar que todo link e imagem aponta para arquivo existente.
- [x] 2.2 Escrever `README.pt-BR.md` com o mesmo conteúdo e a mesma ordem de seções; verificar que tem as mesmas seções do inglês.
- [x] 2.3 Escrever `README.es.md` em espanhol latino com o mesmo conteúdo e ordem; verificar que tem as mesmas seções do inglês.
- [x] 2.4 Conferir os fatos contra o `CLAUDE.md` e as features (hardware, 264 min e 2640 mAh, atalhos do FN, brilho, ClassiCube); verificar que nenhuma especificação inventada aparece e que a bateria nominal não é afirmada.

## 3. Referências e integração

- [x] 3.1 Buscar menções ao `README.md` em `CLAUDE.md`, `tests/`, `openspec/` e `tools/` que dependam de seções movidas e ajustá-las; verificar com `uv run python -I -m unittest discover -s tests`.
- [x] 3.2 Atualizar no `CLAUDE.md` a menção a "7 anos", se existir, e registrar a nova estrutura de READMEs e a pasta `docs/`; verificar relendo o arquivo.
- [x] 3.3 Revisão cruzada final dos três READMEs (seções, links, imagens, idade 6) e da legenda "imagem ilustrativa" na foto do aparelho nos três idiomas.

## Workflow follow-up

- Branch própria `readme-trilingue` criada a partir da `main` no início do `/opsx-apply`.
- Merge e push só a pedido.
