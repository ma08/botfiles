---
name: start-new-task
description: >-
  Initialize a new task folder with status.md, user_inputs/initial.md,
  user_inputs/input_artifacts/, task-progress-artifacts/, and
  task-progress-artifacts/scratchpad/. Supports GitHub issue URL inputs,
  issue-informed slugs (`repo-issue-number-title`), and machine/zellij
  metadata capture with optional live-session issue block sync.
---

# Start New Task

Create a task folder and capture durable metadata for machine, session, and GitHub linkage.

## Invocation

```text
$start-new-task <description>
/start-new-task <description>
```

If no description is provided, ask for one.

## Shared Helpers

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/resolve_task_context.py \
  --project-root "<project-root>" \
  --description "<text>"
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/sync_task_metadata.py --status-file "<status-file>" --sync-github-issue
```

## Process

### Step 1: Determine Task Status Root
1. Check project `AGENTS.md` for `task-status-root:`.
2. If missing, check project `CLAUDE.md`.
3. Default to `context/daily/`.
4. Resolve date as `YYYY-MM-DD`.

### Step 2: Resolve Context Before Slugging
Run:

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/resolve_task_context.py \
  --project-root "<project-root>" \
  --description "<user description>" \
  --max-slug-length 60
```

Use output fields:
- `Task Slug`
- `GitHub Issue` (if detected)
- `Canonical Project Root`
- `Canonical Task Status Root`
- `Machine`
- `Coding Agent`
- `Agent Session ID`
- `Zellij Session`
- `Zellij Link`

### Step 3: Slug and Folder Naming
- If a GitHub issue URL exists, slug format is `repo-issue-<number>-<title>`.
- If `Canonical Project Root` / `Canonical Task Status Root` are emitted for an issue-linked task, create or resume the task there instead of the current repo.
- Enforce max slug length `60`; truncation appends a stable hash suffix.
- Folder format remains `<HH>h<MM>m<SS>sPST-<slug>`.

### Step 4: Existing Task Check
Search for an existing task folder with the same slug:
- If found, ask resume vs create-new.
- For issue-linked work, search the canonical issue-owning repo task root first.
- If resume, hand off to `$save-task-status`.

### Step 5: Create Folder Structure

```text
<HH>h<MM>m<SS>sPST-<slug>/
├── status.md
├── user_inputs/
│   ├── initial.md
│   └── input_artifacts/
└── task-progress-artifacts/
    └── scratchpad/
```

### Step 6: Populate `status.md` and `user_inputs/initial.md`
- Capture the original description verbatim in `user_inputs/initial.md`.
- Keep additional Markdown input notes directly under `user_inputs/`.
- Reserve `user_inputs/input_artifacts/` for user-provided or user-referenced files, images, and local copies of input artifacts.
- Create `user_inputs/input_artifacts/index.md` once the task has a captured input artifact or an external artifact reference that needs provenance without a local copy.
- Include relevant links.
- Keep timestamps in PST (`TZ=America/Los_Angeles date`).
- Treat top-level `task-progress-artifacts/` as the curated deliverables area and `task-progress-artifacts/scratchpad/` as the default destination for raw/intermediate files.

### Step 7: Upsert Task Metadata + Optional Issue Live Block
After creating `status.md`, run:

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<abs-status-file-path>" \
  --github-issue-url "<issue-url-if-any>" \
  --sync-github-issue
```

Behavior:
- Always upserts managed task metadata in status file.
- Sets this task as the current task for the active `{project, coding-agent, agent-session}` context.
- If issue-linked and GitHub CLI auth is available, upserts managed live-session block at top of issue body.
- If dependencies are missing (`gh`, auth, zellij env), core task creation still succeeds.

### Step 8: Confirm and Continue
Ask the user to confirm scope; proceed if they say to continue.

## Current-Task Semantics
- Starting a new task automatically switches the current task for this session.
- This supports reusing one agent session across multiple tasks while keeping `get-task-details` semantically correct.

## Managed Metadata Contract

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

## Degraded Mode Rules
- No `SYSTEM_NAME`: fallback to hostname, then `unknown`.
- No zellij session: `Zellij Session: none`, `Zellij Link: none`.
- No GitHub CLI/auth: skip issue-body update, keep local metadata.
- No GitHub issue URL: local workflow only.
