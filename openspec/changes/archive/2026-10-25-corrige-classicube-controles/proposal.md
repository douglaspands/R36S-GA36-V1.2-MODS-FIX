# Proposal

## Why

No R36S clone, os controles do ClassiCube estão quase inutilizáveis:

- **O analógico esquerdo anda ao contrário** em cima/baixo. O `Window_SDL2.c` passa `-y` ao `Gamepad_SetAxis`, mas o `PlayerInputPad` trata `y` positivo como `zMoving` positivo, que no jogo é andar para trás. O analógico direito tem o mesmo sinal e olha para o lado oposto ao esperado.
- **O analógico direito é lento demais:** cerca de 7°/s com o analógico no fundo (0,115° por frame com `mousesensitivity = 30` e `Gamepad_AxisSensitivity` fixo em NORMAL). Os menus sofrem do mesmo fator: um passo de seleção leva cerca de 1,7 s.
- **A zona morta é fixa em 3%** (1024/32768) e o movimento usa só o ângulo, então qualquer deriva do ADC dos analógicos vira velocidade total. A mitigação prevista no design original (ajustar a zona morta pelo `options.txt`) nunca existiu, porque o ClassiCube não tem essa opção.
- **Os binds padrão do gamepad não servem para o aparelho.** O Start abre o menu de pausa e também está ligado a "definir spawn", que redefine o ponto de respawn quando não há menu aberto. O Y (botão da esquerda no layout Nintendo do aparelho) abre o chat e o teclado virtual por acidente. O "pegar bloco" e o "respawn" não têm botão nenhum.
- **Os ajustes não alcançariam cartões já usados.** O `ClassiCube.sh` só copia o `options.txt` quando ele não existe, então valores novos de sensibilidade nunca chegariam a quem grava com `--keep-roms`.

## What Changes

- No `ports/classicube/compilar.sh`, o patch do `Window_SDL2.c` passa a enviar `+y` (sem negar) nos dois analógicos, corrigindo o movimento, a câmera e a navegação nos menus.
- Zona morta radial de cerca de 20% (6500/32768) nos dois analógicos, com o restante do curso reescalado para 0 a 1.
- `Gamepad_AxisSensitivity` dos dois eixos em HIGHER (4×), definido em `Gamepads_Init`.
- `mousesensitivity = 120` no `options.txt` da feature (cerca de 110°/s no fundo do analógico direito). O `ClassiCube.sh` aplica o valor novo também em cartões existentes, mas só se o valor atual ainda for o antigo (30), para não sobrescrever ajuste feito à mão.
- Novos binds padrão do gamepad, definidos em `PadBind_Defaults` (no `Input.c`, via `compilar.sh`), em vez de gravados no `options.txt`, para que os binds que o jogador salvar no menu continuem valendo:
  - Y: pegar bloco (`BIND_PICK_BLOCK`).
  - Chat: sem botão no gamepad (`BIND_CHAT` desligado).
  - Start: só pausa e envia o chat (`BIND_SET_SPAWN` desligado).
  - L3 + R3 (os dois analógicos apertados): respawn (`BIND_RESPAWN`). O Select não serve de modificador porque é o botão de voltar/escape do ClassiCube.
  - Mantidos: movimento no direcional e analógicos, A pula, X inventário, L quebra, R coloca, B+L velocidade, B+R voar, B+X atravessar paredes, B+cima/baixo voar para cima/baixo, L2/R2 trocam o item da barra, Select+Start sai.
- Testes estáticos para os patches do `compilar.sh`, para o `options.txt` e para a regra do `ClassiCube.sh`.
- Recompilação do binário em podman (o container da toolchain já existe) e atualização do `system/usr/share/classicube/ClassiCube`.

Fora do escopo: diagnóstico dos eixos no aparelho (os valores acima são estimativas a ajustar no primeiro teste real), movimento proporcional à intensidade do analógico, e qualquer mudança em outras features.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `classicube-port`: ganha requisitos novos para o sentido dos analógicos, a zona morta, a velocidade da câmera e dos menus, os binds padrão do gamepad e a sensibilidade em cartões já usados. Os requisitos existentes ficam como estão.

## Impact

- `ports/classicube/compilar.sh` (patches em `Window_SDL2.c` e `Input.c`) e `ports/classicube/receita.toml` se registrar os patches.
- `features/60-port-classicube/system/usr/share/classicube/ClassiCube` (binário novo), `.../options.txt` e `roms/ports/classicube/options.txt` (cópias idênticas).
- `features/60-port-classicube/roms/ports_scripts/ClassiCube.sh` e o espelho em `system/usr/share/classicube/ports_scripts/`.
- `tests/test_port_classicube.py`.
- `openspec/specs/classicube-port/spec.md` (via delta desta change).
- Sem mudança na ABI: o binário continua armhf, glibc até 2.36, com as mesmas bibliotecas.
