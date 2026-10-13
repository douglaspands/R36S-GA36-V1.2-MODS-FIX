# Tasks

## 1. Seleção dos temas (medição no PC)

- [x] 1.1 Para cada candidato (Crystal, es-theme-switch, Graphite-OGA, minimal-EmuELEC, GPi_Mario, GPi_Sonic, GPi_Crash, PokemonUno, KirbyUno e YoshiUno), fixar o commit atual do branch padrão, baixar o tarball do codeload para `work/cache/`, calcular o sha256 e medir o tamanho extraído (com os `exclude` previstos). Verificar que cada tema tem `theme.xml` na raiz após `strip = 1` e registrar a tabela (tema, commit, sha256, MiB) neste arquivo.
- [x] 1.2 Aplicar a ordem de prioridade do design (decisão 5) para caber em 400 MiB e definir a lista final e os nomes dos diretórios de destino. Verificar que a lista tem pelo menos 3 temas infantis e soma no máximo 400 MiB.

### Resultado da seleção (medido em 2026-10-13)

Todos têm `theme.xml` na raiz após `strip = 1`. Os repositórios reais diferem dos nomes do rascunho (prefixo `es-theme-`, e minimal-EmuELEC fica em `EmuELEC/`).

| Tema | Repositório | Commit | sha256 do tar.gz | MiB | Destino | Final |
|---|---|---|---|---|---|---|
| GPi_Mario | RetroHursty69/es-theme-GPi_Mario | d64fa52e0b5c775c0de6493ddb8dc0d41cb1e59a | b0e64a8104c09e5c48fce3368e2cc55c8b10834af896c0723f36799688139065 | 11,0 | Mario (GPi) | sim |
| GPi_Sonic | RetroHursty69/es-theme-GPi_Sonic | 8623e7ae6c92682c8ca0e312bef68e25ddfa5fe9 | df3c999122e06db14357eecf90c1ee352c91c485e3dd9c31fec1734582092ad0 | 11,0 | Sonic (GPi) | sim |
| GPi_Crash | RetroHursty69/es-theme-GPi_Crash | ee31d9c8094a556591623f96191d48ec562ee801 | b8d3d7887cbb07b922813c9f2c0f5446d39a2956bcc7c38c1099aab6882911ce | 11,0 | Crash (GPi) | sim |
| minimal-EmuELEC | EmuELEC/es-theme-minimal-EmuELEC | 628546bade3c08a3904c4105fab35c8d1ae49432 | 31ebe08db71bc1a8ab30ee387acbc01617fc2e257dedfa9095cc87c92b48724d | 13,1 | Minimal EmuELEC | sim |
| es-theme-switch | Jetup13/es-theme-switch | 2066a6e21569590fc94ab875921e575c798785fa | 7ea436d346da1a0d8f9ae3a0bffcfd20276a7906ba157219d4e8bb22c92a24c7 | 13,9 | Switch | sim |
| Graphite-OGA | mtoensing/es-theme-Graphite-OGA | 88d5c479f97f5f592d6dab861ebca23b0bbb830d | b124fbe13f091c7041ca5634943d65229c5485caa9a8f36aaf2dd5481e362e75 | 24,5 | Graphite OGA | sim |
| Crystal | dm2912/Crystal | 8f1fca3b8b673f5c8211b34329d974a727b10930 | c8275150f585afe6941b050e91de30152b9b5ede0dd475751bb38b0f33823c31 | 296,3 | Crystal | sim |
| PokemonUno | RetroHursty69/es-theme-PokemonUno | 6ec2908f74736abbffa61722c1a2004b9c83a447 | b66b550f2567354cae361ebb72d3a3a0fac59b985f6aa51fbca1017c20cc1ef9 | 39,3 | Pokemon | não (orçamento) |
| KirbyUno | RetroHursty69/es-theme-KirbyUno | d0c14f381cae6d0a82a21ebcf5ad323fd2e47719 | b62d05be48af266a64ad27bb4a4e1a9d97d57ed968f7735a48521f5533c1a485 | 39,4 | Kirby | não (orçamento) |
| YoshiUno | RetroHursty69/es-theme-YoshiUno | 45ee23211a325023687810215643da771a17b37a | e1bd1a1350997f8454343aac5ed6f69b245e11c2c21d3f691971d90eabf9360f | 39,4 | Yoshi | não (orçamento) |

Lista final: 380,8 MiB (limite 400), com 3 temas infantis. Todos os 10 somam 499 MiB, então os três 16:9 saem pela ordem de prioridade.

## 2. Conteúdo externo no build

- [x] 2.1 Em `tools/r36img/features.py`, aceitar `[[external]]` (`layer`, `dest`, `url`, `sha256`, `strip`, `exclude` opcional) e `budget_mib`, com validação de campos. Verificar com testes em `tests/test_features.py`: descritor válido, campo faltando, camada inválida e sha256 mal formado.
- [x] 2.2 Criar o módulo de cache e download (`work/cache/external/<sha256>.tar.gz`, download para temporário, conferência de sha256, rename atômico) e a opção `--offline` no `./build.sh`. Verificar com testes que usam um servidor HTTP local (`http.server` em thread): download, reuso do cache sem rede, sha256 divergente e `--offline` sem cache.
- [x] 2.3 Implementar a extração (`strip`, `exclude`, `tarfile` com `filter="data"`) para uma árvore temporária e a mesclagem no plano da camada sob `dest`, com conflitos, metadados e `changes.txt` iguais aos dos arquivos locais. Registrar URL e sha256 no manifest. Verificar com testes: tarball com `../`, link absoluto, dispositivo (todos recusados), `strip = 1`, `exclude` e conflito com outra feature.
- [x] 2.4 Implementar o orçamento (`budget_mib`): somar os bytes extraídos por feature e falhar antes de gerar a imagem se passar, listando o tamanho de cada externo. Mostrar o total no `changes.txt`. Verificar com testes de orçamento respeitado e estourado.
- [x] 2.5 Documentar `[[external]]`, `budget_mib` e `--offline` no README ("Criar uma feature") e no comentário do `features/00-exemplo/feature.toml`. Verificar que `./build.sh --help` mostra `--offline`.

## 3. Feature 50-temas-extras

- [x] 3.1 Criar `features/50-temas-extras/feature.toml` (`order = 50`, `enabled = true`, `budget_mib = 400`) com um `[[external]]` por tema da lista final. Verificar com `./build.sh --features 50-temas-extras` que o build baixa, confere e aplica todos, e que o `changes.txt` mostra os diretórios em `.config/emulationstation/themes/` e o total.
- [x] 3.2 Rodar o mesmo build com `--offline` e verificar que ele usa só o cache e gera o mesmo conteúdo na p8 (mesma listagem `debugfs`).
- [x] 3.3 Adicionar a feature ao README ("Features habilitadas"): lista de temas, como escolher no menu do ES, que exige `--wipe-storage` e como copiar os temas pelo PC num cartão com `--keep-storage`. Verificar que os comandos citados existem.

## 4. Integração

- [x] 4.1 Rodar `./build.sh` com todas as features habilitadas e verificar: nenhum conflito com as features 10 a 42; o `es_settings.cfg` continua com `ThemeSet` = `NES-BOX`; `e2fsck -fn` na p8 passa; e a p8 tem espaço livre de sobra (`debugfs -R stats`).
- [x] 4.2 Gravar num arquivo de teste com `./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage` e verificar que termina com "verificado". Rodar a suíte completa (`R36_SLOW=1 uv run python -I -m unittest discover -s tests`) e verificar que ela passa.

## Workflow follow-up

- O usuário grava o cartão com `--wipe-storage` e valida cada tema no aparelho: aparece na lista; sistemas e jogos legíveis; seleção visível. Os temas reprovados saem do `feature.toml` num ajuste deste change antes do arquivamento.
- Commit na branch `feat/temas-extras` quando o usuário pedir. Arquivar com `/opsx:archive`.
