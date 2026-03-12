#!/usr/bin/env bash
# Validate get-task-details session-aware selection against real personal_os tasks and a synthetic duplicate-session fixture.
# Inputs: botfiles root at ~/pro/botfiles, personal_os root at ~/pro/personal_os, current shell env with CODEX_THREAD_ID/ZELLIJ_SESSION_NAME when available.
# Outputs: Prints syntax, parity, default lookup, explicit slug lookup, no-match behavior, AGENT_SESSION_ID compatibility, and ambiguity handling results.

set -euo pipefail

BOTFILES_ROOT="${BOTFILES_ROOT:-$HOME/pro/botfiles}"
PROJECT_ROOT="${PROJECT_ROOT:-$HOME/pro/personal_os}"
CODEX_GET="$BOTFILES_ROOT/codex/skills/_shared/task_status/scripts/get_task_details.py"
CLAUDE_GET="$BOTFILES_ROOT/claude/skills/_shared/task_status/scripts/get_task_details.py"
CODEX_COMMON="$BOTFILES_ROOT/codex/skills/_shared/task_status/scripts/task_status_common.py"
CLAUDE_COMMON="$BOTFILES_ROOT/claude/skills/_shared/task_status/scripts/task_status_common.py"
CURRENT_SESSION_ID="${CODEX_THREAD_ID:-${AGENT_SESSION_ID:-}}"

printf '== syntax ==\n'
python3 -m py_compile "$CODEX_GET" "$CLAUDE_GET" "$CODEX_COMMON" "$CLAUDE_COMMON"

printf '\n== codex/claude parity ==\n'
diff -u "$CODEX_GET" "$CLAUDE_GET" >/dev/null
diff -u "$CODEX_COMMON" "$CLAUDE_COMMON" >/dev/null
printf 'shared helper copies are in sync\n'

printf '\n== default current-session lookup ==\n'
python3 "$CODEX_GET" --project-root "$PROJECT_ROOT"

printf '\n== explicit slug: issue-16 ==\n'
python3 "$CODEX_GET" --project-root "$PROJECT_ROOT" --task-slug issue-16

printf '\n== explicit slug: personal-os-issue ==\n'
python3 "$CODEX_GET" --project-root "$PROJECT_ROOT" --task-slug personal-os-issue

printf '\n== fail-closed no-match ==\n'
env CODEX_THREAD_ID=does-not-exist AGENT_SESSION_ID=does-not-exist \
    python3 "$CODEX_GET" --project-root "$PROJECT_ROOT"

if [[ -n "$CURRENT_SESSION_ID" ]]; then
    printf '\n== AGENT_SESSION_ID-only compatibility ==\n'
    env -u CODEX_THREAD_ID AGENT_SESSION_ID="$CURRENT_SESSION_ID" \
        python3 "$CODEX_GET" --project-root "$PROJECT_ROOT" --task-slug issue-16
fi

printf '\n== ambiguity handling fixture ==\n'
tmp_root="$(mktemp -d)"
trap 'rm -rf "$tmp_root"' EXIT
task_root="$tmp_root/context/daily/2026-03-11"
mkdir -p \
    "$task_root/14h00m00sPST-dup-a" \
    "$task_root/14h00m01sPST-dup-b"

cat >"$task_root/14h00m00sPST-dup-a/status.md" <<'EOF_A'
# Duplicate A

<!-- TASK-METADATA:START -->
## Task Metadata
- Machine: Sourya-Macbook
- Coding Agent: codex
- Agent Session ID: duplicate-session-id
- GitHub Issue: none
- GitHub Repo: none
- GitHub Issue Number: none
- Zellij Session: personal-os
- Zellij Link: none
- Last Synced: 2026-03-11 ~03:00pm PST
<!-- TASK-METADATA:END -->
EOF_A

cat >"$task_root/14h00m01sPST-dup-b/status.md" <<'EOF_B'
# Duplicate B

<!-- TASK-METADATA:START -->
## Task Metadata
- Machine: Sourya-Macbook
- Coding Agent: codex
- Agent Session ID: duplicate-session-id
- GitHub Issue: none
- GitHub Repo: none
- GitHub Issue Number: none
- Zellij Session: personal-os
- Zellij Link: none
- Last Synced: 2026-03-11 ~03:00pm PST
<!-- TASK-METADATA:END -->
EOF_B

env CODEX_THREAD_ID=duplicate-session-id AGENT_SESSION_ID=duplicate-session-id \
    python3 "$CODEX_GET" --project-root "$tmp_root"
