# Proposal

## Why

O console é um clone do R36S com placa GA36-MB V1.2 e SoC Allwinner A33 (remarcado como RK3326). Ele só funciona com a imagem EmuELEC 4.7 "Nexus" de fábrica (kernel sunxi 3.4.39, `script.bin`), que não pode ser recompilada porque o código-fonte do fork não é público. Hoje, qualquer mudança é feita à mão no cartão: não é reproduzível, quebra fácil (dono e permissões do squashfs, partição p2 com tamanho falso, `.please_resize_me`) e apaga ROMs. O repositório precisa virar uma "fábrica de imagens", em que cada feature pedida gera uma imagem nova, versionada e gravável no cartão de 16 GB.

## What Changes

- Um build sem root parte da imagem base baixada, que nunca é modificada e é verificada por sha256. Ele aplica as features declaradas no repositório e gera:
  - a imagem completa do cartão, com a partição de ROMs já expandida até o fim, comprimida. O tamanho do cartão é um parâmetro do build. O padrão é 15000 MiB (o tamanho exato do cartão atual de 16 GB). O mínimo aceito é 7000 MiB, para caber cartões vendidos como "8 GB", que têm de 7,3 a 7,8 GB reais. Cartões maiores (32, 64, 128 GB) só exigem mudar o parâmetro;
  - uma imagem por partição, para gravação parcial;
  - um manifest com timestamp do build, sha256, offsets e a lista de features aplicadas.
- Cada build é identificado pelo timestamp da geração, e a imagem segue o padrão `r36s_ga36-mb_v1.2-20260416_build_<AAAAMMDD-HHMMSS>.img`, mais `.xz` por ser comprimida.
- As features ficam em diretórios no repositório, organizadas por camada: SYSTEM (squashfs da p7), STORAGE (ext4 da p8), ROMS (FAT32 da p1) e BOOT (arquivos da p2).
- O SYSTEM é reempacotado preservando dono, grupo, modo e bits setuid/setgid de cada arquivo. O build falha se qualquer arquivo não tocado por uma feature tiver os metadados alterados.
- Os labels dos filesystems passam a ter nomes legíveis (`R36-BOOT`, `R36-SYSTEM`, `R36-STORAGE`, `R36-ROMS`). Números de partição, setores de início e a tabela Allwinner (softw411) permanecem idênticos.
- Um script de gravação grava o cartão inteiro ou só partições específicas (`system`, `storage`, `roms`, `boot`). Ele tem travas contra gravar no disco errado e contra apagar ROMs ou saves sem confirmação explícita, e permite regravar o sistema mantendo as ROMs.
- Proteções embutidas:
  - nunca gravar mais de 16 MiB na p2, porque o MBR declara 128 MiB, que se sobrepõem a env, boot e SYSTEM;
  - nunca gerar uma imagem com `.please_resize_me`, que dispara formatação no boot.
- Um `README.md` em português do Brasil explica o passo a passo:
  - pré-requisitos e onde colocar a imagem base;
  - como gerar a imagem, escolhendo o tamanho do cartão;
  - como gravar o cartão inteiro ou só uma partição;
  - como criar uma feature;
  - o que nunca fazer (Windows "reparar" o cartão, gravar na p2, imagens genéricas).
- Uma "feature vazia" de referência: o build sem features deve dar boot igual à base. É o primeiro teste no aparelho.

## Capabilities

### New Capabilities
- `image-build`: gera, a partir da imagem base e das features, a imagem completa do cartão, as imagens por partição e o manifest, preservando a compatibilidade de boot (layout, tabelas, metadados do SYSTEM, labels).
- `feature-layers`: define como uma feature é declarada no repositório, em quais camadas pode atuar e como é aplicada e registrada em cada imagem.
- `sd-flashing`: grava no cartão SD a imagem completa ou partições específicas, com proteção contra disco errado (incluindo cartão menor que a imagem) e contra perda de ROMs e saves.

### Modified Capabilities
<!-- Nenhuma: o projeto ainda não tem specs. -->

## Impact

- **Repositório:** passa a ter scripts de build e de gravação, um diretório de features, a configuração da base, um diretório de saída ignorado pelo git e um `README.md` em pt-BR. A imagem base (2,45 GiB) e as imagens geradas ficam fora do git.
- **Dependências no host (Linux):**
  - `squashfs-tools` ≥ 4.6, com suporte a LZO e pseudo-files;
  - `mtools`, `dosfstools`, `e2fsprogs`, `util-linux` (`sfdisk`), `xz` e `coreutils`;
  - a gravação exige privilégio de escrita no dispositivo (sudo).
- **Cartão:** a primeira gravação completa apaga o conteúdo atual do cartão. O usuário confirmou que tem backup das ROMs. As gravações seguintes podem preservar ROMs (p1) e dados do usuário (p8).
- **Fora do escopo:** alterar kernel e bootloader (p6, boot0, U-Boot, env), portar outro sistema operacional e implementar qualquer feature funcional. Cada feature virá em um change próprio.
