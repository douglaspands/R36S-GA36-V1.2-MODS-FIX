---
trigger: always_on
description: Diretrizes de execução de comandos para compatibilidade com modo auto e prevenção de pedidos de permissão
---

# Diretrizes para Modo Auto (Sem Pedidos de Permissão)

O Antigravity opera em modo auto. Para que o harness execute comandos e tarefas de forma contínua e sem acionar telas de confirmação de permissão para leitura, gravação e operações não destrutivas:

1. **Formato de comandos simples e prefix-matchable**:
   - Cada chamada de shell deve conter apenas um comando direto (ex: `git status`, `git checkout -b <branch>`, `openspec status --change "<name>" --json`, `uv run python -I -m unittest discover -s tests`).
   - NUNCA use laços de repetição inline no shell (`for`, `while`, `until`).
   - NUNCA encadeie comandos com `&&`, `;`, `||` ou quebras de linha múltiplas.
   - NUNCA use substituições de comando (`$(...)` ou backticks) nem expansões de variáveis de shell (`$VAR`, `${VAR}`).
   - NUNCA use pipes complexos nem comandos com redirecionamentos compostos.
   - NUNCA execute código inline longo ou multilinha via `python -c "..."` (aspas compostas e quebras de linha disparam prompt de segurança). Salve em arquivo `.py` e execute com `uv run python -I caminho/script.py`.

2. **Priorize ferramentas nativas do harness (pré-aprovadas sem prompt)**:
   - Para leitura de arquivos: use SEMPRE `read_file`.
   - Para escrita e criação de arquivos: use SEMPRE `write_file`.
   - Para edição pontual: use SEMPRE `edit_file`.
   - NUNCA use utilitários de terminal (`cat`, `head`, `tail`, `grep`, `sed`, `awk`, `echo >`) para ler ou alterar arquivos, pois o harness trata ferramentas nativas com autorização automática enquanto chamadas de shell equivalentes acionam barreiras de confirmação.

3. **Escopo estrito ao Workspace**:
   - Comandos de shell e scripts devem atuar estritamente dentro da raiz do projeto (`/home/douglas/Workspace/r36s/...`).
   - NUNCA faça varreduras em diretórios do sistema ou home (`find /`, `find ~`, `find /usr`), nem tente ler configurações internas do harness como `~/.gemini/antigravity-cli/settings.json`, que acionam proteções de sandbox e prompts de permissão.
   - Se precisar baixar arquivos ou descompactar, faça via script Python limpo (`urllib.request`, `zipfile`) executado via `uv run python -I ...`, evitando chamadas de shell a `curl`, `wget`, `unzip`, `chmod`.

4. **Operações proibidas**:
   - NUNCA use `sudo` em nenhuma hipótese.
   - NUNCA proponha operações destrutivas ou de gravação direta em partições (`dd *of=/dev/*`, `mkfs*`, etc.).
