# retroarch-config-paths Specification

## Purpose
TBD - created by archiving change es-shader-config-gpsp-ghost. Update Purpose after archive.

## Requirements

### Requirement: Pastas de configuração do RetroArch existentes e graváveis
O `retroarch.cfg` SHALL apontar `rgui_config_directory`, `savefile_directory`, `log_dir` e `osk_overlay_directory` para pastas da partição de armazenamento (p8) que existem na imagem base ou são criadas pelo próprio RetroArch, e SHALL NOT apontar nenhum deles para uma pasta da raiz do SYSTEM, que é somente leitura. Os valores são `~/.config/retroarch/config`, `~/savefiles`, `~/.config/emuelec/logs` e `~/overlays/keyboards`.

#### Scenario: Cartão novo
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** o `retroarch.cfg` declara `rgui_config_directory = "~/.config/retroarch/config"`, `savefile_directory = "~/savefiles"`, `log_dir = "~/.config/emuelec/logs"` e `osk_overlay_directory = "~/overlays/keyboards"`, e nenhuma dessas chaves aponta para `/config`, `/saves`, `/logs` ou `/overlays`

#### Scenario: Nenhum caminho absoluto fora de p8, /usr e /tmp
- **WHEN** os valores de diretório do `retroarch.cfg` da imagem são conferidos no PC
- **THEN** cada um começa por `~`, `/usr`, `/tmp` ou `/storage`, com a exceção de `recording_config_directory`, que fica como está

### Requirement: Salvar pelo menu do RetroArch grava na p8
Salvar opções de core, override de core ou de jogo, preset de shader ou remap pelo menu do RetroArch SHALL gravar o arquivo em `/storage/.config/retroarch/config/<core>/`, sem erro, e o RetroArch SHALL lê-lo no jogo seguinte.

#### Scenario: Salvar opções do core
- **WHEN** o usuário muda uma opção do core no menu do RetroArch e escolhe salvar as opções do core
- **THEN** o arquivo `<core>.opt` aparece em `/storage/.config/retroarch/config/<core>/` e o aparelho não mostra erro de gravação

#### Scenario: Opção salva vale no jogo seguinte
- **WHEN** o usuário reabre um jogo do mesmo core depois de salvar
- **THEN** a opção salva está aplicada

### Requirement: Correção em cartão já gravado sem tocar nas escolhas do usuário
No boot, o sistema SHALL trocar cada um dos quatro valores de fábrica no `retroarch.cfg` da p8 pelo valor corrigido, e SHALL NOT alterar uma chave cujo valor já seja outro. A troca SHALL ser feita no mesmo arquivo e não SHALL tocar nas demais linhas. O sistema SHALL funcionar com `--keep-storage` e SHALL NOT travar o boot se o arquivo não existir.

#### Scenario: Cartão gravado com --keep-storage
- **WHEN** o `retroarch.cfg` da p8 tem `rgui_config_directory = "/config"` e o aparelho liga com o SYSTEM novo
- **THEN** depois do boot o valor é `~/.config/retroarch/config`

#### Scenario: Valor já escolhido pelo usuário
- **WHEN** o `retroarch.cfg` tem `savefile_directory` com um valor diferente de `/saves`
- **THEN** o boot não o altera

#### Scenario: Sem retroarch.cfg
- **WHEN** o `retroarch.cfg` não existe na p8
- **THEN** o serviço termina sem erro e o boot segue

### Requirement: Log da correção só com a chave de diagnóstico
O serviço SHALL gravar o que fez em um arquivo legível pelo PC na raiz da R36-ROMS somente quando o arquivo vazio `r36-diagnostico` existir na raiz da R36-ROMS; sem a chave, SHALL NOT gravar nada na p1.

#### Scenario: Com a chave
- **WHEN** `r36-diagnostico` existe na p1 e o aparelho liga
- **THEN** `r36-retroarch.log` na p1 lista as chaves trocadas e os valores finais dos quatro caminhos

#### Scenario: Sem a chave
- **WHEN** `r36-diagnostico` não existe
- **THEN** o aparelho não cria nem altera `r36-retroarch.log`
