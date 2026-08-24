---
name: cross-session-message
description: >-
  Preview or send a bounded instruction into another known live zellij-backed
  coding-agent session outside Symphony.
---

# Cross-Session Message

Use the repo-managed `send-zellij-message` helper when you want to nudge
another live tracked task/session with a bounded instruction.

## Invocation

```text
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
- `--replace-claude-suggestion`
- `--json`

## Behavior

- Run the preview first. The helper is dry-run by default.
- Add `--execute` only after the resolved session/tab target looks correct.
- Use `--submit enter` only when you intentionally want the target session to receive Enter after the text write.
- Require a supported, uniquely resolved agent pane and a visibly empty
  composer before execution. Claude Code autocomplete is a narrow exception
  only after a human confirms it is a suggestion and a flagged preview with
  `--replace-claude-suggestion` reports `preview_probe_required`. Execution
  sends a non-text cursor probe. A real buffered draft is restored unchanged
  and blocked; only `suggestion_probe: verified_empty_buffer` may proceed.
- Treat only `outcome: delivered` with `delivered: true` as a forwarded turn.
  `executed: true`, staging, or an Enter action alone is not delivery.
- If the receipt is unsafe or unverified, stop and use manual inspection. Never
  clear, append to, or submit unknown composer text through the helper.
- Keep Claude suggestion-override messages short enough for the whole staged
  payload to remain visible. If staging is unverified, do not send Enter.
- Stop on ambiguous tab selection, cross-machine targets, or missing tracked session data unless the user is intentionally doing local debug work.
- When `XDG_RUNTIME_DIR` is absent, the helper may select `/run/user/<uid>` only
  if the default namespace lacks an active exact target and that systemd
  namespace contains it live. The receipt records the selected namespace.
- A uniquely supported wrapped Claude or Codex UI may be identified read-only
  when process-command metadata is unavailable. Ambiguity fails closed.
- Use this for bounded prompt delivery, status pings, or resumable instructions only. It is not a remote-control channel.

See `~/pro/botfiles/docs/cross-session-orchestration-contract.md` for the shared contract.
