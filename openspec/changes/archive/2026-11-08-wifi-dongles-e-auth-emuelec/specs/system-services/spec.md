# Spec Delta

## MODIFIED Requirements

### Requirement: Chaves de rede, atualização e rewind desligadas no EmuELEC
O `emuelec.conf` da imagem gerada SHALL declarar `ee_ssh.enabled=0`, `wifi.enabled=0`, `controllers.bluetooth.enabled=0`, `updates.enabled=0`, `global.netplay=0` e `global.rewind=0`.

#### Scenario: Configuração do EmuELEC inspecionada
- **WHEN** o `emuelec.conf` da p8 da imagem gerada é inspecionado
- **THEN** as chaves de rede, bluetooth, atualização, netplay e rewind estão definidas com valor `0` por padrão

## ADDED Requirements

### Requirement: Gerenciamento sob demanda do serviço de conexão ConnMan
O serviço `connman.service` SHALL permanecer desativado no boot quando a rede estiver desligada (`wifi.enabled=0`), e SHALL ser iniciado quando a rede for ativada pelo usuário na interface ou via `network.conf`.

#### Scenario: Inicialização com Wi-Fi desligado
- **WHEN** o sistema inicia com Wi-Fi desativado por padrão
- **THEN** o `connman.service` não consome recursos de CPU ou memória em segundo plano

#### Scenario: Ativação de rede pelo usuário
- **WHEN** o usuário ativa a rede no menu de configurações ou fornece `network.conf` com `radio=on`
- **THEN** o `connman.service` é iniciado para gerenciar conexões sem fio e atribuição de IP
