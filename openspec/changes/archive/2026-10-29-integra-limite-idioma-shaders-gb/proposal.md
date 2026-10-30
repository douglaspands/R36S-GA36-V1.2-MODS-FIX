# Proposal

## Why

Seis changes estão reunidas para implementar e integrar num único ciclo de validação e gravação no cartão SD: `limita-consumo-e-miniaturas-savestate` (A), `retroarch-idioma-do-emuelec` (B), `shaders-gb-gbc-r36s` (C), `brilho-fn-direcional` (D, FN + D-pad ↑/↓ ajusta o brilho), `emuelec-localizacao-ui` (E, tradução completa de pt_BR e es_MX no EmulationStation) e `tema-epic-cody-ml` (F, tema padrão Epic Cody multi-idioma com PT-BR, ES-Latam e EN). Validar as seis juntas num único build economiza ciclos de gravação e testa a interação real de todas no aparelho. Esta change não adiciona comportamento próprio: ela orquestra o desenvolvimento em paralelo (com sub-agentes isolados, incluindo E e F executados com o modelo Flash 3.8), a integração sem conflitos e o build único final contemplando todos os ajustes.

## What Changes

- **Desenvolvimento em paralelo e isolado:** um sub-agente por change, cada um num worktree/branch próprio, na branch com o nome da change (regra do `CLAUDE.md`), com uma matriz de arquivos que cada um pode escrever (write-set) e com `README.md`/`CLAUDE.md` fora do alcance dos agentes. Changes E e F rodam em paralelo via sub-agentes com o modelo Flash 3.8.
- **Qualidade por portões:** suíte completa e `openspec validate --strict` em cada branch, checagem do write-set pelo diff, revisão independente antes da integração.
- **Integração:** branch local `integra-limite-idioma-shaders-gb` a partir da `main`, com o merge das branches A, C, B, D, E e F, a contagem do teste de linhas do `emuelecRunEmu.sh` recalculada e a documentação consolidada numa passada só. Sem push e sem tocar na `main`.
- **Build único:** `./build.sh --idioma pt_BR`, inspeção da imagem sem montar (contemplando savestates, idioma, shaders GB/GBC, atalhos de brilho, catálogos `.mo`/`.po` de localização e o tema Epic Cody ML), `./flash.sh --target-file`, e depois a conferência no aparelho feita pelo usuário.
- **Decisões integradas de projeto:**
  - **B:** o idioma padrão do `--idioma` passa a ser **inglês** (`en_US`) em vez de `pt_BR`; o build desta integração usa `--idioma pt_BR` explicitamente.
  - **C:** os shaders de GB e GBC ficam **ligados por padrão** (a pergunta da task 3.3 está respondida); o usuário só reverte se mudar de ideia depois dos testes.
  - **E:** tradução de 100% das mensagens vazias em `pt_BR` e `es_MX` no ES, preservando nomenclaturas gamer em inglês e calibradas para 640x480.
  - **F:** tema padrão `Epic Cody ML` substituindo o tema original para economizar espaço e fornecendo subset de idioma nativo (PT-BR, ES-Latam, EN).

## Capabilities

### New Capabilities
Nenhuma.

### Modified Capabilities
Nenhuma. O comportamento muda nas changes A, B e C, cada uma com os seus specs delta. Esta change é de processo e não leva spec (`skip_specs: true`).

## Impact

- Branches locais: `limita-consumo-e-miniaturas-savestate`, `retroarch-idioma-do-emuelec`, `shaders-gb-gbc-r36s`, `brilho-fn-direcional`, `emuelec-localizacao-ui`, `tema-epic-cody-ml` e `integra-limite-idioma-shaders-gb`.
- Artefatos das changes B e C são revisados pelos próprios agentes (padrão `en_US` em B; ativação por padrão decidida em C).
- Um único `out/<timestamp>` para gravar e validar.
- Nenhuma gravação em cartão, nenhum `sudo`, nenhum push.
