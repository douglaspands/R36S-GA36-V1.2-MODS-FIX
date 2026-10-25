# Tasks

## 1. Criação da Feature e Instalação dos Shaders

- [x] 1.1 Criar o diretório da feature `features/54-shaders-gba/` com o descritor `feature.toml` (`order = 54`, `enabled = true`) e verificar o reconhecimento da feature pelo build.
- [x] 1.2 Copiar `gba-modern-remaster.glsl` e `gba-modern-remaster.glslp` da pasta `/home/douglas/Games/shaders/shaders_glsl/` para a feature e conferir que o preset aponta para o shader correspondente.
- [x] 1.3 Mover os dois arquivos para `features/54-shaders-gba/system/usr/share/common-shaders/gba/` (camada de baixo do overlay `/tmp/shaders`) e tirar a camada `storage/` da feature.

## 2. Shader opcional pelo EmulationStation

- [x] 2.1 Remover os presets automáticos `gpSP/gpSP.glslp`, `gpSP/gba.glslp` e `mGBA/gba.glslp`, para o shader ficar desligado por padrão e não passar por cima do "SHADER SET" do ES.
- [x] 2.2 Atualizar o `feature.toml` e o `README.md` dizendo que o shader é escolhido no "SHADER SET" do ES.

## 3. Testes Automatizados e Validação

- [x] 3.1 Atualizar `tests/test_shaders_gba.py`: arquivos em `system/usr/share/common-shaders/gba/` com `0644`, sintaxe do preset, conteúdo do shader e ausência de qualquer outro `.glslp` ou camada `storage/` na feature. Rodar `uv run python -I -m unittest discover -s tests`.
- [x] 3.2 Rodar `./build.sh --test --fast` e conferir no `changes.txt` que o shader entra em `/usr/share/common-shaders/gba/` e que nada da feature vai para a p8.
- [ ] 3.3 Validação no aparelho (usuário): abrir um jogo de GBA e conferir que está sem shader; no ES, escolher `gba/gba-modern-remaster.glslp` em "SHADER SET" nas configurações avançadas do GBA, abrir o jogo e conferir o shader aplicado a 60 FPS; voltar a opção para nenhum e conferir que sai.
