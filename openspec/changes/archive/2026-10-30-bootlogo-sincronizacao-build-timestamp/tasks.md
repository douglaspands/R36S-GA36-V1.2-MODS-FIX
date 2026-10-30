# Tasks

## 1. Suporte a `--timestamp` no CLI de Build

- [x] 1.1 Adicionar a opção `--timestamp <YYYYMMDD-HHMMSS>` no `_build_parser()` de `tools/r36img/build.py` com validação de formato e repasse a `build()`.
- [x] 1.2 Adicionar testes em `tests/test_cli.py` cobrindo `--timestamp` válido, timestamp com formato inválido e o comportamento padrão quando omitido.

## 2. Boot Logo com Identificação da Placa-Mãe

- [x] 2.1 Gerar `features/30-telas-icone-controle/boot/bootlogo.bmp` a partir do original da base, substituindo o texto "OPEN SOURCE" por "GA36-MB V1.2-20260416" mantendo BMP 24bpp e tamanho exato de 921.654 bytes.
- [x] 2.2 Atualizar `features/30-telas-icone-controle/gerar.sh` e `LEIA-ME.txt` documentando o `bootlogo.bmp` e seu hash SHA-256.
- [x] 2.3 Atualizar `tests/test_splash.py` para validar o arquivo `boot/bootlogo.bmp` e sua integração na partição `boot` do build.

## 3. Sincronização em Tempo Real e Persistência no `emuelec.conf`

- [x] 3.1 Atualizar `features/62-brilho-fn/system/usr/lib/r36/brilho-aplica` para sincronizar atipicamente `brightness.level=<valor>` no `emuelec.conf` em `salva`, `padrao` e `boot`.
- [x] 3.2 Criar serviço systemd de encerramento (`r36-conf-sync.service` em `features/46-audio` ou `features/62-brilho-fn`) que reaplica os valores reais de `r36-brilho.level` e `r36-audio.volume` no `emuelec.conf` antes do desligamento/reinício.
- [x] 3.3 Atualizar testes em `tests/test_brilho_fn.py` e `tests/test_audio.py` validando que `emuelec.conf` recebe as atualizações em tempo real e preserva os valores de hardware.
- [x] 3.4 Criar `features/62-brilho-fn/system/usr/lib/r36/brilho-es-sync` para sincronizar `brightness.level` na memória RAM do EmulationStation (`SystemConf`) em tempo real via `/proc/<pid>/mem`, refletindo imediatamente no menu do sistema (Configurações do Sistema).

## 4. Verificação e Integração

- [x] 4.1 Executar a suíte de testes do repositório (`python3 -I -m unittest discover -s tests`) e verificar que todos passam sem regressões.
- [x] 4.2 Executar um build de teste com `--timestamp` e inspecionar a partição `boot` (p2) e o `emuelec.conf` gerados.
