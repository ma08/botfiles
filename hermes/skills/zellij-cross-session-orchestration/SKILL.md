---
name: zellij-cross-session-orchestration
description: Use repo-managed zellij helpers from ~/pro/botfiles to inspect, message, and launch parallel coding-agent task sessions.
---

# Zellij Cross-Session Orchestration

Use this skill when the user wants to work with their zellij-based coding-agent workflows from `~/pro/botfiles`, especially for detached task launches or cross-session coordination.

## Trigger conditions

Load this skill when the user asks to:
- start a side task in another zellij session
- inspect another live task/session
- send a message into another live zellij-backed agent session
- use repo-managed `work-*` / zellij orchestration conventions from `~/pro/botfiles`

## Source of truth

Prefer the repo-managed helpers and docs in `~/pro/botfiles`:
- `README.md`
- `docs/cross-session-orchestration-contract.md`
- `codex/skills/start-zellij-session-for-task/SKILL.md`
- `codex/skills/cross-session-context/SKILL.md`
- `codex/skills/cross-session-message/SKILL.md`

## Core commands

### 1) Launch a detached side-task session

Use when the user wants a second coding-agent run without taking over the current terminal.

```bash
start-zellij-session-for-task --project-root "<project-root>" <linear url|linear id|github issue url|task description>
```

Optional target override:

```bash
start-zellij-session-for-task --project-root "<project-root>" --target ml <...>
```

Raw Codex fallback for hosts without the App Server notification wrappers:

```bash
start-zellij-session-for-task --project-root "<project-root>" --no-codex-app-notify <...>
```

Supported targets from the botfiles docs:
- `here` (default)
- `ml`
- `arya`
- `agent`

Behavior to preserve:
- resolves tracker/slug context with shared task-status tooling
- creates a detached zellij session named from the resolved task slug
- renames the initial tab to `[TRACKER-ID]` when available
- launches Codex through `codex-app-notify-session` into a real spawned pane in the detached session (not only via `options --default-shell`) so attach/dump-screen can verify visible Codex UI and `request_user_input` prompts can notify via the App Server proxy
- clears inherited `CODEX_*` metadata before starting child Codex
- seeds the child session with `$start-new-task <original input>`
- uses `codex-app-notify-session --dangerously-bypass-approvals-and-sandbox` by default; use `--no-codex-app-notify` only as an explicit raw-Codex fallback
- fails early for remote targets if the project root is not present there
- supports `--dry-run` for inspection-only requests
- on current Linux/Zellij behavior, prefer a two-step launch pattern for detached sessions: create the background session first, then inject the bootstrap command as a real pane command (for example via `ZELLIJ_SESSION_NAME=<session> zellij run -- <bootstrap-script>`) rather than relying on `attach --create-background ... options --default-shell <script>` to materialize a visible pane
- post-launch verification should inspect the actual spawned pane (commonly `terminal_1`) because the initial `terminal_0` pane may remain empty in detached-session flows


## 2) Inspect another tracked live session

Use the helper instead of manually scraping zellij state.

```bash
get-cross-session-context --project-root "<project-root>" <task slug|tracker ref|session name>
```

Useful flags:
- `--include-transcript-tail 4`
- `--json`
- `--tab-name <name>`
- lower-level overrides only for debug work: `--task-dir`, `--status-file`, `--zellij-session`

Behavior to preserve:
- task/status metadata is the primary source of truth
- transcript tail is only a targeted fallback
- live zellij inspection is diagnostic only
- if multiple task homes match, stop and surface candidates instead of guessing

## 3) Preview or send a bounded cross-session message

Always preview first because the helper is dry-run by default.

```bash
send-zellij-message --project-root "<project-root>" --text "<message>" <task slug|tracker ref|session name>
```

Useful flags:
- `--execute`
- `--submit enter`
- `--tab-name <name>`
- `--json`

Behavior to preserve:
- run preview first and inspect the resolved target
- add `--execute` only once the target looks correct
- use `--submit enter` only when intentional
- large multiline Codex payloads may need an extra delayed confirm Enter; the helper handles this automatically
- refuse ambiguous tab selection or cross-machine targets unless the user intentionally does local debug work with explicit `--zellij-session`
- use this only for bounded prompt delivery, status pings, or resumable instructions; it is not a remote-control channel

## work-* conventions from README

The botfiles README documents reconnect-friendly shell helpers:
- `work-here`
- `work-ml`, `work-ml-ssh`
- `work-arya`, `work-arya-mosh`, `work-arya-ssh`
- `work-agent`, `work-agent-mosh`, `work-agent-ssh`
- raw shell shortcuts like `mml`, `marya`, `magent`

Important conventions:
- `fzf` is needed for interactive picker mode
- if `fzf` is missing, pass a session name explicitly
- local `zellij` is required for `work-here`
- mosh-based flows fall back to SSH if needed
- if already inside zellij on the current host, prefer the built-in session manager instead of nesting

## Verification

When using these helpers, verify with:
- command exit status
- printed attach hint / resolved target
- JSON output when available for structured inspection
- remote-target project-root existence before assuming launch succeeded
- when tracker/task-slug lookup returns `no_match` but you have a concrete session name from a Linear activation comment, retry `get-cross-session-context` with `--zellij-session <session>` for diagnostic live-session inspection only
- for `send-zellij-message`, always do the JSON dry-run preview first; if preview resolves but `--execute` fails, treat the write as not delivered and record the exact helper/zellij failure before choosing a fallback durable note

## Observed debug pitfall

In Arya supervision/debug flows, a freshly launched session may exist in `zellij list-sessions` before any tracker-backed task home, transcript path, or status artifact is discoverable. In that case:
- use Linear comments plus live zellij session existence as passive evidence of liveness
- do **not** claim execution-substrate context beyond what the helper actually resolved
- if `send-zellij-message --execute` times out on a zellij tab-selection action (for example `go-to-tab-name`), treat that as a helper delivery failure, not as a successful nudge
- prefer leaving a durable Linear supervision comment over repeated blind retries when the lane is still fresh and not clearly stalled
- if you launch a fresh detached task and `get-cross-session-context` still reports `no_match`, treat that as "metadata not materialized yet" rather than a failed launch when the start helper already returned success with a concrete session name/tab/attach hint

## Practical debug notes

- In Hermes terminal calls, prefer passing bare tracker IDs like `ZON-101` to `start-zellij-session-for-task` instead of full `https://linear.app/...` URLs when possible. Full Linear URLs can trigger the terminal security scanner because of the `.app` TLD, while the tracker ID avoids the approval interruption and still resolves correctly.
- Do not use `~` inside the terminal tool `workdir`; resolve it to an absolute path such as `/home/azureuser/pro/botfiles` first.
- In cron/supervision environments, verify the helper repo path exists on the current machine before assuming `~/pro/botfiles`-style commands are runnable. If the expected botfiles checkout is absent, fall back to durable passive evidence already referenced from Linear/task artifacts instead of claiming helper-based verification.
- In passive Arya supervision, a `get-cross-session-context ... <TRACKER>` result of `status: no_match` does not by itself mean the lane lacks a reviewer-facing artifact or needs recovery; first inspect recent Linear comments because some review-ready lanes only surfaced their durable handoff in comments rather than a tracked task home.
- If you retry with `--zellij-session <session>` for diagnostic inspection and the helper returns `status: ambiguous` with many candidate task homes, treat that as "no verified live execution substrate" for the target lane. Do not infer liveness from the shared zellij session name alone, and prefer a durable Linear note over any bounded nudge.
- When checking repo-backed PR/CI context from supervision loops, treat broad `gh pr list --search '<TRACKER>'` matches carefully: the command can return unrelated historical PRs that happen to mention the same string somewhere. Only forward PR/CI context when the match is clearly ticket-specific by title, branch, URL, or repo context.
- For Arya pickup of generic Zone tickets that lack repo-local evidence, default the launch root to `~/pro/personal_os` rather than a broad product repo guess. Treat ticket-local evidence as things like an explicit repo/path mention, linked GitHub issue/PR/repo, or existing tracked task metadata.
- Do not treat `start-zellij-session-for-task` success plus `zellij list-sessions` presence as sufficient activation evidence. A stale session name collision or an idle shell pane can produce those signals without a real live Codex surface.
- After a supposedly successful detached launch, verify the target pane itself (for example with `zellij ... action dump-screen -f`) and require visible Codex/start-task output before calling it a real execution path.
- If a pickup ticket remains in `Todo` because a stale session already exists for the expected slug, treat that as a blocked/failed execution verification case, not as successful activation. Prefer leaving a compact Linear explanation comment and clearing the stale session before retrying pickup.
- For tracker-linked work that lacks repo-specific evidence, default canonical project root to `~/pro/personal_os` rather than inferring some other product repo from broad company context alone.
- In pickup loops, do not treat a launched zellij session plus helper success text as sufficient activation evidence. Confirm the detached pane visibly shows Codex/start-new-task output before calling it a real execution path or moving a ticket to `In Progress`.
- If `start-zellij-session-for-task` returns `session already exists`, do not treat that as activation or successful reuse by itself. Immediately inspect with `get-cross-session-context`; if tracker-backed metadata is still missing, you only have a bare/legacy zellij session until Codex visibility is independently verified.
- On this machine/tooling combination, `zellij action dump-screen` does not accept a `--session` selector, so it is not a reliable detached-session verification path from Hermes by itself. Prefer the repo helper outputs plus conservative status handling over ad hoc attach-and-type probing unless you intentionally accept diagnostic-only shell interaction.

## Pitfalls

- Do not treat raw zellij inspection as the main contract when task metadata exists.
- Do not write into another session without previewing first.
- Do not guess among ambiguous sessions/tabs.
- Do not assume cross-machine sends are allowed; the helper intentionally blocks many of them.
- Do not override target/profile behavior unless the user explicitly asks.
