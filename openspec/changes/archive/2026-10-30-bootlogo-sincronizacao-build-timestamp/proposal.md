# Proposal

## Why

O clone do R36S (placa GA36-MB V1.2-20260416) exibe no U-Boot uma tela de abertura com a inscrição genérica "OPEN SOURCE", que deve refletir a identificação correta da placa-mãe do aparelho. Além disso, as alterações de brilho (por atalho FN + D-pad) e de volume (pelos botões físicos laterais) precisam refletir e manter-se sincronizadas em tempo real no arquivo de configurações mestre do sistema (`emuelec.conf`), persistindo confiavelmente mesmo quando o EmulationStation for reiniciado ou desligado pelo menu. Por fim, a fábrica de imagens precisa permitir a passagem de um timestamp explícito no build para gerar imagens idênticas em múltiplos idiomas sob o mesmo identificador de versão.

## What Changes

- **Boot Logo personalizado na partição BOOT (p2)**: substituição do texto "OPEN SOURCE" por "GA36-MB V1.2-20260416" no arquivo `bootlogo.bmp` (640x480, 24 bpp, BMP puro) fornecido pela feature existente `30-telas-icone-controle` na camada `boot/`.
- **Sincronização de Brilho em Tempo Real**: `brilho-aplica` passa a atualizar `brightness.level=<valor>` no `/storage/.config/emuelec/configs/emuelec.conf` nos subcomandos `salva`, `padrao` e `boot`, mantendo paridade com `r36-brilho.level`.
- **Persistência de Brilho e Volume no Shutdown**: proteção do `emuelec.conf` contra a sobrescrita cega da memória do EmulationStation no encerramento/reinicialização do sistema, garantindo que `audio.volume` e `brightness.level` reflitam os valores de hardware salvos.
- **Parâmetro `--timestamp` no build**: adição do argumento opcional `--timestamp <YYYYMMDD-HHMMSS>` na interface de linha de comando (`build.sh` / `r36img.build`), permitindo builds determinísticos sem avançar o relógio entre diferentes idiomas.

## Capabilities

### Modified Capabilities

- `splash-screens`: especifica a personalização do `bootlogo.bmp` do U-Boot na partição 2 (`R36-BOOT`), contendo a identificação "GA36-MB V1.2-20260416" no lugar de "OPEN SOURCE".
- `screen-brightness`: adiciona o requisito de sincronização em tempo real de `brightness.level` no `emuelec.conf` a cada ajuste salvo e na inicialização.
- `audio-output`: adiciona o requisito de preservação e sincronização de `audio.volume` no `emuelec.conf` durante o encerramento e reinicialização do sistema.
- `image-build`: adiciona suporte ao argumento de linha de comando `--timestamp` para fixar o timestamp da versão gerada.

## Impact

- `features/30-telas-icone-controle`: adição de `boot/bootlogo.bmp`, atualização do `gerar.sh` e `LEIA-ME.txt` com novo sha256; `tests/test_splash.py` estendido.
- `features/62-brilho-fn`: atualização do `brilho-aplica` para manipular `brightness.level` no `emuelec.conf`; unit systemd ou hook de shutdown para persistência.
- `features/46-audio`: gancho de encerramento para garantir que `r36-audio.volume` prevaleça no `emuelec.conf` no shutdown.
- `tools/r36img/build.py`: parser CLI atualizado com validação de formato para `--timestamp`.
- Testes unitários atualizados em `tests/test_splash.py`, `tests/test_brilho_fn.py`, `tests/test_audio.py` e `tests/test_cli.py`.
