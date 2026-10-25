# Proposal

## Why

Hoje o ClassiCube só roda o binário que vem no SYSTEM (`/usr/share/classicube/ClassiCube`). Trocar o binário exige gerar a imagem e regravar a p7 com `./flash.sh` (sudo e `--part system`). Isso atrapalha a calibração dos analógicos, que depende de várias rodadas de "mexer no valor, recompilar, testar no aparelho". A p1 (`R36-ROMS`, FAT32) é gravável pelo PC sem root, então deixar o lançador aceitar um binário colocado ali encurta o ciclo.

O spec atual proíbe binário na p1 porque "a FAT32 não guarda permissão de execução". Isso nunca foi medido neste aparelho: o Linux inventa as permissões da FAT pelas opções de montagem (`fmask`/`umask`, `noexec`), e a montagem de `/storage/roms` não está documentada no projeto. O binário pode rodar direto da p1, ou só depois de copiado para a RAM (`/tmp`).

## What Changes

- O `ClassiCube.sh` passa a preferir um binário opcional da p1, `/storage/roms/ports/classicube/ClassiCube-pc`, copiado pelo PC. A ordem de tentativa é:
  1. rodar o `ClassiCube-pc` direto da p1;
  2. se o sistema recusar a execução (código de saída 126), copiar para `/tmp`, dar `chmod +x` e rodar de lá;
  3. se não houver `ClassiCube-pc`, ou se as duas tentativas falharem, rodar o binário do SYSTEM, como hoje.
- O lançador grava `log.txt` em `/storage/roms/ports/classicube/` a cada abertura, com o caminho que funcionou, o código de saída de cada tentativa, as opções de montagem de `/storage/roms` e `/tmp`, e o sha256 do binário da p1 e do SYSTEM. Assim o primeiro teste responde se a FAT32 executa direto, e um binário esquecido na p1 fica visível.
- A feature continua entregando o binário só no SYSTEM. O `ClassiCube-pc` nunca vem na imagem: só existe quando o jogador o copia. Por isso um binário velho na p1 de uma gravação anterior não passa a valer sozinho (o nome do arquivo é outro) e o `--keep-roms` não traz risco novo.
- O requisito "Binário único na partição SYSTEM" muda: o binário entregue pela imagem segue só no SYSTEM, mas a p1 pode levar um binário opcional do jogador. O teste que proíbe qualquer arquivo na p1 passa a proibir só o binário de nome `ClassiCube` (cópia entregue pela imagem), e novos testes cobrem a escolha do binário.
- O `ClassiCube.sh` ganha ganchos de teste (`R36_ROOT` e `R36_TMP`, no mesmo estilo do `classicube-sync`) para os testes rodarem a escolha do binário num diretório temporário.
- README documenta como trocar o binário pelo PC e como ler o `log.txt`.

Fora do escopo: assinar ou validar o binário da p1; atualizar o `ClassiCube-pc` automaticamente; mudar o `classicube-sync` (ele não mexe em binário); remover o binário do SYSTEM, que continua sendo a reserva; qualquer alteração em outros ports.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `classicube-port`: o requisito "Binário único na partição SYSTEM" passa a permitir um binário opcional do jogador na p1, com ordem de tentativa e reserva no SYSTEM; novo requisito de diagnóstico em `log.txt`.

## Impact

- `features/60-port-classicube/roms/ports_scripts/ClassiCube.sh` e o espelho em `features/60-port-classicube/system/usr/share/classicube/ports_scripts/ClassiCube.sh`.
- `tests/test_port_classicube.py` (testes da escolha do binário, do diagnóstico e do teste de binário único).
- `README.md` (item `60-port-classicube`).
- `openspec/specs/classicube-port/spec.md` (via delta desta change).
- Sem mudança na ABI nem no binário do SYSTEM; sem mudança no `classicube-sync`, no `compilar.sh` e na receita.
- Depende do estado do repositório após a change `corrige-classicube-controles` (lançador com a regra de sensibilidade); as duas editam o mesmo `ClassiCube.sh`.
