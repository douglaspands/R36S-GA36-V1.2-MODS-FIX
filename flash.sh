#!/usr/bin/env bash
# Grava um build no cartão SD (inteiro ou por partição). Veja ./flash.sh --help.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# uv fornece o Python do projeto; -I o isola do ambiente e o pacote vem de tools/.
exec uv run --project "$here" --frozen --quiet python -I -c 'import sys; sys.path.insert(0, sys.argv.pop(1)); from r36img.flash import main; sys.exit(main(sys.argv[1:]))' "$here/tools" "$@"
