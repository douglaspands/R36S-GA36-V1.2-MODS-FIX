# Spec Delta

## ADDED Requirements

### Requirement: Sincronizador NTP e servidor PulseAudio desligados no boot
A imagem gerada SHALL NOT iniciar no boot os serviços `systemd-timesyncd.service`, `systemd-timesyncd-setup.service` nem `pulseaudio.service`.

#### Scenario: Boot sem timesyncd nem pulseaudio
- **WHEN** o aparelho termina o boot
- **THEN** nem `systemd-timesyncd.service` nem `pulseaudio.service` estão ativos, e o som via ALSA funciona normalmente no EmulationStation e no RetroArch

### Requirement: Chaves de rede, atualização e rewind desligadas no EmuELEC
O `emuelec.conf` da imagem gerada SHALL declarar `ee_ssh.enabled=0`, `controllers.bluetooth.enabled=0`, `updates.enabled=0`, `global.netplay=0` e `global.rewind=0`.

#### Scenario: Configuração do EmuELEC inspecionada
- **WHEN** o `emuelec.conf` da p8 da imagem gerada é inspecionado
- **THEN** as cinco chaves estão definidas com valor `0`

### Requirement: Omissão de escrita de netplay no cartão em jogos locais
Ao iniciar um jogo Libretro sem argumentos de netplay (`--host`, `--connect` ou `--netplaymode`), o `emuelecRunEmu.sh` SHALL NOT chamar `set_ee_setting` para regravar `netplay.server.ip`, `netplay.server.port` ou `netplay.mode` no `emuelec.conf`.

#### Scenario: Jogo iniciado localmente
- **WHEN** o usuário abre um jogo Libretro normal sem argumentos de netplay
- **THEN** o `emuelecRunEmu.sh` não executa `set_ee_setting "netplay.*"` no `emuelec.conf`
