#!/usr/bin/env zsh
set -euo pipefail

if [[ -f "$HOME/.zshrc" ]]; then
  source "$HOME/.zshrc" >/dev/null 2>&1 || true
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY is not available after sourcing ~/.zshrc" >&2
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is not available" >&2
  exit 2
fi

exec "$@"
