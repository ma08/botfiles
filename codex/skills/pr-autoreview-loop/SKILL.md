---
name: pr-autoreview-loop
description: >-
  Run a repeatable non-Symphony PR autoreview fix loop using current-head
  reviewer artifacts plus the repo-managed `pr-autoreview-loop` helper.
---

# PR Autoreview Loop

Use this skill after a PR is open and an expected autoreviewer/check is
configured for the repo.

## Command

```bash
pr-autoreview-loop status --repo "<repo-root>" --pr <number|url>
pr-autoreview-loop wait --repo "<repo-root>" --pr <number|url>
```

Useful flags:
- `--review-check-substring codex-review`
- `--json`
- `--poll-seconds 30`
- `--timeout-seconds 1800`

## Loop

1. Inspect or wait for the current-head autoreview sweep.
2. If the helper reports `findings`, address the current-head review comments
   and push a new commit.
3. Wait for the next current-head sweep.
4. Repeat until the helper reports `clean`.

## Stop Conditions

- Stop and ask for human input if the helper reports `blocked`.
- Stop and ask for human input if the reviewer/check infrastructure failed and
  there is no in-session retry or re-poll path left.
- Keep the task in progress while the current-head sweep is still pending and
  healthy.

## Matching Rules

- Match only reviewer artifacts that apply to the exact current PR head SHA.
- Prefer top-level PR comments with valid `review-run-meta` markers.
- Fall back to GitHub review objects attached to the exact current head commit.
- Use the review check only for coarse pending/terminal state.

See `~/pro/botfiles/docs/cross-session-orchestration-contract.md` for the
shared contract.
