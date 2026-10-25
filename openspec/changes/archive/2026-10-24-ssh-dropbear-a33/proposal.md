# Proposal

> **Situação (2026-10-25): removida da imagem.** Foi identificado um problema
> com esta feature, e a `45-ssh-dropbear` saiu da imagem: feature, receita em
> `services/dropbear/`, testes e a spec `ssh-server`. O problema será analisado
> numa change futura, que decide se o SSH volta e em que condições. Enquanto
> isso, a spec `system-services` exige a imagem sem servidor SSH. O que está
> abaixo é o registro da implementação original (commit `9a72b09`).

## Why

A imagem de fábrica do clone R36S (GA36-MB V1.2, Allwinner A33) e a base EmuELEC 4.7 não trazem nenhum servidor SSH instalado (nem OpenSSH nem Dropbear), embora a configuração `ee_ssh.enabled=1` esteja presente no `emuelec.conf`. O aparelho não possui Wi-Fi nem Ethernet integrados na placa-mãe, mas usuários utilizam adaptadores de rede ou dongles Wi-Fi USB na porta OTG para depuração, testes e transferências de arquivos sem a necessidade de remover o cartão SD a cada iteração.

Adicionar um servidor SSH leve (Dropbear) com inicialização via systemd e geração automática de chaves de host viabiliza o gerenciamento remoto do console sempre que uma interface de rede estiver disponível.

## What Changes

- Adiciona uma nova feature `features/45-ssh-dropbear` contendo os binários do Dropbear (`dropbear`, `dropbearkey`) compilados ou disponibilizados para armhf (ARMv7-A, glibc <= 2.36) na camada `system` (em `/usr/sbin/`) ou `storage`.
- Adiciona unit do systemd (`dropbear.service` e/ou `dropbearkey.service`) para inicialização automática do daemon no boot, vinculada à disponibilidade de rede ou subindo em background.
- Configura script ou unit de primeiro boot para geração automática das chaves de host (`dropbear_ed25519_host_key`, `dropbear_rsa_host_key`) em `/storage/.cache/ssh/` ou `/etc/dropbear/`.
- Permite autenticação root compatível com as credenciais padrão do EmuELEC (`root` / `emuelec`).
- Adiciona testes automatizados validando o descritor da feature, permissões dos binários e a presença da unit do systemd.

## Capabilities

### New Capabilities
- `ssh-server`: Execução de servidor SSH (Dropbear) no boot, permitindo login remoto via porta 22 (usuário root) quando uma interface de rede compatível (USB Wi-Fi/Ethernet) estiver conectada.

### Modified Capabilities
*(Nenhuma especificação existente teve seus requisitos alterados. A especificação `system-services` foca na remoção de serviços desnecessários como IR/cron, enquanto `ssh-server` governa o novo serviço de acesso remoto).*

## Impact

- **Código e features**: Nova pasta `features/45-ssh-dropbear` com descritor `feature.toml`, unit de serviço e script de suporte.
- **Armazenamento e imagem**: Acréscimo modesto de tamanho na partição `SYSTEM` ou `STORAGE` (< 2 MiB para binários do dropbear e chaves).
- **Dependências de compilação**: Binários armhf compatíveis com glibc 2.36 e arquitetura ARMv7-A.
- **Hardware**: Exige dongle USB Wi-Fi ou adaptador USB-Ethernet compatível plugado na porta OTG do R36S para acesso de rede.
