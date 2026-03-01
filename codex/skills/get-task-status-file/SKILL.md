---
name: get-task-status-file
description: >-
  Print the full path of the current task's status file. Use when: (1) user
  invokes $get-task-status-file or /get-task-status-file, (2) user asks "where
  is my task file?", "what's the status path?", or similar, (3) another skill
  or workflow needs the status file path programmatically. Return one or more
  paths with labels (primary, related) if multiple tasks are relevant.
---

# Get Task Status File

Resolve and print the full path(s) to status file(s) for the current task context.

## Invocation

```
$get-task-status-file [task-slug]
```

Or:

```
/get-task-status-file [task-slug]
```

If no slug is provided, infer the relevant task(s) from conversation context.

## Process

### Step 1: Determine Task Status Root

1. Check the current project's `AGENTS.md` for a `task-status-root:` override
2. If no override is found, check project-level `CLAUDE.md` for compatibility
3. If no override is found, use the default: `context/daily/`

### Step 2: Identify Relevant Task(s)

From the current conversation, determine:

- What task is being worked on right now (primary)
- Whether other tasks are referenced or related
- If a slug argument was provided, use it directly

### Step 3: Search for Task Folders

For each identified task, search for matching folders:

1. Check today's date folder first: `<root>/YYYY-MM-DD/`
2. Then check recent date folders (last 7 days) for the same slug
3. Match both time-prefixed (`*PST-<slug>`) and legacy (`<slug>`) folder names
4. Within each matched folder, resolve status file: `status.md` if present, else `README.md` (legacy)

Example:

```bash
ls -d <root>/*/*<slug>* 2>/dev/null
```

### Step 4: Output Results

Single match: print the full absolute path.

```text
/home/azureuser/pro/project/context/daily/2026-02-24/21h45m59sPST-fix-auth-timeout/status.md
```

Multiple matches: print a labeled list.

```text
Primary (current session):
  /home/azureuser/pro/project/context/daily/2026-02-24/21h45m59sPST-fix-auth-timeout/status.md

Related:
  /home/azureuser/pro/project/context/daily/2026-02-23/14h30m00sPST-auth-refactor/status.md
  /home/azureuser/pro/project/context/daily/2026-02-20/setup-auth-module/README.md
```

No match: state that no task folder was found and suggest using `$start-new-task`.

### Step 5: Verify Files Exist

Before printing any path, confirm the file exists. Only include real files. If a task folder exists without a status file, note it and suggest running `$save-task-status` to create one.

## Labels

- Primary: task most directly related to current conversation context
- Related: tasks with overlapping slugs, shared keywords, or referenced earlier in the session
- Stale: tasks older than 7 days that still match the slug, with an age note

## Tips

- This skill is read-only and never creates or modifies files
- Output absolute paths so they can be used directly in shell commands
- When uncertain about primary task, prefer the most recent match under today's date
