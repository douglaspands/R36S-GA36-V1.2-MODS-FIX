# CLAUDE.md

Fábrica de imagens de cartão SD para o clone do R36S (GA36-MB V1.2, Allwinner A33).
O `README.md` explica o uso; este arquivo guarda as regras de trabalho e os fatos
do aparelho que não se deduzem do código.

## Regras de trabalho

- **Shell e modo auto:** o Antigravity opera em modo auto. Comandos de terminal devem
  usar caminhos relativos à raiz do projeto, um por chamada direta, sem `cd`, sem
  encadear com `&&` ou `;`, sem pipes complexos e sem comandos inline `python -c`
  multilinha. Proibido usar laços (`for`, `while`), substituições (`$(...)`, backticks)
  ou variáveis (`$VAR`). Para ler ou alterar arquivos no projeto, use SEMPRE as
  ferramentas nativas do harness (`read_file`, `edit_file`, `write_file`), que são
  pré-aprovadas e não acionam prompts de permissão. Não use utilitários de shell
  (`cat`, `grep`, `sed`, `awk`, `find /`, `chmod`, `curl`) para inspeção de arquivos ou
  sistema. Lógica não destrutiva, iterações e downloads vão exclusivamente em scripts
  Python dedicados (`uv run python -I script.py`).
- **Sem sudo**, em nenhuma forma, nem indireta (`./flash.sh --device` chama
  `sudo dd`). Para validar uma gravação, use `./flash.sh --target-file`. O que
  precisar de root ou do cartão real vira instrução para o usuário rodar.
- **Python via uv:** `uv run`, `uv add`, `uv sync`. Nada de `pip`, venv manual ou
  `python3` direto (se `uv` não estiver acessível na sandbox, fallback para `python3 -I`).
  Testes: `uv run python -I -m unittest discover -s tests`.
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
  `<sistema>.shaderset` no `emuelec.conf` (p8). Quem grava
  `video_shader`/`video_shader_enable` no `retroarch.cfg` antes do jogo é o
  `/usr/lib/r36/shaderset-aplica` (feature `56-retroarch-ajustes`), chamado pelo
  `emuelecRunEmu.sh`: o ramo `shaderset` do `setsettings.sh` só imprime para
  `true`/`1` e não serve, e o ES não grava nada. O RetroArch 1.17 **ignora o
  `video_shader` do `retroarch.cfg`** quando o jogo não tem preset automático (SNES, por
  exemplo): o preset só entra por `--set-shader`, e por isso o `shaderset-aplica` também
  imprime `--set-shader "/tmp/shaders/<preset>"`, que o `emuelecRunEmu.sh` põe em
  `SHADERSET` antes do `--config`. O
  RetroArch é o 1.17: **sem `video_shader_enable = "true"` nenhum shader vale**,
  nem preset automático, e o `emuelecRunEmu.sh` apaga essa linha depois de cada
  jogo, então ela só existe quando há `shaderset`. O preset automático de core é
  procurado em `rgui_config_directory` (de fábrica `/config`, que não existe numa
  raiz somente leitura e fazia salvar pelo menu dar erro; o `r36-retroarch-prepara`
  e o `retroarch.cfg` da feature 10 usam `~/.config/retroarch/config`; `/saves`,
  `/logs` e `/overlays/keyboards` também foram trocados por pastas da p8), na pasta do `retroarch.cfg` (`/storage/.config/retroarch/<core>/`)
  e em `video_shader_dir/presets` (`/storage/shaders/presets/`). Os scripts estão
  no SYSTEM; leia-os com `mcopy` e `unsquashfs -cat` na imagem do build, sem
  montar. Veja a Decisão 11 na `design.md` da change `shader-gba-vivo-r36s`.
- **Idioma do RetroArch:** o `/usr/lib/r36/idioma-aplica` (feature
  `56-retroarch-ajustes`), chamado pelo `emuelecRunEmu.sh` ao lado do
  `shaderset-aplica`, lê `system.language` do `emuelec.conf` e `Language` do
  `es_settings.cfg` e grava `user_language` no `retroarch.cfg`
  (`pt_BR`=7, `pt_PT`=8, `en_US`/`en_GB`=0, `es_ES`=3, `fr_FR`=2, `de_DE`=4,
  `it_IT`=5; números da enumeração `RETRO_LANGUAGE_*`, conferidos no `retroarch`
  1.17.0 do SYSTEM). **Só ajusta quando o idioma do EmuELEC muda** desde o último
  jogo: o valor de **cada fonte** fica em duas linhas de
  `/storage/.config/retroarch/r36-idioma` (p8), cada fonte é comparada com o próprio
  valor, a que mudou vale e o `emuelec.conf` vence se as duas mudaram (gravar o par
  atual evita oscilar entre fontes divergentes). Uma escolha feita no menu do
  RetroArch vale até a próxima troca no EmuELEC. No caminho comum só lê três arquivos,
  sem processo novo nem escrita no SD. Idioma fora da tabela não mexe no
  `retroarch.cfg`. Onde o ES grava a troca de idioma pelo menu (`emuelec.conf` ou só
  `es_settings.cfg`) ainda não foi visto no aparelho (task 1.1 da change
  `retroarch-idioma-do-emuelec`).
- **Idioma do build:** `./build.sh --idioma <código>` (padrão **`en_US`**; um
  `./build.sh` sem argumento sai em inglês, e português pede `--idioma pt_BR`) troca
  `system.language`, `Language` e `user_language` nas cópias em `work/`; os arquivos da
  feature 10 no repositório ficam em `pt_BR`. O idioma entra no nome da imagem
  (`<prefixo>_<idioma>_build_<timestamp>[-test].img.xz`, `en-us`/`pt-br`), no manifest
  (`"language"`) e no `R36-BUILD.txt` (`idioma:`); o diretório de saída continua
  `<timestamp>[-test]`. Só sai sem idioma se `--features` não traz os arquivos de idioma
  e `--idioma` não foi passado (ou com `--no-features`). Os builds para o aparelho do
  usuário (criança que lê português) são `./build.sh --idioma pt_BR`.
- **Localização da interface (ES):** a feature `10-ptbr-sao-paulo` fornece os
  catálogos completos `pt_BR` e `es_MX` (`.po` e `.mo` compilados) em
  `/usr/config/emuelec/configs/locale/` (SYSTEM), traduzindo 100% das mensagens do
  EmulationStation sem fallback órfão em inglês. Preserva termos técnicos gamer em
  inglês (*Save State*, *Core*, *Shader*, *Bezel*, *BIOS*, *ROMs*, *RetroAchievements*,
  *Scraper*, *Hotkey*, *Netplay*, *Rewind*) e formata menus de ordenação e diálogos
  concisamente para caber na resolução de 640x480 (3.5").
- **Tema Epic Cody ML:** o tema padrão do sistema é o `Epic Cody ML` (feature
  `50-temas-extras`), instalado sob `.config/emulationstation/themes/Epic Cody ML`
  (p8), substituindo o `Epic Cody` upstream para poupar ~180 MiB. Desacopla os textos de
  todos os consoles em variáveis `${sistema.*}` lidas de `_languages/` (`pt-br.xml`,
  `es-latam.xml` e `en.xml`). O seletor `<subset name="language">` traz `pt-br` como
  primeira opção, ativando português nativamente no primeiro boot sem exigir ajuste
  manual.
- **Ordem dos presets automáticos:** em cada pasta de busca o RetroArch tenta
  jogo, pasta do conteúdo (`<core>/gba.glslp`, para ROMs em `roms/gba`) e só
  depois core (`<core>/<core>.glslp`). Um preset por pasta salvo pelo menu passa
  na frente do que o `r36-shader-gba-prepara` cria. A linha `Specific shader
  preset found at` do `emuelec.log` (p8, `.config/emuelec/logs/`, legível sem
  root) diz qual valeu; o log é sobrescrito a cada jogo.
- **Shaders do GB e do GBC:** a feature `55-shaders-gb-gbc` liga o `gb-modern-dmg` e o
  `gbc-modern-remaster` por padrão com o `r36-shader-gb-gbc-prepara.service`
  (`After=r36-shader-gba-prepara.service`: os dois escrevem no `emuelec.conf` e montam
  `/tmp/shaders`, então rodam em série). Como `gb` e `gbc` dividem os cores (e `mGBA`,
  `VBA-M` e `VBA Next` também servem o `gba`), os presets são **por pasta de conteúdo**
  (`<Core>/gb.glslp`, `<Core>/gbc.glslp`), nunca `<Core>/<Core>.glslp`, que valeria
  também para o GBA. Chaves na p1: `r36-gb-sem-shader` e `r36-gbc-sem-shader`. As opções
  de cor do Gambatte vão em `config/Gambatte/gb.opt` (`gambatte_gb_colorization =
  "disabled"`) e `gbc.opt` (`gambatte_gbc_color_correction = "disabled"`), só se a chave
  não existe; um `.opt` por pasta substitui o `Gambatte.opt` global naquela pasta, então
  um `.opt` novo herda o `Gambatte.opt` (sem a chave de cor). Não
  confirmado no aparelho: se o RetroArch 1.17 acha o preset por pasta com ROM em `.zip`
  (os `es_systems.cfg` de gb e gbc listam `.zip` e `.7z`; não se sabe se o core abre o
  arquivo direto ou se o RetroArch o extrai para outra pasta); o `--set-shader`
  do `shaderset-aplica` cobre o caso. Confira pelo `Specific shader preset found at` do
  `emuelec.log`.
- **Shaders de TV (Consoles de Mesa e Arcades):** a feature `57-shaders-tv` instala o shader
  `tv-modern-remaster` (`.glsl` e `.glslp`) em `/usr/share/common-shaders/tv/` (e em `/storage/shaders/tv/`),
  disponível opcionalmente nos menus do EmulationStation e do RetroArch. **Por padrão é DESLIGADO**
  (não cria presets automáticos nem injeta `shaderset` no boot, e remove presets residuais anteriores).
  O shader aplica fusão seletiva de dither horizontal (3 taps) para restaurar 100% da transparência
  analógica de TV (água de Sonic, luzes e sombras de Streets of Rage 2) mantendo bordas de sprites, textos
  e HUD 100% nítidos, scanline milimétrica na grade física de 480p e pipeline ultra-leve de 18 instruções
  para a Mali-400 MP2. Chave opcional na p1: `r36-tv-com-shader` ativa o shader em lote por padrão
  para os sistemas: `megadrive`, `genesis`, `snes`, `nes`, `mastersystem`, `pce`, `pcengine`, `psx`,
  `mame`, `fbneo`, `cps1`, `cps2`, `cps3` e `neogeo`. Diagnóstico condicionado à chave `r36-diagnostico`
  gravado em `r36-shader-tv.log` na p1.
- **Vídeo e som no RetroArch:** contexto `fbdev_mali` (o vsync depende só do
  driver da Mali) e áudio `sdl2` síncrono (`audio_sync` e `audio_rate_control`
  ligados na base; a feature `46-audio` sobe `audio_latency` de 64 para 96 e baixa
  `audio_resampler_quality` de 2 para 1 contra os pipocos). `video_threaded`
  tem de ficar `true`: trocar pelo menu trava o aparelho, o RetroArch grava o
  `retroarch.cfg` na hora, e sem a thread o som fica ruim.
- **Save states e miniaturas:** o ES lê `<rom>.state<N>` e `<rom>.state<N>.png` em
  `/storage/roms/savestates/<sistema>/` (sem `es_savestates.cfg`; o binário cria a
  pasta com `mkdir` sem `-p`). Com `sort_savestates_enable = "true"` (fábrica) o
  RetroArch grava numa subpasta com o nome do core e o ES não vê; a feature 10 e o
  `retroarch-prepara` põem `"false"`. O ES passa o save state depois do
  `--controllers`, na ordem ` -autosave <0|1> -state_slot <X> -state_file "<caminho>"`
  ou só ` -autosave 1` (slot Auto); a cópia do `emuelecRunEmu.sh` corta isso do
  `CONTROLLERCONFIG` e põe o slot em `SNAPSHOT` (`"0"` no slot Auto, porque o
  `setsettings.sh` desliga `savestate_auto_load` quando `SNAPSHOT` é vazio). Se um
  slot escolhido carrega mesmo o arquivo `.state<N>` (e não o `.state.auto`) só se
  confirma no aparelho.
- **Serviços fora do boot:** a `41-servicos-enxutos` tira os links de
  `systemd-timesyncd`, `systemd-timesyncd-setup` e `pulseaudio` (além de IR e cron);
  as units ficam. O bloco de netplay do `emuelecRunEmu.sh` só roda com
  `--host`/`--connect`/`--netplaymode`. As chaves de rede, Bluetooth, atualização e
  rewind do `emuelec.conf` (feature 10) só valem numa p8 nova (`--wipe-storage`).
- **Logs de diagnóstico sob chave:** os logs de áudio (`r36-audio.log`,
  `r36-audio-dac.log`), de bateria (`r36-bateria.log`), de brilho (`r36-brilho.log`) e
  de shader (`r36-shader-gba.log`, também a linha por jogo do `shaderset-aplica`), dos
  shaders do GB/GBC (`r36-shader-gb-gbc.log`), de idioma (`r36-idioma.log`, uma linha
  por jogo do `idioma-aplica`), do
  `r36-retroarch.log` (correção do `retroarch.cfg`) só são gravados na p1 com o arquivo vazio `r36-diagnostico`
  na raiz dela (o registro térmico fica fora). Ao pedir um desses logs ao usuário,
  lembre-o de criar a chave e religar antes de reproduzir o problema. Logs antigos
  não são apagados pelo aparelho. Feature nova que grave log de diagnóstico na p1
  deve usar a mesma chave. Veja a capability `diagnostic-logs`.
- **gpSP sem ghosting:** a feature `56-retroarch-ajustes` põe
  `gpsp_frame_mixing = "enabled"` e `gpsp_boot_mode = "bios"` (Boot to BIOS) no `config/gpSP/gpSP.opt` da p8 se a chave não
  existir (um `gpSP.opt` que já tem `gpsp_boot_mode = "game"` mantém o valor); o arquivo vazio
  `r36-gpsp-sem-ghost` na raiz da p1 remove só a linha do blending.
- **Botão FN:** o driver `udt_joystick` o expõe em
  `/sys/devices/platform/micro_gamepad/fn_key` (código 464, `KEY_FN`, de fábrica).
  O `/usr/lib/r36/fn-remapeia` (feature `20-controle-posicional`, `r36-fn.service`)
  grava 316 (`BTN_MODE`) no boot e, no fim, grava `input_enable_hotkey_btn` no
  `/storage/joypads/micro_gamepad.cfg` da p8 (só essa linha, sem criar o arquivo): `10`
  se a escrita no `fn_key` foi aceita, `8` (o Select) em qualquer outro caso
  (`r36-fn-original`, `sem-fn_key`, escrita recusada). O valor que o `fn_key` devolve na
  leitura **não é o código** (no aparelho voltou `-1088990680` com o 316 gravado): vale o
  sucesso da escrita e o evento 316 no log. O arquivo da feature traz `8`, o
  padrão seguro. Que o 316 é o botão 10 do RetroArch é só hipótese (numeração do
  autoconfig), confirmada no aparelho (o FN abre o menu). O arquivo vazio `r36-fn-original` na raiz da p1 deixa o
  464 e o hotkey em 8. O `emuelecRunEmu.sh` da base traz comentado o ramo do `nds` com
  `echo "318"` (`BTN_THUMBR`) e o `echo "464"` que devolve o FN: se um dia for
  descomentado, sobrescreve o 316. O estado do serviço (`fn_key` antes e depois, uptimes
  `uptime_inicio`, `uptime_fn_key`, `uptime_fim`) fica em `/run/r36-fn.estado`, sem log
  na p1. O `fn_key` só existe depois de o
  `udt_joystick` carregar, bem depois do início do serviço: o `fn-remapeia` espera por
  ele até 60 s (`TimeoutStartSec=120`) e, se não vier, sai com 0 e grava
  `modo=sem-fn_key`. No
  EmulationStation o FN sozinho fica sem função: nenhuma feature traz `es_input.cfg`
  com a entrada `id="10"` do `micro_gamepad` (`tests/test_fn.py` garante). O FN + D-pad
  é lido por fora do ES, pelo `brilho-leitor` (feature `62-brilho-fn`).
- **Brilho da tela:** o backlight é o `/sys/devices/virtual/disp/disp/attr/lcdbl`
  (0 a 255; escala da base `(nível*255+50)/100`). No boot ele é gravado duas vezes pela
  base, as duas antes de a p1 montar: o `lsb_release` (o `show-version.service`, no
  `basic.target`) grava 204, e o `emuelec_autostart.sh` (l.54-56) grava o
  `brightness.level` do `emuelec.conf` antes de chamar o `mount_romfs.sh`. O
  `udt_pwr_events.sh` zera o `lcdbl` ao suspender e o restaura do `emuelec.conf` ao
  acordar; o `emuelecRunEmu.sh` só copia o `brightness.level` para o `screen_brightness`
  do `retroarch.cfg`. A feature `62-brilho-fn` guarda o nível em
  `r36-brilho.level` (p8, ao lado do `emuelec.conf`; o `emuelec.conf` não serve, o ES o
  regrava), com piso 10, passo 5, teto 100 e padrão 80, e o `/usr/lib/r36/brilho-aplica`
  é o único que lê e grava esse nível (`aplica`, `ajusta +|-`, `salva`, `padrao`,
  `boot`); script novo que mexa no `lcdbl` deve chamá-lo. O `r36-brilho.service` espera
  a p1 montar (ordem certa sem `After=`) e aplica o nível; o arquivo
  `r36-brilho-original` na raiz da p1 apaga o nível salvo a cada boot (volta a 80). O
  `udt_pwr_events.sh` (feature 46) chama `brilho-aplica aplica` logo depois de restaurar
  o `lcdbl` no ramo de acordar.
- **D-pad e FN no `evtest`:** o `udt_joystick` cria o dispositivo de entrada
  `micro_gamepad` (e um `udt_keyboard`) só no `insmod` da l.210 do
  `emuelec_autostart.sh`; o número do `eventN` se acha pelo nome em
  `/proc/bus/input/devices`. O FN remapeado chega como `code 316 (BTN_MODE)`. O
  `brilho-leitor` aceita o D-pad como `BTN_DPAD_UP/DOWN`, `KEY_UP/DOWN` ou `ABS_HAT0Y`
  (-1 cima, 1 baixo, 0 solta); a forma real ainda não foi vista no aparelho (o
  `r36-brilho.log`, com `r36-diagnostico`, a registra). Pela numeração do
  `micro_gamepad.cfg` (FN = botão 10, D-pad = 13 a 16) a hipótese é `BTN_DPAD_*`. O
  reset do brilho é FN + clique do L3: pela numeração (L3 = botão 11) a hipótese é
  `BTN_THUMBL` (317), aceito também pelo código; o log registra o que o aparelho emite.
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
  `r36-audio-dac.log` (p1) só leem o codec e só existem com `r36-diagnostico` na p1.
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
  usuário olhar vão em `var/` (no `.gitignore`). As capturas de GB/GBC saem do
  `~/AppImages/retroarch.appimage` com config própria (`--config`) e
  `video_gpu_screenshot = "false"` (quadro do core em 160x144); o PC não tem o Gambatte,
  então elas usam o mGBA com modelo fixo, paleta `Grayscale` e sem correção de cor (veja
  `openspec/changes/shaders-gb-gbc-r36s/verificacao/`).
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
  `r36-shader-gba.log` na p1 (só com `r36-diagnostico`) mostra o que o serviço fez. Valores de parâmetros salvos pelo RetroArch num preset valem mais
  que os padrões do `#pragma parameter`. Para investigar a p8 sem alterar nada:
  `udisksctl mount -b /dev/sdc8` (ou `sudo mount -o ro`).
