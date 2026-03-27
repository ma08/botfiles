# Cross-Session Orchestration Contract

These helpers define the v1 contract for non-Symphony cross-session work in
regular Codex and Claude sessions.

## Target Resolution

Use tracker-first targeting by default. Resolve targets in this order:

1. `--status-file`
2. `--task-dir`
3. `--zellij-session`
4. tracker reference (`ZON-71`, Linear URL, GitHub issue URL)
5. task slug

If resolution is ambiguous, stop and show candidate task homes instead of
guessing.

## Context Read

`get-cross-session-context` returns:

- task/status metadata as the primary source of truth
- tracker metadata when present
- transcript tail as a targeted fallback when a transcript path is available
- zellij session/tab/client details as diagnostics, not the primary contract

Transcript fallback supports Codex session JSONL, Claude per-session JSONL, and
Claude `history.jsonl` fallback filtered by session id when available.

## Message Send

`send-zellij-message` is preview-first and bounded:

- dry-run is the default
- `--execute` is required to perform a write
- `--submit enter` is explicit and best-effort
- message text is length-limited and control-character checked
- cross-machine sends are rejected unless the caller intentionally uses an
  explicit local `--zellij-session` override for debug work
- multi-tab sessions require `--tab-name` unless the helper can deterministically
  choose the tab from `[TRACKER-ID]` or a single-tab session

This helper is for bounded prompt delivery, not remote control.

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
