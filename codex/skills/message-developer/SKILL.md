---
name: message-developer
description: Send contextual WhatsApp messages to the developer during monitoring, blockers, milestones, or explicit questions. Use proactively when the developer may be away.
source: personal
---

# Message Developer Skill

Send proactive notifications to the developer while Codex is running, especially during long-running autonomous tasks.

## When to Use

- Monitoring completion: a long-running process finishes or fails
- Blocker discovered: human intervention is needed (auth, secrets, permissions, approvals)
- Milestone reached: meaningful progress in multi-step work
- Error pattern: repeated failures that are not self-recoverable
- Decision needed: Codex needs a yes/no or option choice before risky actions
- Session ending with pending work: key state should be surfaced quickly

## When NOT to Use

- Routine progress chatter (persist this in task status files instead)
- Every loop iteration (notify only on state changes or significant events)
- Situations where the developer is clearly active in chat and already seeing updates
- Non-actionable messages without clear context or ask

## How to Invoke

```bash
# Simple message
~/pro/botfiles/codex/hooks/run-codex-send.sh "Ralph loop complete: 12/12 tasks passed."

# With a category/title
~/pro/botfiles/codex/hooks/run-codex-send.sh --title "BLOCKER" "Need AWS prod role to continue deploy validation."

# Ask a question with explicit options
~/pro/botfiles/codex/hooks/run-codex-send.sh --title "QUESTION" "Run DB migration now? Reply 1) run now 2) dry-run first"

# Pipe from stdin
echo "Integration tests failed on macOS only; Linux is green." | \
  ~/pro/botfiles/codex/hooks/run-codex-send.sh --title "Error Alert"
```

## Question Pattern

When you need developer input during autonomous work:

1. Send a concise message with context and 2-3 explicit options.
2. Continue only with safe/reversible work while waiting.
3. Also ask in Codex chat when a response is required before high-risk actions.
4. Record the pending question and outcome in task status notes.

## Message Guidelines

- Keep messages short (target under 500 chars for phone readability)
- Lead with status/action needed
- Include task/project context
- For blockers, say exactly what is needed to unblock
- For milestones, include a clear result summary and next immediate step

## Proactive Monitoring Pattern

When asked to monitor a long-running process:

1. Start periodic checks.
2. Notify only on meaningful state changes.
3. Send alerts for completion, failure, blockers, and decisions needed.
4. Persist durable details in task status files (messages are ephemeral).

## Infrastructure

This skill uses the existing shared notification stack:

- Codex sender wrapper: `~/pro/botfiles/codex/hooks/run-codex-send.sh`
- Codex sender CLI: `~/pro/botfiles/codex/hooks/send.py`
- Shared notification utility: `~/pro/botfiles/utils/notify_utils.py`
- Auto turn-complete hook: `~/pro/botfiles/codex/hooks/run-codex-notify.sh`
- Config: `~/pro/botfiles/claude/hooks/.env`
- Required env keys: `WHATSAPP_ENABLED`, `WHATSAPP_TOKEN`, `PHONE_NUMBER_ID`, `NOTIFY_PHONE_NUMBER`, `SYSTEM_NAME`
- Python deps: managed via `uv` project at `~/pro/botfiles/claude/hooks`
