# User-Level Claude Instructions

## Task Status Tracking

When working on non-trivial tasks (multi-step, complex debugging, feature implementation), **proactively** maintain task status documentation.

### Proactive Behavior
- **At task start**: Create a task folder with an initial status file
- **At milestones**: Update the status file when completing sub-tasks, making key decisions, or discovering important information
- **Save artifacts continuously**: When you produce or encounter log output, write scripts, capture errors, or generate any useful output — immediately save it to `task-progress-artifacts/` in the task folder. Don't wait until session end.
- **Before session end**: Ensure the status file reflects the current state so work can be resumed
- Use `/save-task-status` for structured saves, but also update inline when natural

### Task Folder Convention
Every tracked task gets a folder at `<task-status-root>/YYYY-MM-DD/<task-slug>/`:
- **Default root**: `context/daily/` (override per-project in project CLAUDE.md)
- **Naming**: lowercase, hyphenated, descriptive slugs (e.g., `fix-auth-timeout`, `setup-remote-workstation`)
- **Status file**: `status.md` for new tasks; update existing `README.md` if present in legacy folders
- **Artifacts**: **Always** save log snippets, screenshots, adhoc scripts, config snapshots, command outputs, and error traces to `task-progress-artifacts/`. Copy content into the folder (don't just reference external paths that may disappear). The task folder should be a self-contained package.

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
