# Design

## Context

O console R36S clone (GA36-MB V1.2, Allwinner A33) roda EmuELEC 4.7 com kernel sunxi 3.4.39 e glibc 2.36 (ABI armhf, ARMv7-A, VFPv4+NEON).
O sistema de arquivos é composto por três partições principais de dados e sistema:
- `p1` (`R36-ROMS`, FAT32): ROMs, bios e temas adicionais.
- `p2` (`SYSTEM`, squashfs): sistema operacional montado em `/` somente leitura.
- `p8` (`R36-STORAGE`, ext4): armazenamento de configurações e dados do usuário em `/storage`.

A placa-mãe não possui Wi-Fi nem conector Ethernet integrado, mas o kernel suporta adaptadores USB de rede (como adaptadores USB-Ethernet CDC `cdc_ether.ko` e certos dongles Wi-Fi) conectados na porta USB-C OTG. A imagem base não contém nenhum daemon SSH (`sshd` ou `dropbear`).

## Goals / Non-Goals

**Goals:**
- Prover os binários `dropbear` e `dropbearkey` compatíveis com a ABI do sistema (armhf, glibc <= 2.36).
- Integrar a inicialização do Dropbear através de unit do systemd (`dropbear.service`) habilitada na camada `system`.
- Gerar automaticamente chaves de host (Ed25519 e RSA) no primeiro boot em armazenamento persistente (`/storage/.cache/ssh/`).
- Manter o consumo de memória e armazenamento mínimo (< 1 MiB de disco e < 2 MiB de RAM durante execução).
- Incluir suíte de testes validando a estrutura da feature e a sintaxe da unit de serviço.

**Non-Goals:**
- Fornecer OpenSSH completo (desnecessariamente pesado para o ambiente embarcado).
- Compilar módulos de kernel para dongles Wi-Fi não suportados pelo kernel sunxi 3.4.39 de fábrica.
- Criar interface gráfica de pareamento de Wi-Fi no EmulationStation além das ferramentas nativas do EmuELEC.

## Decisions

### 1. Dropbear vs OpenSSH
- **Decisão**: Utilizar o Dropbear.
- **Justificativa**: O binário do Dropbear tem ~400 KiB e consumo de memória irrisório, ideal para um SoC modesto com 512 MiB / 1 GiB de RAM compartilhada com GPU, enquanto o OpenSSH exige múltiplos daemons e bibliotecas adicionais.

### 2. Camada e localização dos binários
- **Decisão**: Binários instalados na camada `system` (`usr/sbin/dropbear` e `usr/sbin/dropbearkey`).
- **Alternativa considerada**: Colocar em `/storage/bin/` na partição ext4 (`storage`).
- **Justificativa**: Colocar na camada `system` mantém os binários no squashfs comprimido e protegido contra corrupção acidental do filesystem de dados, alinhando-se com os demais executáveis do sistema (`/usr/sbin/eemount`, `/usr/sbin/connmand`).

### 3. Persistência de chaves de host em `/storage/.cache/ssh/`
- **Decisão**: Armazenar as chaves de host geradas em `/storage/.cache/ssh/`.
- **Alternativa considerada**: Gerar chaves em `/tmp/` a cada boot.
- **Justificativa**: Gerar em `/tmp/` forçaria o cliente SSH a alertar sobre chave de host alterada a cada reinício do console (`REMOTE HOST IDENTIFICATION HAS CHANGED!`). A pasta persistente em `/storage` evita o erro e economiza tempo de boot subsequente.

### 4. Unit do systemd com `ExecStartPre` para criação de chaves
- **Decisão**: Criar `usr/lib/systemd/system/dropbear.service` com `ExecStartPre` chamando script leve (ou comandos do `dropbearkey`) que verifica e gera as chaves caso não existam antes de executar `dropbear -F -E -r ...`.
- **Justificativa**: Garante que o serviço só suba após as chaves estarem disponíveis, sem necessidade de um serviço separado de setup.

## Risks / Trade-offs

- **[Segurança: senha de root padrão]** → O sistema EmuELEC possui credencial conhecida (`root:emuelec`). Se conectado a redes Wi-Fi abertas, qualquer host na mesma rede pode obter acesso root.
  - *Mitigação*: Documentar que a senha deve ser alterada com `passwd` se o dispositivo for utilizado em redes corporativas ou públicas.
- **[Entropia no primeiro boot]** → Gerar chaves RSA no SoC Allwinner A33 pode demorar alguns segundos se o pool de entropia do kernel estiver baixo.
  - *Mitigação*: Priorizar chave moderna Ed25519 e utilizar RSA de 2048 bits (em vez de 4096), assegurando inicialização rápida.
