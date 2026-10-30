# Tasks

## 1. Ferramenta de Extração e Refatoração do Tema

- [x] 1.1 Criar script em Python (`tools/refatora_epic_cody_ml.py`) para ler o tarball do tema upstream, extrair os textos de todos os consoles/coleções e gerar `_languages/en.xml`.
- [x] 1.2 Implementar a substituição dos nós de texto nos arquivos `theme.xml` de cada console por referências às variáveis `${sistema.*}`.

## 2. Catálogos de Tradução e Calibração Visual

- [x] 2.1 Criar o catálogo `_languages/pt-br.xml` com traduções completas, preservando nomenclaturas técnicas (*16-bit*, *Arcade*, *RPGs*, etc.) e respeitando limites de tamanho para 640x480.
- [x] 2.2 Criar o catálogo `_languages/es-latam.xml` com traduções completas para espanhol latino.
- [x] 2.3 Atualizar o `theme.xml` principal adicionando o `<subset name="language">` com `pt-br` como padrão.

## 3. Integração na Imagem e Verificação

- [x] 3.1 Atualizar `features/50-temas-extras/feature.toml` para instalar `Epic Cody ML` em vez de `Epic Cody` (removendo o original para economizar ~180 MiB na partição storage) e atualizar `features/10-ptbr-sao-paulo` definindo `Epic Cody ML` como padrão em `es_settings.cfg`.
- [x] 3.2 Executar `./build.sh --test` e verificar integridade da partição `storage`, ausência de symlinks e respeito ao orçamento de tamanho.
- [x] 3.3 Adicionar teste automatizado em `tests/` validando sintaxe XML, integridade dos 3 catálogos de idioma e referências de variáveis.
