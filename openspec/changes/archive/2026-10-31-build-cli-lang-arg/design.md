# Design

## Context

Atualmente, `tools/r36img/build.py` expõe argumentos de linha de comando no `./build.sh` que seguem nomes em inglês (`--size-mib`, `--features`, `--no-features`, `--offline`, `--fast`, `--test`, `--timestamp`, `--help`), com exceção de `--idioma`.

A especificação `build-language` e os testes associados (`test_cli.py`, `test_image.py`, `test_idioma_build.py`) foram desenvolvidos em torno da flag `--idioma`.

Na frente de documentação, os três READMEs (`README.md`, `README.pt-BR.md`, `README.es.md`) apresentam o projeto com uma estrutura espelhada em inglês, português e espanhol, mas todos apontam para um único manual técnico em português (`docs/DESENVOLVIMENTO.md`). Além disso, o novo suporte ao console LÖVE (Love2D) integrado ao tema oficial Epic Cody ML ainda não possui uma captura de tela ilustrativa em sua seção dedicada nos READMEs nem explica a motivação de sua escolha frente a outras soluções retro indie populares como PICO-8.

Veja `proposal.md` para a motivação da mudança.

## Goals / Non-Goals

**Goals:**
- Renomear o argumento principal de linha de comando de `--idioma` para `--lang` em `tools/r36img/build.py`.
- Manter `--idioma` como alias aceito (retrocompatibilidade não intrusiva com `help=argparse.SUPPRESS`).
- Atualizar a saída de ajuda (`./build.sh --help`) e mensagens de validação de erro para indicar `--lang`.
- Gerar a captura de tela de alta fidelidade `docs/img/tema-love.png` representando o console LÖVE no tema Epic Cody ML.
- Explicar de forma calorosa, amigável e detalhada a motivação da escolha do LÖVE 11.5 em detrimento do PICO-8 nos três READMEs (apreço pela proposta de "fantasy console" e jogos indie, contrastado com as restrições de código proprietário do PICO-8 e problemas de seus emuladores em diversas variantes do R36S; enquanto LÖVE oferece código aberto compilável nativamente com aceleração Mali-400 GLES2, 640x480 total, áudio estéreo límpido e portabilidade absoluta entre variantes).
- Inserir a imagem `docs/img/tema-love.png` no tópico LÖVE dos 3 READMEs (`README.md`, `README.pt-BR.md`, `README.es.md`).
- Criar as versões localizadas do manual de desenvolvimento:
  - `docs/DEVELOPMENT.md` (inglês)
  - `docs/DESARROLLO.md` (espanhol)
  - `docs/DESENVOLVIMENTO.md` (português)
- Atualizar a referência ao manual técnico em cada README para apontar para o documento no respectivo idioma.
- Atualizar e expandir a suíte de testes unitários para cobrir `--lang` como flag primária e `--idioma` como alias retrocompatível.

**Non-Goals:**
- Não alterar a nomenclatura interna dos arquivos gerados (o padrão `<prefixo>_<idioma>_build_<timestamp>.img.xz` permanece usando o código de idioma como `pt-br` ou `en-us`).
- Não alterar o campo `"language"` no `manifest.json` (que já está em inglês).
- Não alterar os scripts de runtime que rodam no console físico (`idioma-aplica`, `r36-idioma`, etc.).

## Decisions

### Decisão 1: Parser de CLI (`argparse`) com `--lang` principal e alias `--idioma`
- **Escolha**: Definir `--lang` como o argumento oficial documentado no `_build_parser()`, configurando `dest="lang"`. Adicionar `--idioma` mapeado para o mesmo destino (`dest="lang"`) com `help=argparse.SUPPRESS` para manter a saída de `--help` 100% padronizada em inglês.
- **Alternativas consideradas**:
  - *Remoção estrita de `--idioma`*: Causaria erro imediato em qualquer execução que ainda use `--idioma`.
  - *Apenas renomear sem alias*: Quebraria compatibilidade sem benefício prático.

### Decisão 2: Parâmetros da API interna `r36img.build.build(...)`
- **Escolha**: Aceitar `lang=None` e `lang_opcional=False` como parâmetros principais na função `build(...)`, aceitando também `idioma=None` como fallback retrocompatível (`lang = lang or idioma`) caso chamadores usem keyword argument `idioma`.

### Decisão 3: Geração de captura de tela de LÖVE (`docs/img/tema-love.png`)
- **Escolha**: Utilizar o script gerador de capturas de tela `tools/gera_prints_interface.py` estendido com o mockup do carrossel/gamelist do console `love2d` utilizando os assets oficiais do tema (`features/50-temas-extras/.../love2d/poster.png` e logo). Salvar o resultado diretamente em `docs/img/tema-love.png`.

### Decisão 4: Estrutura dos Manuais de Desenvolvimento por Idioma
- **Escolha**:
  - Manter `docs/DESENVOLVIMENTO.md` em português (atualizando para `./build.sh --lang`).
  - Criar `docs/DEVELOPMENT.md` em inglês completo, com referências a `./build.sh --lang`.
  - Criar `docs/DESARROLLO.md` em espanhol completo, com referências a `./build.sh --lang`.
  - Incluir cabeçalho de navegação entre idiomas no topo de cada manual:
    - Em `docs/DEVELOPMENT.md`: `Available in: English | [Português](DESENVOLVIMENTO.md) | [Español](DESARROLLO.md)`
    - Em `docs/DESENVOLVIMENTO.md`: `Disponível em: [English](DEVELOPMENT.md) | Português | [Español](DESARROLLO.md)`
    - Em `docs/DESARROLLO.md`: `Disponible en: [English](DEVELOPMENT.md) | [Português](DESENVOLVIMENTO.md) | Español`
  - Em cada README raiz, direcionar o link para o documento do respectivo idioma:
    - `README.md` aponta para `docs/DEVELOPMENT.md`.
    - `README.pt-BR.md` aponta para `docs/DESENVOLVIMENTO.md`.
    - `README.es.md` aponta para `docs/DESARROLLO.md`.

### Decisão 5: Seção de Motivação do LÖVE vs. PICO-8 nos READMEs
- **Escolha**: Adicionar uma subseção dedicada nos três READMEs explicando a motivação de forma simpática, técnica e inclusiva:
  - Celebrar o conceito e estética dos jogos tipo PICO-8.
  - Explicar o obstáculo das licenças proprietárias do PICO-8 oficial e a incompatibilidade/instabilidade de seus clones em SoCs distintos como o Cortex-A7 A33.
  - Destacar que o LÖVE 11.5 une o prazer de criar jogos em Lua com a liberdade do código aberto, resolução 640x480, som de alta qualidade e execução 100% garantida em qualquer modelo de R36S.

## Risks / Trade-offs

- **[Risco]** Manutenção de três manuais técnicos longos em paralelo.
  → **Mitigação**: Os manuais compartilham exatamente as mesmas seções, tabelas de comandos e estrutura de build, permitindo sincronização sistemática.
- **[Risco]** Scripts externos chamando `--idioma`.
  → **Mitigação**: O alias `--idioma` permanece ativo no parser sem quebrar execuções legadas.
