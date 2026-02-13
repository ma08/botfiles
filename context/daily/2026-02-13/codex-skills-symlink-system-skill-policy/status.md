# Codex Skills Symlink and System Skills Policy

**Goal**: Standardize Codex skills/config symlinks in `botfiles`, keep custom skills source-controlled, and treat `codex/skills/.system` as machine-managed.
**Last Updated**: 2026-02-13 ~06:04AM
**Status**: In Progress

## Current State

Symlink setup is healthy after `setup.sh` + session restart:
- `~/.codex/skills` -> `~/pro/botfiles/codex/skills`
- `~/.codex/config.toml` -> `~/pro/botfiles/codex/config.toml`
- `~/.codex/AGENTS.md` -> `~/pro/botfiles/codex/AGENTS.md`
- `~/.claude/skills` -> `~/pro/botfiles/claude/skills`
- `~/.claude/CLAUDE.md` -> `~/pro/botfiles/claude/CLAUDE.md`

Policy decision captured:
- `codex/skills/.system` should be machine-managed (not source-controlled), due to cross-platform/version drift.

## Progress

- [x] Added Codex skills symlink support in `setup.sh`
- [x] Added Codex `AGENTS.md` symlink support in `setup.sh`
- [x] Added `codex/AGENTS.md`
- [x] Updated docs for Codex skills + AGENTS symlinks
- [x] Removed `codex/skills/message-developer` on request
- [x] Added `.gitignore` rule for `codex/skills/.system/`
- [x] Updated docs to explain machine-managed `.system` behavior
- [x] Verified symlinks and ignore behavior with command output artifacts

## Code Changes

- `.gitignore`: ignore `codex/skills/.system/`
- `README.md`: documented system-skill handling and symlink behavior
- `AGENTS.md`: documented machine-managed `codex/skills/.system/`
- `codex/AGENTS.md`: documented machine-managed system skills
- `codex/skills/README.md`: clarified custom vs system skill handling
- `setup.sh`: codex skills + AGENTS backup/symlink logic

## Artifacts

| File | Description |
|------|-------------|
| `task-progress-artifacts/symlink-verification.txt` | `ls -la` + `readlink` proof for Claude/Codex symlinks |
| `task-progress-artifacts/git-status.txt` | Current working tree status after edits |
| `task-progress-artifacts/system-skill-ignore-check.txt` | `git check-ignore -v` output validating `.system` is ignored |

## Next Steps

- [ ] Review/stage only the intended docs/config changes
- [ ] Commit with a message reflecting `.system` machine-managed policy
- [ ] Optionally ensure no previously tracked `.system` files remain in git history/index

## Notes

### 2026-02-13 ~06:04AM: Status save requested and completed

- Used default task-status path because no project-level `task-status-root` override was found for this repo.
- Saved verification artifacts so this status folder is self-contained for future handoff.
