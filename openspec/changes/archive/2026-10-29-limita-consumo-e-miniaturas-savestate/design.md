# Design

## Context

Ver `proposal.md` (Why). Fatos levantados no `SYSTEM` e nas configurações da base EmuELEC 4.7:

- **Save States e miniaturas no EmulationStation (`usr/bin/emulationstation`):**
  - Em `SaveStateConfig::getDefaultSaveStateConfig()` (`0x148700..0x148998`), quando não há `es_savestates.cfg`, o EmulationStation usa `directory = "{{system}}"` (ou seja, `/storage/roms/savestates/<sistema>`), `defaultCoreDirectory = false` (`0x1488ac`), `file = "{{romfilename}}.state{{slot}}"` e `image = "{{romfilename}}.state{{slot}}.png"`.
  - O `setsettings.sh` (linhas 35–38) grava `savestates_in_content_dir = false` e `savestate_directory = "/storage/roms/savestates/${PLATFORM}"` no `retroarch.cfg`, mas tem o `#mkdir -p "/storage/roms/savestates/${PLATFORM}"` comentado (linha 34). O binário do ES chama `mkdir("/storage/roms/savestates/<sistema>", 0755)` (em `0x515e0`, sem `-p`), que falha com `ENOENT` se `/storage/roms/savestates` não existir na p1.
  - O `retroarch.cfg` de fábrica traz `savestate_thumbnail_enable = "true"`, `video_gpu_screenshot = "false"` e **`sort_savestates_enable = "true"`** (linha 3130). Com `sort_savestates_enable = "true"`, o RetroArch grava `<rom>.state` e `<rom>.state.png` em `/storage/roms/savestates/<sistema>/<Nome do Core>/`, onde o ES nunca procura.
  - Em `SaveState::setupSaveState` (`0x13cd74` e `0x13d2e4`), o ES monta os argumentos na ordem `-autosave <0|1> -state_slot <X> -state_file "<caminho>"` (ou só `-autosave 1` para o slot Auto). Já o `emuelecRunEmu.sh` (linhas 425–432) só entra no `if` quando há ambos `-state_slot` e `-autosave` e corta `CONTROLLERCONFIG` em `%% -state_slot*`, deixando `-autosave <0|1>` preso dentro de `CONTROLLERCONFIG`.
- **Serviços systemd na base (`usr/lib/systemd/system/*.wants/`):**
  - `sysinit.target.wants/systemd-timesyncd.service` (`Restart=always`) e `systemd-timesyncd-setup.service` sobem o daemon NTP em todo boot num aparelho sem rede.
  - `multi-user.target.wants/pulseaudio.service` sobe `/usr/bin/pulseaudio --system --disallow-exit --exit-idle-time=-1 --realtime` em todo boot; segundos depois, `emustation.service` roda `ExecStartPre=emustation-config` -> `set_audio default` -> `rr_audio.sh alsa` -> `systemctl stop pulseaudio`. Nenhuma unidade requer `pulseaudio.service` nem `systemd-timesyncd.service`.
- **Netplay e drivers sem hardware:**
  - `emuelecRunEmu.sh` (linhas 438–440) roda 3 `set_ee_setting "netplay.*"` (`grep` + `sed -Ei` no `emuelec.conf` da p8) antes de todo jogo Libretro, mesmo sem flag de netplay.
  - `retroarch.cfg` traz `wifi_enabled = "true"`, `wifi_driver = "connmanctl"`, `bluetooth_driver = "bluetoothctl"`, `microphone_driver = "alsathread"` e `midi_driver = "alsa"`.

## Goals / Non-Goals

**Goals:**
- Fazer os save states e suas miniaturas `.png` funcionarem de ponta a ponta entre RetroArch e EmulationStation (tanto em cartão novo quanto em cartão atualizado com `--keep-storage` / `--part system`, migrando saves já criados em subpastas de core).
- Eliminar processos residentes inúteis (`systemd-timesyncd`), inicialização descartada no boot (`pulseaudio`), reescritas desnecessárias do `emuelec.conf` a cada jogo (`netplay.*`) e drivers/menus sem hardware no RetroArch.

**Non-Goals:**
- Ativar `video_gpu_screenshot = "true"` (no Mali-400 `glReadPixels` trava quadros; `video_gpu_screenshot = "false"` usa o framebuffer de software da CPU, que é instantâneo).
- Substituir o `setsettings.sh` da base (592 linhas).

## Decisions

### D1: `sort_savestates_enable = "false"` no `retroarch.cfg` e migração no `retroarch-prepara`
Em vez de criar um `es_savestates.cfg` customizado (que dependeria de casar o nome exato de `library_name` de cada core), desligamos `sort_savestates_enable` (`"false"`) no `retroarch.cfg` da feature `10-ptbr-sao-paulo` e aplicamos a mesma troca no `retroarch-prepara` (feature `56-retroarch-ajustes`) quando o valor ainda é `"true"`. Assim o RetroArch grava `<rom>.state` e `<rom>.state.png` direto em `/storage/roms/savestates/<sistema>/`, que é o caminho esperado por `setsettings.sh` e pelo `SaveStateRepository` do ES.
Para aproveitar os save states e miniaturas que o usuário já salvou antes desta change, o `retroarch-prepara` (depois que `/storage/roms` está montado) garante `mkdir -p "$ROOT/storage/roms/savestates"` e percorre `$ROOT/storage/roms/savestates/*/*/*.state*`, movendo cada arquivo para a pasta-mãe `/storage/roms/savestates/<sistema>/` se ainda não existir arquivo de mesmo nome lá, e remove subpastas de core que ficarem vazias (`rmdir`).
- *Alternativa descartada:* `defaultCoreDirectory` em um `es_savestates.cfg`. O `setsettings.sh` não usa subpasta de core e vários sistemas têm múltiplos cores (ex.: `snes9x2005_plus_a33` vs `snes9x2010`), o que esconderia saves ao trocar de core.

### D2: Criação de `/storage/roms/savestates/${PLATFORM}` e parser de `-autosave`/`-state_slot` no `emuelecRunEmu.sh`
No ramo `elif [ ${LIBRETRO} == "yes" ]; then` do `emuelecRunEmu.sh` (feature `10-ptbr-sao-paulo`), adicionamos `mkdir -p "/storage/roms/savestates/${PLATFORM}"` e ajustamos o parser de `CONTROLLERCONFIG` / `SNAPSHOT`:
- Cortar de `CONTROLLERCONFIG` qualquer sufixo a partir de ` -autosave`, ` -state_slot`, ` -state_file` ou ` --`.
- Extrair `SNAPSHOT` quando `-state_slot` estiver presente (`SNAPSHOT="${arguments#*-state_slot }"`, `SNAPSHOT="${SNAPSHOT%% *}"`).
- Quando `-autosave 1` for passado sem `-state_slot` (abertura do `AUTO SAVE` pelo Save State Manager do ES), `SNAPSHOT` recebe `"0"`. O `setsettings.sh` zera `savestate_auto_load`/`savestate_auto_save` quando `SNAPSHOT` é vazio; com `SNAPSHOT` não vazio grava os dois em `"true"` e `state_slot = "0"`, que é o mesmo `state_slot` do ramo vazio. O resultado é o mesmo de reaplicar as duas chaves depois do `setsettings.sh`, sem mexer nas linhas vizinhas do `shaderset-aplica` (zona da change de idioma, matriz D2 da `integra-limite-idioma-shaders-gb`).
- O parser corta o `CONTROLLERCONFIG` em cada marcador (`-autosave`, `-state_slot`, `-state_file`, `--`) e lê o slot pela última ocorrência de ` -state_slot `, então aceita também a ordem antiga (`-state_slot X -autosave 1`). As strings do binário (` -autosave 1 -state_slot `, ` -autosave 0 -state_slot `, ` -state_file "`, ` -autosave 1`) foram conferidas no `usr/bin/emulationstation` da base.
- O `mkdir -p` vem logo depois do parser, ainda antes do `setsettings.sh`.

### D3: Guarda no bloco Netplay do `emuelecRunEmu.sh` e chaves `=0` no `emuelec.conf`
No `emuelecRunEmu.sh`, envolvemos todo o bloco `# Netplay ... # End netplay` num `if [[ "${arguments}" == *"--host"* ]] || [[ "${arguments}" == *"--connect"* ]] || [[ "${arguments}" == *"--netplaymode"* ]]; then`. Em partidas locais (100% dos casos no R36S sem rede), nenhuma das 3 chamadas `set_ee_setting "netplay.*"` roda. O bloco não é reindentado, para o diff contra a base ficar em duas linhas (`if` e `fi`). No `emuelec.conf` da feature 10, `ee_ssh.enabled`, `controllers.bluetooth.enabled`, `updates.enabled`, `global.netplay` e `global.rewind` ficam em `0`.

### D4: Remoção de links do systemd em `41-servicos-enxutos`
Seguindo a decisão da change `otimizacoes-sistema` (remover apenas os symlinks em `*.wants/`, preservando units e binários), adicionamos três blocos `[[remove]]` em `features/41-servicos-enxutos/feature.toml`:
- `usr/lib/systemd/system/sysinit.target.wants/systemd-timesyncd.service`
- `usr/lib/systemd/system/sysinit.target.wants/systemd-timesyncd-setup.service`
- `usr/lib/systemd/system/multi-user.target.wants/pulseaudio.service`

### D5: Drivers `"null"` e ocultação de menus no `retroarch.cfg` e no `retroarch-prepara`
Atualizamos no `retroarch.cfg` da feature 10 e na função `troca` do `retroarch-prepara` (feature 56):
- Drivers: `wifi_enabled` (`"true"` -> `"false"`), `wifi_driver` (`"connmanctl"` -> `"null"`), `bluetooth_driver` (`"bluetoothctl"` -> `"null"`), `microphone_driver` (`"alsathread"` -> `"null"`), `midi_driver` (`"alsa"` -> `"null"`).
- Visibilidade de menus: `menu_show_rewind`, `menu_show_online_updater`, `quick_menu_show_download_thumbnails`, `quick_menu_show_start_recording`, `quick_menu_show_start_streaming`, `settings_show_network`, `settings_show_achievements` e `settings_show_ai_service` (`"true"` -> `"false"`).

## Risks / Trade-offs

- [Algum port ou script chama `systemctl stop pulseaudio`] → `systemctl stop` em unidade inativa retorna `0` sem erro.
- [Saves antigos na subpasta do core têm mesmo nome de um save já na raiz do sistema] → A migração no `retroarch-prepara` só move se o arquivo de destino não existir (`[ ! -e "$ dest" ]`), nunca sobrescrevendo save mais novo.

## Migration Plan

1. Funciona tanto em gravação completa quanto em atualização apenas da partição `system` (`./flash.sh --device /dev/sdX --part system`), pois o `retroarch-prepara` aplica as trocas no `retroarch.cfg` da p8 e migra os saves existentes na p1 no primeiro boot.
2. Rollback: reverter as chaves no `retroarch.cfg` / `feature.toml` e regravar `system`.
