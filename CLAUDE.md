# CLAUDE.md

Fábrica de imagens de cartão SD para o clone do R36S (GA36-MB V1.2, Allwinner A33).
O `README.md` explica o uso; este arquivo guarda as regras de trabalho e os fatos
do aparelho que não se deduzem do código.

## Regras de trabalho

- **Shell:** comandos com caminhos relativos à raiz do projeto, um por chamada,
  sem `cd` e sem encadear com `&&` ou `;`. Lógica longa vai num script temporário
  rodado numa chamada só.
- **Sem sudo**, em nenhuma forma, nem indireta (`./flash.sh --device` chama
  `sudo dd`). Para validar uma gravação, use `./flash.sh --target-file`. O que
  precisar de root ou do cartão real vira instrução para o usuário rodar.
- **Python via uv:** `uv run`, `uv add`, `uv sync`. Nada de `pip`, venv manual ou
  `python3` direto. Testes: `uv run python -I -m unittest discover -s tests`.
- **Uma branch por change:** cada change OpenSpec ganha uma branch própria criada
  a partir da `main` no início do `/opsx:apply`, com o nome da change. Merge e
  push só a pedido.
- **Onde registrar:** regras e fatos duráveis vão neste `CLAUDE.md`; decisões de
  uma change vão nos artefatos OpenSpec dela (proposal, design, specs).

## O aparelho

- **Acesso só pelo cartão SD.** Não há rede, SSH nem Wi-Fi. Tudo que entra ou
  sai do aparelho (cores, perfis de PGO, logs) passa pelo cartão lido no PC. A
  p1 (`R36-ROMS`, FAT32) é gravável no PC sem root; a p8 (`R36-STORAGE`, ext4)
  tem arquivos do root. Nunca propor passos por SSH.
- **Sistema:** EmuELEC 4.7 "Nexus" de fábrica, kernel sunxi 3.4.39. O fonte do
  fork não é público, então só se trocam arquivos das partições.
- **ABI da base**, que todo binário novo precisa respeitar: armhf (ARMv7-A,
  VFPv4 + NEON, hard-float), **glibc 2.36** (`GLIBC_` até 2.36) e **libstdc++
  6.0.29** (GCC 11, `GLIBCXX_` até 3.4.29). Um core C++ compilado com GCC mais
  novo precisa de `-static-libstdc++` ou de GCC 11.
- **Sem overlayfs:** o kernel 3.4.39 não tem overlayfs (nenhuma string do driver
  no binário da p6; os módulos do SYSTEM são de um kernel 5.10). Todo
  `tmp-*.mount` (`tmp-cores`, `tmp-shaders`, `tmp-assets`...) falha no boot e a
  pasta em `/tmp` fica vazia. No lugar, o `emuelec_autostart.sh` copia o SYSTEM
  para a p8 a cada boot com `rsync -a --ignore-existing` (`/usr/lib/libretro` em
  `/storage/cores`, `/usr/share/common-shaders` em `/storage/shaders`, e também
  assets, database, joypads e overlays), e **nunca atualiza** um arquivo que já
  existe na p8: depois de gravar um `system` novo, um arquivo de mesmo nome fica
  com a versão do build anterior até alguém regravá-lo.
- **Cores libretro:** o `emuelecRunEmu.sh` da base carrega
  `/storage/cores/<core>_libretro.so` (a cópia da p8). Um core recompilado com o
  mesmo nome não chega a um cartão que já tem o arquivo; use nome novo ou regrave
  a cópia da p8 num serviço de boot. A lista de cores
  de cada sistema vem do `es_systems.cfg`: o ES lê a cópia em
  `/storage/.config/emulationstation/`, e o SYSTEM tem outra em
  `/usr/config/emulationstation/`.
- **Ports:** o ES lê o sistema `ports` de `/storage/roms/ports_scripts`, a pasta
  FAT32 da p1. O `mount_romfs.sh` tenta montar ali um overlay com
  `lowerdir=/usr/bin/ports` e `upperdir=/storage/.config/emuelec/ports`, mas
  `/usr/bin/ports` não existe na base, então o mount falha e a pasta da p1 fica
  visível. Nenhuma feature cria `/usr/bin/ports`: isso ativa o overlay e esconde
  os ports que o usuário põe pelo PC. Para sobreviver a `--keep-roms`, guarde a
  cópia mestre no SYSTEM e restaure na p1 com um serviço de boot
  `Before=emustation.service` que espera `/storage/roms` virar ponto de montagem.
- **Boot e ES:** o `emuelec-autostart.service` (oneshot) roda o `mount_romfs.sh`
  e, no fim, `systemctl start emustation` de forma síncrona. Um serviço com
  `After=emuelec-autostart.service` e `Before=emustation.service` trava o boot
  no splash para sempre (o ES espera o serviço, que espera o autostart, que
  espera o ES).
- **Shaders no EmuELEC:** a lista "SHADER SET" do ES vem de `emuelec-utils
  getshaders` (`find /tmp/shaders -name '*.glslp'`), e o valor escolhido vai para
  `<sistema>.shaderset` no `emuelec.conf` (p8). O próprio binário do ES escreve
  `video_shader`/`video_shader_enable` no `retroarch.cfg` antes do jogo; o ramo
  `shaderset` do `setsettings.sh` só imprime para `true`/`1` e não serve. O
  RetroArch é o 1.17: **sem `video_shader_enable = "true"` nenhum shader vale**,
  nem preset automático, e o `emuelecRunEmu.sh` apaga essa linha depois de cada
  jogo, então ela só existe quando há `shaderset`. O preset automático de core é
  procurado em `rgui_config_directory` (no nosso `retroarch.cfg` é `/config`, que
  não existe), na pasta do `retroarch.cfg` (`/storage/.config/retroarch/<core>/`)
  e em `video_shader_dir/presets` (`/storage/shaders/presets/`). Os scripts estão
  no SYSTEM; leia-os com `mcopy` e `unsquashfs -cat` na imagem do build, sem
  montar. Veja a Decisão 11 na `design.md` da change `shader-gba-vivo-r36s`.
- **Ordem dos presets automáticos:** em cada pasta de busca o RetroArch tenta
  jogo, pasta do conteúdo (`<core>/gba.glslp`, para ROMs em `roms/gba`) e só
  depois core (`<core>/<core>.glslp`). Um preset por pasta salvo pelo menu passa
  na frente do que o `r36-shader-gba-prepara` cria. A linha `Specific shader
  preset found at` do `emuelec.log` (p8, `.config/emuelec/logs/`, legível sem
  root) diz qual valeu; o log é sobrescrito a cada jogo.
- **Vídeo e som no RetroArch:** contexto `fbdev_mali` (o vsync depende só do
  driver da Mali) e áudio `sdl2` síncrono (`audio_sync` e `audio_rate_control`
  ligados na base; a feature `46-audio` sobe `audio_latency` de 64 para 96 e baixa
  `audio_resampler_quality` de 2 para 1 contra os pipocos). `video_threaded`
  tem de ficar `true`: trocar pelo menu trava o aparelho, o RetroArch grava o
  `retroarch.cfg` na hora, e sem a thread o som fica ruim.
- **Cadeia de ganho do som:** o codec é o `sunxi-pcm-codec` (A33). O ganho de
  saída é um só, analógico: o `speaker volume control` (0 a 63, sem dB) e o
  `Headphone_Volume_Control` do codec andam juntos. O FEX traz
  `DAC_VOL_CTRL_SPK`/`_HEADPHONE` = `0x8d8d`, mas com som tocando esse valor não
  aparece em nenhum registrador e o DAC toca em 0 dB (`DAC_Digital_Part_Control` =
  `0x105`): não há ganho digital a mover. O driver zera o `speaker volume control`
  e o `headphone volume control` ao fechar o stream e devolve o valor ao abrir, então
  um 0 lido com o aparelho parado é o estado ocioso. O registrador do codec se lê em
  `/sys/devices/platform/sunxi-pcm-codec/audio_reg_debug/audio_reg` (o
  `audio_reg_debug` é um diretório). Os botões de volume (`udt_events.sh`) só mexem
  no `speaker volume control`, com `(v*43+50)/100 + 20` (20 a 63; o volume 0 não
  silencia), e nenhum script aplica o `audio.volume` no boot. O `Speaker Function`
  tem os nomes trocados neste clone (`spk` com fone, `h2w/state` 1 ou 2). A feature
  `46-audio` centraliza isso no `/usr/lib/r36/audio-ganho` (`aplica`, `volume <v>`),
  que silencia o volume 0 e aplica o volume salvo (em `r36-audio.volume`, p8; o ES
  regrava o `emuelec.conf` com o `audio.volume` antigo ao reiniciar pelo menu, então
  o `emuelec.conf` não é fonte confiável), chamado depois de cada
  `Speaker Function` (boot, abrir e sair de jogo, acordar); qualquer script novo
  que mexa em volume ou em `Speaker Function` deve chamá-lo. O arquivo
  `r36-audio-original` na raiz da p1 volta ao som de fábrica. O `r36-audio.log` e o
  `r36-audio-dac.log` (p1) só leem o codec.
- **Shaders e `/tmp/shaders`:** o menu do RetroArch lista `video_shader_dir`
  (`~/shaders` = `/storage/shaders`, p8). O "SHADER SET" do ES lista
  `/tmp/shaders`, que fica vazio sem overlay; o `r36-shader-gba-prepara` monta
  `/storage/shaders` ali por bind (`mount -o bind`) quando nada está montado.
- **Shader novo:** siga a capability `retroarch-shaders` (até o arquivamento da
  change `shader-gba-vivo-r36s`, a spec delta dela; depois,
  `openspec/specs/retroarch-shaders/spec.md`), que fixa custo, formato,
  parâmetros, pipeline de cor, ativação no boot e verificação.
- **Medir shader no PC:** o RetroArch do PC não captura o shader direito
  (imagem ampliada e esticada), então os cenários de qualidade visual saem de
  uma réplica numérica em `openspec/changes/shader-gba-vivo-r36s/verificacao/`
  (`uv run --with pillow --with numpy python -I replica.py ...`). Tempo de quadro
  e precisão `mediump` do Mali-400 só se medem no aparelho. Exemplos para o
  usuário olhar vão em `var/` (no `.gitignore`).
- **Imagem base:** `base/R36S GA36-MB V1.2-20260416 - Emuelec - No ROMS.img`
  (sha256 em `config/base.toml`), do post
  <https://www.reddit.com/r/R36S/comments/1w2i8em/r36s_ga36mb_v1220260416_emuelec_no_roms/>.
  Nunca é modificada.

## O cartão no PC

Instruções para o usuário rodar (você não roda `sudo`; veja as regras acima).

- **Terminal:** o usuário usa **zsh** e roda o `sudo` num terminal normal, não pelo
  `!` do agente (ele não tem tty e o `sudo` falha pedindo senha). Em comandos com
  glob, aspe o padrão (`--include='*.glslp'`), senão o zsh responde "no matches
  found". Dê os comandos um por linha, copiáveis.
- **Pontos de montagem:** use `/run/media/douglas/<RÓTULO>` (`R36-ROMS`,
  `R36-BOOT`, `R36-SYSTEM`, `R36-STORAGE`), o mesmo padrão do automount. Prefira
  `udisksctl mount -b /dev/sdcN`, que não precisa de `sudo`. Só use
  `sudo mount` quando for preciso (a p8 ext4 tem arquivos do root, ou `-o ro`);
  nesse caso crie a pasta em `/run/media/douglas/<RÓTULO>` e desmonte no fim. A
  letra do dispositivo muda com a porta e o leitor: confira antes com
  `lsblk -o NAME,SIZE,LABEL,FSTYPE,MOUNTPOINT`.
- **p1 (`R36-ROMS`, FAT32) sem montar:** se o `lsblk` a mostra sem rótulo nem
  FSTYPE, o `udisksctl` diz "not a mountable filesystem" ou o kernel avisa
  `Invalid FSINFO signature` / `Volume was not properly unmounted`, o **primeiro**
  passo é `sudo fsck.vfat -a /dev/sdc1` (com a partição desmontada), antes de
  imagem bruta, regravação ou `--wipe-roms`. Já recuperou a p1 com as ROMs
  intactas depois de uma gravação interrompida. `sudo fsck.vfat -n` só mostra o
  diagnóstico. Depois remonte, confira (`unzip -t`, `diff`) e só então regrave.
- **Gravação que falha na verificação** (`verificação pós-gravação falhou em:
  system`) ou erros `I/O error, dev sdc`, `reset high-speed USB device` e
  `device offline` no `journalctl -k`: é leitor, cartão ou conexão, não o build.
  O `system.img` do build é íntegro (confira o sha256 no `manifest.json`). Use
  porta USB direta do PC, sem hub, ou outro leitor, e regrave só o `system`
  (`./flash.sh --device /dev/sdc --part system --build <ts>`). Não grave em
  leitor que acabou de derrubar a conexão sem antes checar as partições.
- **Conferir ROMs sem enganar-se com o cache:** logo depois de uma queda de USB o
  cache de páginas pode servir dados diferentes dos do disco (`diff` e `unzip -t`
  acusam erro que não existe). Compare lendo direto do disco:
  `dd if=<arquivo> iflag=direct bs=4M | cmp - <cópia>`. Se o cartão for retirado
  no meio, a comparação inteira perde o sentido: o kernel registra `detected
  capacity change from ... to 0`.
- **Backup da p1:** `rsync -rt /run/media/douglas/R36-ROMS/ /mnt/backup/games/roms/`
  (`-rt`, não `-a`: a FAT não guarda dono nem permissão). A cópia bruta é
  `sudo dd if=/dev/sdc1 of=/mnt/backup/games/r36-roms.img bs=4M conv=noerror,sync`.
  Antes de qualquer gravação em cartão suspeito, salve também a p8 (saves) em
  `/mnt/backup/games/r36-storage/`.
- **A p8 vence o SYSTEM nos shaders:** sem overlay, o shader que vale é a cópia
  da p8 em `/storage/shaders` (ou o arquivo que um preset referencia). Uma cópia
  velha de `gba/gba-modern-remaster.*` ou um preset em
  `/storage/.config/retroarch/<core>/` ou `config/<core>/` mantém a versão antiga,
  e gravar só o `system` não a remove. O `r36-shader-gba-prepara.service` (feature `54-shaders-gba`) regrava, a
  cada boot, a cópia da p8 que difere da do SYSTEM com o conteúdo do SYSTEM, apaga
  os presets que só a referenciam, e liga o shader por padrão no GBA (`gba.shaderset=...` no `emuelec.conf`, se a
  chave não existe, e `<core>/<core>.glslp` em `config/` e na pasta do
  `retroarch.cfg`, com `#reference` ao arquivo do SYSTEM); o arquivo `r36-gba-sem-shader` na raiz da p1 desliga o padrão e o
  `r36-shader-gba.log` na p1 mostra o que o serviço fez. Valores de parâmetros salvos pelo RetroArch num preset valem mais
  que os padrões do `#pragma parameter`. Para investigar a p8 sem alterar nada:
  `udisksctl mount -b /dev/sdc8` (ou `sudo mount -o ro`).
