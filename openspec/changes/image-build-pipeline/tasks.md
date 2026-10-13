# Tasks

## 1. Estrutura do repositório

- [x] 1.1 Rodar `git init` e criar `.gitignore` ignorando `base/`, `work/`, `out/` e `*.img*`. Verificar que `git status` não lista nenhuma imagem.
- [ ] 1.2 Mover a imagem base para `base/` (mantendo o nome) e criar `config/base.toml` com caminho, sha256, setores esperados de cada região/partição (D2/D7), labels, limites de tamanho (padrão 15000 MiB, mínimo 7000 MiB) e `image_prefix = "r36s_ga36-mb_v1.2-20260416"`. Verificar que `sha256sum` da base confere com o config.
- [ ] 1.3 Criar o pacote `tools/r36img/`, os wrappers `build.sh` e `flash.sh` (que chamam `python3 -I -m ...`) e `tests/` com unittest. Verificar que `python3 -I -m unittest discover -s tests` roda e que `./build.sh --help` e `./flash.sh --help` mostram uso em pt-BR.
- [ ] 1.4 Implementar a checagem de dependências do host: mksquashfs/unsquashfs ≥ 4.6 com LZO, mtools, mkfs.fat, debugfs, e2fsck, tune2fs e xz. Ela falha com a lista do que falta e o comando `dnf install` sugerido. Verificar com um teste que simula `PATH` sem uma ferramenta.

## 2. Leitura e edição de estruturas binárias

- [ ] 2.1 Implementar o módulo de layout: parse do MBR e da cadeia de EBRs, edição só da entrada 1 (p1) com CHS `FE FF FF`, e parse da softw411. Verificar com testes sobre um MBR sintético, e com um teste somente leitura na base real (pulado se a base não existir) que reproduz a tabela do design.
- [ ] 2.2 Implementar o parser FAT16/FAT32: extensão dos FATs e do diretório raiz, e o fim do último cluster alocado. Verificar com testes sobre imagens criadas com `mkfs.fat` e `mcopy` no próprio teste.
- [ ] 2.3 Implementar a verificação da base (sha256 e abertura somente leitura) e a validação do tamanho do cartão (padrão, mínimo 7000, alinhamento a 4 MiB). Verificar com testes: 6000 falha, 7462 vira 7460, sem parâmetro dá 15000, e base com hash errado falha sem criar saída.

## 3. Reempacotamento do SYSTEM (D4)

- [ ] 3.1 Implementar o parse de `unsquashfs -lln` em uma tabela de metadados (tipo, modo, uid/gid, tamanho, alvo de symlink, nomes com espaço). Verificar com um teste sobre um squashfs pequeno criado no teste com `-pf`, incluindo um arquivo setuid `0/81`.
- [ ] 3.2 Implementar a extração, a geração do pseudo-file `m` para todos os caminhos e o `mksquashfs` com os parâmetros da base. Verificar com um teste de ida e volta, como usuário comum, que preserva setuid, `0/81`, symlinks e mtimes.
- [ ] 3.3 Implementar a verificação pós-empacotamento: metadados sempre, e conteúdo (sha256) a menos que `--fast` seja passado. Ela lista cada divergência. Verificar com um teste que injeta uma divergência de modo e confirma a falha com a lista.
- [ ] 3.4 Fazer a ida e volta do SYSTEM real sem features. Verificar que `unsquashfs -lln` do resultado é igual ao da base, que `busybox` é `-rwsr-xr-x 0/0`, que o helper do dbus é `-rwsr-x--- 0/81` e que `unsquashfs -s` reporta `lzo` e 524288 (teste de integração marcado como lento).

## 4. Features (spec feature-layers)

- [ ] 4.1 Implementar o parse e a validação do `feature.toml` (`schema`, `name`, `order`, `enabled`, `[[remove]]`, `[[meta]]`, `[[override]]`) e rejeitar camadas desconhecidas. Verificar com testes para descritor ausente, campo faltante, `schema` desconhecido e diretório `kernel/`.
- [ ] 4.2 Implementar a ordenação, a seleção (`--features`, `--no-features`, `enabled = false`) e a detecção de conflitos com `override`. Verificar com testes dos cenários de conflito, substituição declarada e feature desabilitada.
- [ ] 4.3 Implementar a aplicação nas árvores das camadas com as regras de metadados: novos `0:0` com 0755/0644, substituídos herdam, `[[meta]]` sobrescreve, remoção de caminho inexistente falha. Verificar com testes dos cenários da spec.
- [ ] 4.4 Implementar a trava `.please_resize_me` em todas as camadas e na base. Verificar com um teste em que uma feature traz o arquivo e o build falha citando a feature e o caminho.
- [ ] 4.5 Criar `features/00-exemplo/`, desabilitada, com um `feature.toml` comentado em pt-BR e um arquivo de exemplo em cada camada. Verificar que o build padrão a ignora e que `--features 00-exemplo` a aplica e a lista em `changes.txt`.

## 5. Construção das partições

- [ ] 5.1 STORAGE (D5): aplicar a camada via script `debugfs -w`, rodar `e2fsck -fn` e aplicar o label `R36-STORAGE`. Verificar com um teste sobre um ext4 pequeno (`mke2fs -d`): `debugfs stat` mostra uid/modo corretos, uma substituição funciona e o e2fsck passa.
- [ ] 5.2 BOOT (D8): extrair os 16 MiB da p2, aplicar a camada com `mcopy` e `MTOOLS_SKIP_CHECK=1`, aplicar o label `R36-BOOT` e checar que tudo fica abaixo de 16 MiB. Verificar com testes: a p2 real sem features fica dentro do limite, e uma FAT16 sintética com conteúdo excedente falha.
- [ ] 5.3 SYSTEM partição (D8): substituir o SYSTEM na p7, gravar `R36-BUILD.txt`, aplicar o label `R36-SYSTEM` e checar a capacidade. Verificar com testes: `mdir` mostra os arquivos, e um SYSTEM grande demais falha com os tamanhos.
- [ ] 5.4 ROMS (D6): criar a p1 esparsa com `mkfs.fat -F 32 -S 512 -h 4956160 -n R36-ROMS`, copiar o conteúdo da p1 base mais a camada `roms` e calcular o `write_length`. Verificar com testes: `fsck.fat -n` passa, a listagem é igual à da base, e o `write_length` cobre o último cluster.

## 6. Montagem da imagem e saídas

- [ ] 6.1 Montar a imagem completa esparsa: bootarea copiada byte a byte, MBR com a p1 ajustada e regiões nos offsets. Verificar que `sfdisk -d` na imagem mostra a p1 de 4956160 até o último setor.
- [ ] 6.2 Implementar a verificação estrutural contra a base: setores 0 a 73727 exceto a entrada da p1, p5 e p6 idênticas, e as demais entradas do MBR iguais. Verificar com um teste que altera um byte do U-Boot e confirma a falha.
- [ ] 6.3 Gerar `out/<timestamp>/` com `parts/*.img`, a imagem `r36s_ga36-mb_v1.2-20260416_build_<timestamp>.img.xz`, `manifest.json` (com timestamp, `write_length` e sha256) e `changes.txt`. Recusar quando o diretório já existir. Verificar com testes: o nome bate com `^r36s_ga36-mb_v1\.2-20260416_build_\d{8}-\d{6}\.img\.xz$`, o timestamp é o mesmo no diretório, no nome, no manifest e no `R36-BUILD.txt`, e um diretório existente não é alterado.
- [ ] 6.4 Finalizar a CLI do `build.sh` (`--size-mib`, `--features`, `--no-features`, `--fast`, `--help` em pt-BR, sem `--version` nem `--force`). Verificar que cada opção aparece no `--help` e que valores inválidos geram erro claro.
- [ ] 6.5 Rodar `./build.sh --no-features` na base real. Verificar: os sha256 conferem com o manifest; `blkid` nas partes mostra os quatro labels; `fsck.fat -n` e `e2fsck -fn` passam; a verificação estrutural e a de metadados passam; a base continua com o mesmo sha256.

## 7. Gravação (spec sd-flashing, D10)

- [ ] 7.1 Implementar a detecção e as travas do alvo via `lsblk -J`: disco inteiro, `RM=1` ou `mmcblk`, sem montagens do host, capacidade suficiente e aviso de espaço sem uso. Verificar com testes sobre fixtures de lsblk, incluindo a saída real deste PC (sda, sdb e nvme recusados; sdc aceito; `/dev/sdc1` recusado).
- [ ] 7.2 Implementar a leitura do layout do cartão (MBR e softw411) e a detecção de "ROMs além da base" via mtools. Verificar com testes usando `--target-file` sobre imagens geradas, com cartão compatível, incompatível e com ROMs extras.
- [ ] 7.3 Implementar o plano de regiões: completa, parcial, `--keep-roms`/`--wipe-roms` (preservando a entrada da p1 do cartão), `--keep-storage`/`--wipe-storage` e p2 limitada a 16 MiB. Verificar com testes de cada cenário de recusa e aceitação da spec.
- [ ] 7.4 Implementar a confirmação (digitar o nome do dispositivo), o `--dry-run` (somente leitura) e a desmontagem via `udisksctl` com fallback. Verificar com testes com entrada simulada: confirmação errada encerra sem escrever, e o dry-run não abre o alvo para escrita.
- [ ] 7.5 Implementar a escrita: conferir o sha256 contra o manifest, gravar via `sudo dd` (ou direto em `--target-file`), fazer fsync e reler as regiões. Verificar ponta a ponta com `--target-file`: gravação completa num arquivo de 15000 MiB; depois `--part system` alterando só a p7; depois `--keep-roms` mantendo a p1 byte a byte.
- [ ] 7.6 Finalizar a CLI do `flash.sh` (`--device`, `--target-file`, `--all`, `--part`, `--keep-*`/`--wipe-*`, `--dry-run`, `--build <timestamp>` (padrão: o mais recente em `out/`), `--help` em pt-BR). Verificar que cada opção aparece no `--help`, que sem `--build` o mais recente é usado, que um `--build` inexistente lista os disponíveis e que combinações inválidas (por exemplo `--keep-roms --wipe-roms`) são recusadas.

## 8. README e validação no aparelho

- [ ] 8.1 Escrever o `README.md` em pt-BR:
  - o que é o aparelho (clone com A33) e por que só esta base funciona;
  - pré-requisitos (`dnf install ...`) e como colocar a base em `base/`;
  - como medir o cartão com `lsblk -b` e gerar imagens para 8, 16 e 32 GB;
  - gravação completa e parcial, com as flags de proteção de ROMs e saves;
  - como criar uma feature passo a passo, a partir do `00-exemplo`;
  - onde ver o `R36-BUILD.txt`, como fazer rollback e o que nunca fazer.

  Verificar executando cada comando do README (os de gravação, com `--dry-run` ou `--target-file`).
- [ ] 8.2 Gerar o build final sem features e rodar `./flash.sh --device /dev/sdc --all --wipe-roms --wipe-storage --dry-run` num terminal do usuário. Verificar que o plano mostra as regiões e os dados que serão apagados.
- [ ] 8.3 Teste no aparelho, feito pelo usuário: gravar de verdade e conferir boot, EmulationStation, labels no PC, `R36-BUILD.txt`, e que o tamanho da p1 em `/sys/block/mmcblk0/mmcblk0p1/size` após o boot bate com o manifest. Registrar o resultado no change.

## Workflow follow-up

- Arquivar o change com `/opsx:archive` depois do teste no aparelho (8.3) aprovado.
- Cada nova feature pedida vira um change próprio que adiciona um diretório em `features/` e gera um novo build.
