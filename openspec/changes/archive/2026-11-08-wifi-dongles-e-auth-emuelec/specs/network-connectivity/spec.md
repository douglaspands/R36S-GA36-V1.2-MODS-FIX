# Spec Delta

## Purpose

Permite que o R36S utilize adaptadores de rede USB (Wi-Fi, Bluetooth e tethering via cabo USB), escaneie redes sem fio e realize a autenticação com sucesso diretamente pelos menus do EmulationStation/EmuELEC, além de permitir pré-configuração opcional via arquivo `network.conf` na partição FAT32.

## ADDED Requirements

### Requirement: Autenticação de Wi-Fi pela interface gráfica do EmuELEC
O sistema SHALL provisionar a rede sem fio e executar a conexão ativa no ConnMan quando o usuário confirmar o SSID e a senha na interface do EmulationStation, reportando o status real da conexão e o endereço IP obtido.

#### Scenario: Conexão bem-sucedida via menu
- **WHEN** o usuário seleciona uma rede Wi-Fi, insere a senha no teclado da tela e confirma
- **THEN** o sistema grava o provisionamento em `/storage/.cache/connman/`, executa `connmanctl connect` para o serviço correspondente e a interface exibe o status de conectado com o IP atribuído por DHCP

#### Scenario: Falha de autenticação ou senha incorreta
- **WHEN** o usuário tenta conectar informando uma senha incorreta ou ponto de acesso inacessível
- **THEN** o sistema reporta falha de conexão para a interface e não mantém conexões inválidas em segundo plano

### Requirement: Escaneamento de redes sem fio em múltiplas interfaces
O script de listagem de redes sem fio (`batocera-wifi`) SHALL listar os pontos de acesso detectados em qualquer interface sem fio disponível no sistema, sem restringir a busca exclusivamente à interface `wlan0`.

#### Scenario: Dongle com interface alternativa
- **WHEN** um adaptador Wi-Fi reconhecido pelo sistema registra uma interface com nome diferente de `wlan0` (como `wlan1`, `ra0` ou `wlx*`)
- **THEN** a lista de redes disponíveis no menu do EmulationStation exibe todos os SSIDs escaneados por essa interface

### Requirement: Biblioteca universal de firmwares de rede
A imagem gerada SHALL fornecer em `/usr/lib/firmware/` os arquivos de microcódigo binários para os adaptadores USB suportados, incluindo as famílias Realtek RTL8821CU, RTL8188EU, RTL8192CU, RTL8192EU, RTL8723AU/BU, MediaTek MT7601U, Ralink RT2800USB e adaptadores Bluetooth USB.

#### Scenario: Detecção de dongle USB
- **WHEN** um adaptador USB suportado de qualquer uma das famílias catalogadas é conectado à porta OTG
- **THEN** o driver carrega seu firmware correspondente a partir de `/usr/lib/firmware/` sem erros de firmware ausente no dmesg

### Requirement: Suporte nativo a ancoragem USB e adaptadores Ethernet
O sistema SHALL reconhecer conexões de rede cabeada e tethering USB via módulo `cdc_ether.ko`, configurando a interface imediatamente via DHCP pelo ConnMan sem exigir digitação de senhas.

#### Scenario: Celular ou adaptador USB-LAN conectado via OTG
- **WHEN** um smartphone com ancoragem USB ativada ou adaptador USB-Ethernet CDC é plugado na porta OTG
- **THEN** a interface de rede é criada e o ConnMan obtém endereço IP automaticamente, disponibilizando conectividade de rede de imediato

### Requirement: Configuração declarativa opcional via FAT32
O sistema SHALL ler o arquivo opcional `network.conf` localizado na raiz da partição `R36-ROMS` (FAT32) durante a inicialização, aplicando as credenciais de rede e ligando o rádio se `radio=on`, ou mantendo-o desligado caso ausente ou `radio=off`.

#### Scenario: Arquivo network.conf com radio=on
- **WHEN** o console inicia com o arquivo `network.conf` na raiz da partição ROMS contendo `radio=on`, `ssid` e `passphrase` válidos
- **THEN** o sistema ativa o rádio no ConnMan e conecta à rede especificada sem necessidade de navegação na interface

#### Scenario: Arquivo ausente ou radio=off
- **WHEN** o console inicia sem o arquivo `network.conf` ou com `radio=off`
- **THEN** os serviços de rádio permanecem desligados e nenhum processo de escaneamento periódico é mantido em segundo plano

### Requirement: Acesso direto ao console via USB Gadget (Mass Storage e RNDIS)
O sistema SHALL suportar a ativação do controlador USB do dispositivo (`android0`) nos modos de dispositivo (gadget), permitindo que o PC acesse a partição de ROMs como unidade de disco removível (`mass_storage`) ou como adaptador de rede virtual (`rndis`), controlado via chaves na partição `R36-ROMS` ou pela diretiva `usb_mode=` no `network.conf`.

#### Scenario: Ativação de modo pendrive (Mass Storage)
- **WHEN** o usuário cria a chave `r36-usb-pendrive` na raiz da partição de ROMs ou define `usb_mode = pendrive` no `network.conf` e conecta o console a um computador
- **THEN** o kernel exporta a partição `/dev/mmcblk0p1` como unidade de armazenamento em massa USB no PC sem necessidade de remover o cartão físico

#### Scenario: Ativação de modo rede virtual (RNDIS)
- **WHEN** o usuário cria a chave `r36-usb-rede` ou define `usb_mode = rede` e conecta o console a um computador
- **THEN** o sistema ativa a interface `usb0` com endereço fixo `192.168.137.2` permitindo comunicação IP direta com o host

### Requirement: Exibição da identificação da imagem no menu de Informações do EmuELEC
O sistema SHALL exibir o nome ou timestamp da imagem de build na linha "Versão" (VERSION) da tela de informações do EmulationStation (*Configurações do Sistema -> Informação*), obtendo o dado a partir de `/flash/R36-BUILD.txt` ou do arquivo `/usr/config/EE_VERSION`.

#### Scenario: Visualização da versão do build na interface
- **WHEN** o usuário navega até a opção de Informações do Sistema no menu principal do EmulationStation
- **THEN** a linha de versão apresenta a identificação do build gravado (ex: `4.7-Nexus (build <timestamp>)`), permitindo ao usuário conferir diretamente na tela qual versão está em execução no console

### Requirement: Privacidade e proteção de credenciais em logs
Os scripts de rede e diagnóstico SHALL NOT registrar a chave ou senha de rede (passphrase) em arquivos de log, relatórios na partição FAT32 ou saídas legíveis.

#### Scenario: Geração de log com chave r36-diagnostico
- **WHEN** o usuário cria a chave `r36-diagnostico` na partição FAT32 e conecta a uma rede protegida
- **THEN** o arquivo `r36-wifi.log` registra eventos de associação, DHCP e erros, mas omite ou mascara o valor da senha
