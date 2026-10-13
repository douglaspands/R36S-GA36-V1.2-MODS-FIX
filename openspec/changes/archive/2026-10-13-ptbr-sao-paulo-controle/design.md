# Design

## Context

- A p8 de fábrica já vem com o `/storage` preenchido. Os valores que importam aqui ficam em:
  - `.config/emuelec/configs/emuelec.conf`: `system.language=es_MX` e `system.timezone=America/Mexico_City`;
  - `.config/emulationstation/es_settings.cfg`: `Language` = `en_US`;
  - `.config/retroarch/retroarch.cfg`: `user_language = "0"` e `menu_driver = "xmb"`;
  - `joypads/micro_gamepad.cfg`: `input_driver = "udev"`, B = 0, A = 1, X = 2, Y = 3, hotkey = 8.
- No boot, o `emustation-config` lê `system.language` e `system.timezone`. Ele compila o locale com `localedef` em `/emuelec/configs/locale/<lang>.UTF-8` quando a pasta não existe e grava `/storage/.cache/timezone`. O SYSTEM já tem `usr/share/i18n/locales/pt_BR`, a tradução `pt_BR` do ES e `zoneinfo/America/Sao_Paulo`.
- Antes de cada jogo, o `setsettings.sh` reescreve `menu_driver` no `retroarch.cfg` a partir de `retroarch.menu_driver` no `emuelec.conf`. Sem esse valor, ele força o `xmb` no A33. O `setsettings.sh` não mexe em `user_language` nem nos binds do controle.
- O RetroArch usa `input_joypad_driver = "sdl2"` e procura os autoconfigs em `~/joypads`. O `retroarch.cfg` não liga nenhum bind de controle (todos os `*_btn` estão `nul`). Os binds e atalhos do `micro_gamepad` vêm só do autoconfig.
- O mapeamento posicional foi validado no aparelho: com A = btn 0 e B = btn 1, os botões ficam corretos. O arquivo que o ES regravou no cartão serve de referência para o cabeçalho `sdl2`, `vendor_id` `26989` e `product_id` `24431`.
- O mecanismo de features só substitui arquivos inteiros. Um arquivo que substitui outro herda dono e modo do original.

## Goals / Non-Goals

**Goals:**
- Cada arquivo substituído é o original de fábrica com o mínimo de linhas alteradas, para que a revisão e o `diff` contra a base sejam triviais.
- Nenhuma mudança no código do `r36img`.

**Non-Goals:**
- Aplicar as mudanças num cartão gravado com `--keep-storage`.
- Mapear controles externos (USB e Bluetooth) ou emuladores standalone.
- Uma operação de "patch chave=valor" nas features. Fica para um change futuro, se o volume de arquivos grandes copiados crescer.

## Decisions

1. **Duas features num único change e numa única branch.** O usuário pediu uma branch para o ajuste todo. As features ficam separadas para que possam ser desligadas de forma independente (`enabled = false`), e não se sobrepõem: nenhuma das duas toca um caminho que a outra também toca, então não é preciso `[[override]]`.
   - `features/10-ptbr-sao-paulo/storage/`: `emuelec.conf`, `es_settings.cfg` e `retroarch.cfg`.
   - `features/20-controle-posicional/storage/`: `joypads/micro_gamepad.cfg`.
   - Alternativa descartada: uma feature só. Ela misturaria idioma e controle, que podem ser revertidos por motivos diferentes.

2. **Os arquivos partem da base de fábrica, não do cartão.** O cartão do usuário tem resíduos de uso: `log_verbosity`, `video_ctx_scaling` repetido, `savestate_directory` de GBA e histórico. Cada arquivo é extraído da p8 da imagem base, e só as chaves deste change são editadas:
   - `emuelec.conf`: `system.language=pt_BR`, `system.timezone=America/Sao_Paulo` e a troca do comentário `#global.retroarch.menu_driver=` por `global.retroarch.menu_driver=rgui`;
   - `es_settings.cfg`: `Language` = `pt_BR`;
   - `retroarch.cfg`: `user_language = "7"` (`RETRO_LANGUAGE_PORTUGUESE_BRAZIL`) e `menu_driver = "rgui"`.

3. **O RGUI é declarado no `emuelec.conf` e também no `retroarch.cfg`.** O `emuelec.conf` é o que vale, porque o `setsettings.sh` o reaplica a cada jogo. O `retroarch.cfg` mantém a consistência para o caso de o RetroArch ser aberto sem passar pelo `setsettings.sh`. Alternativa descartada: só o `retroarch.cfg`, que seria sobrescrito para `xmb` no primeiro jogo.

4. **O `micro_gamepad.cfg` usa a estrutura de fábrica com o cabeçalho `sdl2`.**
   - O cabeçalho (`input_driver = "sdl2"`, `vendor_id` e `product_id`) vem do arquivo validado no cartão, porque é o driver que o RetroArch usa.
   - Os botões de face ficam com A = 0, B = 1, X = 2 e Y = 3.
   - Os atalhos são os de fábrica com o hotkey em 8. Pausa e FPS ficam nos mesmos botões físicos de antes: `input_pause_toggle_btn = "1"` e `input_fps_toggle_btn = "0"`.
   - Volume, troca de slot, reset e rewind não aparecem, então ficam `nul` pelo `retroarch.cfg`.
   - Alternativa descartada: copiar o arquivo do cartão, que tem o hotkey no direcional.

5. **Verificação pelo PC antes do aparelho.** Depois do build, o `changes.txt` deve listar exatamente os 4 caminhos substituídos. A p8 gerada é inspecionada com `debugfs` (somente leitura) e comparada com a base por `diff`. O esperado é que só as chaves listadas acima mudem e que `remappings/` fique idêntico.

## Risks / Trade-offs

- [O usuário grava com `--keep-storage` e não vê mudança] → O README e o resumo do build dizem que este change exige `--wipe-storage`. A gravação será feita com `--wipe-storage`, como o usuário autorizou.
- [Reconfigurar o controle no ES regrava o `micro_gamepad.cfg` com outros atalhos] → É comportamento do EmuELEC, aceito. A especificação documenta o que a imagem entrega.
- [O primeiro boot fica mais lento por causa do `localedef` do `pt_BR`] → Acontece uma vez só. O resultado fica em `/storage`.
- [A tradução pt_BR do ES ou do RetroArch pode estar incompleta] → Os textos sem tradução aparecem em inglês. Não bloqueia.
- [O `user_language` pode ter outro número nesta versão do RetroArch] → Conferir no aparelho que o menu aparece em português. Se não aparecer, corrigir o valor pelo índice da versão instalada.

## Migration Plan

1. Build com `./build.sh`, conferir o `changes.txt` e fazer a inspeção pelo PC.
2. Gravar num arquivo de teste com `--target-file` (sem sudo).
3. O usuário grava o cartão num terminal próprio, com `./flash.sh --device /dev/sdX --all --keep-roms --wipe-storage`. Isso apaga saves e configurações, como autorizado.
4. Validar no aparelho: idioma, hora, RGUI e os botões e atalhos segundo `specs/retroarch-controls`.
5. Rollback: gravar o build anterior ou desligar a feature (`enabled = false`) e gerar de novo.
