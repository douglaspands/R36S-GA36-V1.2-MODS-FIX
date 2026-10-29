# Spec Delta

## MODIFIED Requirements

### Requirement: Chave para desligar e log na p1
O serviço SHALL obedecer ao arquivo vazio `r36-<sistema>-sem-shader` na raiz da R36-ROMS, desfazendo só o que ele mesmo criou, e SHALL registrar o que fez em `r36-shader-<sistema>.log` na raiz da R36-ROMS somente quando existir o arquivo vazio `r36-diagnostico` na raiz da R36-ROMS. Sem `r36-diagnostico`, o serviço SHALL NOT criar nem atualizar o log e SHALL fazer o mesmo trabalho.

#### Scenario: Desligar pelo PC
- **WHEN** existe `r36-<sistema>-sem-shader` e o aparelho é religado
- **THEN** a linha do `emuelec.conf` e os presets criados pelo serviço somem, os do usuário ficam, e, havendo `r36-diagnostico`, o log registra a chave

#### Scenario: Sem a chave de diagnóstico
- **WHEN** a p1 não tem `r36-diagnostico` e o aparelho liga
- **THEN** `r36-shader-<sistema>.log` não é criado nem alterado, e o shader, os presets e a lista "SHADER SET" ficam como com a chave
