# Spec Delta

## Purpose

Definir quais serviços do EmuELEC sobem no boot da imagem gerada, para não gastar boot e memória com funções que o R36S não tem.

## ADDED Requirements

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
