# Spec Delta

## ADDED Requirements

### Requirement: Menu do RetroArch em inglês
A imagem gerada SHALL deixar o menu do RetroArch em inglês, o idioma da imagem base, enquanto o sistema e o EmulationStation continuam em português do Brasil.

#### Scenario: Menu aberto durante um jogo
- **WHEN** o usuário abre o menu do RetroArch durante um jogo
- **THEN** os textos do menu aparecem em inglês

#### Scenario: Configuração conferida no PC
- **WHEN** a p8 da imagem gerada é inspecionada
- **THEN** a configuração do RetroArch declara `user_language` com o valor da imagem base (`0`), e a do EmulationStation continua com `Language` = `pt_BR`

## REMOVED Requirements

### Requirement: Menu do RetroArch em português do Brasil
**Reason**: O usuário prefere o menu do RetroArch em inglês por padrão.
**Migration**: Para voltar ao português, escolha o idioma no próprio RetroArch (Settings > User > Language) e salve a configuração.
