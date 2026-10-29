# Proposal

## Why

Três defeitos aparecem no aparelho. O shader escolhido em "SHADER SET" do EmulationStation não entra no jogo (o `setsettings.sh` do SYSTEM só passa `--set-shader` quando o valor é `true` ou `1`; um caminho `.glslp` não gera nada), e isso vale também para o padrão do GBA. Salvar opções de core, override ou preset pelo menu do RetroArch dá erro, porque o `retroarch.cfg` aponta `rgui_config_directory` para `/config`, que não existe numa raiz somente leitura. E o gpSP, core padrão do GBA, roda sem o interframe blending (ghosting do LCD), que o usuário quer em todos os jogos.

## What Changes

- **Shader do ES vale no jogo:** um script novo (`shaderset-aplica`) lê `<sistema>["<rom>"].shaderset`, `<sistema>.shaderset` e `global.shaderset`, na mesma ordem do `setsettings.sh`, e grava `video_shader` e `video_shader_enable = "true"` no `retroarch.cfg` antes do jogo. Como o RetroArch 1.17 do aparelho ignora o `video_shader` do cfg quando o jogo não tem preset automático (o SNES rodou com `Stock GLSL shaders` mesmo com a linha gravada), o script também imprime `--set-shader "/tmp/shaders/<preset>"`, que o `emuelecRunEmu.sh` põe antes de `--config`, o mesmo canal que a base usa para `true` e `1`. O `emuelecRunEmu.sh` (feature 10) chama o script logo depois do `setsettings.sh`; os valores `none`, `false`, `0` ou vazio ficam sem shader. O `emuelecRunEmu.sh` já apaga essas linhas depois de cada jogo.
- **Caminhos do RetroArch:** um serviço de boot corrige no `retroarch.cfg` da p8, só quando o valor ainda é o de fábrica, `rgui_config_directory` (`/config` para `~/.config/retroarch/config`), `savefile_directory` (`/saves` para `~/savefiles`), `log_dir` (`/logs` para `~/.config/emuelec/logs`) e `osk_overlay_directory` (`/overlays/keyboards` para `~/overlays/keyboards`). O `retroarch.cfg` da feature 10 já nasce com os valores certos, para cartão novo. Salvar opções de core, override e preset pelo menu passa a gravar na p8.
- **gpSP com interframe blending:** o mesmo serviço cria `~/.config/retroarch/config/gpSP/gpSP.opt` com `gpsp_frame_mixing = "enabled"`, ou acrescenta a linha, só se a chave não existir. O arquivo vazio `r36-gpsp-sem-ghost` na raiz da p1 desliga. O mesmo serviço põe `gpsp_boot_mode = "bios"` (Boot mode: Boot to BIOS), com a mesma regra: só se a chave não existir.
- **Padrões do RetroArch:** o `retroarch.cfg` de fábrica passa a trazer o viewport personalizado 768x672 (`custom_viewport_width`/`_height`), `rgui_aspect_ratio = "11"`, `menu_show_load_content_animation = "false"` e `notification_show_autoconfig = "false"` (ajustes que o usuário fez no menu e quer como padrão) e o menu em português do Brasil (`user_language = "7"`).
- **Fora de escopo:** backup ou espelho das configurações no `flash.sh`; `recording_config_directory`; mexer em `video_threaded` ou em outras chaves de vídeo e som.

## Capabilities

### New Capabilities
- `retroarch-config-paths`: o RetroArch grava e lê configuração, opções de core, saves e logs em pastas que existem e são graváveis (p8), inclusive em cartão já gravado com `--keep-storage`, sem sobrescrever o que o usuário já mudou.

- `retroarch-menu`: padrões de aparência e uso do RetroArch (viewport, proporção do RGUI, sem animação de carregamento nem aviso de autoconfig).

### Modified Capabilities
- `retroarch-shaders`: o shader escolhido no "SHADER SET" do ES, por jogo, sistema ou global, passa a ser aplicado ao jogo.
- `gba-emulation`: o gpSP abre os jogos com o interframe blending ligado e com Boot to BIOS por padrão, com chave para desligar o blending na p1.
- `system-locale`: o menu do RetroArch passa de inglês para português do Brasil (remove o requisito "Menu do RetroArch em inglês").

## Impact

- `features/10-ptbr-sao-paulo`: `system/usr/bin/emuelecRunEmu.sh` (uma chamada nova) e `storage/.config/retroarch/retroarch.cfg` (quatro caminhos, cinco padrões de aparência e o idioma).
- Feature nova `56-retroarch-ajustes` (SYSTEM): `shaderset-aplica`, `retroarch-prepara` e o serviço `r36-retroarch-prepara.service`.
- `features/54-shaders-gba`: sem mudança de arquivo; o `gba.shaderset` que ele grava passa a ter efeito.
- Testes novos em `tests/`, mais `README.md` e `CLAUDE.md`.
- Os padrões novos do `retroarch.cfg` (viewport, aspecto, avisos e idioma) só chegam com uma p8 nova (`--wipe-storage`); com `--keep-storage` o usuário muda pelo menu. O `gpSP.opt` só chega ao cartão pelo SYSTEM (`--part system` ou `--keep-storage`); a gravação de uma `p8` nova já traz o `retroarch.cfg` corrigido.
- Não verificável no PC: o fim do erro ao salvar e a entrada do shader dependem do aparelho (`retroarch.log` e `emuelec.log` na p8).
