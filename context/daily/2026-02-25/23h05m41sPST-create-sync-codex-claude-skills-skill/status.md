# Create Sync Codex Claude Skills Skill

**Goal**: Add a Codex skill that compares drift between `claude/skills` and `codex/skills`, and syncs all or selected skills in either direction.
**Last Updated**: 2026-02-25 ~11:05pm PST
**Status**: Complete

## Current State

The new skill `sync-codex-claude-skills` exists under `codex/skills/` with a deterministic helper script and validated metadata/frontmatter.

## Progress

- [x] Initialized skill scaffold via `skill-creator` init script
- [x] Added `scripts/sync_skills.py` for status + directional sync
- [x] Replaced template `SKILL.md` with operational workflow docs
- [x] Validated skill with `quick_validate.py`
- [x] Smoke-tested `status` and `sync` dry-run commands

## Code Changes

- `codex/skills/sync-codex-claude-skills/SKILL.md`: New skill instructions and workflow
- `codex/skills/sync-codex-claude-skills/agents/openai.yaml`: Skill UI metadata
- `codex/skills/sync-codex-claude-skills/scripts/sync_skills.py`: Compare/sync helper script

## Artifacts

| File | Description |
|------|-------------|
| `task-progress-artifacts/sync-skill-validation.txt` | Script status output, dry-run plan, and validator output |

## Next Steps

- [ ] Restart Codex to load the new skill in the active session
- [ ] Use `$sync-codex-claude-skills` for future drift checks and one-command subset/all syncs
