# Tasks

## 1. Extração e Auditoria dos Catálogos

- [x] 1.1 Extrair os arquivos base `pt_BR` e `es_MX` de `usr/config/emuelec/configs/locale/` da partição SYSTEM e catalogar todas as strings vazias (`msgstr ""`).
- [x] 1.2 Mapear e revisar as mensagens para garantir cumprimento da regra de nomenclaturas técnicas (preservando Save State, Core, Shader, Scraper, etc.).

## 2. Tradução e Calibração Visual (640x480)

- [x] 2.1 Traduzir as 122 mensagens faltantes de `pt_BR` com formulação concisa (verificar que nenhuma excede limites de largura de menus e diálogos).
- [x] 2.2 Traduzir as 148 mensagens faltantes de `es_MX` com vocabulário latino-americano conciso.
- [x] 2.3 Compilar os arquivos binários `emulationstation2.mo` com `msgfmt` e verificar ausência de erros de sintaxe ou charset.

## 3. Integração na Feature e Verificação do Build

- [x] 3.1 Integrar os arquivos `.po` e `.mo` na árvore de features (camada `system`).
- [x] 3.2 Executar `./build.sh --test` e verificar que os arquivos aparecem corretamente no SYSTEM com dono `0:0` e permissões adequadas.
- [x] 3.3 Adicionar teste automatizado em `tests/` para validar ausência de strings vazias nos catálogos distribuídos.
