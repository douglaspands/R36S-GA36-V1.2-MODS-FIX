# Fábrica de imagens do R36S clone (GA36-MB V1.2)

Este repositório gera imagens de cartão SD para um **clone do R36S** com placa
**GA36-MB V1.2**. Cada mudança pedida vira uma *feature* versionada, e cada build
gera uma imagem nova, identificada pelo horário em que foi gerada.

## O aparelho e por que só esta base funciona

- O SoC é um **Allwinner A33**, remarcado como RK3326. Imagens "genéricas" de
  R36S (ArkOS, AmberELEC, ROCKNIX...) são para Rockchip e **não dão boot**.
- Ele só funciona com a imagem **EmuELEC 4.7 "Nexus" de fábrica** (kernel sunxi
  3.4.39, `script.bin`). O código-fonte desse fork não é público, então o sistema
  não pode ser recompilado.
- Por isso o build **parte sempre da imagem de fábrica** (`base/`), que nunca é
  modificada, e só troca o que é seguro: arquivos do SYSTEM (squashfs), do
  STORAGE (ext4), das ROMs (FAT32) e da partição de boot (FAT16).

Layout do cartão (setores de 512 bytes):

| Partição | Início    | Conteúdo                                   | Label no PC   |
|----------|-----------|--------------------------------------------|---------------|
| bootarea | 0         | MBR, EBRs, boot0, U-Boot, tabela softw411  | —             |
| p2       | 73728     | FAT16 lida pelo U-Boot (só 16 MiB valem)   | `R36-BOOT`    |
| p5       | 139264    | variáveis do U-Boot (env)                  | —             |
| p6       | 172032    | kernel + initramfs                         | —             |
| p7       | 237568    | FAT16 com o `SYSTEM` (squashfs) e `R36-BUILD.txt` | `R36-SYSTEM` |
| p8       | 1810432   | ext4 `/storage`: saves, configurações      | `R36-STORAGE` |
| p1       | 4956160   | FAT32 `/storage/roms`, até o fim do cartão | `R36-ROMS`    |

## Pré-requisitos

Linux (testado no Fedora) com Python 3.11 ou mais novo:

```bash
sudo dnf install squashfs-tools mtools dosfstools e2fsprogs util-linux xz coreutils
```

O `squashfs-tools` precisa ser 4.6 ou mais novo, com LZO (o do Fedora atende).
O build confere tudo isso e diz o que falta.

A imagem de fábrica vem deste post no r/R36S:
<https://www.reddit.com/r/R36S/comments/1w2i8em/r36s_ga36mb_v1220260416_emuelec_no_roms/>

Coloque-a em `base/`, com o nome exato:

```
base/R36S GA36-MB V1.2-20260416 - Emuelec - No ROMS.img
```

O sha256 esperado está em `config/base.toml`. Se não bater, o build recusa.
A pasta `base/` e todas as imagens ficam fora do git.

## Gerar uma imagem

```bash
./build.sh                    # cartão de 16 GB (15000 MiB), features habilitadas
./build.sh --no-features      # imagem equivalente à de fábrica (teste de referência)
./build.sh --help             # todas as opções
```

O build roda como usuário comum, sem sudo, e leva cerca de 2 minutos. A saída
fica em `out/<AAAAMMDD-HHMMSS>/`:

- `r36s_ga36-mb_v1.2-20260416_build_<timestamp>.img.xz`: a imagem completa,
  para gravar com Etcher ou `xz -dc ... | sudo dd`;
- `parts/*.img`: uma imagem por região, usadas pelo `./flash.sh`;
- `manifest.json`: timestamp, tamanho do cartão, offsets, sha256 e features;
- `changes.txt`: o que cada feature adicionou, substituiu ou removeu.

### Tamanho do cartão

A partição de ROMs vai até o fim do cartão, então a imagem precisa ser gerada
para o tamanho certo. Meça o cartão com o leitor conectado:

```bash
lsblk -b -d -o NAME,SIZE,RM,MODEL
```

Divida o `SIZE` por 1048576 para ter MiB e use um valor **igual ou menor**:

| Cartão vendido como | Tamanho real típico | Comando                         |
|---------------------|---------------------|---------------------------------|
| 8 GB                | 7300 a 7800 MiB     | `./build.sh --size-mib 7400`    |
| 16 GB (o atual)     | 15000 MiB           | `./build.sh`                    |
| 32 GB               | ~29800 MiB          | `./build.sh --size-mib 29800`   |

O mínimo é 7000 MiB, e o valor é arredondado para baixo a múltiplo de 4 MiB.

## Gravar o cartão

Rode o `./flash.sh` **num terminal normal** (ele pede a senha do sudo para
acessar o cartão). Comece sempre com `--dry-run`, que mostra o plano sem
escrever nada:

```bash
./flash.sh --device /dev/sdc --all --wipe-roms --wipe-storage --dry-run
```

Sem `--build`, o script usa o build mais recente de `out/`. Para escolher outro:
`--build 20261013-153045`.

### Gravação completa

Grava a bootarea, a p2 (só 16 MiB), p5, p6, p7, p8 e a p1 (só a parte com dados,
então leva bem menos que gravar 15 GB).

```bash
./flash.sh --device /dev/sdc --all --wipe-roms --wipe-storage     # cartão novo: apaga tudo
./flash.sh --device /dev/sdc --all --keep-roms --keep-storage     # atualiza o sistema, mantém ROMs e saves
./flash.sh --device /dev/sdc --all --keep-roms --wipe-storage     # mantém ROMs, zera configurações
```

- A gravação completa **sempre** exige `--keep-storage` ou `--wipe-storage`,
  porque a p8 guarda saves, savestates e configurações.
- Se a p1 do cartão tiver ROMs além das da imagem de fábrica, o script recusa até
  você escolher `--keep-roms` (mantém a p1 e a entrada dela no MBR) ou
  `--wipe-roms` (apaga).
- `--keep-roms` e `--keep-storage` exigem um cartão já gravado por este
  repositório.

### Gravação parcial

Grava só as partições escolhidas e nenhum byte fora delas. Exige um cartão que já
tenha o layout desta família de imagens (gravado antes com `--all`).

```bash
./flash.sh --device /dev/sdc --part system                  # só o SYSTEM (p7)
./flash.sh --device /dev/sdc --part boot                    # só os 16 MiB da p2
./flash.sh --device /dev/sdc --part storage --wipe-storage  # p8: apaga saves
./flash.sh --device /dev/sdc --part roms --wipe-roms        # p1: apaga ROMs
```

### Proteções do `flash.sh`

- Só aceita **disco inteiro removível** (`RM=1`) ou leitor SD interno
  (`mmcblk`). Recusa `/dev/sdc1` (partição), o SSD do PC e discos com partições
  do sistema montadas. Se o seu leitor USB se declara "fixo" (`RM=0`), use outro
  leitor.
- Recusa cartão menor que a imagem e avisa quando sobra espaço sem uso.
- Mostra dispositivo, modelo, capacidade, labels atuais e o que será apagado, e
  exige que você **digite o nome do dispositivo** (ex.: `sdc`).
- Desmonta as partições do cartão antes de gravar.
- Confere o sha256 de cada parte antes de gravar e relê tudo depois
  ("verificado").

Para testar sem cartão, use um arquivo como alvo (não precisa de sudo):

```bash
mkdir -p work
truncate -s 15000M work/cartao-teste.img
./flash.sh --target-file work/cartao-teste.img --all --wipe-roms --wipe-storage
```

O arquivo é esparso (ocupa só o que foi gravado, cerca de 2,4 GB). Evite `/tmp`,
que em muitos sistemas é um tmpfs pequeno.

## Criar uma feature

Uma feature é um diretório em `features/`. Veja o exemplo comentado em
`features/00-exemplo/`.

1. Copie o exemplo:

   ```bash
   cp -r features/00-exemplo features/10-minha-feature
   ```

2. Edite `features/10-minha-feature/feature.toml`: `name`, `description`,
   `order` (ordem de aplicação, menor primeiro) e troque `enabled = false` por
   `enabled = true`. Apague a seção `[[meta]]` do exemplo.
3. Apague os arquivos de exemplo e coloque os seus nas camadas:
   - `system/`: vai para a raiz `/` do sistema (somente leitura no aparelho);
   - `storage/`: vai para `/storage` (configurações, por exemplo
     `storage/.config/emuelec/configs/emuelec.conf`);
   - `roms/`: vai para `/storage/roms`;
   - `boot/`: vai para a p2 (`bootlogo.bmp` etc.; cuidado com o limite de 16 MiB).
4. Para remover um arquivo da base, declare no `feature.toml`:

   ```toml
   [[remove]]
   layer = "system"
   path = "usr/config/emuelec/bin/put_user_bins_here"
   ```

5. Gere e confira:

   ```bash
   ./build.sh --features 10-minha-feature    # só ela
   ./build.sh                                # todas as habilitadas
   cat out/<timestamp>/changes.txt
   ```

Regras importantes:

- Arquivos novos em `system/` e `storage/` ficam com dono `0:0`, modo `0755` se
  forem executáveis no repositório, senão `0644`. Arquivos que substituem um da
  base herdam dono e modo do original. Use `[[meta]]` para outro dono ou modo.
- Duas features não podem mexer no mesmo caminho, a não ser que a posterior
  declare `[[override]]` apontando a anterior.
- Cada feature nova pedida ganha um change próprio e uma branch própria no git.

## Onde ver qual build está no cartão

O arquivo `R36-BUILD.txt` traz o timestamp, o nome da imagem, o tamanho do cartão
e as features:

- no PC: na partição **R36-SYSTEM**;
- no aparelho: `/flash/R36-BUILD.txt`.

Ele é igual ao campo `build_info` do `manifest.json` do build.

## Rollback

- Grave um build anterior: `./flash.sh --device /dev/sdc --all --keep-roms --keep-storage --build <timestamp>`.
- Ou volte à imagem de fábrica, que continua intacta em `base/`:

  ```bash
  sudo dd if="base/R36S GA36-MB V1.2-20260416 - Emuelec - No ROMS.img" of=/dev/sdc bs=4M conv=fsync status=progress
  ```

## O que nunca fazer

- **Não deixe o Windows "reparar" ou formatar o cartão.** Ele altera a FAT e
  pode estragar a tabela de partições.
- **Não grave nada na p2 além dos 16 MiB.** O MBR declara 128 MiB, mas isso se
  sobrepõe ao env, ao kernel e ao SYSTEM. O `flash.sh` já limita.
- **Não crie `.please_resize_me`** em nenhuma partição: no boot, o aparelho
  formata a p1 e a p8 (ROMs e saves). O build recusa.
- **Não use imagens genéricas de R36S** (ArkOS, AmberELEC etc.): são para
  Rockchip e não dão boot neste clone.
- Não edite a imagem em `base/`. Ela é a referência de tudo.

## Para desenvolvedores

```bash
uv run python -I -m unittest discover -s tests              # testes rápidos (~30 s)
R36_SLOW=1 uv run python -I -m unittest discover -s tests   # inclui builds e gravações reais (~5 min)
```

O Python e as dependências são geridos com [uv](https://docs.astral.sh/uv/)
(`uv sync`; nada de `pip`). A lógica fica em `tools/r36img/` (Python, só
biblioteca padrão). Os testes
lentos usam `work/tests/` para os temporários.
