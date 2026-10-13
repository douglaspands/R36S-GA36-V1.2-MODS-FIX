# Design

## Context

O repositório hoje tem só a imagem base (`R36S GA36-MB V1.2-20260416 - Emuelec - No ROMS.img`, 2,45 GiB) e o `openspec/`. Não é um repositório git. A motivação está em proposal.md, e os requisitos nas specs `image-build`, `feature-layers` e `sd-flashing`.

Fatos levantados na imagem base, que restringem o design:

```
 setor    regiao                         observacao
 -------  -----------------------------  ---------------------------------------------
 0        MBR (55aa)                     p1 primaria no fim; p3 estendida (1..4956160)
 1..4     EBRs das logicas p5..p8        EBR@4 aponta para setor 5 vazio (quirk; manter)
 16       boot0 (eGON.BT0)               Allwinner; nao tocar
 ~38192   U-Boot 2017.09 sunxi           le env/boot pelos NOMES da softw411
 40960    softw411 (tabela Allwinner)    bootloader,env,boot,rootfs,storage,UDISK(size 0)
 73728    p2 FAT16 "Volumn"              MBR e FAT dizem 128 MiB; softw411 diz 16 MiB
 139264   p5 env (texto U-Boot)          root=/dev/mmcblk0p7 disk=/dev/mmcblk0p8
 172032   p6 boot.img (Android)          kernel 3.4.39 + initramfs (monta por /dev/...)
 237568   p7 FAT16 "EMUELEC" 768 MiB     SYSTEM (squashfs lzo1x_999, 512K) + low_pwr.bmp
 1810432  p8 ext4 1,5 GiB (sem label)    /storage: .config, saves, cores, ...
 4956160  p1 FAT32 87 MiB (sem label)    ROMs; mount_romfs.sh monta /dev/mmcblk0p1
```

- **Nada no boot usa labels de filesystem.** O U-Boot usa os nomes da softw411, e o kernel, o initramfs e os scripts usam `/dev/mmcblk0pN`. O único uso de label (`blkid --label EEROMS`) está num caminho de NTFS que não se aplica.
- **`/flash/.please_resize_me`** (na p7) faz o initramfs rodar `mkfs.vfat` na p1 e na p8, e o `fs-resize` reformata a p8.
- **O SYSTEM tem 12.518 entradas** e não tem nós de dispositivo. Todas são `0/0`, exceto `usr/lib/dbus/dbus-daemon-launch-helper` (`0/81`, setuid). `usr/bin/busybox` é setuid root.
- **O usuário já expandiu a p1 à mão** num cartão, e o aparelho deu boot normalmente. Isso indica que o U-Boot não reescreve o MBR.
- **Host:** Fedora, Python 3.14 (`tomllib` disponível), squashfs-tools 4.6.1 (LZO e pseudo-files), mtools, dosfstools, e2fsprogs (`debugfs`), sfdisk e xz. Não há `pv` nem `bmaptool`.

## Goals / Non-Goals

**Goals:**
- Build determinístico e rootless, que falha cedo e com mensagens claras.
- Gravação rápida no dia a dia: gravar só a partição alterada e, na p1, só a parte com dados.
- Verificações automáticas que tornam impossível quebrar o boot em silêncio: layout, metadados do SYSTEM, p2 e `.please_resize_me`.
- Lógica testável sem cartão físico: a gravação aceita um arquivo como alvo.

**Non-Goals:**
- Recompilar o EmuELEC, alterar kernel, initramfs, U-Boot ou env.
- Suportar Windows ou macOS no host. O README orienta usar Linux.
- Fazer backup de ROMs e saves. O script só se recusa a apagá-los sem opção explícita; um backup pode vir num change futuro.
- Redimensionar a p8 ou a p7.

## Decisions

### D1. Python 3 (só biblioteca padrão) para a lógica, com wrappers shell
Os comandos ficam como `./build.sh` e `./flash.sh`, que chamam `r36img.build` e `r36img.flash` dentro de `tools/` com `uv run python -I` (o Python e as dependências do projeto são geridos pelo uv: `pyproject.toml`, `.python-version`, `uv.lock`). Toda a lógica binária fica em Python: editar a entrada da p1 no MBR, ler a softw411, verificar a alocação da FAT16 da p2, comparar metadados e gerar o manifest. As ferramentas externas (mksquashfs, mtools, debugfs, mkfs.fat) entram via `subprocess` com argumentos em lista, sem shell.
- *Alternativa:* só Bash. Rejeitada porque parsear MBR, FAT e listagens em Bash é frágil e difícil de testar.
- *Por que só a stdlib:* não exige virtualenv, e `tomllib` resolve os descritores.

### D2. Estrutura do repositório
```
build.sh  flash.sh  README.md  .gitignore
config/base.toml          # caminho e sha256 da base, layout esperado (setores), labels
base/                     # (gitignored) imagem base movida para ca
features/
  00-exemplo/             # feature de exemplo, desabilitada (documenta o formato)
    feature.toml
    system/ storage/ roms/ boot/
tools/r36img/             # pacote Python: layout, mbr, fat, squash, ext4, build, flash, manifest
tests/                    # unittest: unidades + fixtures sinteticas pequenas
work/  out/               # (gitignored) temporarios e saidas
```
O repositório será inicializado com `git init` e `.gitignore`. Imagens nunca entram no git.

### D3. Descritor de feature em TOML
O arquivo `feature.toml` tem os campos `schema = 1`, `name`, `description`, `order` (inteiro), `enabled` (padrão `true`) e as listas opcionais `[[remove]]` (layer, path), `[[meta]]` (layer, path, mode, uid, gid) e `[[override]]` (layer, path, feature). O nome do diretório é livre; a ordem vem de `order`. A spec `feature-layers` define a semântica.
- *Alternativa:* YAML. Rejeitada porque exige PyYAML, fora da stdlib.

### D4. Reempacotamento do SYSTEM com pseudo-file de metadados
1. `unsquashfs -lln` na base gera a tabela de metadados: tipo, modo, uid/gid, tamanho e alvo de symlink de cada caminho.
2. `unsquashfs -d work/system` extrai como usuário comum. Os donos se perdem no disco, mas a tabela os guarda.
3. As features são aplicadas no diretório. Arquivos novos recebem metadados pelas regras da spec; arquivos substituídos herdam os do original.
4. Gera-se `work/system.pf` com uma linha `"<path>" m <modo> <uid> <gid>` para **todo** caminho final.
5. `mksquashfs work/system SYSTEM -pf work/system.pf -comp lzo -Xalgorithm lzo1x_999 -Xcompression-level 9 -b 524288 -noappend -no-xattrs`. As mtimes vêm do diretório extraído, que o unsquashfs preservou.
6. **Verificação:** `unsquashfs -lln` do resultado é comparado com a tabela esperada (base mais as mudanças das features). Qualquer divergência faz o build falhar. Por padrão, o conteúdo também é verificado: compara-se o sha256 de cada arquivo regular extraído do resultado com o do diretório de trabalho. `--fast` pula essa etapa.
- *Alternativa:* `fakeroot`. Rejeitada como caminho principal porque depende de LD_PRELOAD e de estado entre execuções. Fica como fallback documentado.
- *Alternativa:* append no squashfs (`mksquashfs` sobre o existente). Rejeitada porque não permite remover nem substituir arquivos.

### D5. STORAGE (p8) editado com `debugfs`
A região da p8 é copiada para `work/storage.img`. As features são aplicadas com um script `debugfs -w -f`:
- `mkdir` cria os diretórios necessários;
- `rm` e depois `write` substituem arquivos;
- `sif` define `mode`, `uid` e `gid`;
- `rm` atende às remoções declaradas.

Depois roda `e2fsck -fn` para validar e `tune2fs -L R36-STORAGE` para o label.
- *Alternativa:* `fuse2fs` e cópia. Rejeitada porque os donos dependem de opções do FUSE e o resultado é menos previsível.

### D6. ROMS (p1) recriada do tamanho do cartão
1. O tamanho final é `tamanho_cartao_MiB` alinhado para baixo a 4 MiB. A p1 vai de 4956160 até o último setor.
2. `truncate` cria um arquivo esparso do tamanho da p1. Depois, `mkfs.fat -F 32 -S 512 -h 4956160 -n R36-ROMS`. O `-h` mantém o "hidden sectors" igual ao da base.
3. O conteúdo da p1 base (733 arquivos, 61 MB, incluindo `.update`) é copiado com `mcopy -s` (via diretório temporário), seguido da camada `roms` das features.
4. **Comprimento de gravação:** um parser FAT32 calcula o fim do último cluster alocado, e o manifest registra `write_length`, que é o fim dos FATs e diretórios ou o do último cluster (o que for maior), arredondado a 4 MiB. Gravar só esse trecho é seguro, porque o FAT32 recém-criado marca o resto como livre e o lixo antigo do cartão nos clusters livres não importa.

### D7. Edição do MBR
A bootarea (setores 0 a 73727) é sempre copiada byte a byte da base, nunca regenerada com `sfdisk`. Isso preserva o EBR estranho e a softw411. Só a entrada 1 do MBR (p1) muda. O LBA de início continua 4956160, e o número de setores passa a ir até o fim da imagem. O CHS fica em `FE FF FF`, o valor de "LBA-only". A estendida (p3), as lógicas, a assinatura e o código de boot ficam intactos. Isso é verificado contra a base pela regra estrutural da spec `image-build`.

### D8. P2 (BOOT) e P7 (SYSTEM) editadas com mtools, sem refazer o filesystem
A p2 é copiada para `work/boot.img` (só os 16 MiB reais). Os arquivos entram com `mcopy -o`, e o label com `mlabel`. Usa-se `MTOOLS_SKIP_CHECK=1`, porque a geometria da p2 tem heads e sectors zerados. Um parser FAT16 confere que todo cluster alocado, os FATs e o diretório raiz ficam abaixo de 16 MiB. A p7 recebe o SYSTEM novo e `R36-BUILD.txt` com `mcopy -o`, além do label `R36-SYSTEM`. Antes da cópia, verifica-se se cabe no espaço livre.
- Por que não recriar a FAT da p2: mudaria a geometria que o U-Boot da fábrica lê (`magic.bin`, `bootlogo.bmp`, `bat/`). Manter o filesystem original é o menor risco.
- O registro do build fica em `R36-BUILD.txt` na raiz da p7. No PC ele aparece em `R36-SYSTEM`; no aparelho, em `/flash/R36-BUILD.txt`. Fica fora do SYSTEM para que o build sem features gere um SYSTEM igual ao da base.

### D9. Saída e manifest
```
out/<timestamp>/                   # ex.: out/20261013-153045/
  r36s_ga36-mb_v1.2-20260416_build_<timestamp>.img.xz   # imagem completa (Etcher/dd), xz -T0
  parts/bootarea.img               # setores 0..73727 (MBR, boot0, U-Boot, softw411)
  parts/boot.img    (16 MiB)       parts/env.img   parts/kernel.img
  parts/system.img  (p7 768 MiB)   parts/storage.img (p8)   parts/roms.img (esparso)
  manifest.json                    # timestamp, nome da imagem, tamanho, regioes {offset, size, write_length, sha256}, features
  changes.txt                      # relatorio de diferencas por feature
```
- **Identificador do build:** o timestamp `AAAAMMDD-HHMMSS`, em hora local, capturado uma vez no início do build. Ele é usado no diretório, no nome da imagem, no manifest e no `R36-BUILD.txt`. Não há `--version`: o identificador não é livre, para que o nome sempre siga o padrão. Ordena em ordem alfabética igual à ordem cronológica, e por isso o `flash.sh` escolhe o mais recente pelo maior nome em `out/`.
- **Prefixo:** `image_prefix = "r36s_ga36-mb_v1.2-20260416"` no `config/base.toml`.
  - *Alternativa:* derivar o prefixo do nome da base. Rejeitada porque o nome do arquivo baixado tem espaços e maiúsculas.
- **Diretório já existente** (só acontece com dois builds no mesmo segundo): o build falha sem tocar nele. Não há `--force`.
- O sha256 de `roms.img` cobre só o `write_length`.

### D10. Gravação: regiões, privilégios e travas
- O `flash.sh` monta um **plano de regiões** a partir do manifest. Na gravação completa: bootarea, p2 (16 MiB), p5, p6, p7, p8 e p1 (`write_length`). Na parcial, só as regiões pedidas. `--keep-roms` tira a p1 do plano e preserva a entrada 1 do MBR do cartão dentro da bootarea gravada. `--keep-storage` tira a p8.
- **A gravação sempre usa as imagens de `parts/`.** O `.img.xz` serve só para distribuição. Assim, a gravação completa escreve cerca de 2,4 GB mais os dados da p1, e não 15 GB.
- **Privilégios:** o script roda como usuário e chama `sudo` só para abrir o dispositivo, para leitura (validação, simulação e releitura) e escrita (via `dd` com `oflag=direct conv=fsync`, offsets em bytes). Isso também funciona quando o usuário digita a senha num terminal normal.
- **Detecção do alvo** via `lsblk -J -b -o NAME,TYPE,RM,SIZE,MODEL,TRAN,MOUNTPOINTS`. São recusados: um alvo que não é disco inteiro; um alvo com `RM=0` que não seja `mmcblk*`; um alvo que contenha `/`, `/boot` ou swap ativo; e um alvo menor que o maior offset mais o tamanho do plano. A confirmação é digitar o nome do dispositivo.
- **Layout do cartão** (para gravação parcial, `--keep-roms` e `--keep-storage`): ler 512 bytes do setor 0 e do setor 40960 e comparar as entradas do MBR (exceto o tamanho da p1) e a softw411 com o manifest.
- **ROMs "além da base":** a p1 do cartão é lida com mtools direto no dispositivo (via sudo, só leitura). Se houver qualquer entrada fora da lista da base, ou dados acima de 61 MB, considera-se que há ROMs.
- Antes de escrever, as partições montadas do cartão são desmontadas com `udisksctl unmount` (ou `umount` como fallback).
- **Para testes**, `--target-file <img>` substitui o dispositivo por um arquivo. Assim a lógica toda roda sem cartão e sem sudo.

## Risks / Trade-offs

- [Compressão `lzo1x_999` lenta: alguns minutos por build] → Aceito por compatibilidade. A compressão é paralelizada (o mksquashfs usa todos os núcleos), e o `--fast` só pula a verificação de conteúdo, nunca a de metadados.
- [`mkfs.fat` gerar um FAT32 que o kernel 3.4 não monta, por exemplo com cluster size atípico] → Usar parâmetros padrão do mkfs.fat, que o kernel 3.4 suporta, e registrar o cluster size no manifest. O primeiro teste no aparelho (feature vazia) cobre esse risco.
- [U-Boot reescrever o MBR para um tamanho diferente da p1] → Improvável, porque a expansão manual do usuário funcionou. O teste no aparelho inclui conferir, após o boot, que `/sys/block/mmcblk0/mmcblk0p1/size` bate com o manifest.
- [Gravar a p1 só até `write_length` deixar lixo antigo no fim do cartão] → É irrelevante para o FAT32, e o espaço aparece como livre. O `.img.xz` completo continua disponível para quem quiser zerar tudo.
- [`sudo` dentro do script não funciona via `!` no Claude Code] → O README orienta rodar o `flash.sh` num terminal normal. O `--dry-run` sem acesso ao dispositivo informa o que falta.
- [Leitor USB que reporta `RM=0`] → O script recusa e mostra o motivo, sem opção de contornar (requisito da spec `sd-flashing`). O README sugere usar outro leitor. Se isso acontecer na prática, um change futuro pode avaliar uma exceção.
- [Cartão "8 GB" com menos de 7000 MiB reais] → O build recusa tamanhos abaixo de 7000 MiB, e o flash recusa um cartão menor que o plano. O README explica como medir com `lsblk -b`.
- [O formato do `feature.toml` evoluir] → O descritor tem um campo `schema = 1`, e o build recusa versões que não conhece.

## Migration Plan

1. Mover a imagem base para `base/`, registrar o sha256 em `config/base.toml` e rodar `git init`.
2. Gerar o primeiro build sem features (a feature vazia).
3. Gravar no cartão atual com `./flash.sh --device /dev/sdc --all --wipe-roms --wipe-storage`. O cartão atual tem ROMs e um SYSTEM modificado à mão, e o usuário confirmou que tem backup das ROMs.
4. Testar no aparelho: boot, EmulationStation, labels no PC, tamanho da p1 após o boot, `R36-BUILD.txt`.
5. **Rollback:** gravar um build anterior de `out/` com `--build <timestamp>`, ou a imagem base original com `dd`, que continua intacta em `base/`.
