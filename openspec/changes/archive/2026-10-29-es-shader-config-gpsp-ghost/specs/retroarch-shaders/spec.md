## ADDED Requirements

### Requirement: Shader escolhido no ES aplicado ao jogo
O shader escolhido em "SHADER SET" do EmulationStation, por jogo, sistema ou global, SHALL ser aplicado ao jogo iniciado, para qualquer `.glslp` listado. A prioridade SHALL ser jogo, sistema, global. `none`, `false`, `0` ou a ausência de escolha SHALL abrir o jogo sem shader, e a escolha SHALL NOT valer no jogo seguinte de outro sistema. O mesmo vale para o `gba.shaderset` padrão do GBA.

#### Scenario: Shader escolhido para um sistema
- **WHEN** o usuário escolhe `crt/<preset>.glslp` em "SHADER SET" de um sistema e abre um jogo dele
- **THEN** o RetroArch abre o jogo com esse preset aplicado

#### Scenario: Escolha por jogo vence a do sistema
- **WHEN** o sistema tem um shader escolhido e um jogo tem outro
- **THEN** o jogo abre com o shader do jogo, e os demais com o do sistema

#### Scenario: Nenhum shader
- **WHEN** o "SHADER SET" do sistema é `none` e o usuário abre um jogo
- **THEN** o jogo abre sem shader

#### Scenario: Escolha não vaza para outro sistema
- **WHEN** o usuário abre um jogo com shader e, em seguida, um jogo de outro sistema sem escolha de shader
- **THEN** o segundo jogo abre sem o shader do primeiro

#### Scenario: Padrão do GBA tem efeito
- **WHEN** o `emuelec.conf` tem `gba.shaderset=gba/gba-modern-remaster.glslp` e o usuário abre um jogo de GBA
- **THEN** o jogo abre com o `gba-modern-remaster` aplicado

#### Scenario: Nome com espaço
- **WHEN** o caminho do preset escolhido tem espaço
- **THEN** o shader é aplicado do mesmo jeito

### Requirement: Registro da aplicação do shader só com a chave de diagnóstico
Com o arquivo vazio `r36-diagnostico` na raiz da R36-ROMS, o sistema SHALL acrescentar a `r36-shader-gba.log` uma linha por jogo com o sistema, o valor de `shaderset` lido e o `video_shader` gravado; sem a chave, SHALL NOT gravar nada na p1.

#### Scenario: Com a chave
- **WHEN** `r36-diagnostico` existe e o usuário abre um jogo
- **THEN** a última linha do `r36-shader-gba.log` traz o sistema, o valor lido e o resultado

#### Scenario: Sem a chave
- **WHEN** `r36-diagnostico` não existe e o usuário abre um jogo
- **THEN** o `r36-shader-gba.log` não é criado nem alterado

### Requirement: Preset do ES entregue ao RetroArch pela linha de comando
O preset escolhido no "SHADER SET" SHALL chegar ao RetroArch como `--set-shader "/tmp/shaders/<preset>"` antes de `--config`, porque o RetroArch 1.17 ignora o `video_shader` do `retroarch.cfg` quando o jogo não tem preset automático. O sistema SHALL continuar gravando `video_shader` e `video_shader_enable = "true"` no `retroarch.cfg`.

#### Scenario: Jogo sem preset automático
- **WHEN** o usuário escolheu `rpi/zfast_crt_standard.glslp` para o SNES e abre um jogo dele
- **THEN** a linha de comando do RetroArch no `emuelec.log` traz `--set-shader "/tmp/shaders/rpi/zfast_crt_standard.glslp"` e o jogo abre com o shader aplicado

#### Scenario: Nome com espaço na linha de comando
- **WHEN** o caminho do preset tem espaço
- **THEN** o `--set-shader` leva o caminho entre aspas e o shader é aplicado do mesmo jeito

#### Scenario: Sem escolha
- **WHEN** o `shaderset` é `none`, `false`, `0`, vazio, `true` ou `1`
- **THEN** o script não imprime `--set-shader` (o `true` e o `1` ficam com o `setsettings.sh`)
