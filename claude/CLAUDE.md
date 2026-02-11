# User-Level Claude Instructions

## Task Status Tracking

When working on non-trivial tasks (multi-step, complex debugging, feature implementation), **proactively** maintain task status documentation.

### Proactive Behavior
- **At task start**: Create a task folder with an initial status file
- **At milestones**: Update the status file when completing sub-tasks, making key decisions, or discovering important information
- **Before session end**: Ensure the status file reflects the current state so work can be resumed
- Use `/save-task-status` for structured saves, but also update inline when natural

### Task Folder Convention
Every tracked task gets a folder at `<task-status-root>/YYYY-MM-DD/<task-slug>/`:
- **Default root**: `context/daily/` (override per-project in project CLAUDE.md)
- **Naming**: lowercase, hyphenated, descriptive slugs (e.g., `fix-auth-timeout`, `setup-remote-workstation`)
- **Status file**: `status.md` for new tasks; update existing `README.md` if present in legacy folders
- **Artifacts**: store in `task-progress-artifacts/` subfolder

### Per-Project Overrides
Projects can customize the task-status root by adding to their CLAUDE.md:
```
task-status-root: <custom-path>/YYYY-MM-DD/<task-slug>/
```

## Sycophancy Warning
Provide constructive criticism. Be a good partner in getting quality and pragmatic work done, not a servant.
