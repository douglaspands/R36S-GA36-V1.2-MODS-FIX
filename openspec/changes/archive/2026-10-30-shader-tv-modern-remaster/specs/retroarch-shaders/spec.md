# Spec Delta

## MODIFIED Requirements

### Requirement: Custo compatível com o Mali-400
O shader SHALL rodar no Mali-400 (OpenGL ES 2.0, GLSL ES 1.00, contexto `fbdev_mali`) na tela de 640x480 sem perder quadros: um passe, sem `pow` e sem laço. Shaders LCD usam uma leitura de textura; shaders de TV com fusão de dither MAY usar até 3 leituras horizontais adjacentes na mesma scanline.

#### Scenario: Restrições no arquivo
- **WHEN** o `.glsl` é inspecionado pelos testes
- **THEN** ele não chama `pow(`, shaders LCD têm exatamente uma chamada `COMPAT_TEXTURE(Texture`, shaders de TV têm no máximo três chamadas na mesma scanline, e o `.glslp` tem um passe

#### Scenario: Tempo de quadro no aparelho
- **WHEN** o usuário liga a exibição da taxa de quadros do RetroArch e joga um trecho com rolagem com o shader
- **THEN** a taxa fica na nativa do sistema (60 fps) e não cai em relação ao jogo sem shader

## ADDED Requirements

### Requirement: Perfil tv-modern-remaster para consoles de mesa e arcades
O shader `tv-modern-remaster` SHALL ser disponibilizado em `/usr/share/common-shaders/tv/tv-modern-remaster.glsl` e `.glslp`, calibrado para a tela de 640x480 do R36S com resolução horizontal nativa típica de 256 a 384 pixels e vertical de 224 a 240 linhas.

#### Scenario: Arquivos instalados
- **WHEN** o SYSTEM do build é inspecionado
- **THEN** os arquivos `tv-modern-remaster.glsl` e `tv-modern-remaster.glslp` existem sob `/usr/share/common-shaders/tv/`, com permissão 0644 e dono root

### Requirement: Fusão horizontal seletiva de dither para pseudo-transparências
O shader SHALL detectar padrões de alta frequência de alternância de 1 pixel ($A-B-A$) na mesma scanline horizontal e fundir apenas as regiões de dither, mantendo bordas de contraste, contornos e textos nítidos sem borramento global.

#### Scenario: Água e luzes translúcidas
- **WHEN** uma cena com dithering de xadrez ou barras verticais (água do Sonic, feixes de luz) é processada com `DITHER_BLEND > 0`
- **THEN** o padrão de quadriculado é convertido em uma transição suave e contínua de luminosidade e cor

#### Scenario: Contornos e textos preservados
- **WHEN** uma borda sólida entre duas regiões sem alternância periódica é processada
- **THEN** o shader não aplica mistura de dither e preserva a nitidez original da borda

#### Scenario: Controle de dither pelo menu
- **WHEN** o parâmetro `DITHER_BLEND` é ajustado para `0.0`
- **THEN** nenhuma fusão de dither é aplicada e a imagem preserva os pixels originais

### Requirement: Modulação suave de feixe CRT para telas pequenas
O shader SHALL aplicar uma modulação vertical suave de feixe CRT (beam profile) em vez de scanlines pretas duras, atenuando entre 10% e 15% a transição entre linhas, sem simular máscara de fósforo RGB e mantendo a claridade da tela de 3.5 polegadas.

#### Scenario: Imagem clara sem efeito moiré
- **WHEN** o shader roda em 640x480 sobre jogos com escala vertical fracionária de ~2.14x
- **THEN** a perda média de luminosidade provocada pela modulação de feixe não excede 5% e não há cintilação ou artefato de moiré ao rolar a tela

#### Scenario: Desativação do feixe de TV
- **WHEN** o parâmetro `TV_SCANLINES` é ajustado para `0.0`
- **THEN** o feixe de scanline é desativado e a imagem mantém iluminação vertical uniforme

### Requirement: Ativação por padrão em consoles de mesa e arcades
O serviço oneshot `r36-shader-tv-prepara.service` SHALL configurar o shader `tv-modern-remaster` como padrão no boot para os sistemas `megadrive`, `genesis`, `snes`, `nes`, `mastersystem`, `pce`, `psx`, `mame`, `fbneo`, `cps1`, `cps2`, `cps3` e `neogeo`.

#### Scenario: Primeiro boot sem escolhas prévias
- **WHEN** o aparelho inicializa pela primeira vez ou sem escolhas manuais nesses sistemas
- **THEN** o serviço insere `<sistema>.shaderset=tv/tv-modern-remaster.glslp` no `emuelec.conf` e cria os presets automáticos dos cores correspondentes sob `/storage/.config/retroarch/config/<Core>/<Core>.glslp`

#### Scenario: Preservação de escolha do usuário
- **WHEN** o usuário já tiver selecionado outro shader ou `none` para um sistema no EmulationStation
- **THEN** o serviço não substitui nem altera a configuração existente do usuário

### Requirement: Chave de escape para consoles de mesa e arcades
O serviço SHALL respeitar o arquivo vazio `r36-tv-sem-shader` na raiz da partição `R36-ROMS` (p1), desfazendo as configurações padrão que ele próprio criou para os sistemas de mesa e arcade, e registrando o diagnóstico em `r36-shader-tv.log` apenas quando `r36-diagnostico` existir.

#### Scenario: Desativação via PC
- **WHEN** o arquivo `r36-tv-sem-shader` está presente na p1 e o aparelho inicializa
- **THEN** os presets e entradas de `shaderset` criados pelo serviço para sistemas de mesa e arcade são desativados

#### Scenario: Log condicionado a diagnóstico
- **WHEN** `r36-diagnostico` não existe na p1
- **THEN** o arquivo `r36-shader-tv.log` não é criado nem modificado
