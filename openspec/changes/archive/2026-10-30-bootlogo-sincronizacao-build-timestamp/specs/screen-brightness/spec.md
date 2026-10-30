# Spec Delta

## MODIFIED Requirements

### Requirement: Nível persistente
O sistema SHALL guardar o nível escolhido num arquivo próprio da p8 (`r36-brilho.level`) e SHALL aplicá-lo no boot, ao acordar da suspensão e a cada ajuste. O sistema SHALL manter `brightness.level=<valor>` no `emuelec.conf` sincronizado em tempo real com o nível salvo nos subcomandos de salvamento, boot e redefinição para o padrão, e SHALL restaurar o valor salvo no `emuelec.conf` durante o encerramento do sistema para evitar sobrescrita pelo EmulationStation.

#### Scenario: Depois de reiniciar
- **WHEN** o usuário reduz o brilho, desliga e liga o aparelho
- **THEN** a tela volta ao nível escolhido e o `emuelec.conf` contém o `brightness.level` correspondente ao valor ajustado

#### Scenario: Ajuste em tempo real
- **WHEN** o usuário ajusta o brilho pelo atalho FN + D-pad e solta a tecla
- **THEN** `r36-brilho.level` e `brightness.level` no `emuelec.conf` são atualizados imediatamente com o novo nível

### Requirement: Sincronização em tempo real na interface do EmulationStation
O sistema SHALL sincronizar o valor de `brightness.level` diretamente no cache de memória do EmulationStation (`SystemConf`) ao salvar o brilho ajustado via FN + D-pad, de forma que o menu de configurações do sistema ("Configurações do Sistema" -> "BRILHO") reflita imediatamente o valor real sem necessidade de reiniciar o frontend.

#### Scenario: Reflexão no menu de configurações do EmulationStation
- **WHEN** o usuário altera o brilho através do atalho FN + D-pad enquanto o EmulationStation está em execução
- **THEN** ao abrir o menu principal do EmulationStation ("Configurações do Sistema"), o controle deslizante de brilho exibe exatamente a nova porcentagem ajustada

#### Scenario: Depois de dormir
- **WHEN** o usuário reduz o brilho, suspende o aparelho pelo botão de energia e o acorda
- **THEN** a tela volta ao nível escolhido e não a 80

#### Scenario: Sem nível salvo
- **WHEN** o arquivo do nível não existe
- **THEN** o sistema usa o `brightness.level` do `emuelec.conf` (80 de fábrica) e o comportamento é o de antes

#### Scenario: Cartão que já tinha o arquivo
- **WHEN** a p8 já tem o arquivo do nível e só o `system` é regravado
- **THEN** o nível salvo continua valendo e é sincronizado no `emuelec.conf`
