## ADDED Requirements

### Requirement: Menu do RetroArch em português do Brasil
A imagem gerada SHALL deixar o menu do RetroArch em português do Brasil, junto com o sistema e o EmulationStation, declarando `user_language = "7"` no `retroarch.cfg` de fábrica da p8.

#### Scenario: Menu aberto durante um jogo
- **WHEN** o usuário abre o menu do RetroArch durante um jogo, numa p8 gravada pela imagem
- **THEN** os textos do menu aparecem em português do Brasil

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do RetroArch declara `user_language = "7"` e a do EmulationStation declara `Language` = `pt_BR`

#### Scenario: Idioma trocado pelo usuário
- **WHEN** o usuário escolhe outro idioma em Settings > User Interface > Language e salva
- **THEN** o RetroArch mantém o idioma escolhido

## REMOVED Requirements

### Requirement: Menu do RetroArch em inglês
**Reason**: o usuário passou a querer o menu do RetroArch em português do Brasil, junto com o resto do sistema.
**Migration**: vale o requisito "Menu do RetroArch em português do Brasil", com `user_language = "7"`. Um cartão que mantém a p8 (`--keep-storage`) conserva o idioma que já tem; só uma p8 nova (`--wipe-storage`) recebe o padrão, ou o usuário troca pelo menu.
