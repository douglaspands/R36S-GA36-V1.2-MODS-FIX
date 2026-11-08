# Tasks

## 1. Correção do Backend de Autenticação da Interface do EmuELEC

- [x] 1.1 Corrigir `/usr/bin/batocera/batocera-config wifi enable` para provisionar com `AutoConnect = true`, escanear o SSID, chamar `connmanctl connect` ativamente e verificar a confirmação do DHCP
- [x] 1.2 Corrigir `/usr/bin/batocera/batocera-wifi scanlist` para permitir escaneamento em qualquer interface sem fio (`wlan*`, `ra*`, `wlx*`), sem filtrar exclusivamente `wlan0`
- [x] 1.3 Adicionar testes unitários em `tests/test_wifi_scripts.py` para validar a geração do arquivo de provisionamento e o comando de conexão do ConnMan

## 2. Gerenciamento do Serviço ConnMan e Hotplug USB

- [x] 2.1 Criar regras de udev em `/etc/udev/rules.d/80-network-drivers.rules` para detectar a inserção de adaptadores USB OTG e carregar os drivers correspondentes (inclusive `cdc_ether.ko` para tethering USB)
- [x] 2.2 Configurar o ciclo de vida do `connman.service` para iniciar sob demanda quando a rede for ativada pelo menu do EmulationStation ou por inserção de dongle/cabo
- [x] 2.3 Implementar testes em `tests/test_network_service.py` validando as regras de udev e os estados do serviço ConnMan

## 3. Biblioteca Universal de Firmwares de Rede

- [x] 3.1 Criar a feature `71-firmware-rede` com a árvore de firmwares oficiais (`rtw88/`, `rtl_bt/`, `rtlwifi/`, `mt7601u.bin`, `rt2870.bin`) sob `/usr/lib/firmware/`
- [x] 3.2 Implementar script de verificação e integridade de hashes sha256 dos firmwares em `tools/valida_firmware_rede.py`
- [x] 3.3 Testar o empacotamento no squashfs garantindo que o acréscimo de tamanho permaneça dentro da margem segura da partição SYSTEM

## 4. Provisionamento Declarativo Opcional via FAT32 (`network.conf`)

- [x] 4.1 Criar o script leitor `/usr/lib/r36/wifi-conf-aplica` e o serviço `r36-wifi.service` no boot para interpretar `/storage/roms/network.conf` tratando UTF-8 BOM e quebras de linha Windows CRLF
- [x] 4.2 Fornecer arquivo de exemplo `network.conf.exemplo` na raiz da partição de ROMs (p1) documentando os campos `radio=`, `ssid=` e `passphrase=`
- [x] 4.3 Implementar mascaramento de senhas em logs de diagnóstico condicionados à chave `r36-diagnostico`
- [x] 4.4 Adicionar testes unitários em `tests/test_netconf.py` cobrindo arquivos válidos, inválidos, BOM e ausência de arquivo

## 5. Integração, Build e Validação Final

- [x] 5.1 Rodar a suíte de testes completa do repositório (`python3 -I -m unittest discover -s tests`)
- [x] 5.2 Gerar imagem de teste com `./build.sh --test` e verificar integridade no manifest e no relatório de changes
- [x] 5.3 Documentar o uso de Wi-Fi e tethering nos três manuais técnicos (`docs/DEVELOPMENT.md`, `docs/DESENVOLVIMENTO.md`, `docs/DESARROLLO.md`) e registrar os fatos duráveis em `CLAUDE.md`

## 6. Acesso USB Gadget e Identificação da Versão no EmulationStation

- [x] 6.1 Implementar suporte a USB Gadget (`mass_storage` e `rndis`) em `/usr/lib/r36/wifi-conf-aplica` com acionamento por chaves na p1 (`r36-usb-pendrive`, `r36-usb-rede`, `r36-usb-ambos`) e via `network.conf`
- [x] 6.2 Implementar script/integração de versão (`batocera-version` e drop-in em `/usr/config/EE_VERSION`) para expor a identificação da imagem e timestamp na tela de Informação/Versão do EmulationStation
- [x] 6.3 Validar a exibição da versão do build e regenerar a imagem de teste com as novas integrações

## Workflow follow-up

- [x] Validação física no aparelho: confirmado que o hardware GA36-MB V1.2 não fornece alimentação 5V VBUS para dongles USB passivos na porta OTG em bateria.
- [x] Reversão das features de Wi-Fi e registro da limitação de hardware em CLAUDE.md e manuais técnicos.
- [x] Arquivamento da change.
