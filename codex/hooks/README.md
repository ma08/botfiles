# Codex Hooks

Codex notification wrappers use the shared Python hook environment in
`../../claude/hooks` and the delivery utilities in `../../utils/notify_utils.py`.

## App Server request_user_input Notifications

The App Server notification path is opt-in for direct terminal sessions and
default for detached zellij task launches.

Architecture:

```text
Codex TUI -> local notification proxy -> loopback Codex App Server
```

The proxy forwards WebSocket frames unchanged. It detects
`item/tool/requestUserInput`, sends `Codex Needs Input` through the existing
WhatsApp/Gmail notification channels, dedupes with
`threadId + turnId + itemId + requestId`, and clears pending state on
`serverRequest/resolved`.

Management commands:

```bash
codex-app-notify-start
codex-app-notify-status
codex-app-notify-proxy-logs
codex-app-notify-stop
```

Start a direct terminal session through the proxy:

```bash
codexn-azure
codexn-openai
codexny-azure
```

Detached zellij task sessions use this path by default:

```bash
start-zellij-session-for-task ZON-170
```

Use raw Codex only for fallback/debug work:

```bash
start-zellij-session-for-task --no-codex-app-notify ZON-170
```

State and logs default to:

```text
~/.cache/botfiles/codex-app-server-notify/state.json
~/.cache/botfiles/codex-app-server-notify/events.jsonl
~/.cache/botfiles/codex-app-server-notify/notify-proxy.log
~/.cache/botfiles/codex-app-server-notify/app-server.log
```

Set `CODEX_APP_NOTIFY_DRY_RUN=true` to log notification attempts without sending
WhatsApp or Gmail messages.
