# Tasks

## 1. Ajuste do inicializador e metadados do ClassiCube (Classic Craft)

- [x] 1.1 Modificar `features/60-port-classicube/roms/ports_scripts/ClassiCube.sh` para chamar `"$BIN" --singleplayer` diretamente, sem repassar os argumentos externos do EmulationStation (`"$@"`).
- [x] 1.2 Atualizar `features/60-port-classicube/roms/ports_scripts/gamelist.xml` com tags completas (`<image>`, `<thumbnail>`, `<marquee>`), nome amigável e validar presença dos assets em `ports_scripts/img/` e `ports_scripts/images/`.
- [x] 1.3 Atualizar o teste unitário `tests/test_port_classicube.py` para assegurar que `ClassiCube.sh` contém a flag `--singleplayer`, não repassa `"$@"` e que os arquivos de imagem existem.

## 2. Ajuste da tela de carregamento no emuelecRunEmu.sh

- [x] 2.1 Modificar `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh` para apontar o splash de abertura e fechamento para a imagem da partição `SYSTEM` (`/usr/config/splash/loading-game.png`), garantindo que o ícone do controle seja exibido mesmo com `--keep-storage`.
- [x] 2.2 Atualizar testes em `tests/test_splash.py` e `tests/test_registro_termico.py` para validar o caminho do splash em `emuelecRunEmu.sh`.

## 3. Reorganização dos Temas (Epic Cody padrão e NES-BOX no cartão)

- [x] 3.1 Atualizar `features/50-temas-extras/feature.toml` para instalar `Epic Cody` em `layer = "storage"` (`.config/emulationstation/themes/Epic Cody`), declarar remoção de `.config/emulationstation/themes/NES-BOX` da partição `storage`, e incluir o `NES-BOX` em `layer = "roms"` (`themes/NES-BOX`).
- [x] 3.2 Atualizar `features/10-ptbr-sao-paulo/storage/.config/emulationstation/es_settings.cfg` alterando o tema padrão para `Epic Cody` (`<string name="ThemeSet" value="Epic Cody" />`).
- [x] 3.3 Atualizar `tests/test_temas_extras.py` refletindo a nova distribuição de temas entre as partições `storage` e `roms`.

## 4. Validação de Build e Integração

- [x] 4.1 Executar toda a suíte de testes com `uv run python -I -m unittest discover -s tests` e validar 100% de sucesso.
- [x] 4.2 Executar o build com `./build.sh --test` e verificar que o `changes.txt` contém `Epic Cody` no storage, `NES-BOX` no cartão e a remoção correspondente.
