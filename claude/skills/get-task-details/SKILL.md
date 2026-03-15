---
name: get-task-details
description: >-
  Print rich task details for the current task context: status file path,
  full GitHub issue URL, machine name, coding agent/session id, zellij
  session, zellij link, and a short task recap. Replaces the old
  get-task-status-file interface.
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
  --status-file "<optional-explicit-status-file>" \
  --task-dir "<optional-explicit-task-dir>" \
  --project-root "<project-root>" \
  --task-slug "<optional-slug>"
```

## Output Contract (Human-Readable)
- Default call (no `task-slug`):
  - resolves the current task for this session
  - checks the machine-local current-task pointer first
  - if the pointer is missing or stale, falls back to the latest same-session task in the current project
  - prints a clear no-match message instead of guessing from unrelated recent folders
- Primary task:
  - Task folder
  - Status file path
  - Full GitHub issue URL
  - Machine
  - Coding agent
  - Agent session ID
  - Zellij session
  - Zellij link
  - Recap block with three bullets:
    - what this task is about
    - current status
    - next steps / whether the user needs to do anything
- Direct `--status-file` / `--task-dir` targeting prints the same primary-task recap
- Optional Related tasks (same slug pattern) only when `task-slug` is used
- Optional Stale tasks (>7 days old) only when `task-slug` is used

If no task is found for the current session, print a clear message and suggest `save-task-status` or `start-new-task`.

## Notes
- Read-only: this skill never edits files.
- If recent conversation already includes an exact task folder path or `status.md` path, pass it directly with `--task-dir` or `--status-file` instead of relying on repo/session inference.
- Preserve the full GitHub issue URL in the output; do not collapse it to `owner/repo#number` shorthand.
- Default mode is current-task-for-this-session; use `task-slug` when you intentionally want cross-session lookup.
- Multiple tasks in one agent session are supported: the current task is whichever task was most recently touched by `start-new-task` or `save-task-status` in this session.
- Legacy or unsynced task folders without a managed `Task Metadata` block cannot be auto-resolved as the current session task.
- The recap is best-effort and is derived from common status-file sections such as `**Goal**`, `**Status**`, `## Current State`, and `## Next Steps`.
- Task status root resolution order:
  1. `CLAUDE.md` `task-status-root`
  2. `AGENTS.md` `task-status-root`
  3. default `context/daily/`
