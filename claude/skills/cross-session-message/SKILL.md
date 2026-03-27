---
name: cross-session-message
description: >-
  Preview or send a bounded instruction into another known live zellij-backed
  coding-agent session outside Symphony.
---

# Cross-Session Message

Use the repo-managed `send-zellij-message` helper when the user wants to nudge
another live task/session with a bounded instruction.

## Invocation

```text
$cross-session-message <task slug|tracker ref|session name>
/cross-session-message <task slug|tracker ref|session name>
```

## Command

```bash
send-zellij-message --project-root "<project-root>" --text "<message>" <target>
```

Useful flags:
- `--execute`
- `--submit enter`
- `--tab-name <name>`
- `--json`

## Behavior

- Run the preview first. The helper is dry-run by default.
- Add `--execute` only after the resolved session/tab target looks correct.
- Use `--submit enter` only when you intentionally want the target session to
  receive Enter after the text write.
- Stop on ambiguous tab selection, cross-machine targets, or missing tracked
  session data unless the user is intentionally doing local debug work with an
  explicit `--zellij-session`.
- Use this for bounded prompt delivery, status pings, or resumable instructions
  only. It is not a remote-control channel.

See `~/pro/botfiles/docs/cross-session-orchestration-contract.md` for the
shared contract.
