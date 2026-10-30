# Spec Delta

## ADDED Requirements

### Requirement: Log de brilho sob a chave
O log do ajuste de brilho (`r36-brilho.log`) SHALL ser gravado na raiz da p1 somente quando existir o arquivo vazio `r36-diagnostico` na raiz da p1. Sem ele, o sistema SHALL NOT criar nem atualizar esse arquivo, e o ajuste de brilho SHALL funcionar do mesmo modo.

#### Scenario: Sem a chave
- **WHEN** a p1 não tem `r36-diagnostico` e o usuário ajusta o brilho
- **THEN** o brilho muda e persiste, e `r36-brilho.log` não é criado nem alterado

#### Scenario: Com a chave
- **WHEN** a p1 tem `r36-diagnostico` e o usuário ajusta o brilho
- **THEN** `r36-brilho.log` registra o dispositivo de entrada, o tipo de evento do D-pad (botão ou eixo), o código do L3 quando visto e os níveis aplicados
