# Tasks

## 1. Receita e Compilação do Core

- [ ] 1.1 Criar a receita `cores/picodrive/receita.toml` com repositório upstream fixado (`libretro/picodrive`), commit determinado, sha256 da release/tarball, argumentos de make (`platform=armv`, `use_sh2drc=1`, etc.) e variante `o2` (`picodrive_a33`) configurada com `-O2`, `-mcpu=cortex-a7`, `-mfpu=neon-vfpv4`, `-mfloat-abi=hard` e LTO.
- [ ] 1.2 Executar a compilação no container com `./cores.sh compilar picodrive o2` e verificar a geração bem-sucedida de `picodrive_a33_libretro.so`.
- [ ] 1.3 Executar a verificação de ABI com `./cores.sh abi` confirmando que os símbolos respeitam a base (`GLIBC_ <= 2.36`, ARM hard-float).
- [ ] 1.4 Criar o arquivo `picodrive_a33_libretro.info` compatível com a base.

## 2. Integração no Sistema e Documentação

- [ ] 2.1 Registrar os metadados do build em `cores/picodrive/builds.jsonl` com commit, hash sha256 e flags utilizadas.
- [ ] 2.2 Adicionar `picodrive_a33_libretro.so` e `picodrive_a33_libretro.info` na árvore da feature `features/53-cores-a33/` para distribuição em `/usr/lib/libretro`.
- [ ] 2.3 Atualizar os arquivos `es_systems.cfg` da imagem para incluir `<core>picodrive_a33</core>` na lista de emuladores de `sega32x` e `megadrive`, mantendo o core original como padrão.
- [ ] 2.4 Criar `cores/picodrive/RESULTADOS.md` com o protocolo de testes no aparelho, comparação de FPS, ocupação de CPU e dados térmicos via `r36-thermal.csv`.

## 3. Validação e Testes Automatizados

- [ ] 3.1 Executar a suíte de testes automatizados com `uv run python -I -m unittest discover -s tests` e verificar aprovação completa.
- [ ] 3.2 Validar a geração da imagem via `./build.sh` inspecionando a partição SYSTEM para confirmar a presença dos novos arquivos e a integridade das listas de sistemas.
