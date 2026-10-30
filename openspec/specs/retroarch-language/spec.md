# retroarch-language Specification

## Purpose
O menu do RetroArch acompanha o idioma escolhido no EmuELEC, para que quem troca o idioma do aparelho (por exemplo, a criança que usa o aparelho) o veja nos dois menus, sem abrir o menu do RetroArch.

## Requirements

### Requirement: Idioma do RetroArch segue o do EmuELEC
O sistema SHALL, antes de cada jogo aberto no RetroArch, ajustar o idioma do menu do RetroArch ao idioma escolhido no EmuELEC, para os idiomas que o RetroArch traduz: `pt_BR` em português do Brasil, `pt_PT` em português de Portugal, `en_US` e `en_GB` em inglês, `es_ES` em espanhol, `fr_FR` em francês, `de_DE` em alemão e `it_IT` em italiano.

#### Scenario: Idioma trocado no EmuELEC
- **WHEN** o usuário troca o idioma do EmuELEC de `pt_BR` para `en_US` e abre um jogo
- **THEN** o menu do RetroArch desse jogo aparece em inglês

#### Scenario: Volta ao português
- **WHEN** o usuário volta o idioma do EmuELEC para `pt_BR` e abre um jogo
- **THEN** o menu do RetroArch aparece em português do Brasil

#### Scenario: Cartão que manteve a p8
- **WHEN** o cartão foi gravado com `--keep-storage`, com o RetroArch ainda em inglês, e o idioma do EmuELEC é `pt_BR`
- **THEN** o primeiro jogo abre o menu do RetroArch em português do Brasil

### Requirement: Cada fonte do idioma é comparada com o próprio valor guardado
O sistema SHALL ler o idioma do `emuelec.conf` e do `es_settings.cfg` e comparar cada um com o valor que ele tinha no último ajuste; vale a fonte que mudou, e o `emuelec.conf` quando as duas mudaram. Ao ajustar, o sistema SHALL guardar os dois valores atuais de uma vez, de modo que fontes que divergem entre si não alterem o idioma a cada jogo.

#### Scenario: Troca gravada só no es_settings.cfg
- **WHEN** o `system.language` do `emuelec.conf` é igual ao do último ajuste, mas o `Language` do `es_settings.cfg` mudou, e o usuário abre um jogo
- **THEN** o menu do RetroArch passa a usar o idioma do `es_settings.cfg`

#### Scenario: Troca gravada só no emuelec.conf
- **WHEN** o `system.language` do `emuelec.conf` mudou e o `Language` do `es_settings.cfg` é igual ao do último ajuste
- **THEN** o menu do RetroArch passa a usar o idioma do `emuelec.conf`

#### Scenario: Os dois arquivos mudaram
- **WHEN** o `emuelec.conf` e o `es_settings.cfg` trazem idiomas diferentes, e os dois diferem dos valores do último ajuste
- **THEN** o menu do RetroArch usa o idioma do `emuelec.conf`

#### Scenario: Arquivos que divergem não oscilam
- **WHEN** o `emuelec.conf` e o `es_settings.cfg` trazem idiomas diferentes entre si, sem nenhum deles mudar de um jogo para o outro, e o usuário abre vários jogos seguidos
- **THEN** só o primeiro jogo ajusta o `retroarch.cfg` e grava o estado; os seguintes não escrevem nada e a escolha feita no menu do RetroArch continua valendo

#### Scenario: Nenhum mudou
- **WHEN** os dois arquivos trazem os valores do último ajuste
- **THEN** o `retroarch.cfg` e o registro do último idioma não são tocados

### Requirement: Idioma sem tradução no RetroArch fica como está
Para um idioma do EmuELEC que o sistema não sabe traduzir, ou quando o idioma não puder ser lido, o sistema SHALL manter o idioma do menu do RetroArch como estava, e o jogo SHALL abrir normalmente.

#### Scenario: Idioma fora da tabela
- **WHEN** o idioma do EmuELEC é um que o RetroArch do aparelho não traduz e o usuário abre um jogo
- **THEN** o idioma do menu do RetroArch não muda e o jogo abre

#### Scenario: Idioma ilegível
- **WHEN** o arquivo de configuração do EmuELEC não tem o idioma ou não existe
- **THEN** o idioma do menu do RetroArch não muda e o jogo abre

### Requirement: Escolha feita no menu do RetroArch dura até a próxima troca no EmuELEC
O sistema SHALL ajustar o idioma do RetroArch só quando o idioma do EmuELEC mudar desde o último jogo; enquanto o idioma do EmuELEC não mudar, o idioma que o usuário escolheu no menu do RetroArch SHALL valer.

#### Scenario: Idioma escolhido direto no RetroArch
- **WHEN** o usuário troca o idioma no menu do RetroArch e abre outro jogo, sem ter mexido no idioma do EmuELEC
- **THEN** o RetroArch continua no idioma que ele escolheu

#### Scenario: Troca posterior no EmuELEC
- **WHEN** depois disso o usuário troca o idioma do EmuELEC e abre um jogo
- **THEN** o RetroArch passa a usar o idioma novo do EmuELEC

### Requirement: Registro do ajuste de idioma só com a chave de diagnóstico
Com o arquivo vazio `r36-diagnostico` na raiz da R36-ROMS, o sistema SHALL registrar em um log da p1 o idioma lido do EmuELEC e o que foi gravado no RetroArch; sem a chave, SHALL NOT gravar nada na p1.

#### Scenario: Com a chave
- **WHEN** `r36-diagnostico` existe e o usuário abre um jogo
- **THEN** o log traz o idioma lido e o resultado (trocado, mantido ou sem tradução)

#### Scenario: Sem a chave
- **WHEN** `r36-diagnostico` não existe e o usuário abre um jogo
- **THEN** nenhum log do idioma é criado ou alterado na p1
