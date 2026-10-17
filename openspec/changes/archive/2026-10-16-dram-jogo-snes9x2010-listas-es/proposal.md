# Proposal

## Why

No teste da imagem `20261016-172250-test`, com o ondemand afinado, o clock deixou de cair em jogo, mas o PSX ainda picotou o som, o SNES perdeu quadros, o CPS2 (Marvel vs Capcom) ficou lento em alguns momentos e o N64 piorou. O registro térmico mostra que CPS2 e PSX tinham CPU sobrando (o núcleo mais ocupado ficou em 40 a 53%), o que aponta para a DRAM: em modo normal ela fica na cena `1` (cerca de 360 MHz, segundo o comentário da base). O N64 piorou desde que o máximo desempenho foi desligado, quando perdeu a cena `0` da DRAM. O SNES é o único caso de CPU pura: o snes9x satura um núcleo. O clock ficou travado em 1104 MHz e a bateria marcou 5% a sessão inteira, e o log não traz o teto de frequência nem a frequência real da DRAM para explicar isso. O aparelho não tem Wi-Fi nem SSH, então tudo o que precisa ser conferido no aparelho tem que ser gravado no cartão. O usuário também configurou o EmulationStation à mão para esconder as pastas nas listas e pôr os favoritos no topo, e quer isso fixo na imagem.

## What Changes

- Com um jogo aberto e o máximo desempenho desligado, a DRAM passa para a cena `0`. O governor continua `ondemand`, com o afinamento atual. No menu, a DRAM volta à cena `1`.
- O SNES passa a abrir por padrão no core `snes9x2005_plus` do RetroArch, declarado no `emuelec.conf` no mesmo molde do GBA e do CPS2. Os outros cores de SNES seguem selecionáveis no menu, e `snesh` e `snesmsu1` não mudam.
- O EmulationStation da imagem passa a esconder as pastas nas listas de jogos (`FolderViewMode` `never`) e a mostrar os favoritos no topo (`FavoritesFirst` `true`).
- No boot, o aparelho grava um retrato do sistema em `/storage/roms/r36-sysinfo.txt`: governors e frequências disponíveis da CPU, teto e máximo de frequência, tunables do ondemand, cenas e frequências da DRAM, trip points das zonas térmicas e estado dos dispositivos de resfriamento. Substitui a conferência manual no aparelho pendente da change `cps2-fbalpha2012-ondemand-afinado` (tarefa 1.2).
- O `r36-thermal.csv` ganha três colunas: o teto de frequência da CPU em vigor (`cpu_max_mhz`), a frequência da DRAM (`dram_mhz`) e a tensão da bateria (`bat_voltage`).
- O menu do RetroArch volta ao inglês, o idioma da imagem base (`user_language` `0`). O sistema e o EmulationStation continuam em português do Brasil.
- A imagem é gerada com `./build.sh --test`. A validação no aparelho herda a tarefa 4.4 da change arquivada e cobre também os itens desta.
- Fora do escopo: o Neo Geo continua no `fbalpha2012`, padrão da base. A movimentação das ROMs de Neo Geo da pasta `fbneo` para `neogeo` é feita à parte, direto no cartão.

## Capabilities

### New Capabilities
- `snes-emulation`: qual emulador e core o Super Nintendo usa por padrão na imagem, sem remover as alternativas.
- `es-game-lists`: como as listas de jogos do EmulationStation são apresentadas na imagem (pastas e favoritos).

### Modified Capabilities
- `cpu-frequency-scaling`: com jogo aberto em modo normal, a DRAM fica na cena `0`; no menu, na cena `1`.
- `thermal-control`: o modo normal em jogo deixa de exigir a cena `1`; cada medição ganha o teto de frequência, a frequência da DRAM e a tensão da bateria; o boot grava o retrato do sistema no cartão.
- `system-locale`: o menu do RetroArch deixa de ser em português do Brasil e fica em inglês por padrão.

## Impact

- `features/44-cpu-ondemand`: o script de afinamento passa a gravar a cena `0` da DRAM quando chamado na abertura do jogo; descrição do `feature.toml`.
- `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh`: a chamada após o `normperf` da abertura indica que é abertura de jogo; a da saída não muda.
- `features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf`: `snes.emulator` e `snes.core`.
- `features/10-ptbr-sao-paulo/storage/.config/emulationstation/es_settings.cfg`: `FolderViewMode` e `FavoritesFirst`.
- `features/10-ptbr-sao-paulo/storage/.config/retroarch/retroarch.cfg`: `user_language` volta a `0`; descrição do `feature.toml` da feature 10.
- `features/43-registro-termico`: colunas novas no `thermal-log` e retrato do sistema no início do serviço.
- Testes: `tests/test_cpu_ondemand.py`, `tests/test_ptbr_controle.py` (inclui a contagem de linhas que diferem da base no `emuelecRunEmu.sh`) e `tests/test_registro_termico.py`. README.
- O `es_settings.cfg` e o `emuelec.conf` ficam no `/storage`: só chegam com `--wipe-storage`. Sem mudança nas partições de ROMs, no boot ou no kernel.
