---
name: start-zellij-session-for-task
description: >-
  Start a detached zellij session for a tracker-linked or natural-language
  task, and launch Codex as the default shell with an initial
  `$start-new-task ...` handoff prompt.
---

# Start Zellij Session For Task

Use the repo-managed `start-zellij-session-for-task` helper when the user wants
to spin up a side task in its own zellij session without hijacking the current
terminal. This skill intentionally launches a detached Codex session because the
requested workflow is Codex-based.

## Invocation

```text
$start-zellij-session-for-task <linear url|linear id|github issue url|task description>
/start-zellij-session-for-task <linear url|linear id|github issue url|task description>
```

Optional target override:

```text
$start-zellij-session-for-task --target ml <...>
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

## Behavior

- Resolves tracker and slug context with the shared task-status resolver.
- Uses the resolved task slug as the zellij session name unless overridden.
- Uses `[TRACKER-ID]` as the tab name when a tracker is present.
- Launches Codex as the detached session's default shell so attaching lands on
  the live Codex UI.
- Clears inherited `CODEX_*` session metadata before starting the child Codex
  process.
- Seeds the child interactive Codex session with the exact initial prompt:
  - `$start-new-task <original input>`
- Uses `codex --dangerously-bypass-approvals-and-sandbox`, which is the current
  CLI equivalent of the historical `--yolo` shorthand.
- Prints the launched session name, target, attach hint, initial prompt, and
  any available zellij web link.

## Notes

- This helper intentionally does not switch the current terminal into the new
  session.
- Remote targets reuse the same host-selection defaults as `work-ml`,
  `work-arya`, and `work-agent`.
- If a session with the same name already exists, stop and surface the collision
  instead of launching a second Codex run into it.
- Use `--dry-run` only when the user wants to inspect the resolved launch plan
  without starting the session.
