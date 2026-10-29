# Design

## Context

Ver `proposal.md` para a motivação. O que foi lido (SYSTEM do build `20261028-232634` e p8 da imagem base, só leitura):

- **Shader do ES.** O `emuelecRunEmu.sh` chama `setsettings.sh "${PLATFORM}" "${ROMNAME_SHADER}" "${CORE}"` e insere a saída antes de `--config` na linha do RetroArch. No ramo `shaderset` do `setsettings.sh`, o `echo "--set-shader /tmp/shaders/${2}"` só roda se `${2}` for `true` ou `1`; as linhas que gravariam `video_shader` e `video_shader_enable` estão comentadas. Um caminho como `gba/gba-modern-remaster.glslp` não imprime nada. O `get_setting` procura `<sistema>["<rom>"]...shaderset=`, depois `<sistema>.shaderset=` e depois `global...shaderset=`, e usa `false` se nada existe. O `emuelecRunEmu.sh` apaga `video_shader` e `video_shader_enable` do `retroarch.cfg` depois de cada jogo.
- **Discrepância resolvida.** O `CLAUDE.md` dizia que o binário do ES escreve `video_shader` no `retroarch.cfg` antes do jogo. Quem grava é o `shaderset-aplica`; o binário do ES só tem as cadeias `video_shader_enable = "false"` e `video_shader = "%s"` do bloco de ajustes. O log sob chave (cartão do usuário) mostrou o script gravando o `video_shader` certo para o SNES, e o `emuelec.log` do mesmo jogo mostrou `Stock GLSL shaders will be used`: o RetroArch 1.17 não carrega o preset do cfg quando não há preset automático. O GBA só funcionava pelo preset automático (`Specific shader preset found at .../gpSP/gpSP.glslp`).
- **Caminhos.** O `retroarch.cfg` tem `rgui_config_directory = "/config"`, `savefile_directory = "/saves"`, `log_dir = "/logs"`, `osk_overlay_directory = "/overlays/keyboards"`. Nenhuma dessas pastas existe no SYSTEM (squashfs, somente leitura). Na p8 da base existem `.config/retroarch/config/<Core>/`, `savefiles`, `overlays/keyboards`, `.config/emuelec/logs`. `savefiles_in_content_dir = "true"` deixa o `savefile_directory` sem uso hoje; `log_to_file = "false"` o mesmo para `log_dir`. Com `global_core_options = "false"` e `game_specific_options = "true"`, as opções de core vão para `<rgui_config_directory>/<core>/<core>.opt` (e `<jogo>.opt`), então hoje o RetroArch tenta usar `/config`.
- **Padrão de serviço de boot.** `46-audio` e `54-shaders-gba` editam arquivos da p8 no lugar, esperam a p1 montar (até 20 s) para ler as chaves e usam `R36_ROOT` para os testes. O serviço que roda `Before=emustation.service` sem `After=emuelec-autostart.service` evita o travamento do boot (`CLAUDE.md`).

## Goals / Non-Goals

**Goals:**
- O "SHADER SET" do ES (e o `gba.shaderset` padrão) vale em qualquer sistema.
- Salvar pelo menu do RetroArch no aparelho grava na p8.
- gpSP com interframe blending por padrão, com chave para desligar e escolha do usuário preservada.
- Funcionar com `--keep-storage` e sem root no PC; testes sem aparelho.

**Non-Goals:**
- Backup ou espelho das configurações no `flash.sh`.
- Substituir o `setsettings.sh` (592 linhas da base) ou mexer em outros ramos dele.
- `recording_config_directory`, `video_threaded` e outras chaves de vídeo ou som.
- Mudar o shader em si ou os parâmetros dele.

## Decisions

### D1: Script próprio chamado pelo `emuelecRunEmu.sh`, sem tocar no `setsettings.sh`
Um `shaderset-aplica <sistema> <rom>` em `/usr/lib/r36/` repete a busca do `get_setting` (jogo, sistema, global) no `emuelec.conf`. Para um valor que não é `true`, `1`, `none`, `false`, `0` nem vazio, apaga `video_shader` e `video_shader_enable` do `retroarch.cfg` e grava `video_shader = "/tmp/shaders/<valor>"` e `video_shader_enable = "true"`. Para `none`, `false`, `0` ou vazio, apaga as duas linhas. Para `true` e `1`, não faz nada (o `setsettings.sh` já trata com `--set-shader`). O `emuelecRunEmu.sh` da feature 10 chama o script logo depois da linha do `SHADERSET`; a limpeza que já existe depois do jogo continua valendo. Para um caminho o script também imprime `--set-shader "/tmp/shaders/<valor>"` (D6), e o `emuelecRunEmu.sh` guarda a saída em `R36_SHADER` e a atribui a `SHADERSET`, que a linha seguinte da base já insere antes de `--config`.
- *Alternativa: copiar o `setsettings.sh` para a feature e descomentar as linhas.* Descartada: duplicaria 592 linhas da base e qualquer outra mudança no ramo se perderia numa troca de base. O `emuelecRunEmu.sh` já é uma cópia nossa, então uma linha a mais lá custa menos.
- *Alternativa: gravar o shader num `--appendconfig`.* Descartada: o `RUNTHIS` do EmuELEC já usa `--config` único, e o `retroarch.cfg` é onde o ES e o `emuelecRunEmu.sh` já mexem.
- O caminho usa o valor como está (`gba/x.glslp`, com espaços) entre aspas; o `/tmp/shaders` é o bind da p8 criado pelo `r36-shader-gba-prepara`. O script não valida que o arquivo existe: o RetroArch ignora um preset que falta.

### D2: Feature nova `56-retroarch-ajustes`, num serviço de boot só
O `shaderset-aplica` e o serviço `r36-retroarch-prepara` (script `retroarch-prepara`) ficam numa feature nova do SYSTEM, em ordem 56, fora de `10` (idioma) e de `54` (shader do GBA). O serviço é `Type=oneshot`, `Before=emustation.service`, sem `After=emuelec-autostart.service`, `WantedBy=emuelec.target`, com a mesma espera da p1 (até 20 s) do `54-shaders-gba`, e roda por `R36_ROOT` nos testes. Faz, em ordem:
1. Os quatro valores do `retroarch.cfg` da p8, um `sed` por chave só quando a linha é exatamente `chave = "valor de fábrica"`, escrita no mesmo arquivo (`cat tmp > arquivo`, como o `46-audio`).
2. O `gpSP.opt`, com a chave `r36-gpsp-sem-ghost` (D3).
3. O log, só com `r36-diagnostico` (D5).
O `retroarch.cfg` da feature 10 recebe os valores novos para cartão novo (a p8 de fábrica é copiada de lá).

### D3: `gpSP.opt` com a chave, na pasta que passa a existir
A opção é `gpsp_frame_mixing`, e os valores no binário do core do SYSTEM são `disabled` e `enabled`. O arquivo é `/storage/.config/retroarch/config/gpSP/gpSP.opt` (a pasta `gpSP` é a que o RetroArch usa, como as do `config/` da base). Sem a chave `gpsp_frame_mixing` no arquivo, o serviço acrescenta `gpsp_frame_mixing = "enabled"` (com quebra de linha antes, se faltar); com a chave, nada. Com `r36-gpsp-sem-ghost` na p1, remove só a linha se o valor for `enabled`. O `gpSP.opt` por jogo (`<jogo>.opt`, de `game_specific_options`) continua valendo mais que o global do core, e o RetroArch, ao salvar o menu, regrava o arquivo com todas as opções, inclusive esta.
- *Alternativa: `retroarch-core-options.cfg` global.* Descartada: com `global_core_options = "false"` o RetroArch não o lê.
- *Alternativa: `--appendconfig` com a opção.* Descartada: a opção de core não é do `retroarch.cfg`.
- O `rgui_config_directory` corrigido é pré-requisito: sem ele o RetroArch não leria `config/gpSP/gpSP.opt`.

### D6: Preset por `--set-shader`, não só pelo cfg
O RetroArch 1.17 do aparelho não carrega o `video_shader` do `retroarch.cfg` (medido no SNES: a linha estava gravada e o log mostrou o shader padrão). O que a base já faz para `true` e `1` é passar `--set-shader <caminho>` antes de `--config`, e esse é o canal que vale. O `shaderset-aplica` imprime a opção só para um caminho (nunca para `none`, `false`, `0`, vazio, `true` ou `1`), com o caminho entre aspas, e o `emuelecRunEmu.sh` a atribui a `SHADERSET`. A gravação de `video_shader` e `video_shader_enable = "true"` continua (o `CLAUDE.md` registra que, sem a segunda, nenhum shader vale).
- *Alternativa: só o cfg.* Descartada: não funcionou no aparelho.
- *Alternativa: gravar o preset automático por sistema (`<core>/<core>.glslp`), como o `54` faz para o GBA.* Descartada: um preset por pasta salvo pelo menu passa na frente e a escolha do ES por jogo não teria efeito.
- **Verificação**: a linha `Run Command is:` do `emuelec.log` deve trazer `--set-shader`, e o log do RetroArch, as linhas do preset carregado.

### D7: gpSP inicia pela BIOS
A opção é `gpsp_boot_mode`, com os valores `game` e `bios` ("Boot to game" e "Boot to BIOS") no binário do core do SYSTEM. O `retroarch-prepara` trata a chave como a do blending: cria o `gpSP.opt` ou acrescenta `gpsp_boot_mode = "bios"` só se a chave não existir, e preserva qualquer valor existente. `r36-gpsp-sem-ghost` continua mexendo só no blending. Um cartão cujo `gpSP.opt` já tem `gpsp_boot_mode = "game"` mantém esse valor (limitação aceita: o padrão só vale com o arquivo novo, por exemplo depois de `--wipe-storage`).

### D8: Padrões de aparência e idioma no `retroarch.cfg` de fábrica
O usuário ajustou no menu e quer como padrão: `custom_viewport_width = "768"` e `custom_viewport_height = "672"` (eram 640 e 480), `rgui_aspect_ratio = "11"` (era 6), `menu_show_load_content_animation = "false"` e `notification_show_autoconfig = "false"` (eram `true`). O idioma do menu passa a `user_language = "7"` (Português do Brasil; era `0`), o que remove a decisão anterior de deixar o RetroArch em inglês (spec `system-locale`). Os valores entram só no `retroarch.cfg` da feature 10, ou seja, numa p8 nova; um cartão com `--keep-storage` conserva os valores dele, e o usuário muda pelo menu. Ficam fora o que o aparelho grava sozinho (`savestate_directory` do último sistema, `video_ctx_scaling` repetido, `log_verbosity`) e o que veio da feature 46 (`audio_latency`, `audio_resampler_quality`).
- **Risco**: a fonte do RGUI pode não ter todos os acentos; a conferência é visual no aparelho.

### D4: Só trocar o que ainda é o valor de fábrica
Cada caminho é trocado apenas se a linha for idêntica à de fábrica. Um valor diferente (escolha do usuário ou de outra feature) fica como está, e uma segunda execução não faz nada. Os destinos são pastas que existem na p8 da base ou que o RetroArch cria; o serviço não cria pastas, exceto `config/gpSP/` para o `gpSP.opt`. `recording_config_directory` fica fora: só vale ao gravar vídeo, e a pasta pai não existe na base.
- **Efeito colateral aceito.** `.opt`, overrides e presets que já estejam em `config/<core>/` passam a ser lidos. Como o caminho antigo nunca existiu, só valem os que o nosso serviço (`54`) ou o usuário puseram ali; o `54` já grava os presets de GBA nessa pasta, que passa a ser achada. Deve-se conferir `ls -R /storage/.config/retroarch/config` no cartão de uso antes de gravar.

### D5: Log só com a chave `r36-diagnostico`
Seguindo o `CLAUDE.md`, o serviço grava `r36-retroarch.log` na p1 só com `r36-diagnostico`. O `shaderset-aplica` acrescenta uma linha por jogo a `r36-shader-gba.log` (o mesmo log do shader), também só com a chave e com a p1 montada; o `r36-shader-gba-prepara` trunca o arquivo no boot, então as linhas do jogo começam depois dele. Esses logs entram na lista de logs sob chave do `CLAUDE.md`.

## Risks / Trade-offs

- [O erro de salvar pode ter outra causa além de `/config`] → A causa é provável (pasta inexistente em raiz somente leitura), não provada. A prova vem do `retroarch.log` no aparelho depois do conserto; se persistir, a próxima suspeita é dono ou permissão dos arquivos da p8. Fica registrado nas tarefas como verificação do usuário.
- [`video_shader_enable = "true"` em todos os sistemas com `shaderset`] → É o comportamento que o ES promete; o `emuelecRunEmu.sh` apaga as linhas depois do jogo, e `none` as apaga antes.
- [Config antiga em `config/<core>/` passa a valer] → Descrito em D4; o cartão do usuário deve ser conferido antes de gravar.
- [Blending borra o movimento em alguns jogos] → Ligado só no gpSP e desligável com `r36-gpsp-sem-ghost` ou pela opção do core no menu.
- [Os padrões do `retroarch.cfg` não chegam a quem mantém a p8] → Aceito (D8); o usuário muda pelo menu ou grava a p8 nova.
- [Entrada do shader do ES não é verificável no PC] → Os testes cobrem o script com `R36_ROOT` e o `emuelec.conf` de teste; a aplicação no RetroArch só se vê no aparelho.
- [A espera pela p1 atrasa o boot em até 20 s sem p1] → Igual ao `54-shaders-gba`; sem p1 o padrão (blending ligado) vale.

## Migration Plan

1. Gravar só o `system` (`./flash.sh --device /dev/sdc --part system --build <ts>`): vale com `--keep-storage`, porque o serviço corrige a p8 no boot.
2. Cartão novo ou `--wipe-storage`: o `retroarch.cfg` já vem corrigido.
3. Reverter: gravar o build anterior; os valores já trocados na p8 ficam (apontam para pastas válidas). Para desligar o blending sem regravar, `r36-gpsp-sem-ghost` na p1.
