#!/usr/bin/env bash
set -euo pipefail

# Load shared cross-machine environment (BOTFILES_ROOT, UV_BIN, provider envs).
# shellcheck disable=SC1091
. "$HOME/pro/botfiles/.botrc"

: "${UV_BIN:?UV_BIN is not set. Check shell/10-uv-bin.sh.}"
: "${BOTFILES_ROOT:?BOTFILES_ROOT is not set after sourcing .botrc.}"

exec "$UV_BIN" run \
  --project "$BOTFILES_ROOT/claude/hooks" \
  python "$BOTFILES_ROOT/codex/hooks/codex_notification.py" \
  "${1:-}"
