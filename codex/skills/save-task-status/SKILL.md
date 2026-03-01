---
name: save-task-status
description: Save current task status, plan, or bug report to the project's task-tracking folder. Use proactively when work reaches milestones, before ending sessions, or when switching tasks.
source: personal
---

# Save Task Status Skill

Captures the current state of work and saves it to a structured task folder for future reference, context handoff, and session continuity.

## When to Use

- Before ending a work session
- When switching to a different task
- When work reaches a milestone or sub-task completion
- After completing significant work that should be tracked
- When debugging a complex bug (captures bug report details)
- Immediately after a plan is explicitly accepted
- Proactively, without being asked — keep task status current as you work

## How to Invoke

```
/save-task-status [task-slug]
```

Or just `/save-task-status` — Claude will identify the current task from context.

## Configuration: Task Status Root

**Default path**: `context/daily/YYYY-MM-DD/<task-slug>/`

Projects can override this in their project-level CLAUDE.md. Before using the default, check for a line like:

```
task-status-root: resources/task_working_docs/YYYY-MM-DD/<task-slug>/
```

If found, use that path pattern instead of the default.

## Directory Structure

```
<task-slug>/
├── status.md                     # Primary status file
└── task-progress-artifacts/      # Screenshots, exports, artifacts
```

### File Selection (Backward Compatibility)
When updating an **existing** task folder:
1. If the folder contains `README.md` (legacy pattern), update that file
2. If the folder contains `status.md`, update that
3. For **new** task folders, always create `status.md`

### Accepted Plan Persistence (Required)
- Persist accepted plans in task status files (`status.md`, or legacy `README.md` when present).
- Trigger only on explicit acceptance (discrete accept action or explicit approval text).
- Persist immediately after acceptance and before implementation.
- If no task folder exists, create one first, then append `Plan v1`.
- Append (do not replace) accepted plans under `## Accepted Plans`.
- Use this entry format:
  - `### Plan vN — YYYY-MM-DD ~HH:MMam/pm PST`
  - `**Accepted Signal**: <ui_accept | explicit_text>`
  - `**Supersedes**: <Plan v(N-1) | none>`
  - `**Revision Summary**: <1-2 lines>`
  - Full accepted plan markdown body
- If task targeting is ambiguous, ask a concise clarification before writing.

## Process

### Step 1: Determine Task Status Root
1. Check the current project's CLAUDE.md for a `task-status-root` override
2. If no override found, use the default: `context/daily/YYYY-MM-DD/<task-slug>/`
3. Resolve `YYYY-MM-DD` to today's date

### Step 2: Identify the Task
From the current conversation, determine:
- What task is being worked on?
- What is a good slug? (lowercase, hyphenated, descriptive)
- Does a task folder already exist for this work?

If an existing folder exists (same slug, any date), update it in place.
If no folder exists, create one at the resolved path.

### Step 3: Gather Current Status
Collect from the session:
- What phases/steps are complete?
- What is currently in progress?
- What blockers or notes exist?
- Key file paths and commands
- Bug details if debugging (root cause, attempted fixes, reproduction steps)
- Plan/approach if early in a task

### Step 4: Persist Accepted Plan (When Applicable)
If the session includes an explicitly accepted plan:
1. Ensure the target status file exists.
2. Add `## Accepted Plans` if missing.
3. Append the next `Plan vN` entry using the required format above.
4. Update `Last Updated` with a PST timestamp.
5. Sync `Current State` and `Next Steps` to the latest accepted plan.

If no plan was explicitly accepted, skip this step.

### Step 5: Write or Update the Status File
Use the template below. Include only sections relevant to the current situation — omit sections that don't apply. The goal is a useful document for resuming work, not bureaucratic completeness.

### Step 6: Save Artifacts (Non-Optional)
**Always** actively collect and save artifacts to `task-progress-artifacts/`. Don't wait until the end — save artifacts as they're created during the session.

**What to save** (any of these encountered during work):
- **Log snippets**: Copy relevant log output into `.log` or `.txt` files (don't just reference `/tmp/` paths that will disappear)
- **Screenshots**: UI states, error dialogs, terminal output captures
- **Adhoc scripts**: Any one-off scripts written during the task (bash, python, etc.)
- **Config snapshots**: `.env` excerpts (redacted), config diffs, docker-compose overrides
- **Command outputs**: `curl` responses, test results, benchmark data, `git diff` outputs
- **Error traces**: Stack traces, build errors, crash logs
- **Architecture diagrams**: ASCII diagrams, mermaid files, HTML visualizations

**Naming convention**: Use descriptive filenames with context, e.g.:
- `server-startup-error.log` (not `error.log`)
- `tailscale-ping-benchmark.txt` (not `output.txt`)
- `fix-auth-retry-logic.py` (not `script.py`)

**Key principle**: Artifacts should be **self-contained**. Copy content into the task folder rather than just referencing external paths (like `/tmp/` logs or remote URLs) that may be unavailable later. The task folder should be a complete package that can be shared, referenced from Notion, or used to onboard a fresh agent session.

After saving, reference each artifact in the status file's Artifacts section.

## Status File Template

```markdown
# <Task Title>

**Goal**: <One-line description>
**Last Updated**: YYYY-MM-DD ~HH:MMam/pm
**Status**: <In Progress | Blocked | Testing | Complete>

## Quick Links

| Resource | URL |
|----------|-----|
| <relevant links> | |

## Current State

<Brief description of where things stand>

## Accepted Plans (only when at least one plan is explicitly accepted)

### Plan vN — YYYY-MM-DD ~HH:MMam/pm PST
**Accepted Signal**: <ui_accept | explicit_text>
**Supersedes**: <Plan v(N-1) | none>
**Revision Summary**: <1-2 lines>

<Full accepted plan markdown body>

## Progress

- [x] Completed items
- [ ] In-progress items
- [ ] Pending items

## Things Attempted

<Chronological list of approaches tried, with outcomes>

## Bug Status

| Bug | Root Cause | Status |
|-----|-----------|--------|
| <description> | <cause or "investigating"> | <status> |

## Code Changes

<Files modified and nature of changes>

## Blockers

<Current blockers, if any>

## Artifacts

| File | Description |
|------|-------------|
| `task-progress-artifacts/<filename>` | <what it contains and why it's useful> |

## Next Steps

- [ ] Immediate next action 1
- [ ] Immediate next action 2

## Notes

### YYYY-MM-DD ~HHam/pm: Brief description

**Component**:
- Status: Running/Done/Blocked
- Details: Key info
- Command: `command to check/resume`
```

## Tips

- Be specific about component states (daemon PIDs, container status, iteration counts)
- Include exact commands to resume or check status
- Note any blockers or pending decisions
- For bugs, include reproduction steps, root cause analysis, and attempted fixes
- For accepted plans, append full plan history under `## Accepted Plans` (do not overwrite prior versions)
- Adapt the template — omit sections that don't apply

### Artifact Hygiene
- **Save early, save often** — don't accumulate artifacts mentally; write them to disk as you go
- **Copy, don't reference** — save log content into the task folder, don't just note "see /tmp/foo.log"
- **Use descriptive filenames** — future-you should understand the artifact from its name alone
- **Keep artifacts small and focused** — extract the relevant 50 lines from a 10,000-line log
- **Redact secrets** — strip API keys, tokens, passwords before saving config/env snapshots
