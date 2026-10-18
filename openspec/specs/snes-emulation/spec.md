# snes-emulation Specification

## Purpose
Definir qual emulador e core o Super Nintendo usa por padrão na imagem gerada, priorizando a leveza no hardware do A33 sem remover as alternativas.

## Requirements

### Requirement: snes9x2005_plus como core padrão do SNES
A configuração do EmuELEC SHALL fazer os jogos de Super Nintendo abrirem no core `snes9x2005_plus_a33` do RetroArch, o snes9x2005_plus recompilado para o A33, sem o usuário precisar escolher o core.

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmuELEC declara `snes.emulator=libretro` e `snes.core=snes9x2005_plus_a33`

#### Scenario: Jogo de SNES sem escolha prévia
- **WHEN** o usuário abre um jogo de SNES que não tem core próprio escolhido
- **THEN** o jogo roda no snes9x2005_plus_a33, e o registro térmico traz o core `snes9x2005_plus_a33` nas linhas desse jogo

### Requirement: Outros cores de SNES continuam disponíveis
O snes9x2005_plus original, o snes9x, o snes9x2002 e o snes9x2010 SHALL continuar instalados e selecionáveis pelo menu do EmulationStation, por sistema ou por jogo.

#### Scenario: Jogo escolhido para outro core
- **WHEN** o usuário escolhe o snes9x2005_plus original para um jogo específico de SNES no menu do ES
- **THEN** esse jogo abre no snes9x2005_plus, e os demais jogos de SNES continuam no snes9x2005_plus_a33

### Requirement: Variantes do SNES não mudam
O padrão de core dos sistemas `snesh` e `snesmsu1` SHALL permanecer o da imagem base.

#### Scenario: Configuração das variantes
- **WHEN** a configuração do EmuELEC da imagem é inspecionada
- **THEN** ela não declara `snesh.core` nem `snesmsu1.core`

### Requirement: snes9x2005_plus recompilado para o A33
A imagem SHALL trazer o core `snes9x2005_plus_a33`, do mesmo fonte do `snes9x2005_plus` da base e compilado pelo `./cores.sh` com a variante vencedora da avaliação registrada em `cores/snes9x2005_plus/RESULTADOS.md`, ao lado do original e sem substituí-lo. Ele SHALL manter o nome de biblioteca do original, para compartilhar as opções do core e os saves. As variantes que perderam a avaliação SHALL ficar fora da imagem.

#### Scenario: Original intocado
- **WHEN** o SYSTEM da imagem gerada é comparado com o da base
- **THEN** `snes9x2005_plus_libretro.so` e `snes9x2005_plus_libretro.info` são idênticos aos da base, e `snes9x2005_plus_a33_libretro.so` e `.info` são novos em `/usr/lib/libretro`

#### Scenario: Save compartilhado
- **WHEN** o usuário salva o jogo no snes9x2005_plus original e abre o mesmo jogo no snes9x2005_plus_a33
- **THEN** o snes9x2005_plus_a33 carrega o mesmo save de bateria e usa as mesmas opções do core

#### Scenario: Lista de cores do SNES
- **WHEN** o `es_systems.cfg` da imagem é comparado com o da base
- **THEN** a única diferença é a entrada `snes9x2005_plus_a33` acrescentada ao fim da lista de cores do sistema `snes`, sem mudar o core marcado como padrão no ES nem os sistemas `snesh` e `snesmsu1`

#### Scenario: Variantes perdedoras fora da imagem
- **WHEN** o SYSTEM da imagem gerada é inspecionado
- **THEN** não há em `/usr/lib/libretro` os cores `snes9x2005_plus_a33_o3`, `_pgo_treino`, `_pgo` nem as variantes `snes9x2010_a33_*`
