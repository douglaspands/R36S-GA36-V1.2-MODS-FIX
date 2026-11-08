# Tasks: mrrescue-menu-navegacao-dpad

## 1. Ajuste de Controles no Mr. Rescue

- [x] 1.1 Extrair `features/64-love2d/roms/love/mrrescue.love` para diretório temporário e analisar `main.lua`
- [x] 1.2 Remover o bloco de polling e repetição de eixos analógicos (`axis1`/`axis2` com `xacccool`/`yacccool`) que dispara `gamestates[state].action(...)` em `updateKeys()`
- [x] 1.3 Garantir que a movimentação in-game (`keystate.up`, `keystate.down`, `keystate.left`, `keystate.right`) pelo analógico permaneça funcional
- [x] 1.4 Garantir que `love.gamepadpressed` e `love.joystickpressed` processem todos os direcionais do D-pad (`up`, `down`, `left`, `right`) de forma pontual para os estados de menu
- [x] 1.5 Reempacotar `mrrescue.love` com compressão compatível e validar que o arquivo zip pode ser lido pelo LÖVE 11.5

## 2. Validação e Testes Automatizados

- [x] 2.1 Adicionar teste unitário em `tests/test_love2d.py` verificando que `mrrescue.love` não contém chamadas de `action("down")` ou `action("up")` atreladas a `yacccool` ou `AXIS_COOLDOWN` no laço do `updateKeys()`
- [x] 2.2 Adicionar verificação de integridade garantindo que os mapeamentos do D-pad (`dpup`, `dpdown`, `dpleft`, `dpright` e botões brutos 14 a 17) continuam presentes no `main.lua`
- [x] 2.3 Executar a suíte completa de testes automatizados com `python3 -I -m unittest discover -s tests -p test_love2d.py`
- [x] 2.4 Atualizar a documentação do manual técnico (`docs/DESENVOLVIMENTO.md`, `docs/DEVELOPMENT.md` e `docs/DESARROLLO.md`) documentando o isolamento de menus no D-pad digital
