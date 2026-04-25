---
name: get-task-details
description: >-
  Print rich task details for the current Hermes task context: status file path,
  primary tracker URL, machine name, session id, transcript path, zellij
  session/link, and a short task recap.
---

# Get Task Details

Resolve task status path and metadata in one read-only command.

## Invocation

```text
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

## Output Contract

Default call with no `task-slug`:
- resolves the current task for this session
- checks the machine-local current-task pointer first
- if the pointer is missing or stale, falls back to the latest same-session task in the current project
- prints a clear no-match message instead of guessing from unrelated recent folders

Primary task output should include:
- Task folder
- Status file path
- Primary tracker kind
- Full primary tracker URL
- Tracker human ID
- Tracker title
- GitHub compatibility URL when present
- Machine
- Coding agent/session information
- Transcript path
- Zellij session
- Zellij link
- Recap block covering:
  - what the task is about
  - current status
  - next steps / whether user input is needed

If no task is found for the current session, print a clear message and suggest creating or adopting a tracked task.

## Notes

- Read-only: this skill never edits files.
- If recent context already includes an exact task folder or `status.md` path, pass it directly.
- Preserve the full primary tracker URL in the output.
- The full shared contract lives in `~/pro/botfiles/docs/task-status-tracker-contract.md`.
- Default mode is current-task-for-this-session; use `task-slug` only when you intentionally want cross-session lookup.
- Hermes-specific fallback: if env session IDs are missing but the session title is known, set `HERMES_SESSION_TITLE` or `SESSION_TITLE` before invoking `get_task_details.py`. The shared helper can then resolve the real Hermes session ID from `~/.hermes/state.db`, which mirrors the session identity a human can inspect via `/title`.
- If a tracked task was previously synced under a placeholder/manual session ID, re-run `sync_task_metadata.py` with the real Hermes session ID so current-task pointer lookup and `get-task-details` align for future calls.
