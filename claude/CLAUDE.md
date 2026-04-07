# User-Level Claude Instructions

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

## Shell Environment (two-layer bootstrap)

Botfiles uses a two-layer shell model:

- **`.botenv`** — Non-interactive-safe core: secrets, PATH (`$BOTFILES_ROOT/bin`, `~/.local/bin`, `/usr/local/bin`), `BOTFILES_ROOT`, `EDITOR`, `TERM`, `UV_BIN`. Sourced for ALL shell contexts (interactive, SSH commands, agent exec, cron). This is what non-interactive scripts and hooks should source.
- **`.botrc`** — Interactive layer: sources `.botenv`, then adds aliases (`cc`, `bedcc`, `zj`), shell modules (`20-ssh-workflows.sh`, `30-oracle.sh`), and functions (`oracle`, `work-ml`) on top of the shared executable wrappers.

When writing scripts or hooks that need botfiles env in a non-interactive context, source `.botenv` (not `.botrc`) for a lighter, safer load.

On **bash** machines, `BASH_ENV` is set in the effective login file (`~/.bash_profile` > `~/.bash_login` > `~/.profile`, whichever bash reads first) to point to `.botenv`, so children of login shells automatically inherit the core env. On **zsh** machines, `~/.zshenv` sources `.botenv` directly.

## Shared Cloud CLI Context

- When a task needs cloud actions from the CLI, read `~/pro/personal_os/context/cloud-access.md` first.
- Treat that file as the shared runbook for current Azure/AWS/GCP access patterns, trusted machine context, verification commands, and other cross-machine cloud CLI notes.
- Use the `~/pro/...` path form when referring to it, and consult it before assuming cloud auth is already available or changing login state on a machine.

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
- In this environment, Oracle should be run in API mode by default. Unless the user explicitly asks for browser mode or the task specifically requires ChatGPT web behavior, pass `--engine api` instead of relying on upstream defaults.
- Default to `gpt-5.4-pro` unless the user explicitly asks for another model, a multi-model run, or a faster/cheaper pass.
- Be explicit about engine/model choice. Prefer the local `oracle` wrapper so the intended defaults are applied unless you are intentionally overriding them.
- If the Oracle result is needed for the next step, prefer the foreground `oracle-awaiter` custom subagent and invoke it explicitly when you want to guarantee that path. Let it own one Oracle run and wait for a terminal status before handing the result back.
- Do not rerun, shorten the prompt, or downgrade the model for latency alone.
- For `gpt-5.4-pro`, treat 10-15 minutes as common, 15-40 minutes as a normal slow run, and up to 60 minutes as within tolerance. `in_progress` is not failure.
- If Oracle stays in the main thread, wait or reattach until the session reaches `completed` or `error`. If a polling shell dies or `stdin` closes, restart polling against the same slug; that is not Oracle failure. Skip waiting only when the user explicitly says not to wait.
- When giving timing context, quote local Oracle evidence (`oracle status`, `meta.json`, `output.log`) instead of guessing.
- Prefer the local `oracle` wrapper over raw `npx -y @steipete/oracle`; the wrapper is the supported path for this machine's Node/runtime setup and should enforce the intended default engine/model behavior.
- On Linux/SSH shells without `DISPLAY`, the local `oracle` wrapper auto-runs explicit browser-mode requests under `xvfb-run` so Chrome can launch headfully.
- Browser mode still requires a signed-in ChatGPT Chrome profile, inline cookies, or a configured remote Oracle browser host; `xvfb-run` only fixes the display/launch side.
- For shell-wide API auth outside repos that provide their own `.env`, keep the default Azure Oracle route in `~/pro/botfiles/secrets/local/codex-azure.rc` and keep `~/pro/botfiles/secrets/local/codex-openai.rc` only for direct OpenAI fallback. Oracle also auto-loads a repo-local `.env` when present, so local repo runs do not require extra shell exports.
- On non-Pro models, pass an explicit `--timeout` or use background mode for long Oracle runs instead of relying on `auto`.

## Reviewer Agent

- Use the read-only `reviewer` custom subagent at `~/pro/botfiles/claude/agents/reviewer.md` (synced to `~/.claude/agents/reviewer.md`) for PR or working-tree review focused on correctness, security, regressions, and missing tests.

## Task Status Tracking

When working on any task, **proactively** maintain task status documentation.

### Proactive Behavior
- **At task start**: Use `/start-new-task` to scaffold a task folder with `status.md`, `user_inputs/initial.md`, `user_inputs/input_artifacts/`, `task-progress-artifacts/`, and `task-progress-artifacts/scratchpad/`. For interrupted tracked resumes from another session, use `/continue-task` instead. Keep `/save-task-status` for checkpoint updates once the current session already owns the task. When enough context is already available, keep going in the same turn: gather tracker/local context, ask `AskUserQuestion` only for critical planning gaps, and present a first-pass written plan for approval instead of stopping at boilerplate setup.
- **At any checkpoint**: Use `/get-task-details` to retrieve the active status path plus issue/machine/coding-agent session metadata.
- **At milestones**: Update the status file when completing sub-tasks, making key decisions, or discovering important information
- **Save artifacts continuously**:
- When you produce or encounter log output, write scripts, capture errors, or generate any useful output — immediately save it under `task-progress-artifacts/` in the task folder. Don't wait until session end.
- Keep the top-level `task-progress-artifacts/` folder curated for user-facing deliverables and key evidence that should be easy to browse later.
- Use `task-progress-artifacts/scratchpad/` instead of `/tmp` for raw logs, intermediate screenshots, polling snapshots, JSON dumps, and other scratch work.
- Keep text user input notes under `user_inputs/*.md`.
- Save user-provided or user-referenced files/images in `user_inputs/input_artifacts/`.
- Save generated screenshots to `task-progress-artifacts/scratchpad/` by default, then move or copy the important long-term evidence to top-level `task-progress-artifacts/` when it should be easy to review later.
- When given a short-lived s3 url, download input-context files into `user_inputs/input_artifacts/`; download generated output captures into `task-progress-artifacts/scratchpad/`, then promote them only if they become durable reference material.
- **Before session end**: Ensure the status file reflects the current state so work can be resumed
- Use `/start-new-task` to create new task folders, `/continue-task` to adopt interrupted tracked work, and `/save-task-status` for structured status updates throughout the task lifecycle

### Task Folder Convention
Every tracked task gets a folder at `<task-status-root>/YYYY-MM-DD/<HH>h<MM>m<SS>sPST-<task-slug>/`:
- **Default root**: `context/daily/` (override per-project in project CLAUDE.md)
- **Folder naming**: `<HH>h<MM>m<SS>sPST-<slug>` — time-prefixed with PST timezone (e.g., `21h45m59sPST-fix-auth-timeout`)
- **Full path example**: `context/daily/2026-02-24/21h45m59sPST-fix-auth-timeout/`
- **Slugs**: lowercase, hyphenated, descriptive, under 50 characters
- **Status file**: `status.md` for new tasks; update existing `README.md` if present in legacy folders
- **user_inputs/**: Immutable records of original user inputs. Never overwrite or delete files here. New text inputs get new Markdown files (e.g., `clarifications.md`, `scope-change-YYYY-MM-DD.md`).
- **input_artifacts/**: Under `user_inputs/`, store user-provided or user-referenced files, images, and local copies of input artifacts. Maintain `user_inputs/input_artifacts/index.md` when artifacts are captured or when an external artifact cannot be copied locally.
- **task-progress-artifacts/**: Keep curated deliverables and key evidence in top-level `task-progress-artifacts/`. Put raw log snippets, adhoc scripts, config snapshots, command outputs, screenshots, and error traces in `task-progress-artifacts/scratchpad/`. Copy content into the folder (don't just reference external paths that may disappear). The task folder should be a self-contained package.
- **Timezone**: All timestamps in task files use PST explicitly. Use `TZ=America/Los_Angeles date` for reliable PST regardless of VM timezone. Format: `YYYY-MM-DD ~HH:MMam/pm PST`.
- **Machine identity**: Set `SYSTEM_NAME` in `~/pro/botfiles/secrets/local/machine.rc` so metadata and notifications remain consistent across workflows.
- **Legacy folders**: Existing folders without time prefix or `user_inputs/` continue to work unchanged.

## Cross-Session Orchestration

- For regular non-Symphony multi-session work, prefer the shared skills `cross-session-context`, `cross-session-message`, and `pr-autoreview-loop`.
- Target other sessions by tracker ref or task slug first. Use `--task-dir`, `--status-file`, or `--zellij-session` only for lower-level or debug workflows.
- Treat task/status metadata as the primary source of truth, transcript tail as a targeted fallback, and live zellij inspection as diagnostic context.
- Keep cross-session sends preview-first. `send-zellij-message` should stay in dry-run mode until the resolved session/tab target is clearly correct; use `--execute` and `--submit enter` explicitly.
- For large multiline Codex prompts, `send-zellij-message` now adds a delayed confirm Enter automatically after `--submit enter` because one immediate Enter can leave the prompt staged in the composer.
- Do not use cross-session message send as remote control. It is for bounded prompt delivery into a known live target only.
- For PR-bearing non-Symphony review loops, use `pr-autoreview-loop` to match current-head reviewer output, address findings, push, and wait again until the sweep is clean or genuinely blocked.
- When the PR loop reports `blocked`, or reviewer/check infrastructure fails without an in-session retry path, stop and ask for human input instead of silently spinning.

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
