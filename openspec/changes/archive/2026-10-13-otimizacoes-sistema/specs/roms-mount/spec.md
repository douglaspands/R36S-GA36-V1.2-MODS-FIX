# Spec Delta

## Purpose

Definir as opções de montagem da partição de ROMs no aparelho, para que ler ROMs não gere escritas no cartão.

## ADDED Requirements

### Requirement: ROMs montadas sem atime
Depois que o sistema monta a partição de ROMs em `/storage/roms`, ela SHALL ficar montada com `noatime`, mantendo as demais opções.

#### Scenario: Boot
- **WHEN** o aparelho termina o boot com a p1 montada
- **THEN** `/proc/mounts` mostra `/storage/roms` com `noatime`, e as ROMs e os saves gravados na p1 continuam acessíveis para leitura e escrita

#### Scenario: ROMs não montadas
- **WHEN** `/storage/roms` não é um ponto de montagem
- **THEN** nada é remontado, e o boot continua normalmente
