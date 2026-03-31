---
name: continue-task
description: >-
  Take over an interrupted tracked task from a previous Codex or Claude
  session by resolving the existing task home from a tracker ref, task slug,
  status file, or zellij session, then syncing the status file to the current
  session and reading the status plus transcript tail before continuing.
---

# Continue Task

Use this when the current session needs to resume work that already has a
tracked task folder, especially after a provider failure, a dead session, or a
clean human handoff.

Prefer this over `start-new-task` when a matching tracked task already exists.
Prefer this over `save-task-status` when the current session first needs to
adopt a task that was last owned by another session.

## Invocation

```text
$continue-task <task slug|tracker ref|session name>
/continue-task <task slug|tracker ref|session name>
```

Lower-level overrides:

```text
$continue-task --task-dir <task-dir>
$continue-task --status-file <status-file>
$continue-task --zellij-session <session-name>
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

If the workflow expects the remote live-session block to move to this session,
repeat with `--sync-github-issue`.

## Process

1. Resolve the existing task home first. Target by tracker ref or task slug before using low-level overrides.
2. If resolution is ambiguous, stop and surface the candidates. Do not guess.
3. Read the resolved `status.md` first. Treat task metadata and the local status recap as the source of truth.
4. Use only a short transcript tail as fallback for the final pre-interruption context or when the status file is stale. Do not read the full transcript by default.
5. Adopt the task into the current session by running `sync_task_metadata.py` against the resolved status file. This should make later `get-task-details` and `save-task-status` calls point at the resumed task.
6. If the resolved task home lives in another repo, treat that workspace path as canonical before making code changes. Do not create a duplicate task folder unless the user explicitly wants a forked task history.
7. After adoption, update the status file with a brief takeover note, refreshed current state, and the next planned step.
8. If no tracked task home exists, fall back to `start-new-task` instead of fabricating resume context.

## Output Expectations

- Confirm the adopted task folder, status file, tracker URL, transcript path, and canonical workspace.
- Summarize the current state, the last meaningful progress, and the next unblock or decision.
- If the user only asked to get up to speed, stop after the brief. Otherwise continue the task normally from the adopted status file.

## Notes

- `cross-session-context` remains the read-only inspection tool. `continue-task` is for actual takeover.
- `save-task-status` remains the checkpoint tool once the current session owns the task.
- If the resolved task still points at a live foreign zellij session, treat that as diagnostic context unless the user explicitly asks for cross-session messaging.
