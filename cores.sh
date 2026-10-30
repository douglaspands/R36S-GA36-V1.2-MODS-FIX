#!/usr/bin/env bash
# Compila cores libretro para o A33 a partir de cores/<core>/receita.toml. Veja ./cores.sh --help.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# uv fornece o Python do projeto; fallback para python3 se uv não estiver acessível.
if command -v uv >/dev/null 2>&1 && uv --version >/dev/null 2>&1; then
    exec uv run --project "$here" --frozen --quiet python -I -c 'import sys; sys.path.insert(0, sys.argv.pop(1)); from r36img.cores import main; sys.exit(main(sys.argv[1:]))' "$here/tools" "$@"
else
    exec python3 -I -c 'import sys; sys.path.insert(0, sys.argv.pop(1)); from r36img.cores import main; sys.exit(main(sys.argv[1:]))' "$here/tools" "$@"
fi
