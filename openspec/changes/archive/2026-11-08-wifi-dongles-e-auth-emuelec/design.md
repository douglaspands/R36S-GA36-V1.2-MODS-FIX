# Design

## Context

O console R36S clone (GA36-MB V1.2, Allwinner A33) executa EmuELEC 4.7 ("Nexus") sobre kernel vendor sunxi 3.4.39. O sistema de arquivos é composto por uma partição FAT32 (`R36-ROMS`, p1), partição ext4 (`R36-STORAGE`, p8) e o squashfs raiz (`SYSTEM`, p7).

A interface gráfica do EmulationStation interage com o subsistema de rede exclusivamente por meio dos utilitários `/usr/bin/batocera/batocera-config` e `/usr/bin/batocera/batocera-wifi`, que por sua vez usam o ConnMan (`connmand` / `connmanctl`). Na base de fábrica:
- O `connman.service` não é iniciado no boot nem por ativação D-Bus.
- O `batocera-config wifi enable` cria um arquivo de provisionamento estático mas nunca chama `connmanctl connect`, resultando em falha silenciosa de handshake de autenticação.
- O `batocera-wifi` descarta qualquer interface wireless que não se chame `wlan0`.
- Faltam firmwares redistribuíveis em `/usr/lib/firmware/` para os chips comuns de adaptadores USB.

Veja `proposal.md` para motivação e escopo.

## Goals / Non-Goals

**Goals:**
- Permitir que o usuário realize o fluxo completo de conexão Wi-Fi na interface gráfica do EmuELEC (scan de redes, seleção, digitação da senha e autenticação com obtenção de IP).
- Suportar todos os chips de rádio USB e adaptadores pesquisados nos repositórios: RTL8821CU, RTL8188EU, RTL8192CU, RTL8192EU, RTL8723AU/BU, MT7601U, RT2800USB, RTL8761A/BU e CDC Ethernet.
- Oferecer fallback amigável via arquivo `network.conf` na partição FAT32 acessível pelo Windows.
- Garantir consumo zero de bateria e CPU quando o rádio estiver desligado ou sem adaptador USB plugado.
- Mascarar e proteger senhas de rede contra vazamento em logs.

**Non-Goals:**
- Não inclui suporte a redes corporativas WPA-Enterprise (802.1X com certificados) ou portais cativos.
- Não inclui servidor SSH ou serviços de rede expostos por padrão (mantendo as diretrizes de segurança de `CLAUDE.md`).
- Não recompila o kernel base 3.4.39 (utiliza os módulos e subsistemas existentes e extensíveis por firmware e userspace).

## Decisions

### Decisão 1: Utilizar o ConnMan nativo em vez de introduzir novos daemons de rede
- **Decisão**: Utilizar o `connmand` e `connmanctl` já instalados no `SYSTEM` em vez de portar `wpa_supplicant` autônomo ou `NetworkManager`.
- **Justificativa**: O EmulationStation original do EmuELEC já foi compilado para conversar com `batocera-config` e `batocera-wifi` baseados em ConnMan. Preservar o ConnMan garante 100% de integração com os menus existentes sem exigir recompilação do executável do EmulationStation.
- **Alternativas consideradas**:
  - *wpa_supplicant direto*: Exigiria reescrever completamente a camada `ApiSystem` do EmulationStation ou reimplementar comandos fictícios de `batocera-config`.

### Decisão 2: Handshake ativo de conexão no `batocera-config wifi enable`
- **Decisão**: Quando o EmulationStation chamar `batocera-config wifi enable "$ssid" "$key"`:
  1. O script grava `/storage/.cache/connman/emuelec_wifi.config` com `AutoConnect = true`.
  2. Garante que o ConnMan está ativo (`systemctl start connman.service`).
  3. Dispara `connmanctl enable wifi` e `connmanctl scan wifi`.
  4. Localiza o identificador do serviço gerado pelo ConnMan (`wifi_*_managed_psk`).
  5. Executa `connmanctl connect "$service"` para forçar a negociação WPA 4-way handshake.
  6. Aguarda até 10 segundos pela obtenção de IP e retorna código `0` apenas se a conexão for confirmada, ou `1` em caso de senha inválida ou timeout.
- **Justificativa**: Resolve a raiz do problema onde o sistema achava que estava conectado sem ter transmitido credenciais para o roteador.

### Decisão 3: Escaneamento multi-interface no `batocera-wifi`
- **Decisão**: Substituir a verificação estrita `if [ $TYPE == "wlan0" ]` por uma validação que aceite qualquer interface wireless associada ao serviço (`wlan*`, `ra*`, `wlx*`).
- **Justificativa**: Adaptadores baseados em MediaTek/Ralink ou dongles com nomes previsíveis geram nomes de interface alternativos que eram descartados indevidamente.

### Decisão 4: Empacotamento centralizado de firmwares em feature
- **Decisão**: Criar a feature `71-firmware-rede` injetando os microcódigos binários redistribuíveis do repositório oficial `linux-firmware` sob `/usr/lib/firmware/`:
  - `rtw88/rtw8821c_fw.bin`
  - `rtl_bt/rtl8821c_fw.bin`, `rtl_bt/rtl8821c_config.bin`, `rtl_bt/rtl8761bu_fw.bin`, `rtl_bt/rtl8761a_fw.bin`
  - `rtlwifi/rtl8188eufw.bin`, `rtlwifi/rtl8192cufw.bin`, `rtlwifi/rtl8192cufw_TMSC.bin`, `rtlwifi/rtl8192eu_nic.bin`
  - `rtlwifi/rtl8723aufw_A.bin`, `rtlwifi/rtl8723bu_nic.bin`
  - `mt7601u.bin`, `rt2870.bin`
- **Justificativa**: O kernel não consegue ativar o rádio sem o microcódigo proprietário do chip. O conjunto completo ocupa ~4.2 MiB no squashfs compactado com LZO.

### Decisão 5: Suporte Plug-and-Play para Ancoragem USB de Smartphone (`cdc_ether.ko`)
- **Decisão**: Garantir que o módulo `cdc_ether.ko` (já presente em `/usr/lib/modules/cdc_ether.ko`) seja carregado automaticamente via regra udev ao plugar smartphones Android/iOS ou adaptadores USB-LAN.
- **Justificativa**: Fornece conectividade instantânea sem exigir a compra de adaptadores dedicados; qualquer celular conectado por cabo na porta OTG vira modem de internet para o R36S.

### Decisão 6: Serviço de inicialização e leitor de `network.conf` na FAT32
- **Decisão**: Criar o serviço `r36-wifi.service` no boot (`After=storage.mount`, `Before=emustation.service`):
  1. Verifica `/storage/roms/network.conf`. Se ausente ou `radio=off`, desativa o rádio (`connmanctl disable wifi`).
  2. Se `radio=on`, faz o parse seguro (ignorando BOM do Windows e `\r`), grava as credenciais no ConnMan e sincroniza com `wifi.enabled=1` no `emuelec.conf`.
- **Justificativa**: Une a conveniência de pré-configuração pelo PC com a capacidade de alteração posterior direta na tela do portátil.

### Decisão 7: Acesso ao Console via USB Gadget (Mass Storage e RNDIS)
- **Decisão**: Controlar `/sys/class/android_usb/android0` via `/usr/lib/r36/wifi-conf-aplica` no boot:
  1. Quando configurado com `modo="pendrive"`, exporta a partição `/dev/mmcblk0p1` como unidade de disco removível USB para o PC.
  2. Quando configurado com `modo="rede"`, ativa RNDIS e atribui IP `192.168.137.2` na interface `usb0`.
  3. Quando configurado com `modo="ambos"`, combina RNDIS e Mass Storage simultaneamente.
  4. O modo é determinado por chaves na partição `R36-ROMS` (`r36-usb-pendrive`, `r36-usb-rede`, `r36-usb-ambos`) ou pela diretiva `usb_mode=` no `network.conf`.
- **Justificativa**: Permite acesso rápido para transferência de ROMs e saves ligando um cabo USB direto no PC, sem necessidade de leitor de cartão SD físico.

### Decisão 8: Exibição da Versão/Build no Menu do EmulationStation
- **Decisão**: O EmulationStation lê a versão de `/usr/config/EE_VERSION` (ou via `/usr/bin/batocera-version`). No boot, um script lê `/flash/R36-BUILD.txt` (ou o gerador de imagem embute o timestamp) e atualiza `/usr/config/EE_VERSION` (ou fornece o drop-in `batocera-version`) com o identificador do build formatado (ex: `4.7 (build YYYYMMDD-HHMMSS)`).
- **Justificativa**: Permite ao usuário identificar visualmente em tela qual versão está instalada no console, sem precisar abrir o cartão no PC.

## Risks / Trade-offs

- **[Risco] Dongles com alto consumo de corrente sobrecarregando a porta USB OTG** → Mitigação: Recomendar adaptadores nano (baixo consumo) e desligar o rádio quando não estiver em uso para preservar a bateria do portátil.
- **[Risco] ConnMan demorar no scan travando o menu do EmulationStation** → Mitigação: O `batocera-wifi` usa timeout de 3 segundos no scan; o `batocera-config` executa o connect com timeout limitado de 10s.
- **[Risco] Exposição acidental de senhas em logs** → Mitigação: Todas as funções de diagnóstico (`r36-wifi.log`) mascaram a chave (`passphrase=********`).
