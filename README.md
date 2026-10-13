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
./build.sh --offline          # usa só o cache de downloads das features (sem rede)
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

### Escolher o build

Para ver os builds de `out/`, com o tamanho do cartão e as features de cada um
(não pede sudo nem precisa do cartão):

```bash
./flash.sh --list-builds
```

Sem `--build`, num terminal e com mais de um build em `out/`, o script mostra um
menu numerado antes de acessar o cartão. A opção 1 é o build mais recente, e Enter
escolhe essa opção. Ctrl+D cancela sem gravar. Com um só build, ou fora de um
terminal (scripts, pipe), ele usa o mais recente sem perguntar.

Para pular o menu, indique o build: `--build 20261013-153045`. O plano mostrado
antes da confirmação traz o timestamp, o tamanho do cartão e as features do build
escolhido.

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

## Features habilitadas

- **`10-ptbr-sao-paulo`**: idioma `pt_BR` no sistema, no EmulationStation e no
  RetroArch, fuso `America/Sao_Paulo` e menu RGUI no RetroArch.
- **`20-controle-posicional`**: no RetroArch, os botões de face seguem a posição
  física (baixo = B, direita = A, cima = X, esquerda = Y) e o hotkey é o Select.

| Atalho (no jogo)  | Ação                  |
|-------------------|-----------------------|
| Select + X        | menu do RetroArch     |
| Select + Y        | screenshot            |
| Select + L / R    | carregar / salvar estado |
| Select + L2       | câmera lenta          |
| Select + R2       | avanço rápido         |
| Select + baixo    | pausa                 |
| Select + direita  | FPS                   |
| Select + Start    | sair                  |

Os arquivos dessas duas ficam no `/storage`, então o efeito só aparece num cartão
gravado com `--wipe-storage` (com `--keep-storage` nada muda).

- **`30-splash-padrao-emuelec`**: no boot, antes do EmulationStation, aparece a
  tela da distribuição EmuELEC (logo e a palavra EMUELEC), e ao abrir um jogo, um
  ícone de controle sem texto. As duas substituem a arte de fábrica ("R36S /
  Please Wait.....").
  - A tela de boot fica no SYSTEM e muda com qualquer gravação dele, inclusive
    `--part system` ou `--all --keep-storage`.
  - A tela de jogo é lida do `/storage`, então só muda com `--wipe-storage`.
  - Uma tela própria em `/storage/roms/splash/` (por exemplo `nes.png`) continua
    tendo prioridade sobre o ícone.
  - Para trocar as telas, edite e rode `features/30-splash-padrao-emuelec/gerar.sh`
    (precisa do ImageMagick 7) e atualize os sha256 do `LEIA-ME.txt` da feature.
    O build não precisa do ImageMagick.
  - O logo é marca do EmuELEC: não venda imagens com essa tela (veja o
    `LEIA-ME.txt`).

As três seguintes são otimizações do sistema, cada uma desligável sozinha:

- **`40-zram-swap`**: o swap passa a ser um zram (memória comprimida em RAM) com
  metade da RAM e prioridade 32767, acima do swapfile do LibreELEC (10000). O
  swapfile de 300 MB sai da p8 e o `/storage/.config/swap.conf` desliga a
  recriação dele.
- **`41-servicos-enxutos`**: deixam de subir no boot o controle remoto IR
  (`lircd.socket`, `lircd`, `lircd-uinput`, `eventlircd`) e o `cron`. Só os links
  de ativação saem; as units continuam no SYSTEM.
- **`42-roms-noatime`**: depois do autostart, `/storage/roms` (FAT32 da p1) é
  remontada com `noatime`, para ler ROMs sem escrever a data de acesso no cartão.
  Se `/storage/roms` não for ponto de montagem, nada acontece.

O zram, os serviços e o `noatime` ficam no SYSTEM e valem com qualquer gravação
dele, inclusive `--part system` ou `--all --keep-storage`. A remoção do swapfile e
o `swap.conf` ficam no `/storage`, então só chegam com `--wipe-storage`. Com
`--keep-storage`, o swapfile antigo continua lá, mas só é usado se o zram encher.
Para apagá-lo à mão (por SSH ou no terminal do aparelho):

```bash
echo 'SWAP_ENABLED="no"' > /storage/.config/swap.conf   # senão o boot recria o swapfile
swapoff /storage/.cache/swapfile
rm /storage/.cache/swapfile
```

Para conferir no aparelho: `cat /proc/swaps` (só `/dev/zram0`),
`systemctl is-active lircd eventlircd cron` (`inactive`) e
`grep /storage/roms /proc/mounts` (`noatime`).

- **`50-temas-extras`**: sete temas do EmulationStation instalados na p8 ao lado
  do NES-BOX, que continua sendo o padrão: **Mario (GPi)**, **Sonic (GPi)** e
  **Crash (GPi)** (infantis, feitos para telas 4:3), **Minimal EmuELEC**,
  **Switch**, **Graphite OGA** e **Crystal**. Somam cerca de 381 MiB (limite de
  400 MiB, conferido pelo build). Não entram no git: o build baixa cada um de um
  commit fixo, confere o sha256 e guarda em `work/cache/external/`. A primeira
  vez precisa de rede; depois, `./build.sh --offline` basta.
  - Para escolher: no EmulationStation, Start > Configurações da interface > Tema.
  - Ficam no `/storage`, então só chegam com `--wipe-storage`.
  - Com `--keep-storage`, copie pelo PC: monte a partição ext4 `R36-STORAGE` do
    cartão e copie os diretórios de `.config/emulationstation/themes/` de um
    cartão (ou de um build) para o mesmo caminho dela.
  - PokemonUno, KirbyUno e YoshiUno (16:9) ficaram de fora por falta de espaço no
    orçamento; para testá-los, acrescente um `[[external]]` no `feature.toml`.

Para desligar uma feature, ponha `enabled = false` no `feature.toml` e gere a
imagem de novo.

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

5. Para conteúdo grande que não deve entrar no git (temas, por exemplo), declare
   um `.tar.gz` externo. O build baixa a URL, confere o sha256, guarda em
   `work/cache/external/<sha256>.tar.gz` e aplica o conteúdo na camada, sob `dest`,
   como se estivesse no diretório da feature:

   ```toml
   budget_mib = 400                  # opcional: o build falha se o extraído passar disso

   [[external]]
   layer = "storage"
   dest = ".config/emulationstation/themes/Crystal"
   url = "https://codeload.github.com/dm2912/Crystal/tar.gz/<commit>"   # use um commit, não um branch
   sha256 = "<sha256 do .tar.gz>"    # sha256sum arquivo.tar.gz
   strip = 1                         # níveis de diretório removidos do início (opcional)
   exclude = ["*.md"]                # padrões de caminho a ignorar (opcional)
   ```

   A extração recusa caminhos absolutos, `..`, dispositivos, hard links e links
   simbólicos para fora do destino. A primeira vez precisa de rede; depois o cache
   basta, e `./build.sh --offline` falha listando o que faltar nele.
6. Gere e confira:

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
