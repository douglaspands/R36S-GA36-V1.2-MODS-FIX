---
trigger: always_on
description: Regras de segurança, proteção da imagem base e restrições de comandos do clone R36S
---

# Regras de Segurança e Proteção da Imagem Base

- **Proteção da base e imagens**:
  - NUNCA editar nem deletar arquivos sob `base/**` ou imagens `*.img`.
  - A imagem base `base/R36S GA36-MB V1.2-20260416 - Emuelec - No ROMS.img` é imutável.
- **Proibição estrita de comandos destrutivos**:
  - `rm *base/*`, `rm *.img`, `rm -rf /`, `rm -rf /*`, `rm -rf ~*`.
  - `dd *of=/dev/*`, `sudo dd *`, `mkfs* /dev/*`, `wipefs`, `shred`, `blkdiscard`, `sfdisk /dev/*`.
- **Sem sudo**:
  - Nunca propor comandos com `sudo`.
  - Para validação de gravação, usar `./flash.sh --target-file`.
  - Qualquer ação que exija root ou acesso físico ao cartão SD (`./flash.sh --device`) é instrução para o usuário executar no terminal dele.
