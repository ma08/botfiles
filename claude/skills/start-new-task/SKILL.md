---
name: start-new-task
description: >-
  Initialize a new task folder with status.md, user_inputs/initial.md,
  user_inputs/input_artifacts/, task-progress-artifacts/, and
  task-progress-artifacts/scratchpad/. Supports GitHub issue URL inputs,
  Linear issue URL inputs, default Linear issue creation for trackerless
  starts, tracker-informed slugs, and machine/zellij metadata capture with
  optional live-session issue block sync.
---

# Start New Task

Create a task folder and capture durable metadata for machine, session, and tracker linkage.

## Invocation

```text
/start-new-task <description>
```

## Shared Helpers

```bash
python ~/pro/botfiles/claude/skills/_shared/task_status/scripts/resolve_task_context.py \
  --project-root "<project-root>" \
  --description "<text>"
python ~/pro/botfiles/claude/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<status-file>" \
  --tracker-url "<tracker-url-if-any>" \
  --github-issue-url "<github-issue-url-if-any>" \
  --sync-github-issue
```

## Process

### Step 1: Determine Task Status Root
1. Check project `CLAUDE.md` for `task-status-root:`.
2. If missing, check project `AGENTS.md`.
3. Default to `context/daily/`.
4. Resolve date as `YYYY-MM-DD`.

### Step 2: Resolve Context Before Slugging
Run:

```bash
python ~/pro/botfiles/claude/skills/_shared/task_status/scripts/resolve_task_context.py \
  --project-root "<project-root>" \
  --description "<user description>" \
  --max-slug-length 60
```

Use output fields:
- `Task Slug`
- `Tracker Kind`
- `Tracker URL`
- `Tracker Human ID`
- `Tracker Title`
- `GitHub Issue` (compatibility, when detected)
- `Canonical Project Root`
- `Canonical Task Status Root`
- `Machine`
- `Coding Agent`
- `Agent Session ID`
- `Zellij Session`
- `Zellij Link`

### Step 2A: Create Linear Tracker For Trackerless Starts
If `Tracker Kind` is `none`, create a new Linear ticket before slugging unless the user explicitly asked for local-only/no-tracker work or named a different tracker.

1. Use the Linear skill / Linear MCP tools to create the issue.
2. Infer the most appropriate team/project/labels from local context when obvious; otherwise default to the normal personal workflow team and keep project unset.
3. Include the user's original description, concise goal, likely scope, and acceptance criteria in the Linear issue.
4. Assign to the user when that is the established workspace convention.
5. After creation, rerun `resolve_task_context.py` with the new Linear issue URL and use the resulting tracker-aware fields for all later steps.
6. If Linear tooling/auth is unavailable, continue in degraded local-only mode, record why no tracker was created in `status.md`, and tell the user.

Skip this step only when:
- the original description already contains a GitHub or Linear tracker,
- the user explicitly says not to create a tracker,
- the user explicitly asks for a different tracking destination,
- or Linear creation is blocked and degraded local-only mode is the only viable path.

### Step 3: Slug and Folder Naming
- If the primary tracker is GitHub, slug format is `repo-issue-<number>-<title>`.
- If the primary tracker is Linear, slug format is `<linear-id>-<title>`.
- If `Canonical Project Root` / `Canonical Task Status Root` are emitted for a tracker-linked task, create or resume the task there instead of the current repo.
- Enforce max slug length `60`; truncation appends a stable hash suffix.
- Folder format remains `<HH>h<MM>m<SS>sPST-<slug>`.

### Step 4: Existing Task Check
Search for an existing task folder with the same slug:
- If found, ask resume vs create-new.
- For tracker-linked work, search the canonical task root first when one is emitted by `resolve_task_context.py`.
- If resume, hand off to `/continue-task` unless the current session already owns the task and only needs a checkpoint-style refresh.

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
python ~/pro/botfiles/claude/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<abs-status-file-path>" \
  --tracker-url "<tracker-url-if-any>" \
  --github-issue-url "<issue-url-if-any>" \
  --sync-github-issue
```

Behavior:
- Always upserts managed tracker-aware task metadata in the status file.
- Sets this task as the current task for the active `{project, coding-agent, agent-session}` context.
- If `--sync-github-issue` is set, upserts the managed live-session block on the primary tracker.
- For GitHub trackers, this targets the issue body and requires GitHub CLI auth.
- For Linear trackers, this targets the issue description and requires `LINEAR_API_KEY`.
- If dependencies are missing (`gh`, auth, zellij env), core task creation still succeeds.

### Step 8: Gather Planning Context Immediately
Do not stop after scaffolding unless you are blocked on task targeting or an unresolved resume-vs-new choice.

After `status.md` exists and task metadata is synced:
- Read the primary tracker when one exists.
- For Linear tasks, inspect related issues (`blocks`, `blockedBy`, `relatedTo`, duplicates) when they are likely to affect planning.
- Search the most relevant local context roots before asking the user for more information:
  - the canonical task-status root and nearby `context/` history for the resolved tracker/slug
  - the invoking project root when it differs from the canonical root
  - any explicitly referenced local repos, docs, or `context/` paths mentioned in the tracker or user input
- Capture the most relevant tracker snapshot or reference notes under `user_inputs/input_artifacts/` when practical.

### Step 9: Decide Whether Context Is Sufficient
Treat context as sufficient when you can already identify:
- the likely execution venue or routing path
- the main goal / acceptance criteria
- the load-bearing constraints or dependencies
- a plausible first-pass implementation or investigation plan

If critical planning context is still missing:
- Ask one focused question at a time with `AskUserQuestion`.
- Include a clear recommended option and use the tool's question format to surface the main tradeoffs cleanly.
- Prefer answering questions by inspecting code, docs, tracker history, or saved task artifacts instead of asking the user.
- Save substantive answers as additional Markdown notes under `user_inputs/`.

### Step 10: Draft the First-Pass Plan and Ask for Approval
- Update `status.md` with the current state and a `## Proposed Plan` section before asking for implementation approval.
- Present the plan review using `AskUserQuestion` instead of a plain-text “should I continue?” follow-up.
- Include these options at minimum:
  - `Approve plan`
  - `Grill more`
  - `Revise plan`
  - `Deny plan`
- Add a fifth option only when a task-specific branch is genuinely useful (for example, handoff, split scope, or defer).
- Put the option you currently recommend first.
- If the user chooses `Grill more`, invoke the `grill-me` skill and keep refining the plan.
- If the user chooses `Revise plan`, update the written plan and ask again.
- If the user chooses `Deny plan`, stop and capture the blocker or changed direction in the task file.
- Only start implementation after explicit plan approval.

## Current-Task Semantics
- Starting a new task automatically switches the current task for this session.
- This supports reusing one agent session across multiple tasks while keeping `get-task-details` semantically correct.

## Managed Metadata Contract

The full tracker-aware contract lives in [`docs/task-status-tracker-contract.md`](../../../docs/task-status-tracker-contract.md).

```markdown
<!-- TASK-METADATA:START -->
## Task Metadata
- Tracker Kind: <linear|github|none>
- Tracker URL: <url|none>
- Tracker Human ID: <ZON-8|owner/repo#123|none>
- Tracker Title: <title|none>
- Machine: <SYSTEM_NAME|hostname|unknown>
- Coding Agent: <codex|claude|unknown>
- Agent Session ID: <id|none>
- Task Folder: </abs/task/folder|none>
- Task Status Path: </abs/task/status.md|none>
- Transcript Path: </abs/transcript|none>
- Workspace Path: </abs/workspace|none>
- Remote Session Anchor Kind: <linear_issue_body|github_issue_body|none>
- Remote Session Anchor ID: <LIVE-SESSION|none>
- GitHub Issue: <url|none>
- GitHub Repo: <owner/repo|none>
- GitHub Issue Number: <number|none>
- Linear Issue ID: <uuid|none>
- Linear Issue Identifier: <ZON-8|none>
- Linear Team ID: <uuid|none>
- Linear Team Name: <Zone|none>
- Linear Project ID: <uuid|none>
- Linear Project Name: <Project|none>
- Zellij Session: <name|none>
- Zellij Link: <url|none>
- Last Synced: YYYY-MM-DD ~HH:MMam/pm PST
<!-- TASK-METADATA:END -->
```

## Degraded Mode Rules
- No `SYSTEM_NAME`: fallback to hostname, then `unknown`.
- No zellij session: `Zellij Session: none`, `Zellij Link: none`.
- No GitHub CLI/auth: skip issue-body update, keep local metadata.
- No Linear tooling/auth for trackerless starts: create the local task folder, record why no Linear tracker was created, and do not block task start.
- No tracker URL: local workflow only.
