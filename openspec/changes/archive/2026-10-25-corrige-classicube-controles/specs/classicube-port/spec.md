# Spec Delta

## ADDED Requirements

### Requirement: Sentido dos analógicos
O analógico esquerdo SHALL mover o personagem e o direito SHALL girar a câmera, ambos no sentido físico do movimento: empurrar para cima anda para frente (esquerdo) ou olha para cima (direito), e empurrar para baixo faz o oposto. Nos menus e no inventário, empurrar para cima SHALL mover a seleção para cima.

#### Scenario: Andar para frente
- **WHEN** o jogador empurra o analógico esquerdo para cima, estando no mundo
- **THEN** o personagem anda para frente, e para baixo ele anda para trás

#### Scenario: Olhar para cima
- **WHEN** o jogador empurra o analógico direito para cima
- **THEN** a câmera sobe, e para baixo ela desce

#### Scenario: Seleção em menu
- **WHEN** o jogador empurra o analógico esquerdo ou o direito para cima num menu ou no inventário
- **THEN** a seleção sobe, e para baixo ela desce

### Requirement: Zona morta dos analógicos
Os dois analógicos SHALL ignorar deslocamentos de até cerca de 20% do curso, e o restante do curso SHALL ser reescalado de 0 a 1, para a deriva do ADC não mover o personagem nem a câmera.

#### Scenario: Analógico solto com deriva
- **WHEN** o jogador solta os analógicos e eles leem até 20% do curso em qualquer eixo
- **THEN** o personagem fica parado e a câmera não gira

#### Scenario: Saída da zona morta
- **WHEN** o jogador empurra o analógico direito logo além dos 20% do curso
- **THEN** a câmera começa a girar de forma lenta e contínua, sem salto de velocidade

### Requirement: Velocidade da câmera e dos menus pelo analógico
Com o analógico direito no fundo, a câmera SHALL girar cerca de 110°/s, e a seleção de menus e inventário pelos analógicos SHALL andar um passo em menos de 0,5 s com o analógico no fundo. Esses valores SHALL independer da taxa de quadros.

#### Scenario: Volta completa
- **WHEN** o jogador mantém o analógico direito no fundo para um lado
- **THEN** a câmera completa uma volta em cerca de 3 a 4 segundos

#### Scenario: Navegação em menu
- **WHEN** o jogador mantém o analógico para baixo num menu com vários botões
- **THEN** a seleção desce um item em menos de 0,5 s

### Requirement: Binds padrão do gamepad
O ClassiCube SHALL usar estes binds padrão no `micro_gamepad`, com o layout dos botões da Nintendo: A (direita) pula, X (cima) abre o inventário, Y (esquerda) pega o bloco, L quebra e R coloca bloco, L2 e R2 trocam o item da barra, e clicar L3 e R3 juntos (os dois analógicos apertados) faz respawn. O Select continua sendo o botão de voltar e fechar menus. O chat e a definição do ponto de spawn SHALL NOT ter botão padrão no gamepad.

#### Scenario: Pausar sem mexer no spawn
- **WHEN** o jogador aperta Start no mundo para abrir o menu de pausa
- **THEN** o menu abre e o ponto de respawn não muda

#### Scenario: Y não abre o chat
- **WHEN** o jogador aperta Y no mundo
- **THEN** o bloco sob a mira é copiado para a barra e o chat e o teclado virtual não abrem

#### Scenario: Respawn
- **WHEN** o jogador segura L3 (analógico esquerdo apertado) e aperta R3 (analógico direito apertado) no mundo
- **THEN** o personagem volta ao ponto de respawn

#### Scenario: Combinações de modificador sem efeito duplo
- **WHEN** o jogador aperta B+L ou B+R
- **THEN** só a velocidade ou o voo é acionado, sem quebrar nem colocar bloco

#### Scenario: Binds salvos pelo jogador valem
- **WHEN** o jogador remapeia um bind do gamepad pelo menu do jogo
- **THEN** o bind salvo no `options.txt` prevalece sobre o padrão

### Requirement: Sensibilidade da câmera em cartões já usados
O lançador SHALL passar a sensibilidade da câmera do preset novo (`mousesensitivity = 120`) também ao `options.txt` de um cartão que já o tem, mas somente quando o valor gravado ainda for o do preset antigo (30). Um valor diferente de 30 SHALL ser preservado.

#### Scenario: Cartão gravado com --keep-roms e preset antigo
- **WHEN** o `options.txt` do cartão tem `mousesensitivity = 30` e o jogo é aberto pelo menu Ports
- **THEN** o valor passa a 120 e as demais linhas do arquivo ficam iguais

#### Scenario: Valor ajustado pelo jogador
- **WHEN** o `options.txt` do cartão tem `mousesensitivity` diferente de 30
- **THEN** o lançador não altera o valor
