---
trigger: always_on
description: Diretrizes de execução de comandos para compatibilidade com modo auto e prevenção de pedidos de permissão
---

# Diretrizes para Modo Auto (Sem Pedidos de Permissão)

Para que o harness opere de forma fluida no modo auto sem acionar telas de confirmação de permissão:

1. **Formato de comandos simples e prefix-matchable**:
   - Cada chamada de shell deve conter apenas um comando direto (ex: `git status`, `ls openspec/changes`, `uv run python -I -m unittest discover -s tests`).
   - NUNCA use laços de repetição inline no shell (`for`, `while`, `until`).
   - NUNCA encadeie comandos com `&&`, `;`, `||` ou quebras de linha múltiplas.
   - NUNCA use substituições de comando (`$(...)` ou backticks) nem expansões de variáveis de shell (`$VAR`, `${VAR}`).
   - NUNCA use pipes complexos nem comandos com redirecionamentos compostos.

2. **Priorize ferramentas nativas do harness**:
   - Para leitura de arquivos: use `read_file`.
   - Para edição e escrita: use `edit_file` e `write_file`.
   - Evite invocar utilitários de shell como `cat`, `head`, `tail`, `grep`, `sed`, `awk` ou `echo >` para operações em arquivos quando ferramentas nativas puderem ser usadas. Ferramentas nativas rodam sem risco de bloqueio de permissão de terminal.

3. **Automação ou lógica com iterações**:
   - Quando for necessário iterar sobre arquivos, diretórios ou calcular métricas, utilize um script temporário em Python executado em chamada única (`uv run python -I script.py` ou fallback para `python3 -I script.py`).

4. **Operações proibidas**:
   - NUNCA use `sudo` em nenhuma hipótese.
   - NUNCA proponha operações destrutivas ou de gravação direta em partições (`dd *of=/dev/*`, `mkfs*`, etc.).
