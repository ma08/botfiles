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
- Use `get-task-details` to retrieve current status path plus linked issue, machine, coding-agent session id, and zellij context
- Save task state in date/task folders (default: `context/daily/YYYY-MM-DD/<task-slug>/`)
- New folders use time-prefixed names: `<HH>h<MM>m<SS>sPST-<task-slug>` (e.g., `21h45m59sPST-fix-auth-timeout`)
- Full path example: `context/daily/2026-02-24/21h45m59sPST-fix-auth-timeout/`
- All timestamps in task files use PST explicitly — use `TZ=America/Los_Angeles date` for reliable PST regardless of system timezone
- Format timestamps as: `YYYY-MM-DD ~HH:MMam/pm PST`
- Legacy folders without time prefix continue to work unchanged
- Save generated artifacts under `task-progress-artifacts/`, keeping curated outputs at the top level and raw/intermediate material under `task-progress-artifacts/scratchpad/`
- Keep task input context under `user_inputs/`, with Markdown notes at the root and non-Markdown files in `user_inputs/input_artifacts/`
- Set `SYSTEM_NAME` in `~/pro/botfiles/secrets/local/machine.rc` so task metadata and notifications identify the machine consistently

### Plan Acceptance Persistence (Required)

- Persist accepted plans in the active task status file (`status.md`; use legacy `README.md` only when that is the existing status file)
- Do not use `.codex/plans/` for accepted plan storage
- Treat a plan as accepted only on explicit acceptance (discrete accept action or explicit approval text)
- Persist immediately after acceptance and before implementation
- If no task status file exists, create a task folder first using the task status workflow, then persist `Plan v1`
- Store accepted plans under `## Accepted Plans` and append versions (`Plan v1`, `Plan v2`, ...)
- Each appended plan entry must include: PST timestamp, accepted signal, supersedes value, short revision summary, and full accepted plan body
- If task targeting is ambiguous, ask a concise clarification before writing
- Once task file is saved, ask for the user to review from the plan file and make any changes as needed to the plan. Only after their explicit approval to proceed, proceed to the implementation phase. Remember that approval for implementation is allowed only after review is done from file.

### Input Context Handling

- **Keep text inputs immutable** — store original prompts, clarifications, and review answers as Markdown files directly under `user_inputs/`; add new files instead of overwriting old ones.
- **Capture input artifacts locally** — copy/download user-provided or user-referenced files, images, and other reference materials into `user_inputs/input_artifacts/` whenever practical.
- **Record provenance** — when `input_artifacts/` contains captured files, or an external artifact cannot be captured locally, maintain `user_inputs/input_artifacts/index.md` with local path, original source, PST capture time, and notes.
- **Prefer local references** — once captured, reference `user_inputs/input_artifacts/...` from status files instead of depending on issue URLs or external links alone.

### Artifact Handling

- **Save continuously** — when you produce or encounter log output, write scripts, capture errors, or generate any useful output, immediately save it under `task-progress-artifacts/`. Don't wait until session end.
- **Keep the top level curated** — use `task-progress-artifacts/` for human-reviewable deliverables and key evidence that should be easy to browse later.
- **Use `task-progress-artifacts/scratchpad/` as your scratchpad** instead of `/tmp`. Raw logs, polling snapshots, JSON dumps, temporary screenshots, and intermediate working files belong there by default.
- **Screenshots & images**: save generated or working screenshots to `task-progress-artifacts/scratchpad/` by default; user-provided or user-referenced input images belong in `user_inputs/input_artifacts/`.
- **Short-lived S3 URLs** (typically screenshots): download input-context files to `user_inputs/input_artifacts/`; download work-product captures to `task-progress-artifacts/scratchpad/`, then promote only the important long-term evidence to top-level `task-progress-artifacts/`.
- **Self-contained folders**: copy content into the task folder rather than referencing external paths that may disappear. The task folder should be a complete, portable package.

## Ad-hoc Scripts (Required)

- When running one-off Python/Bash, **write the script into the task's `task-progress-artifacts/scratchpad/` folder first**, with a short header comment explaining purpose + inputs/outputs, then execute it.
- Prefer saved scripts over inline heredocs so work is reproducible and easy to maintain.

## Playwright in SSH VMs

- Headed Playwright needs an X server; SSH-only VMs usually do not have one. Use headless by default.
- If a visual browser is required, run with a virtual display:
  - `xvfb-run -a bash "$PWCLI" open <url> --headed`
- Wrapper script is preferred; if it is not executable, invoke via `bash`:
  - `export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"`
  - `export PWCLI="$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh"`
  - `bash "$PWCLI" open <url>`
- Always `snapshot` before interacting, and re-`snapshot` after navigation or UI changes.
- Save Playwright artifacts (screenshots, traces) in a repo-appropriate location; default to `output/playwright/` when no repo guidance exists.
