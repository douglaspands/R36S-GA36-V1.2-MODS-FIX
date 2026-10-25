# Spec Delta: splash-screens

## MODIFIED Requirements

### Requirement: Tela de carregamento de jogo com símbolo
Ao abrir um jogo sem tela personalizada em `/storage/roms/splash`, a imagem gerada SHALL mostrar um ícone de controle centralizado num fundo escuro, sem texto, em 640x480.

#### Scenario: Abrir um jogo
- **WHEN** o usuário abre um jogo de NES (ou de qualquer outro sistema suportado) sem tela personalizada, mesmo em cartão gravado com `--keep-storage` ou `--part system`
- **THEN** o aparelho mostra o ícone de controle lido a partir da partição `SYSTEM` (`/usr/config/splash/loading-game.png`), sem texto e sem exibir a arte de fábrica do God of War

#### Scenario: Tela personalizada continua prioritária
- **WHEN** existe `/storage/roms/splash/nes.png`
- **THEN** essa imagem é mostrada no lugar do ícone
