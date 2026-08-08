# Codex Global Instructions

These are user-level instructions for the Codex agent shared across all projects/sessions on all machines via:

- `~/pro/botfiles/codex/AGENTS.md`
- `~/.codex/AGENTS.md` (symlink created by `setup.sh`)

## Persistent Global Preferences

- For any long-lived behavior preference that should apply across projects and sessions, update both `~/pro/botfiles/codex/AGENTS.md` and `~/pro/botfiles/claude/CLAUDE.md`.
- If the preference changes a skill's behavior or workflow, update the matching files in both `~/pro/botfiles/codex/skills/` and `~/pro/botfiles/claude/skills/`.
- If the preference is only for one repo, one task, or a temporary session, keep it in the local project instructions or task notes instead of the global botfiles.
- Codex thread titles associated with ZON-155 are a deliberate visual-divider exception: begin them with exactly `------- ZON-155`, then retain the normal ` · stable domain · current status` suffix.

## Human Writing Style

- In user-facing prose and drafts, never use em dashes. Rewrite with periods, commas, parentheses, or colons. Preserve them only inside exact quotations, source text, code, identifiers, or data that must remain unchanged.
- Write plainly and naturally. Lead with the concrete point, use contractions when they fit, vary sentence length, and match the user's own voice when a writing sample is available.
- Remove common AI writing patterns: formulaic openings and closings, vague attribution, promotional inflation, canned transitions, forced three-part lists, conspicuous synonym cycling, excessive headings or bold text, and overly uniform sentence rhythm.
- Do not simulate humanity with invented anecdotes, fake opinions, unnecessary slang, or deliberate mistakes. Preserve the meaning, facts, and precision of the original.

## GitHub Authorship

- Any GitHub write performed by a coding agent, including new or edited issues, PRs, reviews, comments, or similar changes, should use the authenticated human developer account provided by the default GitHub auth flow rather than a separate bot identity.
- Add a short byline in the written GitHub content naming the coding agent. Preferred examples: `_Written by Codex via the developer's authenticated GitHub account._` and `_Written by Claude Code via the developer's authenticated GitHub account._`
- If a GitHub action has no natural body field, put the attribution in the nearest editable text field or a companion comment. When editing existing agent-authored GitHub content, preserve or refresh the byline so the latest agent remains visible.

## Google Workspace Sender Defaults

- The `columbia` gws account alias authenticates the `sk5057@columbia.edu` mailbox, but outbound drafts and messages from that mailbox should default to the verified send-as address `sourya.kakarla@columbia.edu` in most scenarios.
- Use `sk5057@columbia.edu` as the visible From address only when the user explicitly requests it or the specific context requires the primary mailbox identity.
- Before relying on the Columbia send-as identity on a newly configured machine/account, verify that Gmail reports it as accepted. Sending remains separately approval-gated.

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
- Treat GCP `research-cpu-01` as the canonical Personal OS and cloud
  control-plane machine. Its canonical repository is
  `/srv/research/pro/personal_os`; `~/pro/personal_os` resolves there.
- For new Personal OS Codex tasks or chat threads, use the saved project's main
  checkout directly by default. Task folders already isolate work; do not create
  a Personal OS worktree merely because the repository is Git-backed. Create a
  worktree only when the user explicitly requests one or when a concrete branch
  or working-tree conflict makes isolation necessary; state that exception
  before creating it.
- Treat `sourya-mac` as the primary interactive workstation and a synchronized
  Personal OS client, not the canonical server-side checkout.
- Treat the three former Azure VM definitions, four managed disks, and their
  NIC/public-IP/NSG/VNet shells as deleted under ZON-219 Plans v15C/v15D
  (July 24, 2026). Do not assume they can be started, reattached, or reached
  through old Azure IPs. Recovery now uses canonical GCP state, the encrypted
  GCS archive, and retained Zone/WhatsApp Azure Backup points.
- Prefer reusable, machine-agnostic paths (`~/pro/...`) over machine-specific absolute paths
- For data-heavy projects, experiments, or tasks, prefer creating the project/work directory under `~/pro/lab/` so new large datasets, artifacts, checkpoints, and generated outputs land on the dedicated data disk by default.
- When a task needs cloud actions from the CLI, consult `~/pro/personal_os/context/cloud-access.md` first. Treat it as the shared runbook for current Azure/AWS/GCP access patterns, trusted machine context, verification commands, and other cross-machine cloud CLI notes before assuming auth is already in place or changing login state.

## Local Screenshot Payloads

- When the user pastes a payload beginning with `screenshot-info:`, treat it as a durable local screenshot reference, not as prose to summarize. Also support the legacy `screenshot-local:` payload format.
- Current payloads are intentionally compact:
  - `machine`: SSH host alias for the machine that has the file, such as `sourya-mac`
  - `path`: absolute path to the screenshot on that machine
- If you are running on the same machine as the screenshot path, copy the file directly into the active task's `user_inputs/input_artifacts/`.
- If you are running on another machine, treat `machine` as the SSH host and retrieve the image with SSH/SCP into the active task's `user_inputs/input_artifacts/`, for example:
  - `mkdir -p user_inputs/input_artifacts`
  - `scp 'sourya-mac:/Users/sourya4/Pictures/Screenshots/example.png' user_inputs/input_artifacts/`
- If `machine` is not a working SSH alias, consult `~/pro/personal_os/context/machine-ssh-aliases.md` and `~/.ssh/config` to find the right alias. For legacy payloads, prefer `ssh_host` when present.
- After copying the image, update `user_inputs/input_artifacts/index.md` with the source payload details, capture time, and local artifact path.
- Prefer analyzing the captured local artifact over asking for or relying on an expiring S3 URL. If SSH/SCP fails and no local path is reachable, ask for the S3 URL or a fresh payload.

## External Link Access

- If a user-provided link, task-input link, or discovered link appears material to the task but you cannot access its content with the available tools, do not skip it silently or proceed as if the content was known.
- Tell the user which link could not be accessed, briefly state what failed or what permission/auth/context is missing, and explain why the missing content may matter.
- When `request_user_input` is available, use it to ask an interactive multiple-choice question before proceeding. Offer options such as: the user can paste or upload the content, the agent can retry through another available route, or the agent can proceed without that content while recording the limitation.
- If an interactive question tool is unavailable, ask the same choice clearly in chat and wait when the inaccessible content is important to the outcome.

## Shell Environment (two-layer bootstrap)

Botfiles uses a two-layer shell model:

- **`.botenv`** — Non-interactive-safe core: secrets, PATH (`$BOTFILES_ROOT/bin`, `~/.local/bin`, Homebrew/Linuxbrew bins, `/usr/local/bin`), `BOTFILES_ROOT`, `EDITOR`, `TERM`, `UV_BIN`. Sourced for ALL shell contexts (interactive, SSH commands, agent exec, cron). This is what non-interactive scripts and hooks should source.
- **`.botrc`** — Interactive layer: sources `.botenv`, then adds aliases (`cc`, `bedcc`, `zj`), shell modules (`20-ssh-workflows.sh`, `30-oracle.sh`), and functions (`oracle`, `work-ml`) on top of the shared executable wrappers.

`.botenv` should prefer `nvim` for `EDITOR`, `VISUAL`, and `GIT_EDITOR` when Neovim is installed, falling back to `vim` otherwise.

When writing scripts, hooks, or runner wrappers that need botfiles env in a non-interactive context, source `.botenv` (not `.botrc`) for a lighter, safer load. The Codex notify hook (`codex/hooks/run-codex-notify.sh`) is an example — it sources `.botrc` for historical reasons but only needs `.botenv`.

On **bash** machines, `BASH_ENV` is set in the effective login file (`~/.bash_profile` > `~/.bash_login` > `~/.profile`, whichever bash reads first) to point to `.botenv`, so children of login shells automatically inherit the core env. On **zsh** machines, `~/.zshenv` sources `.botenv` directly.

## Codex Configuration Layers

- Keep portable authored Codex defaults in
  `~/pro/botfiles/codex/config.system.toml`; expose that file through the
  root-owned `/etc/codex/config.toml` symlink.
- Keep `~/.codex/config.toml` as a regular mode-`0600` machine-local file for
  project trust, runtime/app state, native plugin installation, marketplace
  materializations, credentials, and host-only integrations.
- Do not symlink the user config into botfiles, union trust paths across hosts,
  copy plugin caches, or use a Git clean filter/generated active config.
- Use `bin/install-codex-system-config` only for the system-link action and the
  `sync-botfiles-machines` verifier for redacted layer checks.
- Keep sibling profile files explicit; `CODEX_HOME` is for test isolation, not
  production host routing.

## Skills

- Codex skills are stored in `~/pro/botfiles/codex/skills`
- `setup.sh` symlinks `~/.codex/skills` to that folder
- Codex custom agents are stored in `~/pro/botfiles/codex/agents`
- `setup.sh` symlinks `~/.codex/agents` to that folder
- Keep Codex/Claude skill counterparts aligned to avoid drift
- Codex system skills in `~/.codex/skills/.system/` are machine-managed and should not be source-controlled in `botfiles`

## Curated Skills

- Keep upstream curated skill directories unchanged unless you are intentionally creating a protected local fork.
- For the curated `pdf` skill, do not hand-edit files under `~/pro/botfiles/codex/skills/pdf/` for local workflow preferences; keep that directory pullable from upstream.
- Put local PDF workflow preferences in `AGENTS.md` / `CLAUDE.md`, `README.md`, and `setup.sh`, not inside the curated skill directory.
- Treat Poppler CLI tools (`pdfinfo`, `pdftoppm`, `pdftotext`) as machine-level prerequisites handled via botfiles setup/docs.
- When a PDF task needs Python packages such as `reportlab`, `pdfplumber`, or `pypdf`, prefer task-local scratchpad scripts run with `uv run --with ...` instead of installing those packages into the active project's environment.

## Oracle Skill

- `~/pro/botfiles/codex/skills/oracle` and `~/pro/botfiles/claude/skills/oracle` are local Oracle workflow skills derived from `steipete/oracle/skills/oracle`; they intentionally include local GPT-5.6 Sol + Pro browser defaults, so do not overwrite them from upstream without reapplying the local policy.
- Keep the Oracle skill copies, `AGENTS.md` / `CLAUDE.md`, the Oracle awaiter agents, and the botfiles shell wrapper aligned when Oracle defaults change.
- On machines where the default Node runtime is below 24, use the local `oracle` and `oracle-mcp` wrappers from `~/pro/botfiles/bin/` (symlinked into `~/.local/bin` by `setup.sh` and also loaded as shell functions from `~/pro/botfiles/.botrc`) instead of raw `npx -y @steipete/oracle`.
- For no-model browser requests, the local wrapper prefers the verified pinned PR #320 source build at `~/pro/lab/tools/oracle-main` when present at the expected commit and otherwise uses `@steipete/oracle@latest` with the same GPT-5.6 Sol target. Use `ORACLE_SOURCE_MAIN=0` to force npm, `ORACLE_SOURCE_MAIN=require` to fail instead of falling back, and `ORACLE_SOURCE_MAIN_VERBOSE=1` to print the selected route. Do not vendor the upstream repo into botfiles; rebuild it in `~/pro/lab/tools/oracle-main` with Node 24/pnpm when the pinned commit changes.
- In this environment, default Oracle requests with no explicit engine/model must use ChatGPT GPT-5.6 Sol with the account/UI Intelligence effort set to Pro through the local wrapper. Pro is a separate ChatGPT effort, not a `gpt-5.6-pro` CLI model identifier. The wrapper should expand plain `oracle -p "<prompt>" [--file ...]` to `--engine browser --model gpt-5.6-sol --browser-model-strategy select`, reusing the verified local Chrome endpoint at `127.0.0.1:9223` when available and otherwise using browser manual-login mode with `"$HOME/pro/botfiles/bin/oracle-chrome-linux"`.
- If the user explicitly asks for another model, engine, a multi-model run, or a faster/cheaper pass, honor that. Otherwise do not silently downgrade the no-model default from GPT-5.6 Sol + Pro to GPT-5.5/5.4 or an API route. Fix or surface browser/profile/canary problems and retry the same target.
- For browser runs with text/source-code context, prefer compact prompts or inline file delivery (`--browser-inline-files` / `--browser-attachments never`) before ChatGPT upload mode. Reserve upload/bundle mode for PDFs, images, binaries, or file sets that truly cannot fit inline.
- Be explicit about engine/model choice. Prefer the local `oracle` wrapper so the intended defaults are applied unless you are intentionally overriding them.
- For default GPT-5.6 Sol + Pro browser runs, keep Oracle in the main thread unless the user explicitly asks for the `oracle_awaiter` custom subagent. Do not ask an extra confirmation question just to use the default Oracle path. If `oracle_awaiter` is used, it should launch the same GPT-5.6 Sol + Pro browser/default wrapper path and apply the same no-silent-downgrade rule.
- When `oracle_awaiter` owns the run, let it own exactly one Oracle session. Do not interrupt it for latency alone, and do not redirect it to a new model, prompt, or second Oracle run unless the user explicitly asks or the Oracle session reaches `error`.
- For GPT-5.6 Sol + Pro browser runs, treat 10-15 minutes as common, 15-40 minutes as a normal slow run, and up to 60 minutes as within tolerance. `in_progress` is not failure.
- If the Oracle result is needed for the next step, wait or reattach until the session reaches `completed` or `error`. If a polling shell dies or `stdin` closes, restart polling against the same slug; that is not Oracle failure. Skip waiting only when the user explicitly says not to wait.
- If the foreground waiter misses a visibly completed GPT-5.6 response, use `oracle session <slug> --harvest` against the same bound tab before treating the run as failed or starting another run.
- When giving timing context, quote local Oracle evidence (`oracle status`, `meta.json`, `output.log`) instead of guessing.
- Prefer the local `oracle` wrapper over raw `npx -y @steipete/oracle`; the wrapper is the supported path for this machine's Node/runtime setup and should enforce the intended default engine/model behavior.
- On Linux/SSH shells without `DISPLAY`, the local `oracle` wrapper auto-runs explicit browser-mode requests under `xvfb-run` so Chrome can launch headfully.
- Browser mode still requires a signed-in ChatGPT Chrome profile, inline cookies, or a configured remote Oracle browser host; `xvfb-run` only fixes the display/launch side.
- For shell-wide API auth outside repos that provide their own `.env`, keep the default Azure Oracle route in `~/pro/botfiles/secrets/local/codex-azure.rc` and keep `~/pro/botfiles/secrets/local/codex-openai.rc` only for direct OpenAI fallback. Oracle also auto-loads a repo-local `.env` when present, so local repo runs do not require extra shell exports.
- On non-Pro models, pass an explicit `--timeout` or use background mode for long Oracle runs instead of relying on `auto`.

## Reviewer Agent

- Use the read-only `reviewer` custom agent at `~/pro/botfiles/codex/agents/reviewer.toml` (synced to `~/.codex/agents/reviewer.toml`) for PR or working-tree review focused on correctness, security, regressions, and missing tests.

## Native Subagent Reasoning

- Whenever spawning a native GPT-5.6 Sol, Terra, or Luna subagent, always set its reasoning effort to `max`. Do not use lower reasoning levels for those model families, including for explorers, workers, or reviewers.

## Task Status Files

- Use the `save-task-status` skill proactively at milestones, before context switches, and before ending a session
- Use `get-task-details` to retrieve current status path plus linked issue, machine, coding-agent session id, and zellij context
- Use the `finish-task` skill when the user wants the standard wrap-up flow for a tracked task: gate on actual closeout readiness, sync status/tracker notes, handle any required downstream heads-up, and clean branches/worktrees only after confirmation. As part of finish-task cleanup, switch relevant repo checkouts back to the updated default branch (usually `main`) when safe; if local state makes that ambiguous, prompt the user to approve or skip the branch switch.
- Use the `continue-task` skill when taking over an interrupted tracked task from a previous session; resolve the existing task home first, sync that `status.md` to the current session, and use transcript tail only as fallback before resuming work
- Use the `start-new-task` skill to continue past scaffolding when enough information is already available: gather tracker/local context, ask targeted interactive questions only for critical planning gaps, and present a written first-pass plan for approval instead of stopping at a generic “continue into planning?” prompt
- When `start-new-task` is invoked without an existing GitHub/Linear tracker, create a new Linear ticket and use it as the tracker by default, unless the user explicitly asks for local-only/no-tracker work or names another tracking destination. If Linear creation is unavailable, record degraded local-only mode and tell the user.
- Save task state in date/task folders (default: `context/daily/YYYY-MM-DD/<task-slug>/`)
- New folders use time-prefixed names: `<HH>h<MM>m<SS>sPST-<task-slug>` (e.g., `21h45m59sPST-fix-auth-timeout`)
- Full path example: `context/daily/2026-02-24/21h45m59sPST-fix-auth-timeout/`
- All timestamps in task files use PST explicitly — use `TZ=America/Los_Angeles date` for reliable PST regardless of system timezone
- Format timestamps as: `YYYY-MM-DD ~HH:MMam/pm PST`
- Legacy folders without time prefix continue to work unchanged
- Save generated artifacts under `task-progress-artifacts/`, keeping curated outputs at the top level and raw/intermediate material under `task-progress-artifacts/scratchpad/`
- Keep task input context under `user_inputs/`, with Markdown notes at the root and non-Markdown files in `user_inputs/input_artifacts/`
- Set `SYSTEM_NAME` in `~/pro/botfiles/secrets/local/machine.rc` so task metadata and notifications identify the machine consistently
- Set `BOT_MACHINE_SSH_ALIAS` in `~/pro/botfiles/secrets/local/machine.rc` to the SSH alias other machines should use for this machine; screenshot payloads use this as their compact `machine` value

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

## Cross-Session Orchestration

- For regular non-Symphony multi-session work, prefer the shared skills `cross-session-context`, `cross-session-message`, and `pr-autoreview-loop`.
- Target other sessions by tracker ref or task slug first. Use `--task-dir`, `--status-file`, or `--zellij-session` only for lower-level or debug workflows.
- Treat task/status metadata as the primary source of truth, transcript tail as a targeted fallback, and live zellij inspection as diagnostic context.
- When running inside Codex Desktop and the target is another Codex Desktop thread, use the `codex_app` thread tools (`list_threads`, `read_thread`, `send_message_to_thread`) instead of zellij. Omit model/thinking overrides unless explicitly requested.
- When renaming a Codex Desktop thread, use the native `codex_app.set_thread_title` tool. Omit `threadId` for the calling thread; pass an exact thread id for another thread. Prefer `<tracker id>: <natural-language title>`, or `[no ticker]: <natural-language title>` when no tracker exists. Do not edit Codex SQLite/JSONL state or ask for a UI refresh; if the native tool is unavailable, skip the rename instead of emulating it.
- Codex CLI and Claude Code should not assume they can message Codex Desktop threads unless an explicit app/tool bridge is available. Do not write SQLite state, JSONL logs, or notification proxy state to simulate a human prompt.
- Keep cross-session sends preview-first. `send-zellij-message` should stay in dry-run mode until the resolved session/tab target is clearly correct; use `--execute` and `--submit enter` explicitly.
- For long or multiline Codex prompts, `send-zellij-message` now adds a delayed confirm Enter automatically after `--submit enter` because one immediate Enter can leave the prompt staged in the composer.
- Do not use cross-session message send as remote control. It is for bounded prompt delivery into a known live target only.
- For PR-bearing non-Symphony review loops, use `pr-autoreview-loop` to match current-head reviewer output, address findings, push, and wait again until the sweep is clean or genuinely blocked.
- When the PR loop reports `blocked`, or reviewer/check infrastructure fails without an in-session retry path, stop and ask for human input instead of silently spinning.

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

## Diagram Authoring (default: Figma)

- For article/blog/explanatory diagrams and similar polished visual figures, **default to authoring natively in Figma** via the Figma MCP, not by generating an SVG/PIL/Mermaid/D2 file and replicating it afterward. The user evaluated PIL, D2, Mermaid, hand-SVG, Excalidraw, and Figma for editorial diagrams (ZON-227, 2026-06-25) and chose Figma: best output quality plus first-class human editability (real text nodes to retype, shapes/curves to drag, full typographic control).
- Build directly in a Figma file (real TEXT nodes, vector curves, shapes) and iterate with a screenshot→critique→fix loop.
- Watching the user's edits is **pull-on-demand, not live**: after the user edits, re-read the file when they say to look. There is no push/webhook; do not assume notification of changes.
- Reach for code-first diagram tools (SVG/PIL) only when the user needs bulk generation, regeneration-from-data, or a git-diffable source of truth — and even then offer "import into Figma as editable" as the final step.
- Tool-reliability notes live in the ZON-227 artifacts under the ZON-223 task folder (`claude-diagram-style-iteration/`).
- Excalidraw gotcha if ever used: its dark background is a canvas app-setting (`viewBackgroundColor`) that does NOT travel through element export/import — bake a background rectangle into the elements instead.
