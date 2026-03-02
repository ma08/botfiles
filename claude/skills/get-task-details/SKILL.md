---
name: get-task-details
description: >-
  Print rich task details for the current task context: status file path,
  linked GitHub issue, machine name, coding agent/session id, zellij session,
  and zellij link. Replaces the old get-task-status-file interface.
---

# Get Task Details

Resolve task status path and metadata in one read-only command.

## Invocation

```text
/get-task-details [task-slug]
```

## Command

```bash
python ~/pro/botfiles/claude/skills/_shared/task_status/scripts/get_task_details.py \
  --project-root "<project-root>" \
  --task-slug "<optional-slug>"
```

## Output Contract (Human-Readable)
- Primary task:
  - Task folder
  - Status file path
  - GitHub issue
  - Machine
  - Coding agent
  - Agent session ID
  - Zellij session
  - Zellij link
- Optional Related tasks (same slug pattern)
- Optional Stale tasks (>7 days old)

If no task is found, print a clear message and suggest `/start-new-task`.

## Notes
- Read-only: this skill never edits files.
- Task status root resolution order:
  1. `CLAUDE.md` `task-status-root`
  2. `AGENTS.md` `task-status-root`
  3. default `context/daily/`
