#!/usr/bin/env bash
set -euo pipefail

# Resolve botfiles root from this script's canonical location so it works
# regardless of where botfiles is cloned.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
BOTFILES_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"

# Force a fresh core-env load so notification flags and UV_BIN stay current.
unset _BOTENV_LOADED
if [ -f "$BOTFILES_ROOT/.botenv" ]; then
    # shellcheck disable=SC1091
    . "$BOTFILES_ROOT/.botenv"
fi

UV_CMD="${UV_BIN:-$(command -v uv || true)}"
HOOK_SCRIPT="$SCRIPT_DIR/antigravity_notification.py"

if [ -n "$UV_CMD" ] && [ -d "$BOTFILES_ROOT/claude/hooks" ]; then
    exec "$UV_CMD" run --quiet \
        --project "$BOTFILES_ROOT/claude/hooks" \
        python "$HOOK_SCRIPT" "$@"
fi

# Fallback: avoid breaking Antigravity's hook JSON contract if uv is unavailable.
if command -v python3 >/dev/null 2>&1; then
    exec python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
event = data.get("hookEventName", "") if isinstance(data, dict) else ""
print(json.dumps({"decision": "allow"} if event == "PreToolUse" else {}))
'
fi

printf '{}\n'
