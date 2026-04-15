---
name: save-status
description: >-
  Save current task status, plan, or investigation notes to the project's
  task-tracking folder. Reconciles machine/zellij/tracker metadata and
  refreshes the current-task pointer for the active session.
---

# Save Status

Update the current task status file and keep task metadata aligned with the active machine/session.

## Invocation

```text
/save-status [task-slug]
```

## Shared Helper

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<status-file>" \
  --tracker-url "<tracker-url-if-any>" \
  --github-issue-url "<github-issue-url-if-any>" \
  --sync-github-issue
```

## Process

### Step 1: Resolve task folder
1. Check `AGENTS.md` `task-status-root` override.
2. Fall back to `CLAUDE.md` override.
3. Default to `context/daily/YYYY-MM-DD/<task-slug>/`.
4. If the task is tracker-linked and a canonical task root is already known, update that canonical task folder instead of creating a same-session duplicate.
5. Update the existing task folder when possible; do not create duplicates for resumed work.

### Step 2: Update core status content
- Refresh `Last Updated` in PST format.
- Update `User Inputs`, `Input Artifacts`, `Current State`, `Progress`, `Artifacts`, and `Next Steps` as needed.
- Keep the `Input Artifacts` section focused on `user_inputs/input_artifacts/` paths and provenance notes.
- Keep the `Artifacts` section focused on curated top-level outputs first; reference `task-progress-artifacts/scratchpad/` items only when deeper evidence is useful.
- Preserve existing accepted-plan history.
- Keep `user_inputs/` append-only; add new notes or captured artifacts instead of overwriting prior inputs.

### Step 3: Reconcile metadata block
Run:

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<abs-status-file-path>" \
  --tracker-url "<tracker-url-if-any>" \
  --github-issue-url "<github-issue-url-if-any>" \
  --sync-github-issue
```

What this does:
- Upserts the managed tracker-aware `TASK-METADATA` block in the status file.
- Updates the machine-local current-task pointer for this `{project, coding-agent, agent-session}` so later `get-task-details` resolves this task as current.
- Recomputes primary tracker metadata, machine, coding agent/session, task paths, workspace path, zellij session/link, and compatibility fields.
- If tracker sync is enabled and dependencies exist, refreshes the live-session compatibility block on the primary tracker.

### Step 4: Degraded-mode handling
If dependencies are missing:
- Missing `gh` or auth failure: skip tracker sync and continue.
- Missing zellij context: use `none` values.
- Missing `SYSTEM_NAME`: use hostname fallback.

### Step 5: Artifact hygiene
- Save generated outputs continuously under `task-progress-artifacts/` and reference them in status.
- Put raw logs, command outputs, polling snapshots, JSON dumps, intermediate screenshots, and adhoc scripts in `task-progress-artifacts/scratchpad/`.
- Keep top-level `task-progress-artifacts/` reserved for curated deliverables and important evidence that should be easy to review later.
- Keep Markdown input notes under `user_inputs/`.
- Capture user-provided or user-referenced files, images, and downloaded reference copies in `user_inputs/input_artifacts/`.
- Maintain `user_inputs/input_artifacts/index.md` when an input artifact is captured or when an external input artifact cannot be copied locally.
- In status summaries, prefer local `user_inputs/input_artifacts/...` references for input context and top-level `task-progress-artifacts/...` references for generated outputs.

## Current-task semantics
- `save-status` is also a task switch for the current session.
- If one agent session touches multiple tasks over time, the most recently synced task becomes the session's current task.

## Notes
- The full tracker-aware contract lives in `~/pro/botfiles/docs/task-status-tracker-contract.md`.
- This is the checkpoint tool once the current session already owns the task.
