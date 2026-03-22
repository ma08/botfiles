# Codex Global Instructions

These are user-level instructions for the Codex agent shared across all projects/sessions on all machines via:

- `~/pro/botfiles/codex/AGENTS.md`
- `~/.codex/AGENTS.md` (symlink created by `setup.sh`)

## Persistent Global Preferences

- For any long-lived behavior preference that should apply across projects and sessions, update both `~/pro/botfiles/codex/AGENTS.md` and `~/pro/botfiles/claude/CLAUDE.md`.
- If the preference changes a skill's behavior or workflow, update the matching files in both `~/pro/botfiles/codex/skills/` and `~/pro/botfiles/claude/skills/`.
- If the preference is only for one repo, one task, or a temporary session, keep it in the local project instructions or task notes instead of the global botfiles.

## GitHub Authorship

- Any GitHub write performed by a coding agent, including new or edited issues, PRs, reviews, comments, or similar changes, should use the authenticated human developer account provided by the default GitHub auth flow rather than a separate bot identity.
- Add a short byline in the written GitHub content naming the coding agent. Preferred examples: `_Written by Codex via the developer's authenticated GitHub account._` and `_Written by Claude Code via the developer's authenticated GitHub account._`
- If a GitHub action has no natural body field, put the attribution in the nearest editable text field or a companion comment. When editing existing agent-authored GitHub content, preserve or refresh the byline so the latest agent remains visible.

## Manual Linear Workflow Policy

- For manual Codex or Claude worker sessions outside Symphony automation, use this shared Linear workflow policy unless the repo or task has an explicit local override.
- `Review` is the default handoff state when implementation is ready for human review. Move the issue to `Review` and leave a reviewer-facing handoff comment that covers what changed, what you verified, and any open risks, questions, or reviewer asks.
- Do not move directly from active implementation to `Done` just because the worker believes the work is finished. `Done` is reserved for explicit final acceptance such as human approval, merge completion, or another clear completion signal.
- Use `Needs Input` when progress is blocked on an external decision, missing information, or another party's response. The accompanying comment should say exactly what input is missing, who it is needed from, and what resumes once it arrives.
- Use `Rework` when review feedback, failed validation, or another concrete signal means the current solution is not ready for approval and needs another implementation pass. Do not use `Needs Input` when the next action is for the worker to make changes.
- Use `Merging` only after the work is effectively approved and the remaining task is landing the change, merging, or completing closely related release housekeeping. It is not a synonym for "almost done."
- If the relevant Linear workspace does not expose one of these states, use the nearest available equivalent and note the mismatch in the status comment or handoff.

## Paths and Conventions

- Assume botfiles lives at `~/pro/botfiles`
- Assume personal OS lives at `~/pro/personal_os`
- Prefer reusable, machine-agnostic paths (`~/pro/...`) over machine-specific absolute paths

## Shell Environment (two-layer bootstrap)

Botfiles uses a two-layer shell model:

- **`.botenv`** — Non-interactive-safe core: secrets, PATH (`$BOTFILES_ROOT/bin`, `~/.local/bin`, `/usr/local/bin`), `BOTFILES_ROOT`, `EDITOR`, `TERM`, `UV_BIN`. Sourced for ALL shell contexts (interactive, SSH commands, agent exec, cron). This is what non-interactive scripts and hooks should source.
- **`.botrc`** — Interactive layer: sources `.botenv`, then adds aliases (`cc`, `bedcc`, `zj`), shell modules (`20-ssh-workflows.sh`, `30-oracle.sh`), and functions (`oracle`, `work-ml`) on top of the shared executable wrappers.

When writing scripts, hooks, or runner wrappers that need botfiles env in a non-interactive context, source `.botenv` (not `.botrc`) for a lighter, safer load. The Codex notify hook (`codex/hooks/run-codex-notify.sh`) is an example — it sources `.botrc` for historical reasons but only needs `.botenv`.

On **bash** machines, `BASH_ENV` is set in the effective login file (`~/.bash_profile` > `~/.bash_login` > `~/.profile`, whichever bash reads first) to point to `.botenv`, so children of login shells automatically inherit the core env. On **zsh** machines, `~/.zshenv` sources `.botenv` directly.

## Skills

- Codex skills are stored in `~/pro/botfiles/codex/skills`
- `setup.sh` symlinks `~/.codex/skills` to that folder
- Keep Codex/Claude skill counterparts aligned to avoid drift
- Codex system skills in `~/.codex/skills/.system/` are machine-managed and should not be source-controlled in `botfiles`

## Curated Skills

- Keep upstream curated skill directories unchanged unless you are intentionally creating a protected local fork.
- For the curated `pdf` skill, do not hand-edit files under `~/pro/botfiles/codex/skills/pdf/` for local workflow preferences; keep that directory pullable from upstream.
- Put local PDF workflow preferences in `AGENTS.md` / `CLAUDE.md`, `README.md`, and `setup.sh`, not inside the curated skill directory.
- Treat Poppler CLI tools (`pdfinfo`, `pdftoppm`, `pdftotext`) as machine-level prerequisites handled via botfiles setup/docs.
- When a PDF task needs Python packages such as `reportlab`, `pdfplumber`, or `pypdf`, prefer task-local scratchpad scripts run with `uv run --with ...` instead of installing those packages into the active project's environment.

## Oracle Skill

- `~/pro/botfiles/codex/skills/oracle` and `~/pro/botfiles/claude/skills/oracle` are kept as verbatim upstream copies of `steipete/oracle/skills/oracle`.
- Do not hand-edit the Oracle skill directory for local preferences; refresh it by replacing it from upstream, and keep local Oracle behavior in `AGENTS.md` / `CLAUDE.md` or botfiles shell modules instead.
- On machines where the default Node runtime is below 22, use the local `oracle` and `oracle-mcp` wrappers from `~/pro/botfiles/bin/` (symlinked into `~/.local/bin` by `setup.sh` and also loaded as shell functions from `~/pro/botfiles/.botrc`) instead of raw `npx -y @steipete/oracle`.
- In this environment, Oracle should be run in API mode by default. Unless the user explicitly asks for browser mode or the task specifically requires ChatGPT web behavior, use `--engine api` instead of relying on upstream defaults.
- In this environment, Oracle should target `gpt-5.4-pro` by default. Treat that as the strongest single-model default here; unless the user explicitly asks for another model, a multi-model run, or a faster/cheaper pass, use `--model gpt-5.4-pro` and do not downgrade just because the run is slow.
- When invoking Oracle from an agent workflow, be explicit about the engine choice rather than assuming Oracle's default mode matches local expectations.
- When invoking Oracle from an agent workflow, be explicit about the model choice too. Prefer the local `oracle` wrapper so the intended `--engine api` and `--model gpt-5.4-pro` defaults are applied unless you are intentionally overriding them.
- In Codex, prefer a dedicated awaiter-style subagent for Oracle work when the Oracle result is needed for the next step. That subagent should own the Oracle session, monitor it, and wait for a terminal status before handing the result back to the main thread.
- Treat long Oracle latency as normal for Pro runs. The installed CLI currently documents `--timeout auto` as 60 minutes for `gpt-5.4-pro`, so several minutes without a final answer is not evidence of failure.
- If an Oracle result is needed for the next step, wait until the session reaches a terminal status. Do not abandon the run for impatience alone; keep monitoring or reattaching with `oracle status` / `oracle session` until the status is `completed` or `error`.
- In Codex, do not leave Oracle waiting as ambient main-thread work when an awaiter-style subagent can own it. Use the main thread to coordinate only after that subagent returns or reports a terminal error.
- Skip waiting only when the user explicitly asks not to wait, explicitly allows parallel work without the Oracle result, or the Oracle session has already reached a terminal error state.
- When giving the user timing context, prefer quoting recent local Oracle evidence instead of guessing. `oracle status` shows recent sessions, session `meta.json` records `startedAt`, `completedAt`, and `elapsedMs`, and `output.log` shows live elapsed progress updates while a run is still in flight.
- Prefer the local `oracle` wrapper over raw `npx -y @steipete/oracle`; the wrapper is the supported path for this machine's Node/runtime setup and should enforce the intended default engine/model behavior.
- On Linux/SSH shells without `DISPLAY`, the local `oracle` wrapper auto-runs explicit browser-mode requests under `xvfb-run` so Chrome can launch headfully.
- Browser mode still requires a signed-in ChatGPT Chrome profile, inline cookies, or a configured remote Oracle browser host; `xvfb-run` only fixes the display/launch side.
- For shell-wide API auth outside repos that provide their own `.env`, use `~/pro/botfiles/secrets/local/codex-openai.rc`. Oracle also auto-loads a repo-local `.env` when present, so local repo runs do not require extra shell exports.
- Oracle API runs on non-Pro models may still inherit shorter auto timeouts from the CLI. If you intentionally use a non-Pro model for a long run, pass an explicit `--timeout` or use background mode rather than relying on `auto`.

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
