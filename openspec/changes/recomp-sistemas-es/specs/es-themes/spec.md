# Spec Delta

## ADDED Requirements

### Requirement: Tema do sistema gba-recomp
O tema Epic Cody ML SHALL trazer uma pasta `gba-recomp/` com `theme.xml`, `logo.png`, `poster.png` e `system.png`, de modo que o sistema `gba-recomp` não caia no visual genérico. A arte SHALL ser derivada da do GBA com um selo "RECOMP" visível, para distinguir a lista dos jogos do core GBA.

#### Scenario: Sistema com arte própria
- **WHEN** o EmulationStation mostra a lista de sistemas com `gba-recomp` presente
- **THEN** o sistema aparece com logo, poster e imagem de sistema próprios, e o selo RECOMP o distingue do sistema `gba`

#### Scenario: Arquivos do tema presentes
- **WHEN** a pasta do tema na p8 da imagem gerada é inspecionada
- **THEN** `gba-recomp/` contém `theme.xml`, `logo.png`, `poster.png` e `system.png`

### Requirement: Textos de gba-recomp nos três idiomas
Os arquivos `_languages/pt-br.xml`, `es-latam.xml` e `en.xml` SHALL declarar as variáveis `gba-recomp.nameLabel`, `sys_line1`, `sys_line2`, `shortdescription` e `longdescription`, e o `theme.xml` do sistema SHALL consumi-las. Nenhum texto SHALL ficar em inglês nos idiomas `pt-br` e `es-latam`, exceto termos técnicos preservados pelo tema (como "Recomp").

#### Scenario: Idioma português
- **WHEN** o tema está em `pt-br` e o jogador vê a lista de sistemas
- **THEN** a descrição de `gba-recomp` está em português

#### Scenario: Variável ausente
- **WHEN** os três arquivos de idioma são conferidos
- **THEN** cada um declara as cinco variáveis `gba-recomp.*`, sem nenhuma faltando

### Requirement: gba-recomp legível em 640x480
Os textos de `gba-recomp` SHALL caber na tela de 640x480, com `sys_line1` e `sys_line2` sem truncamento por reticências, na lista de sistemas e no cabeçalho da lista de jogos, respeitando as margens e o layout unificado do tema.

#### Scenario: Título sem truncamento
- **WHEN** a lista de sistemas mostra `gba-recomp` em qualquer um dos três idiomas
- **THEN** `sys_line1` e `sys_line2` aparecem inteiros, sem reticências

#### Scenario: Lista de jogos com o layout do tema
- **WHEN** o jogador abre a lista de `gba-recomp`
- **THEN** a lista usa o mesmo layout unificado dos demais sistemas, sem elemento cortado nem sobreposto à barra de atalhos
