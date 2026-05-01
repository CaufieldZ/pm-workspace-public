#!/usr/bin/env bash
# call-opencode.sh — thin wrapper around scripts/opencode-client.
# Builds on first call, reuses cached binary after.
#
# Prereqs:
#   1. Go 1.22+ installed (`brew install go` if missing)
#   2. opencode running locally: `opencode serve` (default :4096)
#
# Usage:
#   scripts/call-opencode.sh list
#   scripts/call-opencode.sh prompt "帮我看下这个 PR"
#   scripts/call-opencode.sh prompt -s sesXXX "继续"
#
# Env passthrough: OPENCODE_BASE_URL / OPENCODE_MODEL / OPENCODE_PROVIDER

set -euo pipefail

# Auto-load API key from user-scoped env file (chmod 600, outside repo).
if [[ -f "$HOME/.config/opencode/env" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/.config/opencode/env"
fi

ROOT="$(cd "$(dirname "$0")/opencode-client" && pwd)"
BIN="$ROOT/opencode-client"
SRC="$ROOT/main.go"

if ! command -v go >/dev/null 2>&1; then
  echo "error: go not installed. brew install go" >&2
  exit 127
fi

if [[ ! -x "$BIN" ]] || [[ "$SRC" -nt "$BIN" ]]; then
  echo "building opencode-client..." >&2
  (cd "$ROOT" && go mod tidy && go build -o opencode-client .)
fi

exec "$BIN" "$@"
