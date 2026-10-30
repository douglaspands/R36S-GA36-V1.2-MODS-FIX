# Design

## Context

Ver `proposal.md` (Why). As quatro changes (A, B, C e D) estão só como artefatos (nenhuma task feita) e hoje são pastas não versionadas (`??`) na `main`. Regras do `CLAUDE.md` que moldam a orquestração: uma branch por change criada a partir da `main` com o nome da change; sem `sudo`; Python via `uv`; comandos de shell um por chamada, sem `cd` nem `&&`; merge e push só a pedido (o usuário autorizou o merge local da integração, não o push); `base/`, `work/` e `var/` são ignorados pelo git.

A feature `56-retroarch-ajustes` (de que B depende) já está na `main` (commit `849d780`), então B pode começar já.

## Goals / Non-Goals

**Goals:** nenhum agente altera o trabalho de outro; qualidade e desempenho verificados antes da integração; um só build validado no aparelho.

**Non-Goals:** gravar cartão; executar as tasks de conferência no aparelho (B 5.x, validação visual de C); arquivar as changes; push; mudar o comportamento já especificado em A, B e C, salvo as duas decisões do usuário (D4, D5).

## Decisions

### D1. Um worktree por agente, branch com o nome da change

Cada agente roda com `isolation: "worktree"`. Como a pasta da change está não versionada, ela é commitada antes, na branch da própria change (task 1.2); sem isso o worktree nasceria sem os artefatos. O agente renomeia a branch criada pelo harness para o nome da change (`git branch -m`). `base/` é ignorado pelo git: cada worktree recebe um symlink para `base/` da árvore principal (leitura apenas; a imagem base nunca é modificada). `work/` e `var/` ficam por worktree, então os builds de teste dos agentes não colidem.

*Alternativa descartada:* um agente só, em série. Perde o paralelismo e acumula contexto das quatro changes.

### D2. Matriz de escrita (write-set) exclusiva

| Caminho | Dono | Observação |
|---|---|---|
| `features/41-servicos-enxutos/` | A | |
| `features/10-ptbr-sao-paulo/storage/**` (`emuelec.conf`, `retroarch.cfg`) | A | B não edita; só o build de B regrava cópias em `work/` |
| `features/10-ptbr-sao-paulo/system/usr/bin/emuelecRunEmu.sh` | A e B | **zonas disjuntas**: A só nos trechos de savestate (parser `-autosave/-state_slot`, `mkdir`) e do bloco de netplay (linhas ~425-477); B só **uma** chamada do `idioma-aplica` ao lado da do `shaderset-aplica` (~482) |
| `features/56-retroarch-ajustes/system/usr/lib/r36/retroarch-prepara` | A | |
| `features/56-retroarch-ajustes/system/usr/lib/r36/idioma-aplica` | B | arquivo novo |
| `tools/r36img/build.py`, `build.sh` | B | |
| `features/55-shaders-gb-gbc/**` | C | feature nova |
| `features/62-brilho-fn/**` | D | feature nova |
| `features/46-audio/system/usr/bin/udt_pwr_events.sh` | D | só **uma** chamada do `brilho-aplica` depois do restore do `lcdbl` no ramo de acordar (~l.35-37); nenhuma outra change o edita |
| `features/10-ptbr-sao-paulo/system/usr/config/emuelec/configs/locale/**` | E | catálogos `pt_BR` e `es_MX` (.po e .mo compilados) |
| `features/50-temas-extras/**` | F | substituição de `Epic Cody` por `Epic Cody ML` |
| `features/10-ptbr-sao-paulo/storage/.config/emulationstation/es_settings.cfg` | F | define `ThemeSet = "Epic Cody ML"` (seção isolada de A) |
| `tools/refatora_epic_cody_ml.py` | F | script auxiliar de extração do tema |
| `tests/test_brilho_fn.py` | D | |
| `tests/test_localizacao_ui.py` | E | validação de cobertura dos catálogos |
| `tests/test_tema_epic_cody_ml.py` | F | validação de XMLs, subsets e variáveis do tema |
| `tests/test_otimizacoes.py`, `tests/test_retroarch_ajustes.py` | A | |
| `tests/test_idioma_aplica.py`, `tests/test_idioma_build.py`, `tests/test_image.py`, `tests/test_cli.py` | B | |
| `tests/test_shaders_gb_gbc.py` | C | |
| `tests/test_ptbr_controle.py` | A e B | A adiciona testes ao fim do arquivo; B só a contagem de linhas (~l.232) e a ordem da chamada |
| `openspec/changes/<a-sua-change>/**` | o próprio agente | `verificacao/` de C incluída |
| `README.md`, `CLAUDE.md` | **ninguém** (só a integração) | cada agente grava `docs-<change>.md` na pasta da sua change |

O `emuelecRunEmu.sh` (inclusive o `screen_brightness`, l.67-70) **não** está no write-set de D, e `tests/test_fn.py` e `tests/test_audio.py` são só leitura para D. Um agente que precise de um arquivo fora do seu write-set **para e relata**, sem editar. O diff de cada branch contra a `main` é conferido contra esta matriz antes da integração (task 2.4).

*Por que isso basta:* os conflitos reais de merge ficam restritos a `emuelecRunEmu.sh` e `test_ptbr_controle.py`, em trechos disjuntos, e a um número que só existe depois do merge (D6). D não divide nenhum arquivo com A, B ou C.

### D3. Portões de qualidade (obrigatórios, por branch)

1. `uv run python -I -m unittest discover -s tests` verde no worktree, com os testes novos escritos **antes** do código de cada task (falham primeiro, depois passam).
2. `openspec validate <change> --strict` sem erro.
3. `sh -n` / `bash -n` em todo script tocado; permissões e dono conferidos nos arquivos novos (0755 nos executáveis, 0644 nos demais), como a feature 54.
4. ABI/portabilidade: scripts em `sh` do BusyBox da base, sem recurso de shell que o aparelho não tenha; shaders dentro do perfil da Mali-400 (passe único, uma leitura de textura, `mediump`, sem `pow()` e sem laços).
5. Cada task do `tasks.md` da change marcada `[x]` só com a verificação descrita na própria task rodada e a saída registrada no relatório.
6. **Revisão independente** (D7) com agente novo, sem o contexto de quem implementou.

### D4. B: idioma padrão em inglês

O `--idioma` de B passa a ter padrão `en_US`. Os arquivos das features no repositório não mudam (continuam em `pt_BR`, feature 10); quem gera o idioma é o build, que reescreve `system.language`, `Language` e `user_language` nas cópias em `work/`. Consequências, a cargo do agente de B nos artefatos dele:
- Propostas, design (D3, D6, D7), specs `build-language` e `image-build`, tasks e testes trocam "padrão `pt_BR`" por "padrão `en_US`". Um `./build.sh` sem argumento gera imagem **em inglês**, com `en-us` no nome.
- `test_image.py` e `test_idioma_build.py` cobrem o padrão (`en_US`) **e** `--idioma pt_BR`.
- `./build.sh --help` e o `README.md` (via `docs-retroarch-idioma-do-emuelec.md`) deixam claro que o padrão é inglês e que para português é preciso passar `--idioma pt_BR`.
- O **build desta integração** é sempre `./build.sh --idioma pt_BR`.

*Atenção:* isso inverte o comportamento de quem hoje roda `./build.sh` à espera de português. É o que o usuário pediu; o `README.md` precisa dizer isso no topo da seção do build.

### D5. C: shaders ligados por padrão

A pergunta da task 3.3 de C está respondida: `gb-modern-dmg` e `gbc-modern-remaster` ficam **ligados por padrão** no boot (`gb.shaderset`/`gbc.shaderset` e presets `<Core>/gb.glslp` e `<Core>/gbc.glslp`, com as chaves `r36-gb-sem-shader` e `r36-gbc-sem-shader` na p1 para desligar), como o GBA na feature 54. O agente de C reescreve a task 3.3 no `tasks.md` dele para registrar a decisão e atualiza o `README` via `docs-shaders-gb-gbc-r36s.md`. Se o usuário mudar de ideia depois dos testes, a reversão é uma change pequena (ficam disponíveis só pelo menu) e não bloqueia esta integração.

Só C usa o `~/AppImages/retroarch.appimage` do PC; A e B não, então não há disputa por ele.

### D6. Integração em branch própria, com uma ordem fixa

Branch `integra-limite-idioma-shaders-gb` a partir da `main`, merge `--no-ff` na ordem **A, C, B, D, E, F**: A e C são quase disjuntas; B depois, porque é a que toca A (RunEmu, testes) e porque o teste de build dela exercita as demais; D por ser disjunta; E (`emuelec-localizacao-ui`) e F (`tema-epic-cody-ml`) integradas a seguir por tocarem áreas limpas e específicas (catálogos de localização do ES e temas/es_settings). Depois de cada merge:
- recalcular a contagem de linhas novas do `emuelecRunEmu.sh` em `tests/test_ptbr_controle.py` (cada agente acertou a sua isoladamente; o valor final é da soma). O número vem de rodar o teste e conferir o `git diff` da base, nunca de somar de cabeça;
- conferir que o `retroarch.cfg` de A ainda contém todas as chaves que o build de B reescreve (`user_language`);
- consolidar `README.md` e `CLAUDE.md` a partir dos `docs-*.md`, numa só passada, e remover os `docs-*.md`;
- suíte completa + `openspec validate --strict` de todas as changes e desta.

Resolução de conflito: nunca descartar um lado; se o conflito sair da zona do D2, parar e relatar ao usuário.

### D7. Revisão independente antes do merge

Para cada branch, um agente novo olha: correção, fidelidade aos specs, uso de `sh` portátil, idempotência no boot, interação com `--keep-storage`/`--part system` (arquivos que já existem na p8 nunca são atualizados pela base, ver `CLAUDE.md`), e custo. Os achados voltam ao implementador e a revisão repete até não haver achado aberto. Só então a branch entra na integração.

### D8. Modelo e esforço dos agentes

Implementadores A, B, C, D rodaram em `opus`. Sub-agentes E (`emuelec-localizacao-ui`) e F (`tema-epic-cody-ml`) rodam em paralelo com o modelo **Flash 3.8** (`flash`), com `isolation: "worktree"` (ou workspace branch), conforme solicitado pelo usuário. Os prompts estão em `orquestracao.md`; cada um é autocontido.

### D9. Build único e validação

Um `./build.sh --idioma pt_BR` na branch de integração. Inspeção sem montar (`mcopy`, `unsquashfs -cat/-lls`) de todos os itens de A, B, C, D, E e F e `./flash.sh --target-file`; o `./flash.sh --device` com `sudo dd` é instrução para o usuário (task 6). O build único final contempla todos os ajustes para teste simultâneo no aparelho. O build de teste `--idioma en_US --test` entra no passo 5 para exercitar o padrão e o nome da imagem, sem ser gravado.

## Risks / Trade-offs

- **Número do teste de linhas do RunEmu** → recalculado só após o merge (D6).
- **Três scripts gravam no mesmo `retroarch.cfg`:** o `retroarch-prepara` de A edita o mesmo `retroarch.cfg` que o `shaderset-aplica` e o `idioma-aplica` gravam a cada jogo → a integração tem um teste com os três scripts em sequência sobre o mesmo `retroarch.cfg` (task 4.4).
- **A p8 vence o SYSTEM** (`CLAUDE.md`): arquivos de shader e cores já existentes na p8 não são atualizados pela base → os serviços de C (e de A, no `retroarch-prepara`) são testados com a p8 já populada por uma versão anterior.
- **Falta de hardware real:** tempo de quadro dos shaders, o gravador de idioma do ES, as miniaturas e o D-pad com o FN apertado (botão ou eixo) só se confirmam no aparelho → ficam na task 6.
- **Brilho de D e o `screen_brightness` do RunEmu:** D reaplica o nível ao acordar e no boot, mas o `emuelecRunEmu.sh` (de A e B) continua gravando `screen_brightness` a partir do `brightness.level` do `emuelec.conf` → o RetroArch pode ler outro número que o do `lcdbl`; fica anotado como limite conhecido (Non-Goal de D) e visto no aparelho na task 6.
- **O atalho de D usa o FN que a feature 20 remapeia:** o build único deve conter as duas features e `r36-fn-original` não pode estar na p1 do teste.
- **Inglês como padrão do build** muda o comportamento de quem roda `./build.sh` sem argumento → documentado no `README.md` (D4).
- **`emuelec.conf` de A não chega a uma p8 existente** (achado 2 da revisão de A): decisão do usuário, a gravação é `--all --keep-roms --wipe-storage`. A p1 com as ROMs nunca é apagada; a p8 nova recebe as chaves de fábrica. A não ganha passo de boot para o `emuelec.conf` (fora de escopo).
- **Agente fora do write-set** → para e relata; o diff é conferido (task 2.4).

## Migration Plan

Nada a migrar no repositório. Rollback: descartar a branch de integração e as quatro branches; a `main` nunca é tocada. Depois da validação no aparelho, o usuário decide o merge na `main` e o arquivamento (ordem: A, C, B, D, integração; A e C alteram a capability `retroarch-menu`/`retroarch-shaders` em specs delta distintos, então o `/opsx:sync` vai um por vez).

## Open Questions

- Onde o ES grava a troca de idioma (B task 1.1) só se descobre no aparelho; B entrega com a leitura em duas fontes (D2 de B) e o usuário confirma na task 6.
