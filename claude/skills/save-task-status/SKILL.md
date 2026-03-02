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
python ~/pro/botfiles/claude/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<status-file>" \
  --sync-github-issue
```

## Process

### Step 1: Resolve Task Folder
1. Check `CLAUDE.md` `task-status-root` override.
2. Fall back to `AGENTS.md` override.
3. Default to `context/daily/YYYY-MM-DD/<task-slug>/`.
4. Update existing task folder when possible; do not create duplicates for resumed work.

### Step 2: Update Core Status Content
- Refresh `Last Updated` (PST format).
- Update `Current State`, `Progress`, `Artifacts`, `Next Steps`.
- Preserve existing `## Accepted Plans` history.
- Keep `user_inputs/` immutable.

### Step 3: Reconcile Metadata Block
Run:

```bash
python ~/pro/botfiles/claude/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<abs-status-file-path>" \
  --sync-github-issue
```

What this does:
- Upserts managed `TASK-METADATA` block in status file.
- Recomputes:
  - Machine (`SYSTEM_NAME` -> hostname -> `unknown`)
  - Coding agent (`codex|claude|unknown`)
  - Agent session ID (for example `CODEX_THREAD_ID` when available)
  - Zellij session (`ZELLIJ_SESSION_NAME` or `none`)
  - Zellij link (`ZELLIJ_WEB_ENABLE_LINKS` + `ZELLIJ_WEB_BASE_URL` + session)
  - Linked issue metadata
- If issue-linked and `gh` auth available, upserts top live-session issue block.

### Step 4: Degraded-Mode Handling
If dependencies are missing:
- Missing `gh` or auth failure: skip issue sync and continue.
- Missing zellij context: use `none` values.
- Missing `SYSTEM_NAME`: use hostname fallback.

### Step 5: Artifact Hygiene
Save generated outputs continuously to `task-progress-artifacts/` and reference them in status.

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
- Machine: `machine-name`
- Coding Agent: `codex|claude|unknown`
- Agent Session ID: `id|none`
- Zellij Session: `session|none`
- Zellij Link: https://...|none
- Attach Command: `zellij attach ...|none`
- Last Updated: `YYYY-MM-DD ~HH:MMam/pm PST`
<!-- LIVE-SESSION:END -->
```
