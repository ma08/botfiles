# User-Level Claude Instructions

## Task Status Tracking

When working on any task, **proactively** maintain task status documentation.

### Proactive Behavior
- **At task start**: Use `/start-new-task` to scaffold a task folder with status.md, user_inputs/initial.md, and task-progress-artifacts/. For resuming existing tasks, use `/save-task-status` instead.
- **At any checkpoint**: Use `/get-task-details` to retrieve the active status path plus issue/machine/coding-agent session metadata.
- **At milestones**: Update the status file when completing sub-tasks, making key decisions, or discovering important information
- **Save artifacts continuously**:
- When you produce or encounter log output, write scripts, capture errors, or generate any useful output — immediately save it to `task-progress-artifacts/` in the task folder. Don't wait until session end.
- You should save any screenshots too to the `task-progress-artifacts/` folder so that we can refer to them later long-term if needed.
- Aim to use `task-progress-artifacts/` to save any and all useful artifacts that are relevant to the task at hand. Use it instead of `/tmp` for your scratchpad.
- When given a short-lived s3 url (generally screenshots), first download the file to `task-progress-artifacts/` and then use it as you need to.
- **Before session end**: Ensure the status file reflects the current state so work can be resumed
- Use `/start-new-task` to create new task folders and `/save-task-status` for structured status updates throughout the task lifecycle

### Task Folder Convention
Every tracked task gets a folder at `<task-status-root>/YYYY-MM-DD/<HH>h<MM>m<SS>sPST-<task-slug>/`:
- **Default root**: `context/daily/` (override per-project in project CLAUDE.md)
- **Folder naming**: `<HH>h<MM>m<SS>sPST-<slug>` — time-prefixed with PST timezone (e.g., `21h45m59sPST-fix-auth-timeout`)
- **Full path example**: `context/daily/2026-02-24/21h45m59sPST-fix-auth-timeout/`
- **Slugs**: lowercase, hyphenated, descriptive, under 50 characters
- **Status file**: `status.md` for new tasks; update existing `README.md` if present in legacy folders
- **user_inputs/**: Immutable records of original user inputs. Never overwrite or delete files here. New inputs get new files (e.g., `clarifications.md`, `scope-change-YYYY-MM-DD.md`). User-provided screenshots and reference material go here, not in `task-progress-artifacts/`.
- **Artifacts**: **Always** save log snippets, screenshots, adhoc scripts, config snapshots, command outputs, and error traces to `task-progress-artifacts/`. Copy content into the folder (don't just reference external paths that may disappear). The task folder should be a self-contained package.
- **Timezone**: All timestamps in task files use PST explicitly. Use `TZ=America/Los_Angeles date` for reliable PST regardless of VM timezone. Format: `YYYY-MM-DD ~HH:MMam/pm PST`.
- **Machine identity**: Set `SYSTEM_NAME` in `~/pro/botfiles/secrets/local/machine.rc` so metadata and notifications remain consistent across workflows.
- **Legacy folders**: Existing folders without time prefix or `user_inputs/` continue to work unchanged.

### Per-Project Overrides
Projects can customize the task-status root by adding to their CLAUDE.md:
```
task-status-root: <custom-path>/YYYY-MM-DD/<task-slug>/
```

## Developer Messaging

When monitoring long-running processes or discovering blockers while the developer may be away from the terminal, proactively send WhatsApp notifications using the `message-developer` skill.

### When to Message
- Background monitoring detects completion, failure, or a blocker
- A task reaches a significant milestone during autonomous work
- An error pattern suggests the developer needs to intervene
- Session is ending with important pending state

### When NOT to Message
- The developer is actively interacting (hooks handle this automatically)
- Routine progress that doesn't require attention
- Every iteration of a periodic check (only on state changes)

### Command
```
cd ~/.claude/hooks && uv run python send.py --title "Title" "Message body"
```

## Ralph Loop Workflow

When a plan involves a Ralph loop, the orchestrator session (you) **only prepares the loop files** — it does NOT implement the code changes itself. The Ralph loop agent handles all code generation, testing, and committing.

### What the orchestrator does:
1. Create Ralph files: PROMPT.md, AGENT.md, fix_plan.md, specs/, run-ralph.sh
2. Copy them to the project root
3. Hand off to the user to run `./run-ralph.sh claude|codex [max_iterations]`

### What the orchestrator does NOT do:
- Implement the code changes described in fix_plan.md
- Write the test files described in fix_plan.md
- Mark fix_plan.md tasks as completed
- Commit code changes

The loop agent (spawned by run-ralph.sh) reads PROMPT.md each iteration, picks the next incomplete task from fix_plan.md, implements it, validates, commits, and loops until done.

## Sycophancy Warning
Provide constructive criticism. Be a good partner in getting quality and pragmatic work done, not a servant.

## Design Aesthetics Guidelines
Whenever you are creating any visual artifact (website, iamge, TUI, video etc.) let's always put in effort to pick a unique theme and style that showcases taste, craft, and nuance for the person, project, situation etc. VERY IMPORTANT.

Since the user is a stratup founder, by default, use the startup's branding and design aesthetics found at `~/pro/personal_os/context/zone/ZONE_FRONTEND_STYLE_GUIDE.md`

Always make sure to ask suitable questions to the user for design aesthetics if needed to confirm before implementing.
