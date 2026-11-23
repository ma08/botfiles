# Antigravity Global Config

Shared global instructions, modular rules, skill registration, and lifecycle notification hooks for Google Antigravity (`~/.gemini/config/`).

## Layout & Symlinks

`setup.sh` creates six symlinks inside `~/.gemini/config/`:

- `~/.gemini/config/AGENTS.md` -> `antigravity/AGENTS.md` (core always-on global instructions, kept strictly under Antigravity's 24,000-byte per-file limit)
- `~/.gemini/config/rules` -> `antigravity/rules/` (modular `trigger: model_decision` domain playbooks for Oracle, cross-session orchestration, and diagrams/browser automation)
- `~/.gemini/config/botfiles-skills` -> `codex/skills/` (kept under a non-default name so it does not auto-load at priority 3 or collide with personal `~/.gemini/config/skills/`)
- `~/.gemini/config/skills.json` -> `antigravity/skills.json` (loads `botfiles-skills` via relative path with explicit exclusions for harness-specific or plugin-overlapping skills)
- `~/.gemini/config/hooks` -> `antigravity/hooks/`
- `~/.gemini/config/hooks.json` -> `antigravity/hooks.json`

## Notification Hooks

`hooks.json` wires `Stop` and `PreToolUse` (`ask_question`) into the shared `utils/notify_utils.py` pipeline (local macOS notifications, WhatsApp, and Gmail alerts controlled by `secrets/local/claude-hooks.rc`).

- Always returns valid non-blocking hook JSON (`{}` for `Stop`, `{"decision": "allow"}` for `PreToolUse`).
- Dispatches notification delivery in a detached background process so synchronous hooks never stall Antigravity.

## Testing

Run unit tests:

```bash
cd ~/pro/botfiles/claude/hooks && uv run python -m unittest discover -s ../../antigravity/hooks -p "test_*.py"
```

Manual smoke test (through the wrapper):

```bash
printf '%s\n' '{"hookEventName":"Stop","terminationReason":"NO_TOOL_CALL","fullyIdle":true,"conversationId":"test-conv-1234"}' \
  | ~/pro/botfiles/antigravity/hooks/run-antigravity-notify.sh --sync
```
