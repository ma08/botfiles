---
name: start-task
description: >-
  Initialize a new tracked task folder with status.md, user_inputs/initial.md,
  user_inputs/input_artifacts/, task-progress-artifacts/, and
  task-progress-artifacts/scratchpad/. Supports tracker-aware slugs, canonical
  task roots, machine/session metadata capture, and immediate plan review.
---

# Start Task

Create a task folder and capture durable metadata for machine, session, and tracker linkage.

## Invocation

```text
/start-task <description>
```

If no description is provided, ask for one using `clarify`.

## Shared Helpers

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/resolve_task_context.py \
  --project-root "<project-root>" \
  --description "<text>"
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<status-file>" \
  --tracker-url "<tracker-url-if-any>" \
  --github-issue-url "<github-issue-url-if-any>" \
  --sync-github-issue
```

## Process

### Step 1: Determine task status root
1. Check project `AGENTS.md` for `task-status-root:`.
2. If missing, check project `CLAUDE.md`.
3. Default to `context/daily/`.
4. Resolve date as `YYYY-MM-DD`.

### Step 2: Resolve context before slugging
Run:

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/resolve_task_context.py \
  --project-root "<project-root>" \
  --description "<user description>" \
  --max-slug-length 60
```

Troubleshooting before treating helper execution as broken:
- If the terminal/tool layer returns `BLOCKED: User denied. Do NOT retry.`, do not attribute that to the helper script itself.
- First verify the live machine context with `pwd` and `env | sort | grep -E '^(HOME|PWD|USER)='` so you do not accidentally use paths from another machine profile.
- Retry once with a simpler direct invocation on the verified local path, avoiding unnecessary heredocs/wrappers.
- Only report a helper-script failure when the script itself returns a real stderr/exit failure after path/context verification.

Use output fields such as:
- If the terminal/tool layer returns `BLOCKED: User denied. Do NOT retry.`, do not attribute that to the helper script itself.
- First verify the live machine context with `pwd` and `env | sort | grep -E '^(HOME|PWD|USER)='` so you do not accidentally use paths from another machine profile.
- Retry once with a simpler direct invocation on the verified local path, avoiding unnecessary heredocs/wrappers.
- Only report a helper-script failure when the script itself returns a real stderr/exit failure after path/context verification.

Use output fields such as:
- Task Slug
- Tracker Kind / URL / Human ID / Title
- GitHub Issue compatibility URL when detected
- Canonical Project Root
- Canonical Task Status Root
- Machine
- Coding Agent
- Agent Session ID
- Zellij Session
- Zellij Link

### Step 3: Slug and folder naming
- If the primary tracker is GitHub, slug format is `repo-issue-<number>-<title>`.
- If the primary tracker is Linear, slug format is `<linear-id>-<title>`.
- If canonical project/task roots are emitted for tracker-linked work, create or resume the task there instead of the current repo.
- Enforce max slug length `60`; truncation appends a stable hash suffix.
- Folder format remains `<HH>h<MM>m<SS>sPST-<slug>`.

### Step 4: Existing task check
- Search for an existing task folder with the same slug.
- If found, ask whether to resume or create new using `clarify`, with your recommended option first.
- For tracker-linked work, search the canonical task root first when emitted by `resolve_task_context.py`.
- If resuming, hand off to `continue-task` unless the current session already owns the task.

### Step 5: Create folder structure

```text
<HH>h<MM>m<SS>sPST-<slug>/
├── status.md
├── user_inputs/
│   ├── initial.md
│   └── input_artifacts/
└── task-progress-artifacts/
    └── scratchpad/
```

### Step 6: Populate status and initial input
- Capture the original description verbatim in `user_inputs/initial.md`.
- Keep additional Markdown input notes directly under `user_inputs/`.
- Reserve `user_inputs/input_artifacts/` for user-provided or user-referenced files, images, and local copies of input artifacts.
- Create `user_inputs/input_artifacts/index.md` once the task has a captured input artifact or external artifact reference needing provenance.
- Keep timestamps in PST (`TZ=America/Los_Angeles date`).
- Treat top-level `task-progress-artifacts/` as curated deliverables and `task-progress-artifacts/scratchpad/` as the default destination for raw/intermediate files.

### Step 7: Upsert task metadata
After creating `status.md`, run:

```bash
python ~/pro/botfiles/codex/skills/_shared/task_status/scripts/sync_task_metadata.py \
  --status-file "<abs-status-file-path>" \
  --tracker-url "<tracker-url-if-any>" \
  --github-issue-url "<issue-url-if-any>" \
  --sync-github-issue
```

Behavior:
- Always upserts managed tracker-aware task metadata in the status file.
- Sets this task as the current task for the active `{project, coding-agent, agent-session}` context.
- If `--sync-github-issue` is set, upserts the managed live-session block on the primary tracker.
- If tracker sync dependencies are missing, core task creation still succeeds.
- After sync, verify that the metadata block reflects a real session identity when the runtime supports one. If the task shows `Agent Session ID: none`, treat current-task lookup as degraded and avoid claiming `/get-task-details` will resolve this session reliably until session identity is fixed or explicitly overridden.

### Step 8: Gather planning context immediately
After `status.md` exists and metadata is synced:
- Read the primary tracker when one exists.
- Inspect related issues when they affect planning.
- Search the most relevant local context roots before asking the user for more information.
- Capture the most relevant tracker snapshot or reference notes under `user_inputs/input_artifacts/` when practical.

### Step 9: Decide whether context is sufficient
Treat context as sufficient when you can identify:
- likely execution venue or routing path
- main goal / acceptance criteria
- load-bearing constraints or dependencies
- a plausible first-pass implementation or investigation plan

If critical context is still missing:
- Ask one focused question at a time with `clarify`.
- Put the currently recommended option first and include short tradeoff descriptions.
- Prefer answering questions by inspecting code, docs, tracker history, or saved task artifacts instead of asking the user.
- Save substantive answers as additional Markdown notes under `user_inputs/`.

### Step 10: Draft the first-pass plan and ask for approval
- Update `status.md` with the current state and a `## Proposed Plan` section before asking for implementation approval.
- Present the plan review using `clarify` instead of a plain-text follow-up.
- Include these options at minimum:
  - Approve plan
  - Grill more
  - Revise plan
  - Deny plan
- Put the option you currently recommend first.
- If the user chooses `Grill more`, invoke `grill-me` and keep refining the plan.
- If the user chooses `Revise plan`, update the written plan and ask again.
- If the user chooses `Deny plan`, stop and capture the blocker or changed direction in the task file.
- Only start implementation after explicit plan approval.

## Current-task semantics
- Starting a new task automatically switches the current task for this session.
- This supports reusing one agent session across multiple tasks while keeping `get-task-details` semantically correct.

## Notes
- The full tracker-aware contract lives in `~/pro/botfiles/docs/task-status-tracker-contract.md`.
- Prefer Hermes-native collaboration style, but keep the filesystem/task contract agent-agnostic.
