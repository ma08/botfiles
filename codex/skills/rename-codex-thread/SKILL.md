---
name: rename-codex-thread
description: Rename Codex app thread labels and titles in local Codex state. Use when a user asks to rename, retitle, relabel, or make a Codex chat/thread easier to find in the Codex app sidebar or thread list, especially when the visible label still shows the first prompt such as "$start-new-task ZON-218".
---

# Rename Codex Thread

## Workflow

Use `scripts/rename_codex_thread.py` for all writes. The Codex app sidebar is backed by `~/.codex/state_5.sqlite` or another `state_*.sqlite` database, not just `~/.codex/session_index.jsonl`.

1. Pick a concise, human-readable title.
2. Identify the target thread id.
3. Run the script with `--thread-id <id>` when known.
4. For the active/recent thread, use `--current` only when that is clearly what the user means.
5. Ask the user to refresh or reopen the Codex app if the old label is still cached.

## Commands

Rename a known thread:

```bash
python /home/azureuser/pro/botfiles/codex/skills/rename-codex-thread/scripts/rename_codex_thread.py \
  --thread-id 019eedf1-89cc-7c23-8cc7-a7d2bffd4bff \
  --title "Find the best ways to contribute to Ambuda again"
```

Rename the most recently updated unarchived thread:

```bash
python /home/azureuser/pro/botfiles/codex/skills/rename-codex-thread/scripts/rename_codex_thread.py \
  --current \
  --title "Investigate ncmpcpp crashes and media keys"
```

Preview recent candidates:

```bash
python /home/azureuser/pro/botfiles/codex/skills/rename-codex-thread/scripts/rename_codex_thread.py --list
```

## Notes

- The script creates a timestamped SQLite backup before writing unless `--no-backup` is passed.
- The script updates `threads.title` and `threads.preview`; it leaves `first_user_message` unchanged by default.
- The script appends a matching line to `session_index.jsonl` when that file exists, but the SQLite `threads` table is the authoritative app label source.
- Prefer `--thread-id` over `--current` if multiple Codex sessions may be active.
