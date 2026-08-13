# Cross-Session Orchestration Contract

These helpers define the v1 contract for non-Symphony cross-session work in
regular Codex and Claude sessions. They also document the Codex Desktop
app-thread transport when the runtime exposes `codex_app` tools.

## Target Resolution

Use tracker-first targeting by default. Resolve targets in this order:

1. `--status-file`
2. `--task-dir`
3. `--zellij-session`
4. tracker reference (`ZON-71`, Linear URL, GitHub issue URL)
5. task slug
6. Codex Desktop thread search, when `codex_app` tools are available and no
   task/zellij target resolves or the user explicitly targets a Desktop thread

If resolution is ambiguous, stop and show candidate task homes instead of
guessing.

## Context Read

`get-cross-session-context` returns:

- task/status metadata as the primary source of truth
- tracker metadata when present
- transcript tail as a targeted fallback when a transcript path is available
- zellij session/tab/client details as diagnostics, not the primary contract
- Codex Desktop `read_thread` status and turn summaries when the target is an
  app thread and `codex_app` tools are available

Transcript fallback supports Codex session JSONL, Claude per-session JSONL, and
Claude `history.jsonl` fallback filtered by session id when available.

Codex Desktop thread context is app-level context. It is useful for current turn
status and summaries, but it does not replace task status files for tracked
work.

## Transport Capability

Use the highest-level supported transport available in the current runtime:

- Codex Desktop -> Codex Desktop thread: use `list_threads`, `read_thread`, and
  `send_message_to_thread`.
- Codex Desktop -> zellij-backed terminal session: use the zellij helpers after
  target resolution.
- Codex CLI or Claude Code -> zellij-backed terminal session: use the zellij
  helpers.
- Codex CLI or Claude Code -> Codex Desktop thread: no universal first-class
  transport is assumed. Use an explicit supported bridge if one is available, or
  ask the user to send from a Codex Desktop thread.

Do not treat local Codex app SQLite state, JSONL logs, or notification proxy
state as a prompt-injection API. Those may be valid for read-only diagnostics or
label management when a dedicated skill says so, but they are not a standard way
to make a Desktop thread receive a new human prompt.

## Mac UI Worker Route

Use `mac-ui-worker` when a Codex Desktop source task needs UI-only work through
the Mac task-scoped in-app Browser or native Computer Use.

- Bind one Mac-local worker to the exact source host and task IDs.
- Reuse that worker only for serial jobs from the same source task. Give every
  logical job a unique job ID.
- Declare exactly one surface per job: `iab` or `computer-use`. Split mixed
  workflows into successive serial jobs for the same worker.
- Store source and worker task IDs durably. Titles are labels, not addresses.
- Create a worker only with explicit user authorization and native Desktop
  project/task tools.
- Keep login, MFA, credentials, fresh exact persistent-mutation approval, and
  any native Computer Use handoff in the worker task.
- Return sanitized receipts to the exact source task and keep a recoverable copy
  in the worker.
- Fail closed when Desktop transport or the declared surface is unavailable.
  Do not substitute SQLite or log writes, switch UI surfaces, or use another
  automation mechanism.

This route has no singleton dispatcher, shared worker pool, queue, lease, or
same-source parallel execution in v1. See
`~/pro/botfiles/codex/skills/mac-ui-worker/references/protocol-v1.md` for
the message contract.

## Message Send

`send-zellij-message` is preview-first and bounded for zellij-backed terminal
sessions:

- dry-run is the default
- `--execute` is required to perform a write
- `--submit enter` is explicit and best-effort
- for Codex sessions, long or multiline payloads get a delayed confirm Enter
  after the first Enter because a single immediate Enter can leave the prompt
  staged in the composer instead of submitting it
- message text is length-limited and control-character checked
- cross-machine sends are rejected unless the caller intentionally uses an
  explicit local `--zellij-session` override for debug work
- multi-tab sessions require `--tab-name` unless the helper can deterministically
  choose the tab from `[TRACKER-ID]` or a single-tab session

This helper is for bounded prompt delivery, not remote control.

For Codex Desktop threads, `send_message_to_thread` is the actual send. Preview
means resolving the target thread, surfacing ambiguity, and reading the thread
first when needed. Omit model and reasoning overrides unless the user explicitly
asks for them.

## PR Autoreview

`pr-autoreview-loop` tracks only the current PR head SHA.

Valid current-head reviewer artifacts are:

- a top-level PR comment with a valid `review-run-meta` marker whose `head_sha`
  matches the current head commit
- a GitHub review object attached to the exact current head commit

Reviewer checks are used for coarse pending or terminal status only. They do
not replace current-head artifact matching when multiple historical runs exist.

Derived states:

- `pending`: reviewer/check sweep is still in flight or a matching artifact has
  not landed yet
- `findings`: the latest current-head reviewer artifact contains actionable
  findings
- `clean`: the latest current-head reviewer artifact is clean and the reviewer
  check is not still pending/failing
- `blocked`: the current-head sweep published a blocked result or failed before
  a usable current-head artifact landed; this also includes repos where no
  reviewer infrastructure is detectable, so a current-head sweep cannot publish
- `closed`: the PR is not open

## Loop Policy

The non-Symphony loop is semi-autonomous:

1. inspect or wait for the current-head autoreview sweep
2. if findings exist, address them and push
3. wait for the next current-head sweep
4. repeat until `clean`

Stop and ask for human input when:

- the reviewer reports `blocked`
- the reviewer/check infrastructure fails and there is no in-session retry path
- the repo has no detectable reviewer infrastructure and no valid current-head
  reviewer artifact has been published manually
- the fix would require a product or policy decision rather than an
  implementation change
