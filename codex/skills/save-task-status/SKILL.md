---
name: save-task-status
description: >-
  Save current task status, plan, or bug report to the project's task-tracking
  folder. Reconciles machine/zellij/issue metadata and optionally refreshes
  linked GitHub live-session block when context drifts.
source: personal
---

# Save Task Status

Update the current task status file and keep task metadata aligned with the active machine/session.

## Invocation

```text
/save-task-status [task-slug]
```

## Shared Helper

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<status-file>" \
  --sync-github-issue
```

## Process

### Step 1: Resolve Task Folder
1. Check `AGENTS.md` `task-status-root` override.
2. Fall back to `CLAUDE.md` override.
3. Default to `context/daily/YYYY-MM-DD/<task-slug>/`.
4. If the task is linked to a GitHub issue and the canonical issue-owning repo checkout is known, update that canonical task folder instead of a same-session duplicate in the current repo.
5. Update existing task folder when possible; do not create duplicates for resumed work.

### Step 2: Update Core Status Content
- Refresh `Last Updated` (PST format).
- Update `User Inputs`, `Input Artifacts`, `Current State`, `Progress`, `Artifacts`, and `Next Steps` as needed.
- Keep the `Input Artifacts` section focused on `user_inputs/input_artifacts/` paths and provenance notes.
- Keep the `Artifacts` section focused on curated top-level outputs first; reference `task-progress-artifacts/scratchpad/` items only when deeper evidence is useful.
- Preserve existing `## Accepted Plans` history.
- Keep `user_inputs/` immutable; add new Markdown notes or input-artifact captures instead of overwriting prior inputs.

### Step 3: Reconcile Metadata Block
Run:

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<abs-status-file-path>" \
  --sync-github-issue
```

What this does:
- Upserts managed `TASK-METADATA` block in status file.
- Updates the machine-local current-task pointer for this `{project, coding-agent, agent-session}` so later `get-task-details` resolves this task as current.
- Recomputes:
  - Machine (`SYSTEM_NAME` -> hostname -> `unknown`)
  - Coding agent (`codex|claude|unknown`)
  - Agent session ID (for example `CODEX_THREAD_ID` when available)
  - Zellij session (`ZELLIJ_SESSION_NAME` or `none`)
  - Zellij link (`ZELLIJ_WEB_ENABLE_LINKS` + `ZELLIJ_WEB_BASE_URL` + session)
  - Linked issue metadata
- If issue-linked and `gh` auth available, upserts top live-session issue block including the absolute task folder and status-file paths.

### Step 4: Degraded-Mode Handling
If dependencies are missing:
- Missing `gh` or auth failure: skip issue sync and continue.
- Missing zellij context: use `none` values.
- Missing `SYSTEM_NAME`: use hostname fallback.

### Step 5: Artifact Hygiene
- Save generated outputs continuously under `task-progress-artifacts/` and reference them in status.
- Put raw logs, command outputs, polling snapshots, JSON dumps, intermediate screenshots, and adhoc scripts in `task-progress-artifacts/scratchpad/`.
- Keep top-level `task-progress-artifacts/` reserved for curated deliverables and important evidence that should be easy to review later.
- Keep Markdown input notes under `user_inputs/`.
- Capture user-provided or user-referenced files, images, and downloaded reference copies in `user_inputs/input_artifacts/`.
- Maintain `user_inputs/input_artifacts/index.md` when an input artifact is captured or when an external input artifact cannot be copied locally.
- In status summaries, prefer local `user_inputs/input_artifacts/...` references for input context and top-level `task-progress-artifacts/...` references for generated outputs.

## Current-Task Semantics
- `save-task-status` is also a task switch for the current session.
- If one agent session touches multiple tasks over time, the most recently synced task becomes the session's current task.

## Managed Metadata Block

```markdown
<!-- TASK-METADATA:START -->
## Task Metadata
- Machine: <SYSTEM_NAME|hostname|unknown>
- Coding Agent: <codex|claude|unknown>
- Agent Session ID: <id|none>
- GitHub Issue: <url|none>
- GitHub Repo: <owner/repo|none>
- GitHub Issue Number: <number|none>
- Zellij Session: <name|none>
- Zellij Link: <url|none>
- Last Synced: YYYY-MM-DD ~HH:MMam/pm PST
<!-- TASK-METADATA:END -->
```

## Managed GitHub Block

```markdown
<!-- LIVE-SESSION:START -->
## Live Session

_Written by Codex via the developer's authenticated GitHub account._

- Machine: `machine-name`
- Coding Agent: `codex|claude|unknown`
- Agent Session ID: `id|none`
- Transcript Path: `/abs/path/to/transcript`|`none`
- Zellij Session: `session|none`
- Zellij Link: https://...|none
- Task Folder: `/abs/path/to/task-folder`|`none`
- Status File: `/abs/path/to/status.md`|`none`
- Attach Command: `zellij attach ...|none`
- Last Updated: `YYYY-MM-DD ~HH:MMam/pm PST`
<!-- LIVE-SESSION:END -->
```
