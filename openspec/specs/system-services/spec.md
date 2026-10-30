# system-services Specification

## Purpose

Definir quais serviços do EmuELEC sobem no boot da imagem gerada, para não gastar boot e memória com funções que o R36S não tem.

## Requirements

### Requirement: Serviços de controle remoto desligados
A imagem gerada SHALL NOT iniciar no boot os serviços de controle remoto `lircd.socket`, `lircd.service`, `lircd-uinput.service` e `eventlircd.service`.

#### Scenario: Boot
- **WHEN** o aparelho termina o boot
- **THEN** nenhum desses serviços está ativo, e o controle embutido, os atalhos de hotkey, o volume e o brilho funcionam como antes

### Requirement: Agendador desligado
A imagem gerada SHALL NOT iniciar o `cron.service` no boot.

#### Scenario: Boot
- **WHEN** o aparelho termina o boot
- **THEN** o `cron.service` não está ativo

### Requirement: Serviços do aparelho preservados
Os serviços do fabricante para o hardware (`udt_pwr`, `udt_battery`, `udt-hotkeys`, `udt-headphones`), o áudio, o EmulationStation e o autostart SHALL continuar ativos.

#### Scenario: Funções do aparelho
- **WHEN** o aparelho termina o boot
- **THEN** o botão de energia, a indicação de bateria, os atalhos de hotkey, a troca para fone de ouvido e o som funcionam como antes

### Requirement: Sem servidor SSH
A imagem gerada SHALL NOT incluir nem iniciar servidor SSH (Dropbear ou outro). A feature `45-ssh-dropbear`, da change arquivada `2026-10-24-ssh-dropbear-a33`, saiu da imagem em 2026-10-25 porque foi identificado um problema com ela. A remoção é provisória: o problema será analisado numa change futura, que decide se o SSH volta e em que condições. Até lá, todo acesso ao aparelho passa pelo cartão SD.

#### Scenario: Boot
- **WHEN** o aparelho termina o boot
- **THEN** nenhum serviço SSH está instalado ou ativo, e nenhuma chave de host é gerada em `/storage/.cache/ssh/`

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
