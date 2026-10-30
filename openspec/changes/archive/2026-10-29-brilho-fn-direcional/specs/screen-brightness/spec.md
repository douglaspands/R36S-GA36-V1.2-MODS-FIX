# Spec Delta

## Purpose

Definir o ajuste do brilho da tela do R36S por FN + D-pad ↑/↓, com nível persistente entre boots e sonos, piso que impede a tela de apagar e formas de voltar ao brilho padrão.

## ADDED Requirements

### Requirement: Ajuste do brilho por FN e D-pad
Com o FN apertado, o sistema SHALL aumentar o brilho a cada D-pad ↑ e reduzi-lo a cada D-pad ↓, em passo fixo, repetindo enquanto a seta ficar apertada. Sem o FN, o D-pad SHALL NOT alterar o brilho.

#### Scenario: Aumentar
- **WHEN** o usuário aperta FN + ↑
- **THEN** o brilho sobe um passo e a tela muda na hora; mantendo a seta apertada, o brilho continua subindo até o teto

#### Scenario: Reduzir
- **WHEN** o usuário aperta FN + ↓
- **THEN** o brilho desce um passo; mantendo a seta apertada, continua descendo até o piso

#### Scenario: D-pad sem o FN
- **WHEN** o usuário aperta ↑ ou ↓ sem o FN
- **THEN** o brilho não muda e o D-pad funciona como antes no jogo e no EmulationStation

#### Scenario: Teto
- **WHEN** o brilho já está em 100 e o usuário aperta FN + ↑
- **THEN** o brilho continua em 100

### Requirement: Piso do brilho
O nível de brilho SHALL ficar entre um piso e 100. O sistema SHALL NOT permitir que o ajuste apague a tela, e SHALL NOT aceitar como nível salvo um valor abaixo do piso ou que não seja um número.

#### Scenario: Piso
- **WHEN** o usuário segura FN + ↓ até o fim
- **THEN** o brilho para no piso, com a tela ainda legível, e o `lcdbl` nunca recebe 0 por causa do ajuste

#### Scenario: Arquivo de nível corrompido
- **WHEN** o arquivo do nível salvo está vazio, tem texto ou um número fora de 0 a 100
- **THEN** o sistema ignora o valor, usa o padrão (80) e não trava

### Requirement: Nível persistente
O sistema SHALL guardar o nível escolhido num arquivo próprio da p8 e SHALL aplicá-lo no boot, ao acordar da suspensão e a cada ajuste. O `brightness.level` do `emuelec.conf` SHALL NOT ser a fonte do nível quando o arquivo próprio existir.

#### Scenario: Depois de reiniciar
- **WHEN** o usuário reduz o brilho, desliga e liga o aparelho
- **THEN** a tela volta ao nível escolhido, mesmo que o ES tenha regravado o `emuelec.conf` com `brightness.level` antigo

#### Scenario: Depois de dormir
- **WHEN** o usuário reduz o brilho, suspende o aparelho pelo botão de energia e o acorda
- **THEN** a tela volta ao nível escolhido e não a 80

#### Scenario: Sem nível salvo
- **WHEN** o arquivo do nível não existe
- **THEN** o sistema usa o `brightness.level` do `emuelec.conf` (80 de fábrica) e o comportamento é o de antes

#### Scenario: Cartão que já tinha o arquivo
- **WHEN** a p8 já tem o arquivo do nível e só o `system` é regravado
- **THEN** o nível salvo continua valendo

### Requirement: Voltar ao brilho padrão
O sistema SHALL voltar o brilho ao padrão (80) quando o usuário clicar o analógico esquerdo (L3) com o FN apertado, e no boot quando existir o arquivo vazio `r36-brilho-original` na raiz da p1. Em ambos os casos o nível salvo SHALL ser removido ou regravado com o padrão.

#### Scenario: Reset por FN + L3
- **WHEN** o usuário aperta o FN e clica o analógico esquerdo (L3)
- **THEN** o brilho vai a 80 na hora e persiste nos boots seguintes; segurar o L3 não repete o reset

#### Scenario: L3 sem o FN
- **WHEN** o usuário clica o L3 sem o FN
- **THEN** o brilho não muda

#### Scenario: Reset pela chave
- **WHEN** o usuário cria `r36-brilho-original` na raiz da p1 e religa o aparelho
- **THEN** o nível salvo é descartado, o brilho fica em 80 e o ajuste por FN + D-pad continua funcionando

#### Scenario: p1 indisponível
- **WHEN** `/storage/roms` não monta no tempo de espera
- **THEN** o sistema trata a chave como ausente, aplica o nível salvo e o boot segue sem travar

### Requirement: Compatibilidade com o FN e o boot
O FN SHALL continuar sem função própria no EmulationStation. O serviço do ajuste SHALL NOT atrasar nem travar o boot e SHALL sair com código 0 quando o FN, o D-pad ou o `lcdbl` não existirem.

#### Scenario: FN no EmulationStation
- **WHEN** o usuário aperta só o FN no ES
- **THEN** nada acontece; o `es_input.cfg` não ganha entrada para o FN

#### Scenario: FN não remapeado
- **WHEN** o `fn_key` não foi remapeado (chave `r36-fn-original` ou driver ausente)
- **THEN** o atalho não age, o nível salvo ainda é aplicado no boot e nenhum erro trava o boot

#### Scenario: lcdbl ausente
- **WHEN** `/sys/devices/virtual/disp/disp/attr/lcdbl` não existe
- **THEN** os scripts saem com código 0 sem gravar o nível
