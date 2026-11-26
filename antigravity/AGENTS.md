# Antigravity Global Instructions

These are user-level instructions for Google Antigravity shared across projects and sessions via:

- `~/pro/botfiles/antigravity/AGENTS.md` (symlinked to `~/.gemini/config/AGENTS.md` by `setup.sh`)
- `~/pro/botfiles/antigravity/rules/*.md` (symlinked to `~/.gemini/config/rules/` by `setup.sh` for on-demand domain playbooks)

## Persistent Global Preferences

- For any long-lived behavior preference that applies across projects and sessions, update all three global instruction surfaces together: `~/pro/botfiles/antigravity/AGENTS.md` (or the relevant file in `~/pro/botfiles/antigravity/rules/`), `~/pro/botfiles/codex/AGENTS.md`, and `~/pro/botfiles/claude/CLAUDE.md`.
- Keep every single Antigravity rule file strictly under 24,000 bytes so Antigravity never truncates it silently.
- If a preference changes a skill's behavior or workflow, edit the canonical copy in `~/pro/botfiles/codex/skills/` (which Antigravity loads through `~/.gemini/config/skills.json` -> `botfiles-skills`) and mirror to `~/pro/botfiles/claude/skills/` when a Claude counterpart exists.
- If a preference is only for one repo, one task, or a temporary session, keep it in local project instructions or task notes instead of global botfiles.

## Partner Mindset and Human Writing Style

- Provide constructive criticism. Be a pragmatic partner in getting high-quality work done, not a sycophant.
- In user-facing prose and drafts, never use em dashes. Rewrite with periods, commas, parentheses, or colons. Preserve em dashes only inside exact quotations, source text, code, identifiers, or data that must remain unchanged.
- Write plainly and naturally. Lead with the concrete point, use contractions when they fit, vary sentence length, and match the user's own voice when a writing sample is available.
- Avoid common AI writing patterns: formulaic openings and closings, vague attribution, promotional inflation, canned transitions, forced three-part lists, conspicuous synonym cycling, excessive headings or bold text, and overly uniform sentence rhythm.
- Do not simulate humanity with invented anecdotes, fake opinions, unnecessary slang, or deliberate mistakes. Preserve meaning, facts, and precision.

## GitHub Authorship

- Any GitHub write performed by a coding agent (new or edited issues, PRs, reviews, comments, or similar actions) must use the authenticated human developer account from the default GitHub auth flow rather than a separate bot identity.
- Add a short byline naming the coding agent in the written GitHub content. Preferred examples:
  - `_Written by Antigravity via the developer's authenticated GitHub account._`
  - `_Written by Codex via the developer's authenticated GitHub account._`
  - `_Written by Claude Code via the developer's authenticated GitHub account._`
- If a GitHub action has no natural body field, put the attribution in the nearest editable text field or a companion comment. When editing existing agent-authored GitHub content, preserve or refresh the byline so the latest agent remains visible.

## Google Workspace Defaults

- The `columbia` `gws` account alias authenticates `sk5057@columbia.edu`, but outbound drafts and messages from that mailbox should default to the verified send-as address `sourya.kakarla@columbia.edu` in most scenarios. Use `sk5057@columbia.edu` as the visible From address only when explicitly requested or required.
- Before relying on the Columbia send-as identity on a newly configured machine/account, verify Gmail accepts it. Sending remains separately approval-gated.
- On `research-gpu-01`, Google Workspace CLI access is independently authorized under `~/.config/gws` with explicit aliases (`gws-account work`, `gws-account personal`, `gws-account columbia`) and no implicit default account. Use `gws-calendar-safe` with exact preview/hash approval for Calendar writes and `gws-gmail-draft` for explicit drafts. `gws-cpu` is only an explicit CPU-dependent fallback, never an automatic failover.

## Manual Linear Workflow Policy

- For manual coding-agent sessions outside Symphony automation, use this shared Linear workflow policy unless the repo or task has an explicit local override:
- `Review` is the default handoff state when implementation is ready for human review. Move the issue to `Review` and leave a reviewer-facing comment covering what changed, what was verified, and any open risks, questions, or asks.
- Do not move directly from active implementation to `Done` just because the agent believes work is finished. `Done` is reserved for explicit final acceptance (human approval, merge completion, or another clear completion signal).
- Use `Needs Input` when progress is blocked on an external decision, missing information, or another party's response, and state in the comment what is missing, who owns it, and what resumes once answered.
- Use `Rework` when review feedback, failed validation, or another concrete signal requires another implementation pass by the agent.
- Use `Merging` only after the work is effectively approved and only landing/merging or release housekeeping remains.
- If a Linear workspace lacks one of these states, use the nearest equivalent and note the mismatch in the comment.

## Paths and Machine Topology

- Prefer reusable, machine-agnostic paths (`~/pro/...`) over machine-specific absolute paths.
- Assume `botfiles` lives at `~/pro/botfiles` and Personal OS lives at `~/pro/personal_os`.
- For data-heavy projects, experiments, weights, datasets, checkpoints, or generated outputs, prefer creating the directory under `~/pro/lab/` so large artifacts land on the dedicated data disk.
- Treat GCP `research-cpu-01` as the canonical Personal OS and cloud control-plane machine (`/srv/research/pro/personal_os`, resolved via `~/pro/personal_os`). Treat `sourya-mac` as the primary interactive workstation and a synchronized client.
- For new Personal OS tasks or chats, use the saved project's main checkout directly by default; task folders already isolate work. Create a Git worktree only when explicitly requested or when a concrete branch/working-tree conflict makes isolation necessary (state the exception first).
- Legacy Azure VMs, managed disks, and network shells from ZON-219 were deleted on July 24, 2026; do not reference old Azure IPs (recovery uses canonical GCP state, the encrypted GCS archive, and retained Azure Backup points).
- Before running cloud CLI actions, read `~/pro/personal_os/context/cloud-access.md` first for current Azure/AWS/GCP access patterns and verification commands.

## GPU Independent Daily Work (`research-gpu-01`)

- `research-gpu-01` is set up for daily agent work even while `research-cpu-01` is off. On GPU, prefer GPU-local projects, files, browser, Oracle, Google Workspace (`gws-account`), and cloud CLIs; do not introduce an automatic CPU SSH dependency.
- Keep data and tool environments under `~/pro/lab` (`/srv/research` managed data disk); local NVMe and `/mnt` are disposable.
- GPU cloud CLI logins are independent, machine-local credentials. Never copy CPU browser/OAuth stores, private keys, or GCE metadata tokens; missing or expired logins require fresh authorization.
- Project workspaces on GPU live under `~/pro/` (data-backed under `~/pro/lab/`); follow each workspace's local guide. Existing CPU chats and live CPU-owned services remain CPU-owned.
- Keep notebooks and local model servers on loopback and access them over authenticated SSH tunnels; never publish desktop or model ports publicly. Coordinate reboots, deallocation, or shared-service changes with ZON-389 and active compute owners.

## Local Screenshot Payloads

- When the user pastes a payload beginning with `screenshot-info:` (or legacy `screenshot-local:`), treat it as a durable local screenshot reference, not prose to summarize.
- Compact payloads contain `machine` (SSH host alias, such as `sourya-mac`) and `path` (absolute path on that machine).
- If running on the same machine, copy the file directly into the active task's `user_inputs/input_artifacts/`. Otherwise retrieve it via SCP (`scp '<machine>:<path>' user_inputs/input_artifacts/`). If `machine` is not a working SSH alias, check `~/pro/personal_os/context/machine-ssh-aliases.md` and `~/.ssh/config` (or `ssh_host` for legacy payloads).
- Update `user_inputs/input_artifacts/index.md` with source details, PST capture time, and local artifact path. Prefer the captured local artifact over expiring S3 URLs; ask for an S3 URL or fresh payload only if SSH/SCP fails and no local copy is reachable.

## External Link Access

- If a user-provided, task-input, or discovered link appears material to the task but cannot be accessed with available tools, never skip it silently or assume its contents.
- Tell the user which link failed, briefly state what error/permission/context is missing, and explain why it matters.
- Use `ask_question` (or the active harness's interactive question tool) to offer concrete choices: user pastes/uploads content, agent retries another route, or agent proceeds without it while recording the limitation. If no interactive question tool is available, ask in chat and wait when the content is important.

## Shell Environment (Two-Layer Bootstrap)

- **`.botenv`**: Non-interactive-safe core (`PATH`, secrets, `BOTFILES_ROOT`, `EDITOR`, `TERM`, `UV_BIN`). Source `.botenv` (not `.botrc`) in scripts, hooks, and non-interactive wrappers. Prefer `nvim` for `EDITOR`/`VISUAL`/`GIT_EDITOR` when installed, falling back to `vim`.
- **`.botrc`**: Interactive layer sourcing `.botenv` plus aliases, shell modules, and functions.
- On bash machines, login files set `BASH_ENV` to `.botenv`; on zsh machines, `~/.zshenv` sources `.botenv`.

## Skills and Curated Upstream Policy

- Global custom skills live in `~/pro/botfiles/codex/skills/` and are exposed to Antigravity through `~/.gemini/config/skills.json` -> `botfiles-skills` (with exclusions for harness-specific or plugin-overlapping skills).
- Keep upstream curated skill directories unchanged unless intentionally creating a protected local fork. For the curated `pdf` skill, keep `~/pro/botfiles/codex/skills/pdf/` pullable from upstream; treat Poppler tools (`pdfinfo`, `pdftoppm`, `pdftotext`) as machine prerequisites and prefer `uv run --with ...` scratchpad scripts for Python packages (`reportlab`, `pdfplumber`, `pypdf`).

## Design Aesthetics Guidelines

- When creating any visual artifact (website, image, TUI, video, or interactive UI), invest effort into a cohesive theme and craft tailored to the project and audience.
- For Zone or default founder work, follow `~/pro/personal_os/context/zone/ZONE_FRONTEND_STYLE_GUIDE.md`. Ask brief clarifying questions on visual direction when helpful before implementing.

## Developer Messaging

- When monitoring long-running processes or hitting blockers while the developer may be away, proactively send a WhatsApp update using the `message-developer` skill (state changes, milestones, errors, or ending with important pending state).
- Do not send WhatsApp messages during active back-and-forth interaction or on every polling iteration; hooks already handle normal turn completion and questions.

## Ad-hoc Scripts (Required)

- Before running one-off Python or Bash scripts, write the script into the active task's `task-progress-artifacts/scratchpad/` folder with a short header comment explaining purpose, inputs, and outputs, then execute it. Prefer saved scripts over inline heredocs for reproducibility.

## Task Status Files and Plan Acceptance

- Proactively maintain task state across the lifecycle:
  - `start-new-task`: scaffold a new task folder (`status.md`, `user_inputs/initial.md`, `user_inputs/input_artifacts/`, `task-progress-artifacts/`, `task-progress-artifacts/scratchpad/`). When no GitHub/Linear tracker exists, create a Linear ticket by default unless the user asks for local-only work or names another tracker (if Linear is unavailable, record degraded local-only mode and inform the user). Continue past scaffolding in the same turn when enough context is available: gather context, ask `ask_question` only for critical gaps, and present a written first-pass plan.
  - `continue-task`: take over an interrupted tracked task by resolving its existing task home first, syncing `status.md` to the current session, and using transcript tail only as fallback.
  - `save-task-status`: update task state proactively at milestones, before context switches, and before ending a session.
  - `get-task-details`: retrieve current status path plus linked issue, machine, coding-agent session ID, and zellij context.
  - `finish-task`: run the closeout flow (gate on merge/closeout readiness, sync status/tracker notes, check downstream heads-ups, and clean branches/worktrees only after explicit confirmation, switching relevant checkouts back to the updated default branch when safe).
- **Folder layout and timestamps:**
  - Default root: `context/daily/YYYY-MM-DD/<HH>h<MM>m<SS>sPST-<task-slug>/` (override per project via `task-status-root:` in project `AGENTS.md` or `CLAUDE.md`). Slugs are lowercase, hyphenated, and under 50 characters. Legacy folders without time prefixes continue to work unchanged.
  - Use PST explicitly for all task timestamps (`TZ=America/Los_Angeles date`), formatted as `YYYY-MM-DD ~HH:MMam/pm PST`.
  - Machine identity comes from `SYSTEM_NAME` and `BOT_MACHINE_SSH_ALIAS` in `~/pro/botfiles/secrets/local/machine.rc`.
  - `task_status_common.py` auto-detects Antigravity via `ANTIGRAVITY_CONVERSATION_ID` / `ANTIGRAVITY_AGENT` and resolves its `transcript.jsonl`. Pass `--coding-agent antigravity` (and `--agent-session-id <id>`) to `sync_task_metadata.py` only as a fallback when those env vars are absent.

### Plan Acceptance Persistence (Required)

- Persist accepted plans in the active task status file (`status.md`, or legacy `README.md` only when that is the existing status file). Never rely on ephemeral harness plan folders for accepted plan storage.
- Treat a plan as accepted only on explicit acceptance (discrete accept action or explicit approval text), and persist immediately before implementation.
- If no task status file exists yet, create the task folder first and persist `Plan v1`.
- Store accepted plans under `## Accepted Plans` and append versions (`Plan v1`, `Plan v2`, ...), each with PST timestamp, accepted signal, supersedes value, short revision summary, and full accepted plan body.
- Ask a brief clarification before writing if task targeting is ambiguous. When a plan file is saved for review, wait for explicit user approval before starting implementation.

### Input Context and Artifact Handling

- **Immutable text inputs:** Store original prompts, clarifications, and review answers as separate Markdown files directly under `user_inputs/`; add new files instead of overwriting old ones.
- **Captured input artifacts:** Copy/download user-provided or user-referenced files and images into `user_inputs/input_artifacts/`, maintain `user_inputs/input_artifacts/index.md` with local path, original source, PST capture time, and notes, and prefer local references over external URLs.
- **Continuous artifact saving:** Save logs, scripts, errors, and useful outputs under `task-progress-artifacts/` as you go rather than waiting until session end. Keep the top level curated for deliverables and key evidence; use `task-progress-artifacts/scratchpad/` instead of `/tmp` for raw logs, polling snapshots, JSON dumps, and working screenshots.
- **Short-lived S3 URLs:** Download input-context files into `user_inputs/input_artifacts/`; download work-product captures into `task-progress-artifacts/scratchpad/` and promote durable evidence to top-level `task-progress-artifacts/`. Keep task folders self-contained and portable.
