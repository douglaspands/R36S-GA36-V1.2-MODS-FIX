# Proposal

## Why

O console clone do R36S (GA36-MB V1.2, Allwinner A33) de fábrica não possui Wi-Fi nem rede interna. No entanto, usuários frequentemente conectam adaptadores USB OTG (Wi-Fi, Bluetooth ou cabo USB de celular) para baixar capas (scraper), sincronizar conquistas (RetroAchievements), netplay ou transferir arquivos.

Atualmente no sistema de fábrica (EmuELEC 4.7):
1. O serviço ConnMan (`connman.service`) não é iniciado no boot, quebrando o subsistema de rede do backend.
2. O script de conexão `/usr/bin/batocera/batocera-config wifi enable` não realiza o handshake de conexão (`connmanctl connect`), fazendo com que a interface do EmulationStation falhe ao autenticar.
3. O escaneador `/usr/bin/batocera/batocera-wifi` filtra exclusivamente por `wlan0`, ignorando adaptadores com outros identificadores de interface.
4. Faltam firmwares e regras de carregamento automático para os principais dongles USB pesquisados nos ecossistemas de portáteis (`RTL8821CU`, `RTL8188EU`, `RTL8192CU`, `RTL8192EU`, `RTL8723AU/BU`, `MT7601U`, `RT2800USB`, `RTL8761A/BU`).

Esta mudança implementa compatibilidade abrangente de adaptadores USB de rede e garante que a própria interface do EmuELEC consiga escanear, selecionar, digitar a senha e autenticar com sucesso no ponto de acesso, oferecendo também o fallback declarativo via arquivo `network.conf` na partição FAT32 (`R36-ROMS`).

## What Changes

- **Autenticação Direta na Interface do EmuELEC**: Correção no fluxo de conexão do EmulationStation (`batocera-config wifi enable`) para efetuar o provisionamento com `AutoConnect=true` e executar o comando explícito de conexão (`connmanctl connect`), aguardando a confirmação do DHCP e informando o status real na tela.
- **Suporte a Múltiplas Interfaces no Escaneamento**: Ajuste no `batocera-wifi scanlist` para listar redes em qualquer interface sem fio disponível (`wlan*`, `ra*`, `wlx*`).
- **Gerenciamento Inteligente do ConnMan**: Ativação e gestão sob demanda do `connman.service`, mantendo-o desligado quando o rádio estiver inativo para poupar 100% de CPU e bateria.
- **Biblioteca Universal de Firmwares**: Instalação dos microcódigos de rádio redistribuíveis (`linux-firmware`) para os chips pesquisados (`rtw88/rtw8821c_fw.bin`, `rtl_bt/`, `rtlwifi/`, `mt7601u.bin`, `rt2870.bin`).
- **Detecção e Módulos de Rede**: Regras de udev para detecção de USB IDs na porta OTG, carregamento do driver correspondente e suporte nativo a tethering USB via `cdc_ether.ko` (já disponível no sistema).
- **Provisionamento Declarativo Opcional via FAT32 (`network.conf`)**: Leitor no boot que permite ao usuário pré-configurar `radio=on`, `ssid=...` e `passphrase=...` diretamente no Windows na partição `R36-ROMS`.
- **Acesso Direto ao Aparelho via USB Gadget (Mass Storage e Rede)**: Suporte ao controlador USB (`android0`) nos modos pendrive (`mass_storage` expondo a partição de ROMs `mmcblk0p1` no PC para transferência de jogos/saves sem remover o cartão) e rede virtual (`rndis` com IP 192.168.137.2), acionáveis por chaves na partição de ROMs (`r36-usb-pendrive`, `r36-usb-rede`, `r36-usb-ambos`) ou declarados via `usb_mode=` no `network.conf`.
- **Identificação da Imagem na Interface do EmuELEC**: Integração do nome e timestamp da imagem de build na tela de informações do EmulationStation (*Configurações do Sistema -> Informação / Versão*), lendo os metadados de `/flash/R36-BUILD.txt` e alimentando `/usr/config/EE_VERSION` / `batocera-version`.
- **Privacidade e Diagnóstico**: Garantia de que a senha de rede nunca é gravada em logs de diagnóstico e que o rádio permanece inativo por padrão.

## Capabilities

### New Capabilities
- `network-connectivity`: Suporte a adaptadores de rede USB (Wi-Fi, Bluetooth, CDC Ethernet), carregamento de firmwares/módulos, escaneamento e autenticação no roteador diretamente pela interface do EmulationStation/EmuELEC e via `network.conf` na partição FAT32 (`R36-ROMS`).

### Modified Capabilities
- `system-services`: Permite que os serviços de rede (`connman.service`) sejam gerenciados e iniciados sob demanda quando o rádio estiver ativado, sem desperdiçar recursos quando desligado.

## Impact

- **Imagens do Sistema (SYSTEM squashfs)**: Modificação em `/usr/bin/batocera/batocera-config`, `/usr/bin/batocera/batocera-wifi`, adição de firmwares em `/usr/lib/firmware/` e regras udev.
- **Partição STORAGE (ext4)**: Criação/ajuste das configurações do ConnMan em `/storage/.cache/connman/`.
- **Partição ROMS (FAT32)**: Leitura opcional de `network.conf` na raiz da partição no primeiro boot ou reinicialização.
- **Consumo de Energia**: Zero consumo quando sem dongle/rádio desligado.
- **Compatibilidade**: Sem quebras no EmulationStation, preservando menus existentes e adicionando funcionalidade real.
