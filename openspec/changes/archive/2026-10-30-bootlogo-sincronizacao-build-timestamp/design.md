# Design

## Context

O R36S clone (GA36-MB V1.2) utiliza U-Boot que lê `bootlogo.bmp` da partição 2 (`R36-BOOT`, FAT16). A base traz um arquivo BMP 24bpp de 640x480 com a inscrição "OPEN SOURCE".

O EmuELEC armazena configurações globais em `/storage/.config/emuelec/configs/emuelec.conf` (p8), incluindo `brightness.level` e `audio.volume`. O script `audio-ganho` (feature `46-audio`) já grava em tempo real em `r36-audio.volume` e no `emuelec.conf`, enquanto o `brilho-aplica` (feature `62-brilho-fn`) apenas grava em `r36-brilho.level`, deixando o `brightness.level` desatualizado. Além disso, o EmulationStation mantém os dados carregados em memória RAM durante toda a sua execução e, ao receber ordens de encerramento ou reinício pelo menu, faz o dump da sua memória de volta ao `emuelec.conf`, sobrescrevendo valores que foram ajustados em tempo de execução via botões físicos externos.

No pipeline de compilação de imagens (`tools/r36img/build.py`), a função interna `build()` já aceita o argumento `timestamp=...`, porém a interface de linha de comando (`build.sh`) não expunha essa opção no parser `argparse`.

## Goals / Non-Goals

**Goals:**
- Personalizar o `bootlogo.bmp` do U-Boot com o texto exato "GA36-MB V1.2-20260416" mantendo formato e resolução da base na feature `30-telas-icone-controle`.
- Sincronizar `brightness.level` no `emuelec.conf` imediatamente ao soltar o atalho FN + D-pad no `brilho-aplica salva`, bem como no boot e reset padrão.
- Blindar o `emuelec.conf` contra a sobrescrita do EmulationStation no shutdown/reboot, garantindo que os valores salvos de áudio e brilho persistam.
- Expor `--timestamp` na CLI do build com validação rigorosa do formato `AAAAMMDD-HHMMSS`.

**Non-Goals:**
- Alterar as outras telas de boot (o ícone de controle em tela cheia do EmuELEC no framebuffer Linux permanece como está).
- Modificar o binário C++ do EmulationStation para alterar seu gerenciamento interno de memória.
- Modificar a imagem base imutável.

## Decisions

### Decisão 1: Geração e integração do `bootlogo.bmp` na feature `30-telas-icone-controle`
- **Abordagem**: A feature `30-telas-icone-controle` ganha a camada `boot/bootlogo.bmp`. Um script de processamento limpa a caixa delimitadora `y: 424..441, x: 201..446` da imagem base com `#ffffff` e renderiza o texto `"GA36-MB V1.2-20260416"` centralizado com tipografia limpa.
- **Alternativas consideradas**:
  - *Criar uma nova feature*: Desnecessário, pois a feature 30 é exatamente a responsável pelo conjunto de telas e identidades visuais de boot do sistema.

### Decisão 2: Atualização atômica do `emuelec.conf` no `brilho-aplica`
- **Abordagem**: Implementar em `brilho-aplica` a função `grava_emuelec()` equivalente à do `audio-ganho`, usando arquivo temporário `.r36tmp` para escrita atômica com substituição de linha `brightness.level=.*` (ou inserção caso ausente). Chamada em `salva`, `padrao` e `boot`.
- **Alternativas consideradas**:
  - *Chamar `set_ee_setting` do `/etc/profile.d/99-emuelec.conf`*: O `brilho-aplica` roda como script leve POSIX `/bin/sh` sem carregar o ambiente pesado do `/etc/profile`, garantindo execução rápida a cada evento de soltura do D-pad.

### Decisão 3: Sincronização no Shutdown via Systemd Unit (`r36-conf-sync.service`)
- **Abordagem**: Criar um serviço oneshot do systemd (ou adicionar gancho `ExecStop` associado ao shutdown) com `DefaultDependencies=no`, ordenado `Before=shutdown.target reboot.target poweroff.target halt.target` e `After=local-fs.target`. Antes de desmontar a partição STORAGE, ele lê `r36-audio.volume` e `r36-brilho.level` e regrava as chaves correspondentes no `emuelec.conf`.
- **Alternativas consideradas**:
  - *Modificar os scripts de shutdown do ES*: O ES chama `systemctl reboot/poweroff` diretamente através de wrappers ou chamadas C++; uma unit do systemd que roda no shutdown é a única garantia infalível de execução antes de desmontar o filesystem.

### Decisão 4: Suporte a `--timestamp` no CLI
- **Abordagem**: Em `tools/r36img/build.py`, adicionar `--timestamp` ao `_build_parser()`. Validar com regex `^\d{8}-\d{6}$`. Se informado, passar diretamente a `build(..., timestamp=args.timestamp)`.

## Risks / Trade-offs

- **[Risco] Corrupção do `emuelec.conf` em desligamentos abruptos**:
  $\rightarrow$ Mitigação: Sempre usar escrita atômica via arquivo temporário (`cat tmp > target` ou `mv`) e validação de valor numérico antes de gravar.
- **[Risco] Formato BMP incompatível com o leitor rígido do U-Boot**:
  $\rightarrow$ Mitigação: O arquivo deve ser rigorosamente BMP v3 24bpp (sem compressão, sem alpha channel, tamanho exato de 921654 bytes: 54 cabeçalho + 640x480x3). Testes automatizados verificarão o cabeçalho e tamanho.
- **[Risco] Sobrescrita de diretório ao passar `--timestamp` duplicado**:
  $\rightarrow$ Mitigação: A função `build()` já possui a trava que aborta com erro caso o diretório de destino `<timestamp>` já exista.

### Decisão 4: Sincronização em tempo real na memória RAM do EmulationStation (`SystemConf`)

- **Contexto:** Ao testar o atalho FN + D-pad, constatou-se que o volume ajustado refletia perfeitamente nas configurações do EmuELEC/EmulationStation, mas o brilho não. A engenharia reversa no assembly ARM do binário `/usr/bin/emulationstation` revelou que:
  1. O volume de áudio é consultado dinamicamente direto no mixer ALSA (`VolumeControl::getVolume()`), logo mudanças externas refletem instantaneamente no menu;
  2. O brilho da tela no menu ("Configurações do Sistema" -> "BRILHO", `0x20e0d0`) é lido exclusivamente de um cache em memória RAM (`SystemConf::getInstance()->get("brightness.level")`, uma `std::map<std::string, std::string>`), carregado do `emuelec.conf` apenas uma única vez na inicialização do executável.
  3. Modificações em disco (`emuelec.conf`) feitas pelo `brilho-aplica` durante a execução não são monitoradas pelo EmulationStation.
- **Solução adotada:** Implementação do utilitário `/usr/lib/r36/brilho-es-sync` (chamado por `brilho-aplica salva`, `padrao` e `boot`). O script:
  1. Localiza o PID de `emulationstation`;
  2. Lê o ponteiro do singleton `SystemConf` em endereço fixo no `.bss` (`0x006f0f0c`);
  3. Navega na árvore binária balanceada (`std::_Rb_tree` de `std::map`) até a chave `"brightness.level"`;
  4. Atualiza diretamente o buffer SSO (Small String Optimization) e o tamanho da string na memória do processo via `/proc/<pid>/mem`.
- **Benefício:** Atualização atômica em microssegundos, sem reiniciar o EmulationStation, garantindo que o slider do menu reflita 100% o valor do atalho de hardware.
