# Spec Delta

## ADDED Requirements

### Requirement: mGBA recompilado para o A33
A imagem SHALL trazer o core `mgba_a33`, compilado pelo `./cores.sh` com otimizações para a arquitetura Cortex-A7 do A33, ao lado do `mgba` original da base e sem substituí-lo. Ele SHALL manter a compatibilidade com saves e opções do core mGBA original e estar disponível para seleção no menu do EmulationStation.

#### Scenario: Original intocado
- **WHEN** o SYSTEM da imagem gerada é comparado com o da base
- **THEN** `mgba_libretro.so` e `mgba_libretro.info` permanecem inalterados, e `mgba_a33_libretro.so` e `.info` estão presentes em `/usr/lib/libretro`

#### Scenario: Compatibilidade e saves compartilhados
- **WHEN** o usuário alterna um jogo entre o `mgba` original e o `mgba_a33`
- **THEN** o `mgba_a33` carrega os mesmos arquivos de save de bateria (.srm) e preserva as configurações do core

#### Scenario: Disponível no EmulationStation
- **WHEN** o `es_systems.cfg` da imagem gerada é inspecionado
- **THEN** a entrada `mgba_a33` está presente na lista de cores do sistema `gba`, mantendo o `gpsp` como padrão
