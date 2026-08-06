---
name: get-task-details
description: >-
  Print rich task details for the current task context: status file path,
  primary tracker URL, machine name, coding agent/session id, transcript
  path, zellij session, zellij link, and a short task recap. Replaces the
  old get-task-status-file interface. Use reorient-myself instead when the
  user wants a first-principles audit of whether the task is on the right track.
---

# Get Task Details

Resolve task status path and metadata in one read-only command.

## Scope Boundary

Use this skill for factual operational orientation: which task is active, where its durable context lives, and what its recorded state says. Do not turn the three-line recap into a strategic audit.

When the user asks whether the task is pursuing the right objective, wants blind spots challenged, or needs a paste-ready recovery prompt, use `reorient-myself` instead. That skill may use this output as evidence.

## Invocation

```text
$get-task-details [task-slug]
/get-task-details [task-slug]
```

## Command

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/get_task_details.py \
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
  - Primary tracker kind
  - Full primary tracker URL
  - Tracker human ID
  - Tracker title
  - GitHub compatibility URL when present
  - Machine
  - Coding agent
  - Agent session ID
  - Transcript path
  - Zellij session
  - Zellij link
  - Recap block with three bullets:
    - what this task is about
    - current status
    - next steps / whether the user needs to do anything
  - When the status file lacks one of those recap fields, or its `Last Updated`
    value is over 14 days old, performs a bounded read-only runtime investigation:
    the first linked GitHub PR, then the primary GitHub/Linear tracker, then a
    matching local Git checkout. Runtime-derived recap lines are labeled
    `Runtime investigation`.
- Direct `--status-file` / `--task-dir` targeting prints the same primary-task recap
- Optional Related tasks (same slug pattern) only when `task-slug` is used
- Optional Stale tasks (>7 days old) only when `task-slug` is used

If no task is found for the current session, print a clear message and suggest `save-task-status` or `start-new-task`.

## Notes
- Read-only: this skill never edits files.
- If recent conversation already includes an exact task folder path or `status.md` path, pass it directly with `--task-dir` or `--status-file` instead of relying on repo/session inference.
- Preserve the full primary tracker URL in the output; do not collapse it to shorthand.
- The full tracker-aware contract lives in [`docs/task-status-tracker-contract.md`](../../../docs/task-status-tracker-contract.md).
- Default mode is current-task-for-this-session; use `task-slug` when you intentionally want cross-session lookup.
- Multiple tasks in one agent session are supported: the current task is whichever task was most recently touched by `start-new-task` or `save-task-status` in this session.
- Legacy or unsynced task folders without a managed `Task Metadata` block cannot be auto-resolved as the current session task.
- The static recap recognizes both header fields such as `- Status:` and
  `**Status**:`, then prefers the newest `## Current State` items when no
  explicit status exists. Runtime investigation is a fallback, never a write.
- Task status root resolution order:
  1. `AGENTS.md` `task-status-root`
  2. `CLAUDE.md` `task-status-root`
  3. default `context/daily/`
