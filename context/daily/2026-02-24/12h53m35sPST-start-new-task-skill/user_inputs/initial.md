# Task: Implement start-new-task Skill + save-task-status Updates

**Captured**: 2026-02-24 ~12:53pm PST

## Original Description

> Implement the following plan: start-new-task Skill + save-task-status Updates

Plan was provided in detail covering:
1. Create `/start-new-task` skill to scaffold task folders with `user_inputs/` directory
2. Update `/save-task-status` to be aware of `user_inputs/` and new naming convention
3. Update `CLAUDE.md` to reference new workflow and conventions
4. Update `codex/AGENTS.md` to stay aligned with Claude conventions
5. Later addition: create `get-task-status-file` skill to print full path of relevant task status files

## Extracted Requirements

- Time-prefixed folder names: `<HH>h<MM>m<SS>sPST-<slug>`
- PST timezone convention for all timestamps
- `user_inputs/` directory as immutable record store
- Backward compatibility with legacy folders
- Both thin and rich templates for `user_inputs/initial.md`
- `get-task-status-file` skill for resolving and printing task file paths
