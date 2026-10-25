# Design

## Context

Motivação e escopo em `proposal.md`. O estado atual, lido no código do ClassiCube 1.3.9 já com os patches de `ports/classicube/compilar.sh` (`work/ports/classicube/src/src/`):

- **Eixos.** `Window_SDL2.c:ProcessJoystick` lê `SDL_GameControllerGetAxis` (cima é negativo no SDL), zera valores com módulo até 1024 e chama `Gamepad_SetAxis(port, axis, x/32768, -y/32768, delta)`. Quem consome:
  - `InputHandler.c:PlayerInputPad` faz `angle = Math_Atan2f(x, y)` (a função tem a assinatura `(x, y)` mas calcula `atan2(y, x)`), `xMoving = cos`, `zMoving = sin`. Com `y = +1` sai `zMoving = +1`. No jogo `zMoving < 0` é frente (`PlayerInputNormal`: W faz `zMoving -= 1`). O resultado ignora a intensidade: só o ângulo conta.
  - `Camera.c:OnAxisUpdate` soma `upd->x/y` no delta do mouse. Pitch positivo é olhar para baixo.
  - `Menus.c:Menu_PadAxis` usa `ySteps`; `Menu_CycleSelected(+1)` desce.
  - As outras plataformas do ClassiCube não são consistentes (Dreamcast, PS1, PS2 e Vita passam `y` direto; SDL2, 3DS e GC/Wii passam `-y`), então o sinal certo para o SDL2 sai da leitura dos consumidores, não de comparação com portes.
- **Velocidade.** `Gamepad_SetAxis` entrega `x * delta * 60 * fator`. O fator vem de `Gamepad_AxisSensitivity` (NORMAL = 1,0; HIGHER = 4,0) e nenhum menu o altera. A câmera converte cada unidade em `0,0002/3 * 57,2958 * mousesensitivity` graus, ou 0,0038 × `mousesensitivity`. Com 30: 0,115°/frame, cerca de 7°/s. Os menus acumulam `y/100` por frame para gerar passos.
- **Binds.** `Input.c:PadBind_Defaults` guarda os padrões; `InputBind_Load` usa o que estiver em `options.txt` como `pad-<Nome>` e cai no padrão caso contrário. Mapeamento de dois botões `{ botão1, botão2 }` significa segurar o 1 e apertar o 2, e `InputBind_Claims` dá prioridade ao de dois botões sobre o de um (B+L não quebra bloco). O `padDevice` define Start como pausa e confirmação, A como confirmação e **Select como escape**.
- **Layout físico.** `micro_gamepad` é o layout Nintendo: `a:b0` é o botão da direita, `b:b1` o de baixo, `x:b2` o de cima, `y:b3` o da esquerda. Os cliques dos analógicos são `leftstick:b11` e `rightstick:b12`.
- **Lançador.** `ClassiCube.sh` só copia o `options.txt` se não existir e só acrescenta `auto-pause`. O arquivo é reaproveitado entre gravações com `--keep-roms`.
- **Restrições.** Sem sudo; Python via `uv run`; o build roda em podman com `cores/toolchain` (glibc 2.36). A ABI do binário não muda. Não há como testar o jogo no aparelho dentro da sessão.

## Goals / Non-Goals

**Goals:**
- Que o sentido, a zona morta, a velocidade e os binds do gamepad do spec saiam do binário e do lançador, de forma reprodutível a partir do tarball verificado por sha256.
- Que o patch falhe de forma ruidosa (como os atuais) quando o código-fonte não tiver o trecho esperado.

**Non-Goals:**
- Medir os eixos reais do aparelho: os valores abaixo são estimativas razoáveis, ajustáveis na próxima rodada.
- Tornar o movimento proporcional à intensidade (muda o `PlayerInputPad`, que é código de todos os backends).
- Criar menu ou opção para zona morta e sensibilidade dos analógicos no jogo.

## Decisions

### 1. Corrigir o sinal na origem (`ProcessJoystick`), não nos consumidores
Trocar `-y / PAD_AXIS_SCALE` por `y / PAD_AXIS_SCALE`. Os três consumidores (movimento, câmera e menus) passam a concordar com a convenção "y positivo é para baixo", que é a do `PlayerInputNormal` e do mouse.
- *Alternativa:* inverter dentro de `PlayerInputPad`, `OnAxisUpdate` e `Menu_PadAxis`. Rejeitada: três patches em código compartilhado em vez de um na camada SDL2.
- *Alternativa:* `Camera.Invert`. Rejeitada: só afeta a câmera.

### 2. Zona morta radial de 20% com reescala, no mesmo `ProcessJoystick`
Com `m = hypot(x, y) / 32768` e `dz = 0,2`: se `m <= dz` os dois eixos vão a 0; senão, ambos são multiplicados por `(m - dz) / (1 - dz) / m`. Radial, para que um analógico inclinado na diagonal não ganhe zona morta maior no eixo menor, e com reescala para que a câmera não "salte" ao sair da zona morta. O limiar antigo (módulo até 1024 por eixo) é removido.
- *Alternativa:* só subir o limiar por eixo, sem reescala. Rejeitada: a câmera saltaria de 0 para 0,2 do curso.
- *Alternativa:* zona morta menor (10%). Possível ajuste futuro: 20% é o valor conservador sem medição, porque a deriva de ADC de clone é comum e o movimento é tudo-ou-nada.

### 3. Sensibilidade do analógico em HIGHER, definida em `Gamepads_Init`
`Gamepad_AxisSensitivity[PAD_AXIS_LEFT] = Gamepad_AxisSensitivity[PAD_AXIS_RIGHT] = AXIS_SENSI_HIGHER` no início de `Gamepads_Init` (`Window_SDL2.c`). Os dois eixos recebem o mesmo valor: o esquerdo só importa nos menus, onde o ganho de 4× leva um passo a ~0,4 s com o analógico no fundo (`4 × y × delta × 60 / 100` por frame, 25 frames a 60 fps).

### 4. `mousesensitivity = 120` no `options.txt`, não no código
Câmera: `0,0038 × 120 × 4 × 60 ≈ 110°/s` com o analógico no fundo; volta completa em ~3,3 s. O jogador ainda ajusta pelo menu do jogo ("Mouse sensitivity", até 200, que dá ~183°/s). Fica em `options.txt` e não em constante C porque é a opção que o próprio jogo expõe.
- *Alternativa:* multiplicar a câmera por uma constante no patch e deixar `mousesensitivity = 30`. Rejeitada: o menu do jogo passaria a mostrar um valor que não corresponde ao que se sente.

### 5. Preset novo chega a cartões antigos só se o valor ainda é o padrão antigo
O `ClassiCube.sh` troca `mousesensitivity = 30` por `120` no `options.txt` da p1 com um `sed` restrito a essa linha exata, e não mexe se o valor for outro ou se a chave não existir (nesse caso o jogo usa o padrão do código, 30, e a linha é acrescentada com 120). Isso cobre `--keep-roms` sem apagar ajuste do jogador. A edição só roda quando o valor muda, para não regravar a FAT32 a cada abertura.
- *Alternativa:* forçar o valor sempre. Rejeitada: apaga ajuste feito de propósito.
- *Alternativa:* versionar o preset (por exemplo `# preset = 2`). Rejeitada por ora: um segundo mecanismo para uma única chave.

### 6. Binds novos em `PadBind_Defaults`, não em `options.txt`
Patch por substituição exata de três linhas da tabela em `Input.c`:

| Bind | Antes | Depois |
|---|---|---|
| `BIND_SET_SPAWN` | Start | desligado `{0,0}` |
| `BIND_CHAT` | Y (`CCPAD_4`) | desligado `{0,0}` |
| `BIND_RESPAWN` | desligado | `{ CCPAD_LSTICK, CCPAD_RSTICK }` |
| `BIND_PICK_BLOCK` | desligado | Y (`CCPAD_4`) |

Mantidos como estão: pular em A, inventário em X, quebrar em L e colocar em R, velocidade B+L, voar B+R, noclip B+X, voo subir/descer B+cima/baixo, troca de item da barra em L2/R2. Colocar nos padrões do código preserva qualquer bind que o jogador salve (`pad-*` no `options.txt` vence). Gravar no `options.txt` faria o contrário: nos cartões novos prenderia o jogador a esses binds.
- Respawn em L3+R3 e não em Select+algo: o Select é o botão de escape do `padDevice` e abriria a pausa ao ser segurado como modificador.
- Chat desligado: sem teclado, o chat só abre o teclado virtual. O `BIND_SEND_CHAT` em Start continua, e só vale dentro do chat.
- `BIND_SET_SPAWN` desligado: Start já é pausa, e `LocalPlayer_HandleSetSpawn` roda quando não há menu aberto, então Start pode redefinir o ponto de respawn a cada pausa. O jogador que quiser o bind pode recolocá-lo no menu do jogo.

### 7. Verificação
Sem aparelho na sessão, os testes são estáticos em `tests/test_port_classicube.py`: o `compilar.sh` contém cada patch (sem `-y`, zona morta, `AXIS_SENSI_HIGHER`, as três linhas de `PadBind_Defaults`) e levanta erro se o padrão não for encontrado; o `options.txt` tem `mousesensitivity = 120` e as duas cópias (p1 e SYSTEM) são idênticas; o `ClassiCube.sh` tem sintaxe válida e a regra da sensibilidade, exercitada num `options.txt` temporário nos dois casos do spec. A matemática do patch de zona morta ganha um teste numérico em Python equivalente. A verificação real fica com o jogador no aparelho.

## Risks / Trade-offs

- [Os valores são estimativas, sem medição dos eixos] → A zona morta e a sensibilidade são constantes simples no `compilar.sh` e a sensibilidade também está no `options.txt`; o primeiro teste real calibra. Se o alcance real dos analógicos for menor que ±32767, a câmera fica mais lenta que o previsto e a ação é subir `mousesensitivity`.
- [A zona morta de 20% pode tirar a precisão fina do movimento] → O movimento do ClassiCube já é tudo-ou-nada; para a câmera, a reescala mantém a progressão suave.
- [Padrão de patch não encontrado após atualizar o ClassiCube] → Cada substituição levanta `RuntimeError` se o trecho não existir, como os patches atuais, e o tarball segue fixo na versão 1.3.9 por sha256.
- [Quem já remapeou binds no menu do jogo] → Preservado: os binds salvos vencem os padrões novos. Quem remapeou Y para chat continua com chat.
- [O `sed` do lançador na FAT32] → A regravação só ocorre quando a linha antiga está lá; no máximo uma vez por cartão.
- [Binário novo exige recompilar em podman] → O container `cores/toolchain` já existe no projeto; a ABI não muda, então os testes de ABI existentes cobrem o resultado.

## Migration Plan

1. Recompilar com `ports/classicube/compilar.sh` e conferir ABI com os testes existentes.
2. Regravar o SYSTEM; o `ClassiCube.sh` novo (SYSTEM e p1) ajusta a sensibilidade nos cartões antigos na primeira abertura.
3. Rollback: voltar o commit e regravar o SYSTEM. O `mousesensitivity = 120` que o lançador gravou na p1 permanece, e o jogador o ajusta pelo menu do jogo.
