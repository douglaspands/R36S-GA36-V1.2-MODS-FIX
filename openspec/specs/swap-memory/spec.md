# swap-memory Specification

## Purpose

Definir onde o aparelho faz swap e com que prioridade, para usar memória comprimida em RAM em vez de escrever no cartão SD.

## Requirements

### Requirement: Swap em zram
O aparelho SHALL ativar no boot um swap zram com metade da RAM total, com prioridade maior que a de qualquer swap em arquivo.

#### Scenario: Swap ativo no boot
- **WHEN** o aparelho termina o boot com o SYSTEM gravado pelo build
- **THEN** `/proc/swaps` lista `/dev/zram0` com tamanho próximo de metade de `MemTotal` e a maior prioridade da lista

#### Scenario: zram indisponível
- **WHEN** o dispositivo `/dev/zram0` não existe
- **THEN** o boot continua normalmente, sem swap zram, e o motivo fica registrado no journal

### Requirement: Sem swapfile no cartão
O STORAGE da imagem gerada SHALL NOT conter o swapfile e SHALL desligar a criação de swap em arquivo.

#### Scenario: Cartão gravado com wipe-storage
- **WHEN** o cartão é gravado com `--wipe-storage` e o aparelho inicia
- **THEN** `/storage/.cache/swapfile` não existe e não é recriado, e `/proc/swaps` lista só o zram

#### Scenario: Espaço liberado
- **WHEN** a p8 gerada é comparada com a da base
- **THEN** o espaço livre aumenta em pelo menos 300 MB
