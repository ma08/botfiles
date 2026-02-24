# Codex Global Instructions

These are user-level instructions shared across machines via:

- `~/pro/botfiles/codex/AGENTS.md`
- `~/.codex/AGENTS.md` (symlink created by `setup.sh`)

## Paths and Conventions

- Assume botfiles lives at `~/pro/botfiles`
- Assume personal OS lives at `~/pro/personal_os`
- Prefer reusable, machine-agnostic paths (`~/pro/...`) over machine-specific absolute paths

## Skills

- Codex skills are stored in `~/pro/botfiles/codex/skills`
- `setup.sh` symlinks `~/.codex/skills` to that folder
- Keep Codex/Claude skill counterparts aligned to avoid drift
- Codex system skills in `~/.codex/skills/.system/` are machine-managed and should not be source-controlled in `botfiles`

## Task Status Files

- Use the `save-task-status` skill proactively at milestones, before context switches, and before ending a session
- Save task state in date/task folders (default: `context/daily/YYYY-MM-DD/<task-slug>/`)
- Save artifacts under `task-progress-artifacts/` (logs, screenshots, scripts, command outputs)

## Ad-hoc Scripts (Required)

- When running one-off Python/Bash, **write the script into the task's `task-progress-artifacts/` folder first**, with a short header comment explaining purpose + inputs/outputs, then execute it.
- Prefer saved scripts over inline heredocs so work is reproducible and easy to maintain.
