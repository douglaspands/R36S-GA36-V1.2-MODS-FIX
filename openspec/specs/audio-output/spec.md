# audio-output Specification

## Purpose
Configurar a saída de som do R36S (codec interno do A33 e amplificador externo): volume 0 que silencia, volume salvo aplicado no boot e folga no buffer de áudio contra os pipocos. Também registrar na p1 o que o aparelho expõe e aplica, e oferecer uma chave para voltar ao som de fábrica.

## Requirements
### Requirement: Volume zero silencia
Fora do modo original, `audio.volume` igual a 0 SHALL silenciar a saída por completo (`speaker volume control` em 0). Qualquer valor acima de 0 SHALL devolver o som no nível correspondente, pela escala de fábrica (20 + volume × 0,43). Os botões de volume SHALL manter o comportamento de passo de fábrica (passo de 3 em `audio.volume`, de 0 a 100, com repetição ao segurar).

#### Scenario: Descer até zero
- **WHEN** o usuário segura o botão de volume até `audio.volume` chegar a 0
- **THEN** o `speaker volume control` fica em 0 e não sai som nem chiado do alto-falante com o volume parado

#### Scenario: Subir a partir de zero
- **WHEN** o usuário aperta o botão de aumentar com `audio.volume` em 0
- **THEN** `audio.volume` passa a 3 e o `speaker volume control` passa ao valor de fábrica para 3 (21)

### Requirement: Volume salvo aplicado no boot
No boot, o ganho analógico SHALL ser ajustado de acordo com o `audio.volume` salvo no `emuelec.conf`, sem esperar o primeiro toque num botão de volume. O mesmo ajuste SHALL ser reaplicado depois de cada troca do caminho de saída (`Speaker Function`), feita no boot, ao abrir e fechar um jogo e ao acordar da suspensão.

#### Scenario: Volume baixo salvo
- **WHEN** o aparelho liga com `audio.volume=29` no `emuelec.conf`
- **THEN** antes de o EmulationStation abrir, o `speaker volume control` já é 32 (o correspondente a 29)

#### Scenario: Retorno da suspensão
- **WHEN** o aparelho acorda da suspensão e o sistema religa a saída e troca o `Speaker Function`
- **THEN** o ganho analógico corresponde ao `audio.volume` salvo

#### Scenario: Troca de caminho ao abrir um jogo
- **WHEN** o lançador de jogos executa `amixer cset name='Speaker Function' ...`
- **THEN** logo em seguida o `audio-ganho aplica` roda e o ganho analógico corresponde ao `audio.volume` salvo

### Requirement: Volume guardado em arquivo próprio
O volume SHALL ser guardado também num arquivo próprio da feature (`r36-audio.volume`, na p8), que vale mais que o `audio.volume` do `emuelec.conf` na leitura. O sistema SHALL manter `audio.volume` no `emuelec.conf` sincronizado em tempo real pelos botões de volume e SHALL reaplicar o valor de `r36-audio.volume` no `emuelec.conf` durante o encerramento do sistema (shutdown/reboot), impedindo que a sobrescrita de memória do EmulationStation reverta o volume salvo. Sem nenhum dos dois, vale o padrão 29.

#### Scenario: Reiniciar pelo menu do EmulationStation
- **WHEN** o usuário baixa o volume pelos botões e reinicia o aparelho pelo menu do EmulationStation
- **THEN** no boot seguinte e no encerramento, o `emuelec.conf` e o `speaker volume control` preservam e refletem o volume real deixado pelo usuário

#### Scenario: Ajuste em tempo real pelos botões
- **WHEN** o usuário aperta os botões de volume
- **THEN** `r36-audio.volume` e `audio.volume` em `emuelec.conf` são atualizados imediatamente com o novo valor

### Requirement: Folga no buffer de áudio do RetroArch
No boot, o `retroarch.cfg` da p8 SHALL passar a ter `audio_latency = "96"` se estiver em `"64"`, e `audio_resampler_quality = "1"` se estiver em `"2"`. Um valor diferente desses (escolhido pelo usuário) SHALL NOT ser alterado. Nenhuma outra chave do arquivo SHALL ser alterada.

#### Scenario: Cartão com valores de fábrica
- **WHEN** o `retroarch.cfg` da p8 tem `audio_latency = "64"` e `audio_resampler_quality = "2"`
- **THEN** depois do boot ele tem `audio_latency = "96"` e `audio_resampler_quality = "1"`, e as demais linhas estão iguais, inclusive `video_threaded = "true"`

#### Scenario: Valor escolhido pelo usuário
- **WHEN** o `retroarch.cfg` tem `audio_latency = "128"`
- **THEN** depois do boot ele continua com `audio_latency = "128"`

#### Scenario: Pipocos em cena pesada
- **WHEN** o usuário joga nas telas em que ouvia pipocos antes da mudança
- **THEN** os pipocos somem ou ficam claramente mais raros

### Requirement: Chave para voltar ao som de fábrica
Um arquivo chamado `r36-audio-original` na raiz da p1 SHALL desligar a correção no boot seguinte. Isso inclui:
- volume 0 na escala de fábrica (`speaker volume control` = 20, sem mudo);
- `audio_latency` e `audio_resampler_quality` de volta a `"64"` e `"2"`, só se estiverem nos valores que a correção grava.

Remover o arquivo SHALL religar a correção no boot seguinte.

#### Scenario: Comparar com o original
- **WHEN** o usuário cria `r36-audio-original` na p1 pelo PC e liga o aparelho
- **THEN** o volume 0 volta a dar `speaker volume control` = 20 e o `retroarch.cfg` volta a `audio_latency = "64"` e `audio_resampler_quality = "2"`

#### Scenario: Religar
- **WHEN** o usuário apaga `r36-audio-original` e liga o aparelho
- **THEN** a correção volta a valer integralmente

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
