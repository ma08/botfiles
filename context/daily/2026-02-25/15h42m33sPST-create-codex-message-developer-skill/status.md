# Create Codex Message Developer Skill

**Goal**: Create a Codex equivalent of Claude's message-developer skill so Codex can proactively notify or ask the developer during long-running work.
**Last Updated**: 2026-02-25 ~03:46pm PST
**Status**: Complete

## Current State

Codex now has a dedicated `message-developer` skill, a Codex-native sender command, and verified end-to-end delivery for both proactive and end-of-turn notifications. User confirmed it is working.

## Progress

- [x] Reviewed Claude source skill at `claude/skills/message-developer/SKILL.md`
- [x] Added Codex skill docs and agent metadata
- [x] Added Codex sender CLI and wrapper script
- [x] Ran smoke checks for `--help` paths
- [x] Sent real proactive skill message and verified WhatsApp API success (`status=200`) in `hooks.log`
- [x] Verified end-of-turn hook notification delivery in `hooks.log`
- [x] User confirmation received: `working!`

## Code Changes

- `codex/skills/message-developer/SKILL.md`: New Codex skill instructions and usage patterns
- `codex/skills/message-developer/agents/openai.yaml`: New skill interface metadata
- `codex/hooks/send.py`: New Codex sender CLI using shared `notify_utils.send_notification`
- `codex/hooks/run-codex-send.sh`: New uv-based wrapper script for consistent execution

## Artifacts

| File | Description |
|------|-------------|
| `task-progress-artifacts/smoke-tests-and-status.txt` | `--help` output for new sender commands and current git status snapshot |
| `task-progress-artifacts/proactive-notification-verification.txt` | Relevant `hooks.log` lines proving proactive + hook notifications were sent successfully (`status=200`) |

## Next Steps

- [x] Restart Codex so the newly added skill is loaded into the skill registry
- [x] Send a real test message with `codex/hooks/run-codex-send.sh --title "Proactive Test" "..."`
