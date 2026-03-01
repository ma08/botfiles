---
name: start-new-task
description: >-
  Initialize a new task folder with status.md, user_inputs/initial.md, and
  task-progress-artifacts/. Use when: (1) user invokes $start-new-task or
  /start-new-task, (2) user describes new work ("let's fix X", "I need to set
  up Y", "new task"), (3) beginning of a session with a clear new effort worth
  tracking, (4) Codex detects a distinct new task. Do NOT use when resuming an
  existing task (use $save-task-status), for trivial one-off questions, or
  when a task folder already exists.
---

# Start New Task

Scaffold a task folder with status tracking, user input preservation, and artifact storage.

## Invocation

```
$start-new-task <description>
```

Or:

```
/start-new-task <description>
```

If no description is provided, ask for one before proceeding.

## Process

### Step 1: Determine Task Status Root

1. Check the current project's `AGENTS.md` for a `task-status-root:` override
2. If no override is found, check project-level `CLAUDE.md` for compatibility
3. If no override is found, use the default: `context/daily/`
4. Resolve the date component to today's date (`YYYY-MM-DD`)

### Step 2: Get Current PST Time

Run:

```bash
TZ=America/Los_Angeles date +'%Hh%Mm%Ss'
```

Use this output regardless of system timezone. This produces the time component for the folder name (for example, `21h45m59s`).

### Step 3: Generate Slug and Folder Name

1. Parse the task description into a slug: lowercase, hyphenated, descriptive, under 50 characters
2. Build the folder name: `<HH>h<MM>m<SS>sPST-<slug>`
3. Build the full path: `<task-status-root>/YYYY-MM-DD/<HH>h<MM>m<SS>sPST-<slug>/`

### Step 4: Check for Existing Task

Search for an existing folder with the same slug (any date, any time prefix). If found:

- Ask the user whether to resume the existing task or start a new one
- If resume: hand off to `$save-task-status` with the existing folder
- If new: proceed with creation

### Step 5: Create Folder Structure

```
<HH>h<MM>m<SS>sPST-<slug>/
├── status.md
├── user_inputs/
│   └── initial.md
└── task-progress-artifacts/
```

Create all directories and files in one pass.

### Step 6: Populate status.md

Use the status template below. Fill in:

- Task title from the description
- Goal from the description
- Current PST timestamp
- Status: `In Progress`
- Reference to `user_inputs/initial.md`
- If the task is being created because a plan was explicitly accepted, add `## Accepted Plans` and append `Plan v1` with full plan markdown

### Step 7: Populate user_inputs/initial.md

Assess description richness:

- Rich description (specific requirements, multiple sub-goals, technical details):
  - Pre-populate using the rich template below
  - Include the original description verbatim
  - Extract requirements and open questions
- Thin description (brief phrase like `fix auth timeout`):
  - Create using the thin template with placeholder comments

### Step 8: Confirm with User

Ask the user to review and optionally expand `user_inputs/initial.md` before implementation. If the user says "just go" (or equivalent), proceed and capture additional inputs later as new files under `user_inputs/`.

## Folder Naming Convention

Format: `<HH>h<MM>m<SS>sPST-<slug>`

Examples:

- `21h45m59sPST-fix-auth-timeout`
- `08h12m03sPST-setup-remote-workstation`
- `14h30m00sPST-migrate-db-to-postgres`

Rationale:

- Visual disambiguation: multiple tasks on the same day are immediately distinguishable
- Chronological sorting: file explorers and `ls` sort these in creation order
- Explicit timezone: PST suffix removes ambiguity across machines in different timezones

## Timezone Convention

All timestamps in task files use PST explicitly.

- Use `TZ=America/Los_Angeles date` for reliable PST regardless of VM or machine timezone
- Format timestamps as: `YYYY-MM-DD ~HH:MMam/pm PST`
- Never rely on the system default timezone

## user_inputs Contract

- Immutable: never overwrite or delete existing files in `user_inputs/`
- New inputs get new files: `clarifications.md`, `scope-change-YYYY-MM-DD.md`, `feedback.md`, etc.
- Copy content in: do not reference ephemeral URLs or `/tmp` paths
- User-provided screenshots and reference material: save to `user_inputs/`, not `task-progress-artifacts/`
- Purpose: immutable records for alignment evaluation, session handoff, and long-term version control

## Templates

### status.md Template

```markdown
# <Task Title>

**Goal**: <One-line goal from description>
**Started**: YYYY-MM-DD ~HH:MMam/pm PST
**Last Updated**: YYYY-MM-DD ~HH:MMam/pm PST
**Status**: In Progress

## User Inputs

- [`user_inputs/initial.md`](user_inputs/initial.md) - original task description and requirements

## Current State

Task just started. See `user_inputs/initial.md` for full requirements.

## Progress

- [ ] <First logical step>

## Artifacts

| File | Description |
|------|-------------|
| *none yet* | |

## Next Steps

- [ ] Review `user_inputs/initial.md` and confirm approach
- [ ] Begin implementation
```

Optional snippet (add only when a plan was explicitly accepted):

```markdown
## Accepted Plans

### Plan v1 — YYYY-MM-DD ~HH:MMam/pm PST
**Accepted Signal**: <ui_accept | explicit_text>
**Supersedes**: none
**Revision Summary**: Initial accepted plan

<Full accepted plan markdown body>
```

### user_inputs/initial.md - Rich Template

Use when the description contains specific requirements, multiple sub-goals, or technical details.

```markdown
# Task: <Task Title>

**Captured**: YYYY-MM-DD ~HH:MMam/pm PST

## Original Description

> <User's exact words, verbatim>

## Extracted Requirements

- <Requirement 1>
- <Requirement 2>
- <Requirement 3>

## Open Questions

- <Question about scope, priority, or approach>

## Additional Context

<Any relevant context from the conversation: links, file paths, error messages>
```

### user_inputs/initial.md - Thin Template

Use when the description is a brief phrase with minimal detail.

```markdown
# Task: <Task Title>

**Captured**: YYYY-MM-DD ~HH:MMam/pm PST

## Original Description

> <User's exact words, verbatim>

## Requirements

<!-- Expand with specific requirements, acceptance criteria, or constraints -->

## Context

<!-- Add relevant links, file paths, error messages, or background -->
```

## Relationship with save-task-status

- `start-new-task` creates the initial folder structure, `status.md`, and `user_inputs/initial.md`
- `save-task-status` maintains and updates status files through the task lifecycle
- Both skills share the same `task-status-root` configuration
- After `$start-new-task`, use `$save-task-status` for subsequent status updates
- If `$save-task-status` is invoked and no task folder exists, run `$start-new-task` first
- If creation is triggered by an accepted plan, persist that plan immediately as `Plan v1` in `## Accepted Plans`
