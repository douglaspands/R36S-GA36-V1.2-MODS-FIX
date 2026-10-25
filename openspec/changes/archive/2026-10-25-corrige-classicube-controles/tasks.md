# Tasks

## 1. Patches dos analógicos e dos binds no `compilar.sh`

- [x] 1.1 Criar a branch `corrige-classicube-controles` a partir da `main` (regra do projeto) e conferir com `git branch --show-current`.
- [x] 1.2 Em `ports/classicube/compilar.sh`, no patch de `Window_SDL2.c`, trocar `-y / PAD_AXIS_SCALE` por `y / PAD_AXIS_SCALE` em `ProcessJoystick` e verificar que o `RuntimeError` dispara se o trecho original não existir (rodar o bloco Python contra uma cópia alterada no scratchpad).
- [x] 1.3 No mesmo patch, trocar o limiar `Math_AbsI(...) <= 1024` por zona morta radial de 20% com reescala (design, decisão 2) e verificar com um teste numérico em Python que o resultado é 0 em até 20% do curso, 0 logo após o limiar e 1,0 no fundo, nos dois eixos e na diagonal.
- [x] 1.4 No patch de `Window_SDL2.c`, definir `Gamepad_AxisSensitivity` dos dois eixos como `AXIS_SENSI_HIGHER` no início de `Gamepads_Init` e verificar o padrão `RuntimeError` como em 1.2.
- [x] 1.5 Acrescentar ao `compilar.sh` o patch de `src/Input.c` que troca as três linhas de `PadBind_Defaults` (set spawn e chat desligados, respawn em L3+R3, pegar bloco em Y; design, decisão 6) e verificar que ele aplica sobre o tarball verificado e que o `RuntimeError` dispara quando o trecho falta.
- [x] 1.6 Atualizar `ports/classicube/receita.toml` se ela registrar os patches e verificar que `test_recipe_and_build_script` continua passando.
- [x] 1.7 Cobrir os patches em `tests/test_port_classicube.py` (`compilar.sh` contém o `y` sem negação, a zona morta, `AXIS_SENSI_HIGHER` e as três linhas dos binds) e verificar com `uv run python -I -m unittest discover -s tests` que os testes novos passam.

## 2. Binário novo

- [x] 2.1 Rodar `./ports/classicube/compilar.sh` (podman, sem sudo) e verificar que termina com "Compilação concluída" e que o `features/60-port-classicube/system/usr/share/classicube/ClassiCube` foi atualizado.
- [x] 2.2 Verificar com os testes existentes (`test_binary_architecture_and_abi`, `test_binary_libraries_against_base`, `test_binary_exists_and_stripped`) que o binário continua armhf, hard-float, sem `GLIBC_` acima de 2.36 e sem símbolos de depuração.

## 3. Sensibilidade no preset e no lançador

- [x] 3.1 Trocar `mousesensitivity = 30` por `120` no `options.txt` de `features/60-port-classicube/roms/ports/classicube/` e na cópia de `system/usr/share/classicube/`, e verificar com `cmp` que ficam idênticos (`test_system_ports_mirror_and_sync`).
- [x] 3.2 No `ClassiCube.sh`, trocar `mousesensitivity = 30` por `120` no `options.txt` da p1 só quando o valor for exatamente o antigo (design, decisão 5), acrescentando a linha quando a chave não existir; copiar o mesmo arquivo para `system/usr/share/classicube/ports_scripts/` e verificar `bash -n` e a igualdade entre as duas cópias.
- [x] 3.3 Cobrir as duas regras em `tests/test_port_classicube.py`, executando o trecho do lançador num `options.txt` temporário: valor 30 vira 120 sem tocar nas outras linhas, valor 80 permanece, chave ausente recebe 120; verificar que os testes passam.

## 4. Documentação e fechamento

- [x] 4.1 Atualizar o item `60-port-classicube` do `README.md` com o sentido dos analógicos, a zona morta, a sensibilidade e os binds padrão do gamepad, e verificar que o texto bate com o spec desta change.
- [x] 4.2 Rodar `uv run python -I -m unittest discover -s tests` completo e verificar que não há falhas novas.
- [x] 4.3 Rodar `openspec validate corrige-classicube-controles --strict` e verificar que passa.
- [x] 4.4 Gerar o cartão de teste com `./build.sh` (sem sudo) e verificar com `./flash.sh --target-file` num arquivo temporário que o SYSTEM leva o binário novo.

## Workflow follow-up

- Teste no aparelho pelo jogador: andar para frente com o analógico para cima, girar a câmera, navegar no inventário, pausar com Start sem mover o spawn, pegar bloco no Y e respawn em L3+R3. Se a câmera ficar lenta ou o personagem andar sozinho, ajustar `mousesensitivity` e a zona morta (decisões 2 e 4 do design).
- Arquivar a change só depois dessa validação, a pedido do usuário.
