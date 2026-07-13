---
name: rename-codex-thread
description: Rename Codex app thread labels and titles in local Codex state. Use when a user asks to rename, retitle, relabel, or make a Codex chat/thread easier to find in the Codex app sidebar or thread list, especially when the visible label still shows the first prompt such as "$start-new-task ZON-218".
---

# Rename Codex Thread

## Workflow

Prefer the Codex app `set_thread_title` tool for writes when it is available. It supports known thread IDs without directly mutating app state and is the required path for connected remote-host threads. Use `scripts/rename_codex_thread.py` as the local-state fallback when the app tool is unavailable. The local Codex app sidebar is backed by `~/.codex/state_5.sqlite` or another `state_*.sqlite` database, not just `~/.codex/session_index.jsonl`.

1. Pick a concise, human-readable title using the default format below.
2. Identify the target thread id.
3. Call `set_thread_title` with `threadId` and `title` when the tool is available.
4. Otherwise run the fallback script with `--thread-id <id>` when known.
5. For the active/recent local thread, use the fallback script's `--current` only when that is clearly what the user means.
6. Ask the user to refresh or reopen the Codex app if the old label is still cached.

## Default Title Format

Use this format by default:

```text
<tracker id> · <stable domain> · <current status>
```

Examples:

- `ZON-274 · Provider recovery · Pilot rerunning`
- `owner/repo#123 · Webhook retries · Testing idempotency`
- `[no ticker] · Notification debugging · Reproducing failure`

For tracker-backed work, use the human-facing tracker identifier from task metadata or local context, such as a Linear identifier (`ZON-221`) or an equivalent GitHub issue reference (`owner/repo#123`). Do not use raw tracker UUIDs. If no Linear ticket, GitHub issue, or equivalent tracker exists, use `[no ticker]` as the prefix.

Keep the middle segment to roughly 2–4 words describing the durable task domain. Once established, preserve it unless it is clearly inaccurate. Keep the final segment to roughly 2–5 words describing the latest material state. Change it only when the task state has actually changed, not to substitute stylistic synonyms. Use a soft target of roughly 70 characters; do not forcibly truncate useful status text.

## Commands

Rename a known thread:

```bash
python3 ~/pro/botfiles/codex/skills/rename-codex-thread/scripts/rename_codex_thread.py \
  --thread-id 019eedf1-89cc-7c23-8cc7-a7d2bffd4bff \
  --title "ZON-218: Find the best ways to contribute to Ambuda again"
```

Rename the most recently updated unarchived thread:

```bash
python3 ~/pro/botfiles/codex/skills/rename-codex-thread/scripts/rename_codex_thread.py \
  --current \
  --title "[no ticker]: Investigate ncmpcpp crashes and media keys"
```

Preview recent candidates:

```bash
python3 ~/pro/botfiles/codex/skills/rename-codex-thread/scripts/rename_codex_thread.py --list
```

## Notes

- The script creates a timestamped SQLite backup before writing unless `--no-backup` is passed.
- The script updates `threads.title` and `threads.preview`; it leaves `first_user_message` unchanged by default.
- Title-only writes preserve `updated_at` and `updated_at_ms` by default so renaming does not make an inactive thread look recent. Pass `--touch-updated-at` only when that legacy behavior is explicitly required.
- The script appends a matching line to `session_index.jsonl` when that file exists, but the SQLite `threads` table is the authoritative app label source.
- Prefer `--thread-id` over `--current` if multiple Codex sessions may be active.
