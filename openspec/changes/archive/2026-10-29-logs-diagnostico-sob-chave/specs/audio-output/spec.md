# Spec Delta

## MODIFIED Requirements

### Requirement: Diagnóstico de áudio na p1
Quando a raiz da p1 tiver o arquivo vazio `r36-diagnostico`, o sistema SHALL gravar a cada boot `r36-audio.log` na raiz da p1, substituindo o anterior, com os controles do mixer, o dump da interface de registradores do driver, o `speaker volume control` e o `headphone volume control` antes e depois de uma troca de `Speaker Function`, o modo e os valores aplicados. Sem esse arquivo, o sistema SHALL NOT gravar o log nem fazer as leituras de diagnóstico, e SHALL aplicar o modo, as chaves do RetroArch, o `Speaker Function` e o volume salvo do mesmo modo. Sem a p1 ou sem a interface, o serviço SHALL seguir sem travar o boot.

#### Scenario: Log após o boot
- **WHEN** a p1 tem `r36-diagnostico` e o usuário lê a p1 no PC depois de ligar o aparelho
- **THEN** `r36-audio.log` existe e mostra os controles do mixer, os volumes antes e depois do `Speaker Function`, o modo e os valores aplicados

#### Scenario: Sem a chave de diagnóstico
- **WHEN** a p1 não tem `r36-diagnostico` e o aparelho liga
- **THEN** `r36-audio.log` não é criado nem alterado, e o `Speaker Function`, as chaves de áudio do `retroarch.cfg` e o volume salvo são aplicados como com a chave

#### Scenario: p1 indisponível
- **WHEN** `/storage/roms` não está montado em até 20 s
- **THEN** o serviço termina sem erro, o boot segue e o EmulationStation abre normalmente

#### Scenario: Interface ausente
- **WHEN** a p1 tem `r36-diagnostico` e o caminho da interface de registradores não existe no aparelho
- **THEN** o log registra que não há interface, o som sai normalmente e nenhum erro aparece

### Requirement: Amostragem do codec com áudio tocando
Quando a raiz da p1 tiver o arquivo vazio `r36-diagnostico`, o sistema SHALL gravar nos primeiros minutos do boot `r36-audio-dac.log` na raiz da p1 com o dump do codec e os controles do mixer a cada mudança de estado. Esse registro SHALL ser só de leitura (nenhuma escrita em registrador), ter tamanho máximo e não atrasar o boot. Sem esse arquivo, o sistema SHALL NOT ler o codec para esse fim nem criar o log.

#### Scenario: Log com som tocando
- **WHEN** a p1 tem `r36-diagnostico` e o usuário deixa a música do menu e um jogo tocarem nos primeiros minutos do boot
- **THEN** `r36-audio-dac.log` tem uma entrada por mudança de estado do codec, com o dump completo

#### Scenario: Sem a chave de diagnóstico
- **WHEN** a p1 não tem `r36-diagnostico`
- **THEN** o amostrador termina sem erro e sem criar o arquivo

#### Scenario: Sem interface ou sem p1
- **WHEN** a interface de registradores ou a p1 não existe
- **THEN** o amostrador termina sem erro e sem criar o arquivo
