# display-aspect-ratio Specification

## Purpose
Definir a proporção de tela padrão dos jogos na imagem gerada: cada core usa a proporção que ele mesmo informa, em vez de uma proporção fixa imposta pelo sistema.

## Requirements

### Requirement: Proporção "core provided" como padrão
A configuração global do EmuELEC SHALL declarar a proporção de tela dos jogos como "core provided", para que cada core use a proporção que informa. A imagem NÃO SHALL forçar 4:3 nem outra proporção fixa para todos os jogos.

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do EmuELEC declara `global.ratio=core`, e não `4/3`

#### Scenario: Jogo de proporção não 4:3
- **WHEN** o usuário abre um jogo cujo core informa uma proporção diferente de 4:3
- **THEN** o RetroArch exibe o jogo na proporção informada pelo core, e o `aspect_ratio_index` gravado para a sessão é `22`

### Requirement: Proporção por sistema continua escolhível
A escolha de proporção feita pelo usuário no menu do EmulationStation, para um sistema ou jogo, SHALL continuar valendo sobre o padrão global.

#### Scenario: Sistema com proporção própria
- **WHEN** o usuário escolhe outra proporção para um sistema no menu do ES
- **THEN** os jogos desse sistema usam a proporção escolhida, e os demais continuam em "core provided"
