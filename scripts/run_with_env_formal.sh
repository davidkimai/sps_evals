#!/usr/bin/env zsh
set -euo pipefail
ROOT="/Users/jasontang/sps-track3-package"
source ~/.zshrc >/dev/null 2>&1
source "$HOME/.elan/env" >/dev/null 2>&1 || true
export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"
cd "$ROOT"
exec python3 "$ROOT/scripts/run_vericoding_formal_eval_v1.py" "$@"
