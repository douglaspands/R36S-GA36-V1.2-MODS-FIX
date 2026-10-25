# Tasks

## 1. Lançador com escolha do binário e log

- [ ] 1.1 Criar a branch `classicube-binario-na-rom` a partir da `main` (regra do projeto) e conferir com `git branch --show-current`.
- [ ] 1.2 No `ClassiCube.sh`, introduzir os ganchos `R36_ROOT` (prefixo de `PORT_DIR`, `SHARE_DIR` e `DB_FILE`) e `R36_TMP` (padrão `/tmp`) sem mudar o comportamento, e verificar com `bash -n` e com `uv run python -I -m unittest discover -s tests -p "test_port_classicube.py"` que os testes existentes (incluindo `test_launcher_script` e os de sensibilidade) continuam passando.
- [ ] 1.3 Implementar a ordem de tentativa (design, decisão 3 e 4): `ClassiCube-pc` direto da p1; em 126/127, cópia para `$R36_TMP/ClassiCube-pc` com `chmod 0755`, execução e `rm -f`; em 126/127 de novo ou sem `ClassiCube-pc`, binário do SYSTEM. Cobrir em `tests/test_port_classicube.py` com um `R36_ROOT` temporário e binários de teste em shell: sem `ClassiCube-pc` roda o do SYSTEM; `ClassiCube-pc` executável roda direto; `ClassiCube-pc` sem bit de execução roda pela cópia em `R36_TMP`; `ClassiCube-pc` que também não executa da cópia (`R36_TMP` inexistente) cai no SYSTEM; `ClassiCube-pc` que sai com código 3 não dispara segunda abertura. Verificar que os testes novos passam.
- [ ] 1.4 Implementar o `log.txt` (design, decisão 5): caminho usado, código de saída de cada tentativa, linhas de montagem de `/storage/roms` e `/tmp` (ou "não é ponto de montagem"), sha256 do SYSTEM e do `ClassiCube-pc` (ou "indisponível" sem `sha256sum`), regravado inteiro antes e depois de cada tentativa, com falha de escrita ignorada. Cobrir em `tests/test_port_classicube.py`: log com os dois sha256 quando o `ClassiCube-pc` difere do SYSTEM, só o registro da última abertura após duas execuções, e jogo aberto mesmo com `log.txt` não gravável (diretório somente leitura). Verificar que os testes passam.
- [ ] 1.5 Copiar o `ClassiCube.sh` para `features/60-port-classicube/system/usr/share/classicube/ports_scripts/ClassiCube.sh`, verificar `bash -n` e `cmp` entre as duas cópias (coberto por `test_system_ports_mirror_and_sync`).
- [ ] 1.6 Atualizar a verificação de estrutura em `tests/test_port_classicube.py` para exigir que a imagem não leve `roms/ports/classicube/ClassiCube` nem `ClassiCube-pc`, e verificar que o teste passa.

## 2. Documentação

- [ ] 2.1 Atualizar o item `60-port-classicube` do `README.md` com o `ClassiCube-pc`: como copiar pelo PC, a ordem de tentativa, o `log.txt`, o aviso de apagar o `ClassiCube-pc` ao regravar o SYSTEM e a necessidade de `--part system` uma vez para levar o lançador novo; verificar que o texto bate com o spec desta change.

## 3. Fechamento

- [ ] 3.1 Rodar `uv run python -I -m unittest discover -s tests` completo e verificar que não há falhas novas.
- [ ] 3.2 Rodar `openspec validate classicube-binario-na-rom --strict` e verificar que passa.
- [ ] 3.3 Gerar o cartão de teste com `./build.sh --test --offline` (sem sudo), gravá-lo num arquivo temporário com `./flash.sh --target-file` e verificar, extraindo da `system.img` (`mcopy` e `unsquashfs`) e da `roms.img` (`mdir`), que o SYSTEM leva o lançador novo igual ao da p1 e que a p1 não leva `ClassiCube` nem `ClassiCube-pc`.

## Workflow follow-up

- O usuário grava o SYSTEM (`./flash.sh --device /dev/sdX --part system`), copia um binário para `R36-ROMS/ports/classicube/ClassiCube-pc`, abre o jogo e lê o `log.txt` no PC.
- Registrar no `CLAUDE.md`, na seção "O aparelho", o fato medido de a FAT32 de `/storage/roms` executar ou não direto (e as opções de montagem), e decidir a simplificação da Open Question do design.
- Arquivar a change depois de revisada.
