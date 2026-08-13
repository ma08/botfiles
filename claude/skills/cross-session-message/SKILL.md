---
name: cross-session-message
description: >-
  Preview or send a bounded instruction into another known live zellij-backed
  coding-agent session or Codex Desktop thread outside Symphony.
---

# Cross-Session Message

Use the repo-managed `send-zellij-message` helper when the user wants to nudge
another live zellij-backed task/session with a bounded instruction. When running
inside Codex Desktop and the target is a Codex Desktop thread, use the app
thread tools as the Desktop transport.

For UI-only work routed to the Mac in-app Browser or native Computer Use, use
`mac-ui-worker` instead of treating a generic cross-session message as a UI-job
protocol.

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

Codex Desktop thread path, when `codex_app` tools are available:

0. If the thread tools are not already visible, use the runtime's tool
   discovery to load `list_threads`, `read_thread`, and
   `send_message_to_thread`.
1. Use `list_threads` with the tracker id, task slug, or visible title.
2. If the result is ambiguous, stop and surface the candidates.
3. Use `read_thread` if you need to confirm the current target state.
4. Send with `send_message_to_thread`, passing `threadId` and `hostId`.
5. Omit `model` and `thinking` unless the user explicitly asks to override the
   destination thread's settings.

## Behavior

- Run the preview first. The helper is dry-run by default.
- Add `--execute` only after the resolved session/tab target looks correct.
- Use `--submit enter` only when you intentionally want the target session to
  receive Enter after the text write.
- Long or multiline Codex prompts may require a second confirm Enter; the helper
  now adds that delayed confirm automatically when it detects that case.
- Stop on ambiguous tab selection, cross-machine targets, or missing tracked
  session data unless the user is intentionally doing local debug work with an
  explicit `--zellij-session`.
- For Codex Desktop threads, the preview step is target resolution and, when
  useful, `read_thread`; `send_message_to_thread` is the actual send.
- If no zellij session exists but a unique Codex Desktop thread is found, the
  Desktop path is valid and should not be treated as a zellij failure.
- Codex CLI and Claude Code do not automatically have Codex Desktop thread
  tools. If `codex_app` tools are unavailable, do not edit SQLite state or local
  logs to simulate a human prompt. Use zellij if the target is terminal-backed,
  or ask the user to send from a Codex Desktop thread / provide an explicit
  supported bridge.
- Use this for bounded prompt delivery, status pings, or resumable instructions
  only. It is not a remote-control channel.
- A `mac-ui-worker/v1` request must use the exact recorded source and worker
  IDs, a unique job ID, exactly one declared surface, and the protocol envelope.
  Do not send UI jobs by title or to a shared worker guessed from history.

See `~/pro/botfiles/docs/cross-session-orchestration-contract.md` for the
shared contract.
