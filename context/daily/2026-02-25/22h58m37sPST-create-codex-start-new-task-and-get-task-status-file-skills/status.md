# Add Codex Task-Tracking Skills

**Goal**: Create Codex equivalents of Claude `start-new-task` and `get-task-status-file` skills.
**Last Updated**: 2026-02-25 ~10:58pm PST
**Status**: Complete

## Current State

Both Codex skills were created under `codex/skills/` with full `SKILL.md` instructions and `agents/openai.yaml` metadata. Both pass `skill-creator` quick validation.

## Progress

- [x] Reviewed Claude source skills for `start-new-task` and `get-task-status-file`
- [x] Initialized new Codex skill folders using `init_skill.py`
- [x] Replaced template bodies with Codex-adapted equivalent workflows
- [x] Validated both skills with `quick_validate.py`

## Code Changes

- `codex/skills/start-new-task/SKILL.md`: Added full start-new-task workflow for Codex
- `codex/skills/start-new-task/agents/openai.yaml`: Added skill UI metadata
- `codex/skills/get-task-status-file/SKILL.md`: Added full status-file lookup workflow for Codex
- `codex/skills/get-task-status-file/agents/openai.yaml`: Added skill UI metadata

## Artifacts

| File | Description |
|------|-------------|
| `task-progress-artifacts/skill-creation-validation.txt` | Validation command outputs and git status for newly created skills |

## Next Steps

- [ ] Restart Codex to ensure new skills are loaded into the available skill list
