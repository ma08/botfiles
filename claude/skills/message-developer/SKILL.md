---
name: message-developer
description: Send contextual WhatsApp messages to the developer during monitoring, on blockers, or at milestones. Use proactively when the developer may be away.
source: personal
---

# Message Developer Skill

Send WhatsApp notifications to the developer when they may be away from the terminal. Fills the gap between deterministic hook events (Stop, Notification, PreToolUse) and contextual situations where Claude should proactively reach out.

## When to Use

- **Monitoring completion**: A long-running background process finishes or fails
- **Blocker discovered**: Something needs human intervention (permissions, auth, config)
- **Milestone reached**: Significant progress in a multi-step autonomous task
- **Error pattern**: Repeated failures that aren't self-recoverable
- **Session ending with pending work**: Important state the developer should know about

## When NOT to Use

- Routine progress updates (save to status.md instead)
- Every iteration of a monitoring loop (only at significant events)
- When the developer is actively in the conversation (hooks handle this)
- For asking questions (use AskUserQuestion — the PreToolUse hook handles notification)

## How to Invoke

```bash
# Simple message
cd ~/.claude/hooks && uv run python send.py "Your message here"

# With a title/category
cd ~/.claude/hooks && uv run python send.py --title "BLOCKER" "Ralph loop stuck on Task 7 — missing import"

# Monitoring complete
cd ~/.claude/hooks && uv run python send.py --title "Monitoring Complete" "Ralph finished 12/12 tasks, all tiers passed"

# Pipe from stdin
echo "Deployment failed on step 3" | cd ~/.claude/hooks && uv run python send.py --title "Error Alert"
```

## Message Guidelines

- Keep messages under 500 characters (WhatsApp readability on phone)
- Lead with the most important info (status/action needed)
- Include task context (which task, which project)
- Use `--title` to categorize: "Monitoring Update", "BLOCKER", "Task Complete", "Error Alert"

## Proactive Monitoring Pattern

When asked to monitor a long-running process:

1. Set up periodic checks (background bash with sleep)
2. On each check, analyze status
3. Send WhatsApp only on **state changes** or **significant events** — not every check
4. Always also update the task status file (WhatsApp is ephemeral, status.md is permanent)

## Infrastructure

This skill uses the existing WhatsApp hook infrastructure:

- **CLI entry point**: `~/.claude/hooks/send.py`
- **WhatsApp sender**: `~/.claude/hooks/whatsapp.py` (Meta Cloud API v17.0)
- **Config**: `~/.claude/hooks/.env` (WHATSAPP_TOKEN, PHONE_NUMBER_ID, NOTIFY_PHONE_NUMBER, SYSTEM_NAME)
- **Dependencies**: `~/.claude/hooks/.venv` (requests, python-dotenv via uv)
