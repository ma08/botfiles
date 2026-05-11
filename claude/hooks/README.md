# Claude/Codex Notification Hooks

This directory contains the Python hook implementation used by Claude Code
settings and by Codex wrapper scripts.

## Main Files

- `notification.py` - Claude notification hook entrypoint.
- `pretooluse_notification.py` - Claude permission/request notification hook.
- `stop.py` - Claude stop/turn-complete hook.
- `send.py` - manual message sender used by the `message-developer` skill.
- `utils.py` and `whatsapp.py` - compatibility shims over shared utilities in
  `../../utils/notify_utils.py`.
- `../../codex/hooks/codex_app_server_notify_proxy.py` - Codex App Server
  WebSocket proxy that detects `item/tool/requestUserInput` and uses the shared
  notification utilities for WhatsApp/Gmail delivery.

Runtime secrets live in `~/pro/botfiles/secrets/local/*.rc`; do not put real
tokens in this directory. The old local `.env` path remains ignored only for
migration safety.

## Smoke Tests

```bash
cd ~/pro/botfiles/claude/hooks
uv run python send.py --title "Hook smoke" "Manual notification test"
uv run python test_whatsapp.py
```

Codex uses wrappers in `../../codex/hooks/` that run this project with `uv`.
For App Server request-user-input notifications, use `codexn*` aliases or
`start-zellij-session-for-task` so Codex traffic runs through the notification
proxy.
