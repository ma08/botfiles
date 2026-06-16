---
name: channel-access
description: Use local read-only iMessage, WhatsApp, and LinkedIn channel access wrappers for raw message discovery, sample exports, and CRM provenance workflows.
metadata:
  openclaw:
    category: "productivity"
    requires:
      bins:
        - zone-channel-health
        - zone-wa-read
        - zone-imsg-read
        - zone-li-read
---

# Channel Access

Use this skill when a task needs local iMessage, WhatsApp, or LinkedIn context from the
developer's private channel stores, including CRM updates, relationship context,
meeting logistics, follow-up reconstruction, or raw procedural discovery.

## Security Rules

- Default to read-only access.
- Do not send, edit, delete, forward, explicitly mark-read, mutate
  contacts/groups, connect, react, follow, endorse, archive, or otherwise write
  to channels unless the user explicitly approves that action and the relevant
  write-enable mechanism is intentionally set for that call.
- For LinkedIn v1, no write paths are implemented. Bounded message-thread opens
  may incidentally mark conversations read when the user has approved that
  workflow; do not perform explicit read/unread state changes.
- Do not paste full raw private threads into task artifacts, Notion, GitHub,
  Linear, public logs, or cloud tools.
- Use bounded searches/windows by default.
- Save full raw validation samples only under
  `~/pro/lab/zone-channel-ingest/samples/`.
- Let wrapper query audit logs record command arguments/counts; do not create
  extra message-content logs unless the user asks.

## State

Private state lives under:

```bash
~/pro/lab/zone-channel-ingest/
```

Main labels:

- iMessage: `imessage-sourya-mac`
- WhatsApp: `whatsapp-sourya`
- LinkedIn: `linkedin-sourya`

Config:

```bash
~/pro/lab/zone-channel-ingest/config/channel-ingest.env
```

## Health

Start with:

```bash
zone-channel-health
```

This reports installed versions, private store paths, disk usage/cap, WhatsApp
auth status, whether the copied iMessage database exists, and LinkedIn browser
state paths.

For LinkedIn-specific checks:

```bash
zone-li-health
```

## WhatsApp

Read-only examples:

```bash
zone-wa-read auth status
zone-wa-read chats list --limit 20
zone-wa-read messages list --limit 20
zone-wa-read messages search "query" --limit 20
zone-wa-read messages context --chat JID --id MSG_ID --before 5 --after 5
```

On-demand sync:

```bash
zone-wa-sync
```

Pairing is an interactive human step:

```bash
zone-wa-auth --phone "+15551234567"
```

Do not run pairing or sync with broad history/backfill options unless the task
requires it and the storage cap has been checked.

## iMessage

Pull a copied database from `sourya-mac`:

```bash
zone-imsg-pull
```

Copy attachments too only when the task needs media and storage has been
reviewed:

```bash
zone-imsg-pull --with-attachments
```

Read-only examples against the copied Linux database:

```bash
zone-imsg-read chats --limit 20 --json
zone-imsg-read search --query "query" --limit 20 --json
zone-imsg-read history --chat-id ID --limit 50 --json
```

Linux `imsg` is read-only for a copied macOS `chat.db`; it is not a live
iMessage client and cannot send messages.

## LinkedIn

LinkedIn access uses a dedicated VM Chrome profile plus Playwright browser
automation. It is read-only by construction in v1.

Human login from a VM GUI/remote desktop terminal:

```bash
zone-li-login
```

Read-only examples:

```bash
zone-li-health
zone-li-read recent --limit 20 --open-limit 10 --max-messages 50
zone-li-read thread --thread-url "https://www.linkedin.com/messaging/thread/..." --max-messages 50
zone-li-read thread --profile-url "https://www.linkedin.com/in/example/" --max-messages 50
zone-li-read thread --name "Person Name" --max-messages 50
zone-li-read profile --thread-url "https://www.linkedin.com/messaging/thread/..." --experience-limit 3
zone-li-read profile --profile-url "https://www.linkedin.com/in/example/" --experience-limit 3
```

Rules:

- Keep LinkedIn raw outputs private under `~/pro/lab/zone-channel-ingest/`.
- Do not paste full raw LinkedIn threads into task artifacts, Notion, GitHub,
  Linear, or cloud tools.
- Do not implement or invoke LinkedIn sends, connection requests, reactions,
  follows, archives, deletes, or broad profile scraping from this skill.
- Prefer bounded recent-inbox scans and explicit user-provided profile/thread
  targets.
- Profile parsing v1 is limited to CRM-relevant visible fields: name, headline,
  location, profile URL, about snippet, company/profile URLs, and a small recent
  experience window. Do not pull education, skills, posts/activity, or full
  history unless separately approved.

## Samples

Write full samples privately:

```bash
zone-channel-sample whatsapp
zone-channel-sample imessage chats --limit 20 --json
zone-channel-sample imessage history --chat-id ID --limit 50 --json
zone-li-sample recent --limit 5 --open-limit 2 --max-messages 20
zone-li-sample thread --thread-url "https://www.linkedin.com/messaging/thread/..." --max-messages 50
zone-li-sample thread --profile-url "https://www.linkedin.com/in/example/" --max-messages 50
zone-li-sample profile --thread-url "https://www.linkedin.com/messaging/thread/..." --experience-limit 3
```

After creating a sample, summarize only metadata in task artifacts unless the
user explicitly asks to promote content.

## Troubleshooting

- If `zone-imsg-pull` fails, check SSH access to `sourya-mac`, remote
  `sqlite3`, and macOS Full Disk Access/TCC behavior. Do not install a Mac-side
  LaunchAgent without explicit user approval.
- If `zone-imsg-read` fails with Swift libraries missing, verify
  `ZONE_CHANNEL_SWIFT_RUNTIME_DIR` in the private config.
- If `wacli` commands fail on locks or auth, use `zone-channel-health` and
  `zone-wa-read auth status` before retrying.
- If `zone-li-health` reports `login_required_or_not_verified`, run
  `zone-li-login` from a VM GUI/remote desktop terminal and complete LinkedIn
  login manually.
- If LinkedIn selectors fail, keep the raw failure private and update the
  Playwright extractor rather than broadening scans or using private APIs
  without fresh user approval.
