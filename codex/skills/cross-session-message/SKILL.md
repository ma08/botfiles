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

Within an accepted Mac UI job, do not use this skill to relay routine
clarification, login, MFA, credential entry, approval, or handoff between the
worker and source. Those checkpoints stay between Sourya and the worker by
default. The only approval exception is an exact, visibly pre-declared,
single-use source delegation. Cross-task sends must match a callback,
dependency result, correction, cancellation, or terminal receipt allowed by
the complete initial `mac-ui-worker/v1` envelope.

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
- `--replace-claude-suggestion`
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
- The preview resolves one supported Claude Code or Codex pane and inspects its
  composer without mutation. An unsafe, non-empty, busy, ambiguous, or
  unsupported composer blocks execution.
- Claude Code autocomplete is a narrow exception only with explicit
  `--replace-claude-suggestion`. The helper requires visible suggestion text
  while the cursor remains at the empty-prompt position. A flagged preview
  reports `preview_probe_required`; execution sends a non-text end-of-line
  cursor probe. A real buffered draft moves the cursor, is restored without
  changing text, and fails closed. Only an empty buffer behind autocomplete
  may proceed.
- Execution writes only to the resolved pane id. It verifies staging before any
  Enter, and reports `delivered: true` only after the staged text is observed as
  a new agent turn.
- Receipts distinguish `preview_safe`, `preview_unsafe`, `unsafe_composer`,
  `staged`, `delivered`, and `unverified`. `executed: true` means a mutation was
  attempted; it does not mean delivery. Gate follow-through on
  `outcome: delivered` and `delivered: true`.
- Long or multiline Codex prompts receive a delayed confirm Enter only when the
  intended payload is still visibly staged after the first Enter.
- Stop on ambiguous tab selection, cross-machine targets, or missing tracked
  session data unless the user is intentionally doing local debug work with an
  explicit `--zellij-session`.
- If a non-interactive shell lacks `XDG_RUNTIME_DIR`, the helper keeps an active
  default zellij namespace. When that namespace has only a missing or exited
  target and `/run/user/<uid>` has the exact live session, it selects the live
  systemd namespace and records that choice in the receipt. It never switches
  away from an active default target.
- Explicit-session debug sends may identify a uniquely supported wrapped
  Claude or Codex UI from a read-only screen fingerprint when process-command
  metadata is unavailable. Ambiguous or multiple matches fail closed.
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
- A later generic message cannot broaden an active Mac UI job. Value-safe
  corrections use the exact protocol correction envelope; material expansion
  requires a new complete request and job ID.

## Manual fallback

If the helper reports an unsafe or unverified composer, stop automated sends.
Attach to the resolved session, inspect the exact agent pane, and let the human
decide how to handle any existing draft, selector, or unknown UI state. Do not
clear it, append a retry, or send Enter through the helper. After the composer is
manually returned to a visibly empty supported state, start again with a fresh
preview.

If the human confirms that Claude's visible text is autocomplete rather than a
real draft, repeat the preview with `--replace-claude-suggestion`. Require
`preview_probe_required`, then execute with the same flag. Execution may stage
text only after `suggestion_probe: verified_empty_buffer` and
`composer_preflight: safe_claude_suggestion_override`. Keep the message short
enough for the whole staged payload to remain visible and verifiable. If
staging is unverified, do not send Enter.

See `~/pro/botfiles/docs/cross-session-orchestration-contract.md` for the
shared contract.
