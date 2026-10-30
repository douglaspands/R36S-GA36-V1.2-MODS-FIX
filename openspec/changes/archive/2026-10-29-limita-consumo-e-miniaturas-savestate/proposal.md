# Proposal

## Why

O clone do R36S (GA36-MB V1.2, Allwinner A33, 4x Cortex-A7 sem rede nem Wi-Fi) ainda sobe serviços em segundo plano no boot (`systemd-timesyncd` residente na RAM e `pulseaudio` em `--realtime` que é morto segundos depois pelo `emustation-config`), regrava 3 chaves de `netplay.*` no `emuelec.conf` do cartão SD antes de cada jogo Libretro e mantém no `retroarch.cfg` drivers ativos para hardwares inexistentes (Wi-Fi, Bluetooth, microfone e MIDI) e menus de recursos pesados/online (Rewind, Netplay, Streaming, Gravação). Ao mesmo tempo, as miniaturas (`.png`) de Save State no EmulationStation não funcionam hoje porque o `retroarch.cfg` de fábrica traz `sort_savestates_enable = "true"` (gravando `.state` e `.state.png` numa subpasta com o nome do core, enquanto o EmulationStation procura direto em `/storage/roms/savestates/<sistema>/`), falta `mkdir -p` da pasta de savestates por sistema e o parser de `-autosave`/`-state_slot` do `emuelecRunEmu.sh` espera os argumentos na ordem inversa da que o binário do ES envia.

## What Changes

- **Miniaturas e Save States funcionando no EmulationStation:**
  - Manter `savestate_thumbnail_enable = "true"` e mudar `sort_savestates_enable` de `"true"` para `"false"` no `retroarch.cfg` (camada `storage` da feature `10-ptbr-sao-paulo`) e no script de boot `retroarch-prepara` (feature `56-retroarch-ajustes`, para cartões gravados com `--keep-storage` / `--part system`), fazendo o RetroArch gravar `<rom>.state` e `<rom>.state.png` diretamente em `/storage/roms/savestates/<sistema>/`, onde o `SaveStateRepository` do EmulationStation lê.
  - No `retroarch-prepara`, garantir `mkdir -p /storage/roms/savestates` e migrar sem sobrescrever (`mv -n` / cópia segura) arquivos `*.state*` que já estejam em subpastas de core (`/storage/roms/savestates/<sistema>/<core>/`) para `/storage/roms/savestates/<sistema>/`.
  - No `emuelecRunEmu.sh`, garantir `mkdir -p "/storage/roms/savestates/${PLATFORM}"` antes de abrir qualquer jogo Libretro e corrigir a extração de `-autosave`, `-state_slot` e `-state_file` de `CONTROLLERCONFIG` e `SNAPSHOT` na ordem emitida pelo binário do EmulationStation.
- **Enxugamento de serviços no Systemd (`41-servicos-enxutos`):**
  - Remover os links de ativação `sysinit.target.wants/systemd-timesyncd.service`, `sysinit.target.wants/systemd-timesyncd-setup.service` e `multi-user.target.wants/pulseaudio.service`.
- **Corte de gastos com Netplay, rede e recursos sem hardware no EmuELEC e RetroArch:**
  - No `emuelec.conf`: declarar `ee_ssh.enabled=0`, `controllers.bluetooth.enabled=0`, `updates.enabled=0`, `global.netplay=0` e `global.rewind=0`.
  - No `emuelecRunEmu.sh`: executar a limpeza `set_ee_setting "netplay.*"` no `emuelec.conf` apenas quando o jogo for iniciado com argumentos de netplay (`--host`, `--connect` ou `--netplaymode`), evitando 3 escritas `sed -Ei` no cartão SD a cada partida normal.
  - No `retroarch.cfg` e no `retroarch-prepara`: definir `wifi_enabled = "false"` e `wifi_driver`, `bluetooth_driver`, `microphone_driver` e `midi_driver` como `"null"`, e ocultar no menu RGUI os itens de recursos sem rede ou que comem desempenho (`menu_show_rewind`, `menu_show_online_updater`, `quick_menu_show_download_thumbnails`, `quick_menu_show_start_recording`, `quick_menu_show_start_streaming`, `settings_show_network`, `settings_show_achievements` e `settings_show_ai_service` em `"false"`).

## Capabilities

### New Capabilities
- `savestate-thumbnails`: Gravação de save states e miniaturas `.png` pelo RetroArch diretamente em `/storage/roms/savestates/<sistema>/`, migração de saves em subpastas de core no boot e carregamento de slots pelo Save State Manager do EmulationStation.

### Modified Capabilities
- `system-services`: Desativação no boot de `systemd-timesyncd.service`, `systemd-timesyncd-setup.service` e `pulseaudio.service`, desativação de chaves de rede/atualização/rewind no `emuelec.conf` e omissão de escritas de `netplay.*` no `emuelec.conf` em jogos locais.
- `retroarch-menu`: Drivers de periféricos inexistentes (`wifi`, `bluetooth`, `microphone`, `midi`) em `"null"` e ocultação de menus de rede, gravação, streaming e rewind no RetroArch, aplicados tanto na imagem quanto no boot via `retroarch-prepara`.

## Impact

- `features/41-servicos-enxutos/feature.toml`: remoção dos 3 links de ativação do systemd (`pulseaudio`, `systemd-timesyncd`, `systemd-timesyncd-setup`).
- `features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf`: chaves `ee_ssh.enabled`, `controllers.bluetooth.enabled`, `updates.enabled`, `global.netplay` e `global.rewind` em `0`.
- `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`: criação de `/storage/roms/savestates/${PLATFORM}`, correção do parser de `-autosave`/`-state_slot`/`-state_file` e guarda condicional no bloco de `netplay`.
- `features/10-ptbr-sao-paulo/storage/.config/retroarch/retroarch.cfg` e `features/56-retroarch-ajustes/system/usr/lib/r36/retroarch-prepara`: `sort_savestates_enable = "false"`, `savestate_thumbnail_enable = "true"`, drivers sem hardware em `"null"`, visibilidade de menus enxuta e migração de saves de subpastas de core no boot.
- Testes em `tests/test_otimizacoes.py`, `tests/test_ptbr_controle.py` e `tests/test_retroarch_ajustes.py`.
