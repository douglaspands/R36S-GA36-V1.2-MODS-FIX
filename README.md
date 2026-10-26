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
- **Sem rede, SSH nem Wi-Fi: tudo pelo cartão SD.** O aparelho não tem conexão
  nenhuma. Para pôr ou tirar arquivos (cores, logs, perfis), tire o cartão e leia
  ou grave no PC: a `R36-ROMS` (FAT32) abre sem root, a `R36-STORAGE` (ext4) tem
  arquivos do root.

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
./build.sh --test             # marca o build como imagem de teste (sufixo -test)
./build.sh --help             # todas as opções
```

O build roda como usuário comum, sem sudo, e leva cerca de 2 minutos. A saída
fica em `out/<AAAAMMDD-HHMMSS>/`:

- `r36s_ga36-mb_v1.2-20260416_build_<timestamp>.img.xz`: a imagem completa,
  para gravar com Etcher ou `xz -dc ... | sudo dd`;
- `parts/*.img`: uma imagem por região, usadas pelo `./flash.sh`;
- `manifest.json`: timestamp, tamanho do cartão, offsets, sha256 e features;
- `changes.txt`: o que cada feature adicionou, substituiu ou removeu.

Com `--test`, o build é marcado como imagem de teste (intermediária, para
experimentar uma ideia): a pasta vira `out/<timestamp>-test/` e a imagem
`..._build_<timestamp>-test.img.xz`. O conteúdo da imagem não muda. O
`manifest.json` ganha `"test": true` e o `R36-BUILD.txt` ganha a linha
`teste: sim`. O `./flash.sh` trata o build de teste como qualquer outro: ele
aparece no menu e no `--list-builds` com o marcador `test`, e se indica com
`--build <timestamp>-test`.

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
- Se o cartão já tinha a antiga moldura do Game Boy (feature removida) e foi
  gravado com `--keep-storage`, apague pelo PC na `R36-STORAGE`:
  `.config/retroarch/config/Gambatte/gb.cfg`, `gb.opt`, `gbc.cfg`, `gbc.opt` e
  `shaders/presets/Gambatte/gb.glslp`, `gbc.glslp`. Com `--wipe-storage` não há
  nada a fazer.

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

- **`10-ptbr-sao-paulo`**: idioma `pt_BR` no sistema e no EmulationStation, fuso
  `America/Sao_Paulo` e menu RGUI no RetroArch. O menu do RetroArch fica em
  inglês por padrão (`user_language = "0"`, o valor da imagem base); para o
  português, use o próprio menu: Settings > User Interface > Language >
  Portuguese (Brazil). Também troca
  vários padrões de fábrica (cada um dá para voltar pelos menus):
  - proporção de tela "Core provided" (`global.ratio=core`) em vez de 4/3; para
    outra, use o menu do EmulationStation (Configurações de jogos > Proporção);
  - OK/Cancel sem inversão (`menu_swap_ok_cancel_buttons = "false"`): no menu do
    RetroArch, o botão da direita confirma e o de baixo volta; para inverter,
    ative "Trocar botões OK/Cancelar" no RetroArch (Configurações > Entrada >
    Controles do menu);
  - gpSP como core de GBA (`gba.emulator=libretro`, `gba.core=gpsp`) em vez do
    mGBA; para voltar, escolha o core do GBA nas opções do sistema no
    EmulationStation. A BIOS do GBA continua opcional e não vem na imagem.
  - snes9x2005_plus recompilado para o A33 como core de SNES
    (`snes.emulator=libretro`, `snes.core=snes9x2005_plus_a33`, que vem da
    `53-cores-a33`), mais leve que o snes9x. O snes9x2005_plus original e os outros
    cores de SNES continuam instalados: para trocar, escolha o core nas opções do
    sistema ou do jogo no EmulationStation. `snesh` e `snesmsu1` não mudam.
    Se desligar a `53-cores-a33`, volte esta chave para `snes9x2005_plus` (um
    teste confere).
  - fceumm como core de NES (`nes.emulator=libretro`, `nes.core=fceumm`) em vez do
    nestopia da base, por ser mais leve para o A33. O nestopia e os outros cores
    continuam instalados: para voltar, escolha o nestopia nas opções do sistema ou
    do jogo no EmulationStation. O `fds` não muda. Fica no `/storage`, então só
    chega com imagem nova ou `--wipe-storage`. Save states do nestopia não carregam
    no fceumm; saves de bateria (.srm) costumam ser compatíveis.
  - pastas ocultas nas listas de jogos (`FolderViewMode` `never`) e favoritos no
    topo (`FavoritesFirst` `true`). Para voltar, no EmulationStation: Start >
    Configurações da interface (lista de jogos) > mostrar pastas / favoritos primeiro.
    Ficam no `/storage`, então só chegam com `--wipe-storage`.
  - fbalpha2012 como core de CPS2 (`cps2.emulator=libretro`,
    `cps2.core=fbalpha2012`) em vez do fbneo da base, por ser mais leve para o A33. Os
    outros cores (fbneo, mame2003_plus, mame2010, AdvanceMame) continuam
    instalados: para trocar, escolha outro core nas opções do sistema ou do jogo
    no EmulationStation. CPS1, CPS3 e os demais sistemas de arcade não mudam.
  - máximo desempenho desligado (`global.maxperf=0`): o aparelho esquenta menos,
    mas rende menos nos sistemas pesados (GBA, PSP, N64); para ligar, use o menu
    do EmulationStation, por sistema ou por jogo. A imagem base chamava `maxperf`
    em todo jogo, sem ler a chave; por isso a feature traz uma cópia do
    `/usr/bin/emuelecRunEmu.sh` em que, depois de saber o sistema e o jogo, o
    `maxperf` só é chamado quando a chave (jogo, sistema ou global, nessa ordem)
    vale `1`, e o `normperf` roda nos demais casos. Só imagem nova ou regravada
    recebe esse padrão; num cartão já gravado, desligue a opção no menu. Ao
    trocar a imagem base, reconfira a cópia: `tests/test_ptbr_controle.py` compara
    o script com o da base e só aceita essas diferenças.
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

- **`30-telas-icone-controle`**: uma única imagem, o ícone de controle sem
  texto, do boot até o jogo: no boot (antes do EmulationStation), no carregamento
  do EmulationStation, ao abrir um jogo e na volta dele. Ela substitui a arte de
  fábrica ("R36S / Please Wait.....", o God of War, que também aparecia como
  fundo do carregamento do ES com a lista de collections por cima). A tela de
  boot da distribuição EmuELEC saiu da imagem.
  - A tela de boot fica no SYSTEM e muda com qualquer gravação dele, inclusive
    `--part system` ou `--all --keep-storage`.
  - A tela de jogo, o `logo.png` e o `splash.xml` do EmulationStation também
    estão no `/storage`, que o ES lê primeiro, então o carregamento do ES só
    muda com `--wipe-storage`. Com `--keep-storage`, o ES continua mostrando a
    arte antiga no carregamento.
  - Uma tela própria em `/storage/roms/splash/` (por exemplo `nes.png`) continua
    tendo prioridade sobre o ícone.
  - Para trocar as telas, edite e rode `features/30-telas-icone-controle/gerar.sh`
    (precisa do ImageMagick 7) e atualize os sha256 do `LEIA-ME.txt` da feature.
    O build não precisa do ImageMagick.

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
Para apagá-lo à mão, com o cartão no PC e a `R36-STORAGE` montada (os arquivos
são do root, então os comandos pedem sudo; troque `<ponto>` pelo ponto de
montagem):

```bash
echo 'SWAP_ENABLED="no"' | sudo tee <ponto>/.config/swap.conf   # senão o boot recria o swapfile
sudo rm <ponto>/.cache/swapfile
```

Para conferir no aparelho: `cat /proc/swaps` (só `/dev/zram0`),
`systemctl is-active lircd eventlircd cron` (`inactive`) e
`grep /storage/roms /proc/mounts` (`noatime`).

- **`43-registro-termico`**: só mede o calor, sem mudar nada. O serviço
  `r36-thermal-log` anexa uma linha a cada 5 s em `R36-ROMS/r36-thermal.csv`
  (no aparelho, `/storage/roms/r36-thermal.csv`), sem usar o cron. Não mexe no
  clock, no governor nem na DRAM: quem escolhe o governor de cada jogo é a
  `10-ptbr-sao-paulo` (chave `maxperf`).
  Serve para descobrir quanto cada `sistema:core` esquenta e quanto clock usa de
  fato, antes de definir tetos de clock.
  - **Colunas:** `date`, `uptime_s`, `boot`, uma `temp_<zona>` por
    `thermal_zone*` (em °C), `cpu_mhz`, `cpu_max_mhz` (teto de clock em vigor,
    `scaling_max_freq`), `governor`, `cpus_online`, `cpu0` a
    `cpu3` (ocupação em %, no intervalo; vazio se o núcleo está desligado),
    `dram_scene`, `dram_mhz` (clock da DRAM, do `cur_freq` do devfreq),
    `bat_status`, `bat_pct`, `bat_voltage` (mV), `bat_current` (mA, com o sinal
    que o kernel informa), `bat_charge_now` e `bat_charge_full` (mAh, o que o
    driver acredita ter), `bat_pct_est`, `system`, `emulator`, `core` e `rom`
    (os quatro últimos vêm do `emuelecRunEmu.sh` em execução e ficam vazios no
    menu). Sem hora certa no relógio, `uptime_s` e `boot` ordenam e separam as
    sessões. Os campos de bateria que o kernel não expõe ficam vazios.
  - **`bat_pct_est`:** percentual estimado só pela tensão (curva genérica de
    Li-ion, com filtro de 4 amostras), vazio com o carregador ligado. Serve só
    para comparar com o `bat_pct` do kernel: não aparece no ES nem no RetroArch e
    não altera o `capacity`.
  - **Retrato do sistema:** uma vez por boot, no primeiro ciclo em que o log
    pode gravar, o serviço grava `R36-ROMS/r36-sysinfo.txt` (substitui o do boot
    anterior): governors e clocks disponíveis, teto e máximo, tunables do
    ondemand (já afinados), cenas e clocks da DRAM, trip points das zonas
    térmicas e estado dos dispositivos de resfriamento, um `caminho: valor` por
    linha, com `(ausente)` no que o aparelho não tem. Serve para ler no PC o que
    não dá para conferir no aparelho (sem Wi-Fi nem SSH). A seção `== bateria ==`
    traz o `uevent` de cada `power_supply` (`caminho/uevent: CHAVE=valor`), os
    campos da bateria (`status`, `capacity`, `voltage_now`, `current_now`,
    `charge_now`, `charge_full`, `charge_full_design`, `capacity_level`) e as
    últimas 80 linhas do `dmesg` que citam o `axp`, com o prefixo `dmesg:`.
  - **Diagnóstico da bateria:** para medir o erro do percentual do ES, siga a
    descarga completa. Carregue a bateria a 100%, ligue o aparelho e use-o (um
    trecho no menu e um em jogo) até desligar sozinho. No PC, copie
    `r36-thermal.csv`, `r36-thermal.1.csv` e `r36-sysinfo.txt` da `R36-ROMS` e
    rode `uv run python -I tools/analisa_bateria.py r36-thermal.1.csv r36-thermal.csv`.
    O resumo, por boot, traz tensão, `bat_pct` e `bat_pct_est` do início, a
    diferença entre os dois percentuais e a queda por hora de cada um nas linhas em
    `Discharging`. **Antes de gravar o cartão**, copie os CSVs que quer guardar: a
    primeira gravação com as colunas novas move o `r36-thermal.csv` antigo para
    `r36-thermal.1.csv` e apaga o `.1` que já existia.
  - **Limites:** o arquivo vira `r36-thermal.1.csv` ao passar de 1 MB (2 MB no
    máximo, somando os dois), e nada é gravado com menos de 64 MB livres na p1
    ou se `/storage/roms` não estiver montado. A gravação não usa `sync`: numa
    queda de energia perdem-se cerca de 30 s de log.
  - **Sessão de medição:** 5 min no menu e 10 min em cada um de NES, Mega Drive,
    SNES, GBA (Mario Kart), PSX, N64, PSP e CPS2. Depois, abra o CSV no PC.
    A ocupação do núcleo mais ocupado dá o teto aproximado:
    `clock x ocupação / 0,8`.
  - **Desligar:** `enabled = false` em `features/43-registro-termico/feature.toml`
    e gerar de novo. Os CSVs que já estão no cartão podem ser apagados à mão.
  - Fica no SYSTEM, então vale com qualquer gravação dele. Para conferir no
    aparelho: `systemctl is-active r36-thermal-log` (`active`).

- **`44-cpu-ondemand`**: afina o governor `ondemand` para o clock subir cedo e
  não cair no meio do jogo, sem ligar o máximo desempenho. Com o ondemand ativo:
  `up_threshold` 30 (sobe de clock com 30% de carga, em vez dos 50% da base),
  `sampling_down_factor` 10 (demora 10 amostragens para descer) e piso de
  600 MHz (`scaling_min_freq` 600000), que corta os clocks de 240 a 504 MHz
  vistos em jogo. O menu continua variando de 600 a 1200 MHz.
  O `/usr/bin/cpufreq` roda no boot e chama `/usr/lib/r36/cpu-ondemand-tune`; o
  `emuelecRunEmu.sh` chama o mesmo script depois de cada `normperf`, porque a
  troca de `performance` para `ondemand` zera os tunables. Com o governor
  `performance` (máximo desempenho ligado) o script não faz nada.
  O `r36-cpu-ondemand.service` (oneshot, `After=emuelec-autostart.service`) roda
  o mesmo script uma vez depois do autostart, porque o `normperf` do boot zera
  os tunables e o piso; sem ele o menu parado ficaria nos valores da base.
  Na abertura do jogo o `emuelecRunEmu.sh` passa o argumento `jogo`, e o script
  põe a DRAM na cena `0` (a mesma do máximo desempenho); no menu, depois do
  `normperf` da saída, a DRAM volta à cena `1`. Sem a feature, a DRAM fica na
  cena `1` também em jogo.
  - **Desligar:** `enabled = false` em `features/44-cpu-ondemand/feature.toml` e
    gerar de novo; o ondemand volta aos valores da imagem base e a DRAM volta à
    cena `1` em jogo.
  - **Conferir:** no log da `43-registro-termico`, `cpu_mhz` sem valores abaixo
    de 600 em jogo e `dram_scene` `0` em jogo, `1` no menu.
    No `r36-sysinfo.txt` do boot: `up_threshold` 30, `sampling_down_factor` 10
    e `scaling_min_freq` 600000.
    No aparelho: `cat /sys/devices/system/cpu/cpufreq/*/up_threshold`
    (30) e `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq` (600000).
  - Fica no SYSTEM, então vale com qualquer gravação dele.

- **`46-audio`**: volume 0 mudo, volume salvo no boot e menos pipocos no som.
  - **Volume:** o ganho de saída é um só, analógico (`speaker volume control`, 0 a
    63); o DAC toca em 0 dB, então não há ganho digital a redistribuir. Na base o
    volume 0 dá `speaker volume control` = 20 e não silencia, e o `audio.volume`
    salvo só vale depois do primeiro toque num botão de volume. A feature faz o
    volume 0 silenciar (`speaker volume control` = 0), aplica o `audio.volume`
    salvo (padrão 29) já no boot e mantém a escala de fábrica acima de 0. O volume
    fica também em `r36-audio.volume` (p8, ao lado do `emuelec.conf`), que vale mais
    que o `audio.volume` do `emuelec.conf`: o EmulationStation regrava o
    `emuelec.conf` com o valor antigo ao reiniciar pelo menu. Tudo
    passa pelo `/usr/lib/r36/audio-ganho`, que o boot, o `emuelecRunEmu.sh` (abrir
    e sair de jogo), o `udt_pwr_events.sh` (acordar) e o `udt_events.sh` (botões de
    volume) chamam; os dois últimos são cópias da base com a chamada acrescentada.
    O chiado com som tocando vem do amplificador analógico e a feature não o
    altera.
  - **Pipocos:** no `retroarch.cfg` da p8, `audio_latency` `64` vira `96` (cerca
    de 32 ms a mais de atraso) e `audio_resampler_quality` `2` vira `1` (resampler
    mais leve). Só mudam enquanto estiverem no valor de fábrica: um valor
    escolhido no menu do RetroArch é respeitado, e é pelo menu que se volta a
    `64` ou `128`, por exemplo.
  - **`r36-audio.log`:** a cada boot a feature grava na raiz da p1 os controles do
    mixer, a interface de registradores do driver do codec, o efeito de um
    `Speaker Function` e o que o `audio-ganho` aplicou. Sem nenhuma escrita em
    registrador. O dump do boot é feito com o DAC parado; por isso o
    `r36-audio-amostra.service` (só leitura, 10 minutos depois do boot) grava em
    `r36-audio-dac.log` o dump do codec a cada mudança de estado, com a música do
    menu e os jogos tocando.
  - **Voltar ao som de fábrica sem regravar:** crie um arquivo vazio
    `r36-audio-original` na raiz da p1 (`R36-ROMS`, pelo PC) e ligue o aparelho:
    o volume 0 volta a dar `speaker volume control` = 20 (sem mudo) e
    `audio_latency`/`audio_resampler_quality` voltam a `64`/`2` (se estiverem nos
    valores da feature). Apague o arquivo para religar a correção. Serve para
    comparar, no mesmo cartão, com o jogo em pausa.
  - **Desligar:** `enabled = false` em `features/46-audio/feature.toml` e gerar de
    novo; os scripts da base voltam. As chaves do RetroArch já gravadas na p8
    voltam a `64`/`2` ligando o aparelho uma vez com `r36-audio-original` antes
    de gravar o build sem a feature, ou pelo menu do RetroArch.
  - Fica no SYSTEM, então vale com `--part system` ou `--keep-storage`.

- **`50-temas-extras`**: cinco temas extras do EmulationStation além do NES-BOX de
  fábrica (que continua sendo o padrão imutável). Para não sobrecarregar a partição
  `storage` (p8, ext4 com tamanho fixo), os temas são divididos entre o sistema e o
  cartão:
  - **Na partição do sistema (`storage`, p8 ext4):** temas leves, ocupando cerca de 37 MiB:
    - **Minimal EmuELEC** (em `.config/emulationstation/themes/Minimal EmuELEC`)
    - **Graphite OGA** (em `.config/emulationstation/themes/Graphite OGA`)
  - **Na partição de ROMs (`roms`, p1 FAT32):** temas mais ricos em mídia e espaço,
    instalados em `themes/` na raiz FAT32 (visíveis no aparelho em `/storage/roms/themes/`):
    - **Switch** (em `themes/Switch`)
    - **Crystal** (em `themes/Crystal`)
    - **Epic Cody** (em `themes/Epic Cody`, tema 4:3 640x480 do CodyV59 adaptado para o RG351V)
  - Somam cerca de 553 MiB descompactados (limite de 700 MiB no `budget_mib`,
    conferido pelo build). Não entram no git: o build baixa cada um de um commit
    fixo, confere o sha256 e guarda em `work/cache/external/`. A primeira vez
    precisa de rede; depois, `./build.sh --offline` basta.
  - Para escolher: no EmulationStation, Start > Configurações da interface > Tema.
  - Como os temas mais pesados ficam na partição FAT32 (`R36-ROMS`), você pode
    inclusive adicionar outros temas ou customizá-los diretamente pelo computador
    (Windows, Mac ou Linux) colocando as pastas em `themes/` na raiz do cartão.
  - Com `--keep-storage` e `--keep-roms`, os temas existentes no cartão não são
    apagados.

- **`52-psp-desempenho`**: o `ppsspp.ini` global (PPSSPP standalone) fica mais
  leve para o A33 (4x Cortex-A7, Mali-400 MP2), valendo para qualquer jogo de
  PSP sem ini próprio. Dez chaves mudam, o resto é igual ao de fábrica:
  - `InternalResolution` 2 → 1 (resolução nativa, 480x272);
  - `CPUSpeed` 666 → 0 (o jogo escolhe a frequência, sem overclock);
  - `NumWorkerThreads` 8 → 4 (um por núcleo);
  - `SkipGPUReadbackMode` 0 → 1 (pula leituras de volta da GPU);
  - `SplineBezierQuality` 1 → 0 (curvas em qualidade baixa);
  - `ShowFPSCounter` 2 → 0 (sem contador na tela);
  - `TextureFiltering` 3 → 2 (textura nearest, usa menos banda da GPU);
  - `ReplaceTextures` True → False (sem busca por pacotes de textura);
  - `AchievementsEnable` True → False (sem conquistas do RetroAchievements);
  - `EnableCheats` True → False (o PPSSPP não processa cheats).
  - O PPSSPP lê a cópia do `/storage`
    (`.config/ppsspp/PSP/SYSTEM/ppsspp.ini`), então só chega com
    `--wipe-storage`. Com `--keep-storage`, ajuste pelo menu do PPSSPP.
  - Para religar o contador de FPS, entre no menu do PPSSPP e vá em
    Configurações > Gráficos > Mostrar contador de FPS.
  - Para religar a filtragem linear, vá em Configurações > Gráficos >
    Filtragem de textura. Para usar cheats, ligue a opção de cheats em
    Configurações > Sistema.
  - Os inis por jogo de fábrica (God of War, Ridge Racer e outros, em
    `*_ppsspp.ini`) continuam valendo sobre o global. Pular quadros automático
    segue ligado.

- **`53-cores-a33`**: cores recompilados para o A33 com o `./cores.sh` (veja
  "Compilar um core"), instalados **ao lado** dos originais em
  `/usr/lib/libretro`. Hoje é um só:
  - **`snes9x2005_plus_a33`**: o snes9x2005_plus do mesmo fonte da base,
    compilado com `-O2`, LTO e `-mcpu=cortex-a7`. É o core padrão do SNES (chave
    na `10-ptbr-sao-paulo`). No Yoshi's Island usou 10% menos CPU que o original;
    na tela a diferença não aparece, mas sobra mais folga quando o aparelho
    esquenta.
  - O `snes9x2005_plus` original fica intocado e continua na lista de cores do
    SNES. O `snes9x2005_plus_a33` aparece no fim dessa lista e usa o mesmo nome
    de biblioteca do original, então as opções do core e os saves são os mesmos.
  - Na avaliação também foram testados `-O3`, PGO e o `snes9x2010` (`-O2` e
    `-O3`); todos perderam e ficaram fora da imagem. Receitas, registros e
    resultados estão em `cores/snes9x2005_plus/` e `cores/snes9x2010/`
    (`RESULTADOS.md`).
  - O `.so` e o `.info` ficam no SYSTEM e chegam com `--part system`. A lista de
    cores (`es_systems.cfg`) e o padrão do SNES (`emuelec.conf`) ficam no
    `/storage`, então só chegam com `--wipe-storage`. Com `--keep-storage`, o
    SNES continua no core escolhido antes, e o `snes9x2005_plus_a33` não aparece
    na lista de cores.

- **`54-shaders-gba`**: o shader `gba-modern-remaster` para Game Boy Advance,
  que dá cor viva à imagem (vibrance, curva em S e realce) sem lavar o vermelho,
  suaviza as bordas com um filtro sharp-bilinear que não cintila nem borra e
  desenha uma grade LCD leve entre os pixels (aspecto de tela de console), numa
  só passada GLSL leve para a Mali-400.
  - Parâmetros no menu do RetroArch (Shaders, Shader Parameters), com o padrão:
    `VIBRANCE` 0,45; `SATURATION` 1,10; `HIGHLIGHT ROLLOFF` 0,35 (quanto do
    reforço de cor sai dos tons claros; nenhuma cor fica abaixo da original, e
    pele, amarelo e pastéis ganham cor sem clarear); `S-CURVE Contrast` 0,28; `HIGHLIGHT SHOULDER` 0,05;
    `PIXEL SOFTNESS` 0,15; `LCD GRID (0=Off)` 0,10, bem sutil (0 desliga a grade);
    `BRIGHTNESS` 0 (de -0,30 a 0,30, clareia ou escurece tudo).
  - **Vem ligado nos jogos de GBA**, sem escolher nada no ES. O
    `r36-shader-gba-prepara.service` roda no boot, antes do ES, e liga o shader
    de dois jeitos: acrescenta `gba.shaderset=gba/gba-modern-remaster.glslp` ao
    `emuelec.conf` (o que a opção "SHADER SET" do ES grava) quando essa chave
    não existe, e cria o preset automático do RetroArch de cada core de GBA
    (`config/gpSP/gpSP.glslp`, `mGBA/mGBA.glslp`, `VBA-M/VBA-M.glslp` e
    `VBA Next/VBA Next.glslp`) apontando para
    `/usr/share/common-shaders/gba/gba-modern-remaster.glslp`, no SYSTEM. Uma
    escolha sua em `gba.shaderset` (inclusive `none`) e um preset que já existe,
    como um que você salvou com outros valores, nunca são sobrescritos. Funciona
    com `--keep-storage`, porque nasce no boot.
  - **Diagnóstico:** o serviço deixa o que fez em `R36-ROMS/r36-shader-gba.log`
    (legível pelo PC). Se o shader não entrar, o log mostra se a chave e os
    presets foram criados.
  - **Desligar:** crie um arquivo vazio chamado `r36-gba-sem-shader` na raiz da
    `R36-ROMS` (pelo PC). No boot seguinte o serviço apaga só o que ele mesmo
    criou (a linha `gba.shaderset` exata e os presets de uma linha) e não os
    recria; apagar o arquivo religa o shader. Os valores do shader se ajustam no
    menu do RetroArch (Shaders, Shader Parameters).
  - Os arquivos ficam em `/usr/share/common-shaders/gba/` (SYSTEM), a camada de
    baixo de `/tmp/shaders`, que é a pasta que o ES lista. Chegam ao cartão em
    qualquer gravação do `system`, inclusive com `--keep-storage`.
  - Uma cópia do shader na p8 (`/storage/shaders/gba/`) esconde a do SYSTEM, e
    presets que a referenciam mantêm o shader antigo ligado. Isso ficou na p8
    depois de versões de teste e de gravações do `system`, e o shader parecia
    não mudar. O mesmo serviço apaga, a cada boot, a cópia da p8 que difere da
    do SYSTEM e os presets que contêm só a referência a ela; cópia idêntica,
    outros presets e outros shaders seus ficam. Consequência: edições suas no
    `gba-modern-remaster.glsl` dentro da p8 não sobrevivem ao boot.

- **`58-ports-exec`**: copiar um port pelo PC e jogar. A p1 (FAT32) não guarda
  permissão de execução e pode estar montada com `noexec`, então o
  `r36-ports-exec.service` prepara os executáveis no boot, antes do
  EmulationStation.
  - Para cada arquivo ELF (executáveis e bibliotecas `.so`) dentro de
    `R36-ROMS/ports/` (até 4 níveis de pasta), guarda uma cópia com permissão
    de execução na p8, em `/storage/.config/r36-ports-exec/<sha256>`, e a monta
    por cima do arquivo da p1 (`mount --bind`). O script do port segue
    chamando o mesmo caminho, mas o processo roda da cópia. Nenhum script de
    port precisa de edição, e saves, mapas e opções continuam sendo gravados
    na p1, visíveis no PC.
  - **Instalar um port**: copie o script para `R36-ROMS/ports_scripts/` e a
    pasta do port (binário e dados) para `R36-ROMS/ports/<nome>/`, e ligue o
    aparelho. O port aparece no menu "Ports" e executa; não há build nem
    gravação do SYSTEM, e a imagem não guarda lista de ports.
  - **Trocar um binário**: copie o novo por cima pelo PC e religue. A cópia é
    pelo conteúdo (sha256), então o binário novo vira uma cópia nova e a
    antiga é apagada, assim como as de ports removidos.
  - **Log**: `R36-ROMS/ports/r36-ports-exec.log` traz, do último boot, uma
    linha por executável (`ok` ou `ERRO`, o caminho, o sha256 e a mensagem de
    erro) e as opções de montagem de `/storage` e `/storage/roms`. Um erro em
    um arquivo não impede os outros nem o boot.
  - **Limites**: só varre `R36-ROMS/ports/`; o que um port criar ou trocar com
    o aparelho ligado só vale no boot seguinte; binários que reescrevem a si
    mesmos em execução não são atendidos. Para levar o serviço ao aparelho,
    grave o SYSTEM uma vez (`--part system`).

- **`60-port-classicube`**: o ClassiCube 1.3.9 (recriação do Minecraft Classic
  em C) como port nativo, no menu Ports como "Classic Craft (ClassiCube)". Roda
  offline, com texturas clássicas e sons já no cartão.
  - O binário é compilado por `./ports/classicube/compilar.sh` (container
    `localhost/r36-cores-a33`, Cortex-A7, GLES 2.0 + SDL2), que aplica ajustes
    ao fonte: texturas em `GL_RGBA` (o driver da Mali-400 recusa o `BGRA` do
    build Linux e a tela ficava preta), janela já com foco (sem window manager
    o jogo abria em pausa), leitura do `gamecontrollerdb.txt` da base (o SDL
    2.0.9 ignora `SDL_GAMECONTROLLERCONFIG_FILE`) e os controles descritos
    abaixo.
  - **Controles** (botões no layout Nintendo do aparelho): o direcional e o
    analógico esquerdo andam; o analógico direito gira a câmera. Cima anda
    para frente e olha para cima; nos menus, cima sobe a seleção. Os dois
    analógicos têm zona morta de 20% do curso (o resto é reescalado), para a
    deriva do ADC não mover nada. Com o analógico direito no fundo a câmera
    gira cerca de 110°/s (`mousesensitivity = 120` no `options.txt`) e um
    passo de menu leva menos de 0,5 s.
    - A pula, X inventário, Y pega o bloco, L quebra, R coloca, L2/R2 trocam
      o item da barra, `L3 + R3` (os dois analógicos apertados) faz respawn.
    - B+L velocidade, B+R voar, B+X atravessar paredes, B+cima/baixo voar para
      cima/baixo.
    - Start abre a pausa e Select volta/fecha menus; `Select + Start` fecha o
      jogo e volta ao EmulationStation. Chat e "definir spawn" não têm botão
      (Start não redefine mais o respawn); o jogador pode ligá-los no menu do
      jogo, e os binds que ele salvar valem mais que os padrões.
    - Cartões gravados com `--keep-roms` recebem a sensibilidade nova na
      primeira abertura, mas só se o `options.txt` ainda tiver
      `mousesensitivity = 30`; outro valor é preservado.
  - O binário é um port como os outros: a imagem o entrega em
    `R36-ROMS/ports/classicube/ClassiCube` (p1), não há cópia no SYSTEM, e o
    `58-ports-exec` o torna executável no boot. Mapas e opções ficam na mesma
    pasta; o `ClassiCube.sh` recria ali o `options.txt` e os pacotes de textura
    e som que faltarem. Se o binário faltar, ou o sistema o recusar, o
    lançador avisa (`ports/classicube/log.txt`, e o `r36-ports-exec.log` traz
    o motivo) e volta ao EmulationStation.
  - **Atualizar o binário**: o binário que está na p1 é sempre o que vale, e
    `--keep-roms` não regrava a p1. Para trocar o do cartão, compile com
    `./ports/classicube/compilar.sh` (ele grava em
    `features/60-port-classicube/roms/ports/classicube/ClassiCube`), copie o
    arquivo para `R36-ROMS/ports/classicube/` pelo PC e religue o aparelho; não
    precisa de `flash.sh`. Uma gravação completa já leva o binário da imagem.
  - **Primeira vez com esta versão**: grave o SYSTEM uma vez
    (`./flash.sh --device /dev/sdX --part system`) para levar o serviço
    `r36-ports-exec` e o lançador novo; em cartão gravado com `--keep-roms`,
    copie também o binário para a p1.
  - O `r36-classicube-sync.service` roda no boot, antes do EmulationStation
    (espera até 20 s o `mount_romfs.sh` montar `/storage/roms`; não espera o
    `emuelec-autostart`, que só termina depois de abrir o ES), e
    repõe em `R36-ROMS/ports_scripts/` o lançador e a capa que faltarem ou
    estiverem diferentes, a partir da cópia em
    `/usr/share/classicube/ports_scripts/`. Assim o jogo também aparece num
    cartão gravado com `--keep-roms`. No `gamelist.xml` dessa pasta ele só
    acrescenta a entrada do ClassiCube quando ela falta, sem mexer nas outras.
  - Outros ports copiados pelo PC para `R36-ROMS/ports_scripts/` continuam
    aparecendo no menu: a feature não cria `/usr/bin/ports`, então o overlay
    que o `mount_romfs.sh` tenta montar nessa pasta segue falhando, como na
    base. Para instalar outro port basta copiar o script e a pasta pelo PC (veja
    `58-ports-exec`).
  - Apagar o `ClassiCube.sh` do cartão não remove o jogo, porque o boot o
    recria. Para tirá-lo, desligue a feature e grave o `system` de novo.

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
   layer = "roms"
   dest = "themes/Crystal"
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

O arquivo `R36-BUILD.txt` traz o nome da imagem, o tamanho do cartão e as
features. A versão é o timestamp no fim do nome da imagem, registrado na linha
`imagem:` (`..._build_<timestamp>.img.xz`):

- no PC: na partição **R36-SYSTEM**;
- no aparelho: `/flash/R36-BUILD.txt`.

Num build gerado com `--test`, o nome da imagem termina em `-test.img.xz` e o
arquivo tem a linha `teste: sim`; um build normal não tem essa linha.

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

### Compilar um core

O `./cores.sh` compila cores libretro para o A33 a partir de uma receita
versionada, num container sem root. O `./build.sh` não depende dele: usa os
binários já commitados em `features/53-cores-a33`.

Pré-requisitos, sem sudo: `podman` rootless (no Fedora já vem configurado),
`readelf` (binutils) e rede na primeira compilação (imagem `debian:bookworm`
fixada por digest e o fonte do core, guardado em `work/cache/cores/`). O
toolchain é o cross-GCC armhf do bookworm, com glibc 2.36, a mesma da base.

```bash
./cores.sh compilar snes9x2005_plus o3      # compila, confere a ABI, copia para a feature e registra
./cores.sh verificar                        # ABI e sha256 dos binários commitados contra o registro
./cores.sh perfil snes9x2005_plus <R36-ROMS>/pgo/snes9x2005_plus   # importa o perfil do PGO
./cores.sh resumo <R36-ROMS>/r36-thermal.csv --roms <R36-ROMS>      # tabela das sessões
```

- **`compilar <core> <variante>`**: baixa o fonte do commit da receita (confere o
  sha256), roda o `make` do upstream com `CC=a33-cc`, um wrapper que acrescenta
  as flags da variante **depois** das do Makefile, e confere o binário: só
  bibliotecas que a base tem, `GLIBC_` até 2.36, `GLIBCXX_` até 3.4.29, ARMv7
  com VFPv4 e hard-float, `retro_*` em modo ARM e sem seções de depuração. Se
  passar, copia o `.so` para a feature e acrescenta uma linha em
  `cores/<core>/builds.jsonl` (flags efetivas, versão do GCC, imagem, sha256).
- **`verificar [<core>]`**: repete a checagem de ABI nos binários commitados e
  confere que o sha256 de cada um é o do último registro da variante.
- **`perfil <core> <dir>`**: copia os `.gcda` gravados pelo build instrumentado
  (`R36-ROMS/pgo/<core>/`, com o cartão no PC) para `cores/<core>/pgo/`,
  conferindo que há um por objeto, e registra os hashes em `perfil.json`.
- **`resumo <csv> [--roms <ponto>]`**: lê o `r36-thermal.csv` da `43-registro-termico`
  e imprime uma tabela Markdown por sessão (`boot`, `core`, `rom`), com duração,
  ocupação, clock e temperatura; com `--roms`, também o CRC32 e o SHA1 das ROMs.

Para acrescentar um core:

1. Crie `cores/<core>/receita.toml` copiando a do `snes9x2005_plus`: repositório,
   commit completo, URL do `.tar.gz` do commit e o sha256 dele, os argumentos do
   `make`, o nome do `.so` que ele gera, o `.info` da base e as variantes (nome
   do core e flags). Para um core em C++, veja o limite de `GLIBCXX_` no
   `CLAUDE.md`.
2. `./cores.sh compilar <core> <variante>` para cada variante.
3. Em `features/53-cores-a33`, crie o `.info` de cada variante a partir do da
   base (só `display_name` e `display_version` mudam) e acrescente as `<core>`
   no `es_systems.cfg` das duas camadas.
4. Rode os testes e `./cores.sh verificar`, e commite binários, `builds.jsonl` e
   receita juntos.
