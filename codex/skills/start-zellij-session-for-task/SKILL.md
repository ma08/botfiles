---
name: start-zellij-session-for-task
description: >-
  Start a detached zellij session for a tracker-linked or natural-language
  task, and launch Codex or Claude as the default shell with an initial
  `$start-new-task ...` handoff prompt.
---

# Start Zellij Session For Task

Use the repo-managed `start-zellij-session-for-task` helper when the user wants
to spin up a side task in its own zellij session without hijacking the current
terminal. Codex is the default backend, but Claude and Bedrock Claude can be
selected explicitly.

## Invocation

```text
$start-zellij-session-for-task [--backend codex|claude|bedccy] <linear url|linear id|github issue url|task description>
/start-zellij-session-for-task [--backend codex|claude|bedccy] <linear url|linear id|github issue url|task description>
```

Optional target override:

```text
$start-zellij-session-for-task --target ml <...>
```

Backend override:

```text
$start-zellij-session-for-task --backend bedccy <...>
$start-zellij-session-for-task --backend claude <...>
```

Paused app-server notification path:

```text
$start-zellij-session-for-task --codex-app-notify <...>
```

Supported targets:
- `here` (default)
- `ml`
- `arya`
- `agent`

## Command

```bash
start-zellij-session-for-task --project-root "<project-root>" <user input>
```

If the user explicitly names a machine, pass `--target ml|arya|agent`. Otherwise
default to `here`.

If the user explicitly asks for Claude, pass `--backend claude`; if they ask for
`bedccy` or Bedrock Claude, pass `--backend bedccy`.

## Behavior

- Resolves tracker and slug context with the shared task-status resolver.
- Uses the resolved task slug as the zellij session name unless overridden.
- Uses `[TRACKER-ID]` as the tab name when a tracker is present.
- Launches Codex through raw vanilla `codex` by default, preserving the shared
  `~/.codex/auth.json` ChatGPT login cache.
- `--backend claude` launches `claude --dangerously-skip-permissions`.
- `--backend bedccy` launches `CLAUDE_CODE_USE_BEDROCK=1 claude --dangerously-skip-permissions`.
- Use `--codex-app-notify` only when intentionally testing the paused App Server
  notification path; it only affects the Codex backend.
- Uses the current machine's default Codex profile instead of forcing a
  profile override when the backend is Codex.
- Clears inherited `CODEX_*` session metadata before starting a child Codex
  process.
- Seeds the child interactive session with the exact initial prompt:
  - `$start-new-task <original input>`
- Uses `codex --dangerously-bypass-approvals-and-sandbox` for Codex launches,
  preserving the current CLI equivalent of the historical `--yolo` shorthand.
- Prints the launched session name, target, attach hint, initial prompt, and
  any available zellij web link.
- For remote targets, fails early if the resolved project root does not exist on
  the target host.

## Notes

- This helper intentionally does not switch the current terminal into the new
  session.
- Remote targets reuse the same host-selection defaults as `work-ml`,
  `work-arya`, and `work-agent`.
- If a session with the same name already exists, stop and surface the collision
  instead of launching a second Codex run into it.
- Use `--dry-run` only when the user wants to inspect the resolved launch plan
  without starting the session.
- If `--codex-app-notify` is explicitly enabled and the helper reports that
  `codex-app-notify-session` is unavailable, rerun without `--codex-app-notify`
  for the default raw-Codex path.
