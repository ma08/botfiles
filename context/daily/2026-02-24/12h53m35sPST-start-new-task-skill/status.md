# Implement start-new-task Skill + save-task-status Updates

**Goal**: Create `/start-new-task` skill, update `/save-task-status`, update CLAUDE.md and AGENTS.md for time-prefixed folder naming and `user_inputs/` convention
**Last Updated**: 2026-02-24 ~12:53pm PST
**Status**: Complete

## User Inputs

- [`user_inputs/initial.md`](user_inputs/initial.md) — original task description and requirements

## Current State

All files created and modified per plan. Implementation is complete and verified.

## Progress

- [x] Create `claude/skills/start-new-task/SKILL.md` — 214 lines, 8-step process, templates, conventions
- [x] Update `claude/skills/save-task-status/SKILL.md` — added user_inputs/ awareness, folder naming, timezone, relationship section, tips
- [x] Update `claude/CLAUDE.md` — updated task folder convention, skill references, PST timezone
- [x] Update `codex/AGENTS.md` — updated task status section with time prefix and PST
- [x] Create `claude/skills/get-task-status-file/SKILL.md` — 82 lines, read-only path resolution skill
- [x] Verify symlink chain: `~/.claude/skills/start-new-task/` and `~/.claude/skills/get-task-status-file/` both resolve correctly

## Code Changes

| File | Change |
|------|--------|
| `claude/skills/start-new-task/SKILL.md` | **Created** — new skill with 8-step process, folder naming, timezone, user_inputs/ contract, thin/rich templates |
| `claude/skills/get-task-status-file/SKILL.md` | **Created** — read-only skill to resolve and print task status file paths |
| `claude/skills/save-task-status/SKILL.md` | **Modified** — Changes A-H from plan: directory structure, user_inputs/ section, naming/timezone, Step 2/3 updates, template updates, relationship section, tips |
| `claude/CLAUDE.md` | **Modified** — Changes A-C: `/start-new-task` reference, folder naming format, user_inputs/ and PST conventions |
| `codex/AGENTS.md` | **Modified** — Change A: time prefix format, PST timezone, backward compat note |

## Next Steps

- [ ] Commit changes
- [ ] Manual verification: invoke `/start-new-task` in a test session
- [ ] Manual verification: invoke `/save-task-status` on the test task
- [ ] Manual verification: invoke `/get-task-status-file` to resolve paths
