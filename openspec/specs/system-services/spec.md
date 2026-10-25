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
