---
name: continue-task
description: >-
  Resume an interrupted tracked task in Hermes by resolving the existing task
  home from a task slug, tracker ref, session name, task dir, or status file,
  then syncing task metadata to the current session before continuing.
---

# Continue Task

Use this when the current Hermes session needs to take over work that already
has a tracked task folder and status file.

Prefer this over starting a new task when a matching tracked task already
exists.

## Invocation

```text
/continue-task <task slug|tracker ref|session name>
```

Lower-level overrides:

```text
/continue-task --task-dir <task-dir>
/continue-task --status-file <status-file>
/continue-task --zellij-session <session-name>
```

## Commands

Resolve and inspect the task home first:

```bash
get-cross-session-context --project-root "<project-root>" <target> --include-transcript-tail 6
```

Explicit overrides when needed:

```bash
get-cross-session-context --project-root "<project-root>" --task-dir "<task-dir>" --include-transcript-tail 6
get-cross-session-context --project-root "<project-root>" --status-file "<status-file>" --include-transcript-tail 6
get-cross-session-context --project-root "<project-root>" --zellij-session "<session-name>" --include-transcript-tail 6
```

Adopt the resolved task into the current session:

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<resolved-status-file>" \
  --tracker-url "<resolved-tracker-url-if-any>" \
  --github-issue-url "<resolved-github-issue-if-any>"
```

## Process

1. Resolve the existing task home first.
2. If resolution is ambiguous, stop and surface the candidates. Do not guess.
3. Read the resolved `status.md` first. Treat task metadata and local status recap as the source of truth.
4. Use only a short transcript tail as fallback for final pre-interruption context.
5. Adopt the task into the current session by running `sync_task_metadata.py` against the resolved status file.
6. If the task home lives in another repo, treat that workspace as canonical before making code changes.
7. After adoption, update the status file with a short takeover note, refreshed current state, and next step.
8. If no tracked task home exists, stop and suggest creating one instead of fabricating resume context.

## Output Expectations

- Confirm the adopted task folder, status file, tracker URL, transcript path, and canonical workspace.
- Summarize the current state, last meaningful progress, and next unblock or decision.
- If the user only asked to get up to speed, stop after the brief. Otherwise continue from the adopted status file.

## Notes

- `cross-session-context` is the read-only inspection tool. `continue-task` is for actual takeover.
- `get-task-details` is the read-only recap tool once the current session owns the task.
- If the resolved task still points at a live foreign zellij session, treat that as diagnostic context unless the user explicitly wants cross-session messaging.
