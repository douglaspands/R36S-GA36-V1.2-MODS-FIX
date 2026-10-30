# Tasks

## 1. Calibração Estrutural de Layout e Rodapé no theme.xml

- [x] 1.1 Atualizar as coordenadas horizontais de toda a coluna de informações da esquerda para a margem segura `x = 0.025` no `theme.xml` raiz e verificar alinhamento uniforme.
- [x] 1.2 Calibrar a hierarquia tipográfica no `theme.xml` raiz ajustando `sys_line1` para `fontSize: 0.045` (`size: 0.52 0.045`) e `sys_line2` para `fontSize: 0.150` (`size: 0.52 0.200`), verificando que o bounding box comporta palavras longas sem reticências.
- [x] 1.3 Declarar a estilização explícita de `<helpsystem name="help">` em `<view name="system">` com fonte Acre Medium (`0.022`), ícones de botões em âmbar (`#FFAE00`) e texto em cinza neutro (`#A0A0A0`).
- [x] 1.4 Reposicionar e redimensionar o gráfico do console (`controller`) para `pos: 0.35 0.62` e `maxSize: 0.28 0.28`, verificando que o limite inferior termina em `y = 0.90` com respiro livre acima do rodapé.

## 2. Localização Dinâmica do Botão de Ação em SVG

- [x] 2.1 Criar os arquivos vetoriais `_art/var/button-pt.svg` e `_art/var/button-es.svg` com a inscrição `(A) ENTRAR` estilizada no mesmo padrão gráfico do original `button.svg`.
- [x] 2.2 Vincular o elemento `<image name="buttonA">` à variável dinâmica `${buttonImage}` no `theme.xml` raiz, garantindo fallback limpo para `./_art/var/button.svg`.

## 3. Curadoria de Títulos, Tags nos Consoles e Catálogos de Tradução

- [x] 3.1 Inserir o bloco `<text name="sys_line1" extra="true"><text>${sistema.sys_line1}</text></text>` nos arquivos `theme.xml` dos 59 sistemas que não possuíam a linha 1 declarada.
- [x] 3.2 Curar a divisão de títulos em `_languages/pt-br.xml`, `es-latam.xml` e `en.xml` para todos os sistemas com nomes longos (GBC, N64, NDS, PSX, PS2, Turbografx-16, Todos os Jogos, etc.), atribuindo a família/fabricante a `sys_line1` e o identificador do modelo a `sys_line2`.
- [x] 3.3 Revisar e traduzir 100% dos termos remanescentes em inglês nos catálogos `_languages/pt-br.xml` e `es-latam.xml` (`Options` -> `RetroArch`, `Pixel Games` -> `Console Fantasia`, `LCD SCREEN` -> `Portátil LCD`, `Color COMPUTER` -> `Computador TRS-80`, `Multiple Arcade Machine Emulator` -> `Emulador Arcade`, etc.) e normalizar capitalização.
- [x] 3.4 Definir a variável `<buttonImage>` em cada catálogo (`pt-br.xml`, `es-latam.xml` e `en.xml`) apontando para o respectivo arquivo SVG localizado.

## 4. Atualização da Ferramenta de Geração e Testes

- [x] 4.1 Atualizar `tools/refatora_epic_cody_ml.py` com as novas tabelas de tradução, regras de layout calibradas e injeção automática de `sys_line1` e `${buttonImage}`.
- [x] 4.2 Adicionar testes automatizados em `tests/test_temas_extras.py` validando ausência de truncamento de títulos em 640x480, presença das tags nos consoles e integridade dos SVGs de botões.
- [x] 4.3 Executar a suíte de testes unitários (`python3 -I -m unittest discover -s tests`) e verificar que todos os testes passam sem regressões.
