# Tasks: Localização Dinâmica do Top Label da Lista de Jogos

- [x] 1. Limpar bitmap de fundo da lista de jogos <!-- id: 1-limpar-fundo -->
  - [x] 1.1 Tratar `ingame-global-bg.png` em `features/50-temas-extras/storage/.config/emulationstation/themes/Epic Cody ML/_art/` removendo os pixels de "SELECT GAME" da região superior esquerda (`x=0..204, y=10..52`) preenchendo com a cor de fundo padrão.
  - [x] 1.2 Tratar `ingame-global-bg.jpg` de forma idêntica se presente.

- [x] 2. Configurar variável `${top_label}` e atualizar XMLs do tema <!-- id: 2-configurar-xmls -->
  - [x] 2.1 Adicionar a chave `<top_label>GAMES</top_label>` em `_languages/pt-br.xml`.
  - [x] 2.2 Adicionar a chave `<top_label>JUEGOS</top_label>` em `_languages/es-latam.xml`.
  - [x] 2.3 Adicionar a chave `<top_label>GAMES</top_label>` em `_languages/en.xml`.
  - [x] 2.4 Atualizar `theme.xml` raiz vinculando `<text name="top_label" extra="true"><text>${top_label}</text>...</text>`.

- [x] 3. Atualizar ferramenta de refatoração e testes <!-- id: 3-atualizar-tool-e-testes -->
  - [x] 3.1 Atualizar `tools/refatora_epic_cody_ml.py` para incluir `top_label` nos dicionários e na limpeza/geração automatizada.
  - [x] 3.2 Atualizar `tests/test_tema_epic_cody_ml.py` validando que `top_label` existe em todos os catálogos, possui os valores esperados ("GAMES" em pt-br e en, "JUEGOS" em es-latam) e que o `theme.xml` faz referência à variável.
  - [x] 3.3 Executar a suíte de testes com `python3 -I -m unittest discover -s tests` e validar conformidade total.
