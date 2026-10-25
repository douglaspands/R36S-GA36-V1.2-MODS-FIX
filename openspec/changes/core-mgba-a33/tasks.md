# Tasks

## 1. Receita e Compilação do Core

- [ ] 1.1 Criar a receita `cores/mgba/receita.toml` com repositório upstream, commit fixado, sha256 do arquivo fonte, variáveis de make e a variante `o2` configurada para Cortex-A7 (`-O2`, `-mcpu=cortex-a7`, `-mfpu=neon-vfpv4`, `-mfloat-abi=hard`, `-flto`).
- [ ] 1.2 Executar a compilação da variante com `./cores.sh compilar mgba o2` e verificar a geração bem-sucedida de `mgba_a33_libretro.so`.
- [ ] 1.3 Executar a verificação de ABI com `./cores.sh abi` e confirmar que todos os símbolos respeitam a base (`GLIBC_ <= 2.36`, `libstdc++ <= 6.0.29`, ARM hard-float).
- [ ] 1.4 Criar o arquivo `mgba_a33_libretro.info` adaptado do `.info` da base, preservando a compatibilidade de saves e opções.

## 2. Integração no Sistema e Documentação

- [ ] 2.1 Registrar os metadados do build em `cores/mgba/builds.jsonl` com data, commit, hash sha256 e flags utilizadas.
- [ ] 2.2 Adicionar os arquivos `mgba_a33_libretro.so` e `mgba_a33_libretro.info` à feature do sistema correspondente em `features/` para inclusão em `/usr/lib/libretro`.
- [ ] 2.3 Atualizar a lista de cores do sistema GBA no `es_systems.cfg` da imagem para incluir `mgba_a33`, mantendo `gpsp` como padrão.
- [ ] 2.4 Criar `cores/mgba/RESULTADOS.md` com os parâmetros do build e as instruções para o teste de fumaça no console físico.

## 3. Validação e Testes Automatizados

- [ ] 3.1 Executar a suíte de testes com `uv run python -I -m unittest discover -s tests` e verificar aprovação completa.
- [ ] 3.2 Executar a geração da imagem via `./build.sh` e inspecionar a partição SYSTEM para garantir a presença dos binários e a integridade do `es_systems.cfg`.
