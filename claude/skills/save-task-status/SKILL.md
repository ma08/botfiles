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

### Step 4: Write or Update the Status File
Use the template below. Include only sections relevant to the current situation — omit sections that don't apply. The goal is a useful document for resuming work, not bureaucratic completeness.

### Step 5: Save Artifacts
If there are relevant artifacts (screenshots, exports, etc.):
- Save to `task-progress-artifacts/` subfolder
- Reference in the status file

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
- Reference file paths for key artifacts
- For bugs, include reproduction steps, root cause analysis, and attempted fixes
- For plans, include implementation approach, technical decisions, and testing checklist
- Adapt the template — omit sections that don't apply
