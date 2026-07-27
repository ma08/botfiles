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

## Paths and Storage Conventions

- For data-heavy projects, experiments, or tasks, prefer creating the project/work directory under `~/pro/lab/` so new large datasets, artifacts, checkpoints, and generated outputs land on the dedicated data disk by default.

## Shell Environment (two-layer bootstrap)

Botfiles uses a two-layer shell model:

- **`.botenv`** — Non-interactive-safe core: secrets, PATH (`$BOTFILES_ROOT/bin`, `~/.local/bin`, Homebrew/Linuxbrew bins, `/usr/local/bin`), `BOTFILES_ROOT`, `EDITOR`, `TERM`, `UV_BIN`. Sourced for ALL shell contexts (interactive, SSH commands, agent exec, cron). This is what non-interactive scripts and hooks should source.
- **`.botrc`** — Interactive layer: sources `.botenv`, then adds aliases (`cc`, `bedcc`, `zj`), shell modules (`20-ssh-workflows.sh`, `30-oracle.sh`), and functions (`oracle`, `work-ml`) on top of the shared executable wrappers.

`.botenv` should prefer `nvim` for `EDITOR`, `VISUAL`, and `GIT_EDITOR` when Neovim is installed, falling back to `vim` otherwise.

When writing scripts or hooks that need botfiles env in a non-interactive context, source `.botenv` (not `.botrc`) for a lighter, safer load.

On **bash** machines, `BASH_ENV` is set in the effective login file (`~/.bash_profile` > `~/.bash_login` > `~/.profile`, whichever bash reads first) to point to `.botenv`, so children of login shells automatically inherit the core env. On **zsh** machines, `~/.zshenv` sources `.botenv` directly.

## Shared Cloud CLI Context

- When a task needs cloud actions from the CLI, read `~/pro/personal_os/context/cloud-access.md` first.
- Treat that file as the shared runbook for current Azure/AWS/GCP access patterns, trusted machine context, verification commands, and other cross-machine cloud CLI notes.
- Use the `~/pro/...` path form when referring to it, and consult it before assuming cloud auth is already available or changing login state on a machine.
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
- When `AskUserQuestion` or another interactive question tool is available, use it to ask an interactive multiple-choice question before proceeding. Offer options such as: the user can paste or upload the content, the agent can retry through another available route, or the agent can proceed without that content while recording the limitation.
- If an interactive question tool is unavailable, ask the same choice clearly in chat and wait when the inaccessible content is important to the outcome.

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
- If the Oracle result is needed for the next step, prefer the foreground `oracle-awaiter` custom subagent and invoke it explicitly when you want to guarantee that path. Let it own one Oracle run and wait for a terminal status before handing the result back. The subagent should launch the same GPT-5.6 Sol + Pro browser/default wrapper path and apply the same no-silent-downgrade rule.
- Do not rerun, shorten the prompt, or downgrade the model for latency alone.
- For GPT-5.6 Sol + Pro browser runs, treat 10-15 minutes as common, 15-40 minutes as a normal slow run, and up to 60 minutes as within tolerance. `in_progress` is not failure.
- If Oracle stays in the main thread, wait or reattach until the session reaches `completed` or `error`. If a polling shell dies or `stdin` closes, restart polling against the same slug; that is not Oracle failure. Skip waiting only when the user explicitly says not to wait.
- If the foreground waiter misses a visibly completed GPT-5.6 response, use `oracle session <slug> --harvest` against the same bound tab before treating the run as failed or starting another run.
- When giving timing context, quote local Oracle evidence (`oracle status`, `meta.json`, `output.log`) instead of guessing.
- Prefer the local `oracle` wrapper over raw `npx -y @steipete/oracle`; the wrapper is the supported path for this machine's Node/runtime setup and should enforce the intended default engine/model behavior.
- On Linux/SSH shells without `DISPLAY`, the local `oracle` wrapper auto-runs explicit browser-mode requests under `xvfb-run` so Chrome can launch headfully.
- Browser mode still requires a signed-in ChatGPT Chrome profile, inline cookies, or a configured remote Oracle browser host; `xvfb-run` only fixes the display/launch side.
- For shell-wide API auth outside repos that provide their own `.env`, keep the default Azure Oracle route in `~/pro/botfiles/secrets/local/codex-azure.rc` and keep `~/pro/botfiles/secrets/local/codex-openai.rc` only for direct OpenAI fallback. Oracle also auto-loads a repo-local `.env` when present, so local repo runs do not require extra shell exports.
- On non-Pro models, pass an explicit `--timeout` or use background mode for long Oracle runs instead of relying on `auto`.

## Reviewer Agent

- Use the read-only `reviewer` custom subagent at `~/pro/botfiles/claude/agents/reviewer.md` (synced to `~/.claude/agents/reviewer.md`) for PR or working-tree review focused on correctness, security, regressions, and missing tests.

## Native Subagent Reasoning

- Whenever spawning a native GPT-5.6 Sol, Terra, or Luna subagent, always set its reasoning effort to `max`. Do not use lower reasoning levels for those model families, including for explorers, workers, or reviewers.

## Task Status Tracking

When working on any task, **proactively** maintain task status documentation.

### Proactive Behavior
- **At task start**: Use `/start-new-task` to scaffold a task folder with `status.md`, `user_inputs/initial.md`, `user_inputs/input_artifacts/`, `task-progress-artifacts/`, and `task-progress-artifacts/scratchpad/`. When no GitHub/Linear tracker exists, create a new Linear ticket and use it as the tracker by default unless the user explicitly asks for local-only/no-tracker work or names another tracking destination; if Linear creation is unavailable, record degraded local-only mode and tell the user. For interrupted tracked resumes from another session, use `/continue-task` instead. Keep `/save-task-status` for checkpoint updates once the current session already owns the task. When enough context is already available, keep going in the same turn: gather tracker/local context, ask `AskUserQuestion` only for critical planning gaps, and present a first-pass written plan for approval instead of stopping at boilerplate setup.
- **At any checkpoint**: Use `/get-task-details` to retrieve the active status path plus issue/machine/coding-agent session metadata.
- **At closeout**: Use `/finish-task` when the user wants the standard end-of-task flow: resolve the current task, gate on real merge/closeout readiness, sync tracker notes/state, handle required downstream heads-up, and clean branches/worktrees only after explicit confirmation. As part of cleanup, switch relevant repo checkouts back to the updated default branch (usually `main`) when safe; if local state makes that ambiguous, prompt the user to approve or skip the branch switch.
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
- **Machine identity**: Set `SYSTEM_NAME` in `~/pro/botfiles/secrets/local/machine.rc` so metadata and notifications remain consistent across workflows. Set `BOT_MACHINE_SSH_ALIAS` there to the SSH alias other machines should use for this machine; screenshot payloads use it as their compact `machine` value.
- **Legacy folders**: Existing folders without time prefix or `user_inputs/` continue to work unchanged.

## Cross-Session Orchestration

- For regular non-Symphony multi-session work, prefer the shared skills `cross-session-context`, `cross-session-message`, and `pr-autoreview-loop`.
- Target other sessions by tracker ref or task slug first. Use `--task-dir`, `--status-file`, or `--zellij-session` only for lower-level or debug workflows.
- Treat task/status metadata as the primary source of truth, transcript tail as a targeted fallback, and live zellij inspection as diagnostic context.
- When running inside Codex Desktop and the target is another Codex Desktop thread, use the `codex_app` thread tools (`list_threads`, `read_thread`, `send_message_to_thread`) instead of zellij. Omit model/thinking overrides unless explicitly requested.
- Codex CLI and Claude Code should not assume they can message Codex Desktop threads unless an explicit app/tool bridge is available. Do not write SQLite state, JSONL logs, or notification proxy state to simulate a human prompt.
- Keep cross-session sends preview-first. `send-zellij-message` should stay in dry-run mode until the resolved session/tab target is clearly correct; use `--execute` and `--submit enter` explicitly.
- For long or multiline Codex prompts, `send-zellij-message` now adds a delayed confirm Enter automatically after `--submit enter` because one immediate Enter can leave the prompt staged in the composer.
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
Whenever you are creating any visual artifact (website, image, TUI, video etc.) let's always put in effort to pick a unique theme and style that showcases taste, craft, and nuance for the person, project, situation etc. VERY IMPORTANT.

Since the user is a startup founder, by default, use the startup's branding and design aesthetics found at `~/pro/personal_os/context/zone/ZONE_FRONTEND_STYLE_GUIDE.md`

Always make sure to ask suitable questions to the user for design aesthetics if needed to confirm before implementing.

### Diagram Authoring (default: Figma)

For article/blog/explanatory diagrams and similar polished visual figures, **default to authoring natively in Figma** via the Figma MCP (`use_figma`), not by generating an SVG/PIL/Mermaid/D2 file and replicating it afterward. The user evaluated PIL, D2, Mermaid, hand-SVG, Excalidraw, and Figma for editorial diagrams (ZON-227, 2026-06-25) and chose Figma: best output quality plus first-class human editability (real text nodes to retype, shapes/curves to drag, full typographic control).

- Build directly in a Figma file: real TEXT nodes, vector curves, shapes; iterate with the screenshot→critique→fix loop using `get_screenshot`.
- Watching the user's edits is **pull-on-demand, not live**: after the user edits, re-read with `get_screenshot` / `get_metadata` / `get_design_context` when they say to look. There is no push/webhook; do not assume you'll be notified of changes.
- Reach for code-first diagram tools (SVG/PIL) only when the user needs bulk generation, regeneration-from-data, or a git-diffable source of truth — and even then, offer "import into Figma as editable" as the final step.
- The reliability of each tool for editorial diagrams is documented in the ZON-227 artifacts under the ZON-223 task folder (`claude-diagram-style-iteration/`).
- Excalidraw gotcha if ever used: its dark background is a canvas app-setting (`viewBackgroundColor`) that does NOT travel through element export/import — bake a background rectangle into the elements instead.
