# Tasks

## 1. Serviços do systemd em `41-servicos-enxutos`

- [x] 1.1 Em `features/41-servicos-enxutos/feature.toml`, acrescentar `[[remove]]` para `usr/lib/systemd/system/sysinit.target.wants/systemd-timesyncd.service`, `usr/lib/systemd/system/sysinit.target.wants/systemd-timesyncd-setup.service` e `usr/lib/systemd/system/multi-user.target.wants/pulseaudio.service` e atualizar a descrição da feature. Verificar lendo o `feature.toml`.
- [x] 1.2 Em `tests/test_otimizacoes.py`, adicionar asserções garantindo que `41-servicos-enxutos` remove os links de `systemd-timesyncd.service`, `systemd-timesyncd-setup.service` e `pulseaudio.service` sem remover as units originais. Verificar com `uv run python -I -m unittest tests.test_otimizacoes`.

## 2. Configuração do EmuELEC e lançamento no `emuelecRunEmu.sh`

- [x] 2.1 Em `features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf`, definir `ee_ssh.enabled=0`, `controllers.bluetooth.enabled=0`, `updates.enabled=0`, `global.netplay=0` e `global.rewind=0`. Verificar com `grep -E '^(ee_ssh\.enabled|controllers\.bluetooth\.enabled|updates\.enabled|global\.netplay|global\.rewind)=' features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf`.
- [x] 2.2 Em `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`, no ramo Libretro:
  - criar `/storage/roms/savestates/${PLATFORM}` com `mkdir -p`;
  - corrigir a extração de `CONTROLLERCONFIG` e `SNAPSHOT` para cortar `-autosave`, `-state_slot`, `-state_file` e `--` na ordem enviada pelo EmulationStation, preservando o `savestate_auto_load = "true"` quando `-autosave 1` vier sem `-state_slot`;
  - proteger o bloco `# Netplay ... # End netplay` (incluindo os 3 `set_ee_setting "netplay.*"`) para rodar somente quando `${arguments}` contiver `--host`, `--connect` ou `--netplaymode`.
  Verificar com `bash -n features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`.
- [x] 2.3 Em `tests/test_ptbr_controle.py`, cobrir as chaves `=0` do `emuelec.conf`, o `mkdir -p "/storage/roms/savestates/${PLATFORM}"`, a extração de `CONTROLLERCONFIG`/`SNAPSHOT` (com `-autosave` antes de `-state_slot` e com `-autosave 1` sozinho) e a omissão de `set_ee_setting "netplay.*"` sem flag de netplay. Verificar com `uv run python -I -m unittest tests.test_ptbr_controle`.

## 3. Save states, drivers e menus no `retroarch.cfg` e no `retroarch-prepara`

- [x] 3.1 Em `features/10-ptbr-sao-paulo/storage/.config/retroarch/retroarch.cfg`, definir `sort_savestates_enable = "false"` (mantendo `savestate_thumbnail_enable = "true"`), `wifi_enabled = "false"`, `wifi_driver = "null"`, `bluetooth_driver = "null"`, `microphone_driver = "null"`, `midi_driver = "null"`, e colocar em `"false"` as chaves `menu_show_rewind`, `menu_show_online_updater`, `quick_menu_show_download_thumbnails`, `quick_menu_show_start_recording`, `quick_menu_show_start_streaming`, `settings_show_network`, `settings_show_achievements` e `settings_show_ai_service`. Verificar com `grep` no arquivo.
- [x] 3.2 Em `features/56-retroarch-ajustes/system/usr/lib/r36/retroarch-prepara`, aplicar via `troca` no `retroarch.cfg` da p8 a mudança de `sort_savestates_enable` (`"true"` -> `"false"`), dos drivers sem hardware (`wifi_enabled`, `wifi_driver`, `bluetooth_driver`, `microphone_driver`, `midi_driver`) e das 8 chaves de visibilidade de menu, além de criar `/storage/roms/savestates` (quando a p1 estiver montada) e mover sem sobrescrever (`[ ! -e "$dest" ]`) arquivos `*.state*` de subpastas `/storage/roms/savestates/<sistema>/<core>/` para `/storage/roms/savestates/<sistema>/`. Verificar com `sh -n features/56-retroarch-ajustes/system/usr/lib/r36/retroarch-prepara`.
- [x] 3.3 Em `tests/test_retroarch_ajustes.py` e `tests/test_ptbr_controle.py`, adicionar testes cobrindo as novas chaves no `retroarch.cfg`, a atualização de um `retroarch.cfg` de fábrica pelo `retroarch-prepara` e a migração de arquivos `.state` e `.state.png` de subpastas de core sem sobrescrever arquivos existentes. Verificar com `uv run python -I -m unittest tests.test_retroarch_ajustes tests.test_ptbr_controle`.
