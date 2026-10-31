# Proposal

## Why

Todos os argumentos de linha de comando aceitos pelo `./build.sh` (`--size-mib`, `--features`, `--no-features`, `--offline`, `--fast`, `--test`, `--timestamp`, `--help`) estão em inglês, exceto `--idioma`. Padronizar a interface CLI com `--lang` torna as opções consistentes entre si e segue as convenções usuais de ferramentas de linha de comando.

Além disso, a documentação técnica detalhada (`docs/DESENVOLVIMENTO.md`) existe atualmente apenas em português, limitando o alcance internacional do projeto. Expandir os manuais para inglês e espanhol, incluir a captura de tela do console LÖVE no tema oficial nos READMEs e registrar detalhadamente e de forma amigável a motivação da escolha do LÖVE (em contraste com as limitações de portabilidade do PICO-8 fechado nas múltiplas variantes do R36S) fortalece a usabilidade e a divulgação global do projeto.

## What Changes

- **CLI do Build**:
  - Substituição/padronização da opção `--idioma` por `--lang` no parser de argumentos do build (`tools/r36img/build.py`).
  - Suporte a `--idioma` como alias retrocompatível de `--lang` (suprimido na ajuda para manter saída limpa).
  - Atualização do `--help` e mensagens de erro do `./build.sh` para indicar `--lang`.
  - Atualização da função `build` e suíte de testes (`test_cli.py`, `test_image.py`, `test_idioma_build.py`).
- **Documentação, Motivação do LÖVE e Ilustrações**:
  - Inclusão da motivação acolhedora e detalhada da escolha do LÖVE em relação ao PICO-8 (amor pelo espírito indie e retro, mas necessidade de uma plataforma 100% aberta, compilável nativamente com aceleração Mali-400 e funcional em todas as variantes de hardware do R36S, aproveitando os 640x480 nativos).
  - Geração de print oficial do console LÖVE no tema Epic Cody ML (`docs/img/tema-love.png`) e inserção no tópico dedicado a LÖVE nos três READMEs (`README.md`, `README.pt-BR.md`, `README.es.md`).
  - Criação dos manuais de desenvolvimento em inglês (`docs/DEVELOPMENT.md`) e espanhol (`docs/DESARROLLO.md`), além da atualização do manual em português (`docs/DESENVOLVIMENTO.md`).
  - Atualização dos links e referências do manual técnico em cada README correspondente ao respectivo idioma (`README.md` -> `docs/DEVELOPMENT.md`, `README.es.md` -> `docs/DESARROLLO.md`, `README.pt-BR.md` -> `docs/DESENVOLVIMENTO.md`).
  - Atualização das instruções de build e diretrizes em `CLAUDE.md` e `GEMINI.md` para `./build.sh --lang pt_BR`.

## Capabilities

### New Capabilities
<!-- Nenhuma nova capability introduzida -->

### Modified Capabilities
- `build-language`: Atualiza o requisito do argumento de linha de comando para `--lang <código>` (mantendo `--idioma` como alias retrocompatível).
- `image-build`: Atualiza os cenários e requisitos de identificação de saída para referenciar a opção `--lang` na geração da imagem.

## Impact

- CLI do build: `./build.sh --lang pt_BR` passa a ser a invocação padrão em documentações e scripts.
- Testes automatizados: `test_cli.py`, `test_image.py` e `test_idioma_build.py`.
- Documentação internacional do projeto: manuais completos em três idiomas (`docs/DEVELOPMENT.md`, `docs/DESARROLLO.md`, `docs/DESENVOLVIMENTO.md`) e links contextualizados nos READMEs.
- Assets visuais e clareza da plataforma: nova imagem `docs/img/tema-love.png` e fundamentação amigável do LÖVE vs. PICO-8.
- Zero impacto no runtime do console R36S ou nas partições físicas geradas.
