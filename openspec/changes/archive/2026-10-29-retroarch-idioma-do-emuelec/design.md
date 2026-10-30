# Design

## Context

Ver `proposal.md` (Por quê). O que existe hoje, lido do repositório e do cartão do usuário (só leitura):

- **Idioma do EmuELEC.** A feature 10 grava `system.language=pt_BR` no `emuelec.conf` (p8, `/storage/.config/emuelec/configs/`) e `Language` = `pt_BR` no `es_settings.cfg` (`/storage/.config/emulationstation/`). O comentário do `emuelec.conf` lista os valores: `fr_FR, en_US, en_GB, de_DE, pt_BR, es_ES, it_IT, eu_ES, tr_TR, zh_CN`. No cartão do usuário os dois arquivos dizem `pt_BR`, então não dá para saber, só por eles, qual o ES grava ao trocar o idioma pelo menu.
- **Idioma do RetroArch.** É `user_language` no `retroarch.cfg` (números do RetroArch: `0` inglês, `1` japonês, `2` francês, `3` espanhol, `4` alemão, `5` italiano, `6` holandês, `7` português do Brasil, `8` português de Portugal...). A change `es-shader-config-gpsp-ghost` (D8) põe `7` no `retroarch.cfg` de fábrica.
- **Ponto de ganho.** O `emuelecRunEmu.sh` (feature 10) já chama o `shaderset-aplica` antes de cada jogo, e o RetroArch lê o `retroarch.cfg` ao abrir. O `retroarch.cfg` é regravado pelo RetroArch ao sair, com o `user_language` que estava em uso.
- **Pré-requisito.** A feature `56-retroarch-ajustes` e o ponto de chamada no `emuelecRunEmu.sh` vêm da change `es-shader-config-gpsp-ghost`, que precisa estar na `main` antes do apply.

## Goals / Non-Goals

**Goals:**
- Trocar o idioma no EmuELEC vale no menu do RetroArch no jogo seguinte, sem abrir o RetroArch.
- Uma escolha feita direto no menu do RetroArch não ser desfeita a cada jogo.
- Funcionar em qualquer cartão (`--keep-storage` incluído) e ser testável no PC.

**Non-Goals:**
- Idioma do sistema, do ES e dos temas; padrão de fábrica do `user_language`; idiomas sem tradução no RetroArch 1.17; acentos e fonte do RGUI.

## Decisions

### D1: Script próprio chamado pelo `emuelecRunEmu.sh`
Um `idioma-aplica` em `/usr/lib/r36/` (feature 56), chamado ao lado do `shaderset-aplica`, protegido por `[ -x ]`. Roda por `R36_ROOT` nos testes, como os outros.
- *Alternativa: serviço de boot.* Descartada: a troca de idioma no ES não reinicia o aparelho (reinicia só o ES); o jogo é o momento seguro em que o RetroArch lê o arquivo.
- *Alternativa: gravar `user_language` pelo `setsettings.sh`.* Descartada: duplicaria 592 linhas da base.

### D2: Fonte do idioma e verificação no aparelho
O script lê as DUAS fontes, só com o `read` do shell (sem processo novo e sem escrita no caminho comum): `system.language=` do `emuelec.conf` (mesma busca simples das outras chaves `system.*`) e `Language` do `es_settings.cfg`. Cada fonte é comparada com o **próprio valor guardado** (`r36-idioma`, D4): se o `emuelec.conf` mudou, vale o `emuelec.conf` (ele também vence quando as duas mudaram); senão, se o `es_settings.cfg` mudou, vale o dele; se nenhuma mudou, não faz nada. Comparar as duas fontes com um único idioma guardado oscilaria quando elas divergem (conf `pt_BR`, ES `en_US`: o jogo 1 aplica `pt_BR`, o jogo 2 vê o ES diferente e aplica `en_US`, o jogo 3 vê o conf diferente e volta a `pt_BR`, reescrevendo o `retroarch.cfg` e desfazendo a escolha do menu a cada jogo); com um valor guardado por fonte, só a primeira rodada escreve. Motivo: o `emuelec.conf` sempre tem `system.language` (build e feature 10), então a regra "o `emuelec.conf` vence sempre que tem a chave" nunca veria uma troca gravada só no `es_settings.cfg`. A task 1.1, no aparelho, confirma qual dos dois arquivos o ES grava; a regra acima vale para qualquer resposta. O valor lido é limpo de espaços e de CR.

**Ponto a confirmar na task 1.1.** O `emuelecRunEmu.sh` da base lê `/storage/.emulationstation/es_settings.cfg`, e o `idioma-aplica` lê `/storage/.config/emulationstation/es_settings.cfg` (o caminho do ES documentado acima). Se os dois caminhos forem arquivos diferentes no aparelho, a task 1.1 diz qual é o que o ES grava, e o `ESCFG` do script é ajustado. Não muda o código antes dessa confirmação.

### D3: Tabela fixa do código do EmuELEC para o número do RetroArch
`pt_BR`=7, `pt_PT`=8, `en_US`=0, `en_GB`=0, `es_ES`=3, `fr_FR`=2, `de_DE`=4, `it_IT`=5. Outros códigos (`eu_ES`, `tr_TR`, `zh_CN`...) ficam fora: o script não mexe e registra "sem tradução". Os números vêm da enumeração do RetroArch e são conferidos no binário do aparelho (as cadeias dos idiomas no `retroarch` do SYSTEM) na tarefa de verificação. A mesma tabela serve ao build (D6), cujo padrão é `en_US` (decisão do usuário): o idioma de fábrica de um `./build.sh` sem argumento é o inglês, `user_language = "0"`.

**Conferência no binário (task 1.2).** `usr/bin/retroarch` do SYSTEM da imagem base, lido sem montar (`mcopy ::/SYSTEM`, `unsquashfs -cat`, `strings`): é o RetroArch `1.17.0` (`[INFO] Version: 1.17.0`, `Built: Aug 18 2025`). Os rótulos do menu de idioma aparecem no pool de cadeias na ordem `English`, `Japanese`, `French - Français`, `Spanish - Español`, `German - Deutsch`, `Italian - Italiano`, `Dutch - Nederlands`, `Portuguese (Brazil) - Português (Brasil)`, `Portuguese (Portugal) - Português (Portugal)`, `Russian`..., que é a ordem de `RETRO_LANGUAGE_*` de 0 a 9 do `libretro.h` (`ENGLISH`=0, `JAPANESE`=1, `FRENCH`=2, `SPANISH`=3, `GERMAN`=4, `ITALIAN`=5, `DUTCH`=6, `PORTUGUESE_BRAZIL`=7, `PORTUGUESE_PORTUGAL`=8): os números da tabela batem. Depois do `Turkish` a ordem do pool deixa de seguir a enumeração (`English (United Kingdom)` vem logo após `Asturian`), por isso o `en_GB` fica em `0` (inglês), que é seguro, e não no número do inglês britânico. O binário também traz a tabela ISO de autodetecção (`pt_BR`, `pt_PT`, `zh_CN`..., `en_GB`) e a chave `user_language`. O número em si é ABI estável do libretro; a confirmação visual (menu em inglês com `0`, em português com `7`) é da task 5.1.

### D4: Só ajustar quando o idioma do EmuELEC mudou
O script guarda em `/storage/.config/retroarch/r36-idioma` (p8) o par de valores que as duas fontes tinham no último ajuste: duas linhas, `emuelec.conf` e depois `es_settings.cfg`. Um estado antigo de uma linha só vale para as duas fontes. Só grava `user_language` quando uma fonte difere do próprio valor guardado (ou quando o arquivo não existe, que é o primeiro jogo depois de gravar o SYSTEM; o `emuelec.conf` vence). Sempre que aplica, ou vê diferença, grava o par atual de uma vez, para que a outra fonte não pareça "mudada" no jogo seguinte. Assim a escolha feita no menu do RetroArch vale até o usuário trocar o idioma no EmuELEC, e um cartão com `--keep-storage` é acertado no primeiro jogo.
- *Alternativa: sempre sobrescrever.* Descartada: desfaria a escolha do usuário a cada jogo.
- *Alternativa: guardar o estado na p1.* Descartada: a p1 é do usuário; a p8 já guarda configuração do aparelho.
- Efeito: um cartão que já tem o `r36-idioma` e o mesmo idioma não é tocado.
- Custo por jogo no caminho comum (idioma igual ao guardado): três leituras (`emuelec.conf`, `es_settings.cfg` e `r36-idioma`) com o `read` do próprio shell, nenhum `sed` e nenhuma escrita no SD. O `r36-idioma` só é regravado (o par inteiro) quando uma fonte difere do valor guardado dela: depois de acertar o `retroarch.cfg`, ou, para um idioma fora da tabela, sem tocar no `retroarch.cfg` (assim a volta a um idioma da tabela conta como troca). Um `retroarch.cfg` ausente ou um idioma ilegível não gravam o estado, para que o primeiro jogo com os arquivos presentes ainda acerte o idioma.

### D5: Escrita do `retroarch.cfg` e log
A troca é um `sed` no mesmo arquivo (`cat tmp > arquivo`, como o `shaderset-aplica`), só na linha `user_language = "<n>"`; sem a linha, acrescenta. Sai com código 0 em qualquer caso, e o jogo abre mesmo se o `retroarch.cfg` ou o `emuelec.conf` não existirem. Com `r36-diagnostico` na p1, acrescenta uma linha por jogo a `r36-idioma.log`, na mesma chave dos demais logs (capability `diagnostic-logs`).

### D6: Idioma do build por `--idioma`
`./build.sh --idioma <código>` aceita os códigos da tabela do D3 (**`en_US` por padrão**, decisão do usuário) e recusa outro com erro e a lista. Um `./build.sh` sem argumento gera imagem em inglês; para português é `./build.sh --idioma pt_BR`. Os arquivos da feature 10 no repositório continuam em `pt_BR`: quem gera o idioma da imagem é sempre o build, mesmo no padrão. O build troca o valor de três chaves: `system.language` no `emuelec.conf`, `Language` no `es_settings.cfg` e `user_language` no `retroarch.cfg`, usando a mesma tabela. A troca acontece depois do planejamento das features, sobre cópias dos três arquivos em `work/` para as quais as entradas do plano passam a apontar (com o tamanho novo); os arquivos de `features/` no repositório não mudam, e o build segue reprodutível. A troca exige que cada chave exista exatamente uma vez no arquivo (fora de comentário); a ausência é erro claro com o caminho e a chave. O build não presume mais nada do conteúdo dos três arquivos (outras changes mexem em outras chaves do `retroarch.cfg`). O estado do D4 (`r36-idioma`) não é gravado pelo build: no primeiro jogo (o `r36-idioma` não existe numa p8 nova) o script reescreve o `retroarch.cfg` uma vez, com conteúdo idêntico, porque o `user_language` já bate, e grava o `r36-idioma` com os valores que os dois arquivos do build trazem (o build não grava o estado; quem grava é o script, nesse primeiro jogo); a partir do segundo jogo é o caminho comum, sem escrita, mesmo que as duas fontes divergissem.
- Os três arquivos precisam vir das features selecionadas (hoje, a `10-ptbr-sao-paulo`). Um `--features` que não os traga (por exemplo `./build.sh --features 10-minha-feature`, o fluxo de quem cria uma feature) sai **sem idioma** quando `--idioma` não foi passado: o padrão `en_US` é opcional, e o nome, o manifest e o `R36-BUILD.txt` ficam sem idioma, em vez de levar um idioma que não vale dentro da imagem. Com `--idioma` explícito, a falta é erro que diz qual arquivo falta. A função `build()` do Python aceita `idioma=None` (sem idioma) e `idioma_opcional`, que o `./build.sh` liga quando usa o padrão.
- *Alternativa: uma feature por idioma.* Descartada: triplicaria arquivos que só diferem em três valores.
- *Alternativa: arquivo `idioma.toml` em `config/`.* Descartada: o idioma muda de build para build, como o tamanho do cartão, então fica na linha de comando.
- Sem as features que trazem esses arquivos (`--no-features`) não há o que trocar: `--idioma` com `--no-features` é erro, e o build sem features continua igual à base.

### D7: Idioma no nome, no manifest e no registro
A imagem completa passa a se chamar `<prefixo>_<idioma>_build_<timestamp>[-test].img.xz`, com o código em minúsculas e `_` trocado por `-` (o padrão `en_US` vira `en-us`; `pt_BR` vira `pt-br`). O diretório de saída fica `<timestamp>[-test]`, sem o idioma, porque o `flash.sh --build` e o menu dele escolhem por esse nome. O manifest ganha `"language": "en_US"` (código original) e o `R36-BUILD.txt`, a linha `idioma: en_US` (ou o código de `--idioma`). Um build sem features não leva idioma no nome (`<prefixo>_build_<timestamp>.img.xz`, como hoje) nem no manifest.
- *Alternativa: idioma no diretório também.* Descartada: quebraria o `flash.sh --build <timestamp>` e os builds antigos em `out/`.
- Efeito: **BREAKING** para quem procura a imagem pelo nome antigo e para quem roda `./build.sh` sem argumento esperando português (agora sai em inglês, `en-us` no nome); o `README.md` (no topo da seção do build) e os testes do nome (`tests/test_image.py`) mudam junto.

## Risks / Trade-offs

- [O ES pode gravar a troca de idioma em outro lugar] → D2 e a verificação no aparelho; a spec não depende do arquivo.
- [Números do RetroArch para os idiomas podem diferir no fork] → Conferência no binário na tarefa de verificação; a tabela é uma tabela, trocar é uma linha.
- [O RGUI pode não ter fonte para alguns idiomas] → Fora de escopo; a conferência é visual no aparelho, e o usuário volta o idioma pelo EmuELEC.
- [Troca de idioma pelo menu do RetroArch e depois reinício mantém o idioma dele] → É o efeito desejado (D4).
- [Troca de valor em arquivos de configuração por regex pode errar com um arquivo que não tem a chave] → O build falha com erro claro se alguma das três chaves não existir no arquivo de origem, e um teste cobre os três arquivos reais da feature 10.
- [Dependência da change `es-shader-config-gpsp-ghost`] → Registrada no proposal e nas tarefas; o apply só começa com ela na `main`.

## Migration Plan

1. Gravar só o `system` (`./flash.sh --device /dev/sdc --part system --build <ts>`): vale com `--keep-storage`, porque o script roda no SYSTEM.
2. Reverter: gravar o build anterior; o `r36-idioma` e o `user_language` ficam na p8 e não fazem mal.
