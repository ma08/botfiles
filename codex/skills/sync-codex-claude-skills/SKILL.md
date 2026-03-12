---
name: sync-codex-claude-skills
description: Compare, audit drift, and sync skills between `claude/skills` and `codex/skills`. Use when user asks to keep skills aligned across Claude and Codex, sync all skills, sync a specific skill or subset, or identify which skills differ between both directories.
---

# Sync Codex Claude Skills

Compare skill directories across Claude and Codex, then safely sync all or selected skills in an explicit direction.

## Script

Use:

```bash
python ~/pro/botfiles/codex/skills/sync-codex-claude-skills/scripts/sync_skills.py ...
```

The script auto-discovers repo root from the current directory. It supports both standard skill directories (`claude/skills`, `codex/skills`) and hidden project skill directories (`.claude/skills`, `.codex/skills`). If needed, pass an explicit root:

```bash
python scripts/sync_skills.py --repo-root ~/pro/botfiles ...
```

## Standard Workflow

### 1. Check drift first

```bash
python scripts/sync_skills.py status
```

This reports:

- skills only in `claude/skills` or `.claude/skills`
- skills only in `codex/skills` or `.codex/skills`
- skills in both but different
- skills in both and identical

### 2. Choose direction and scope

Decide sync direction explicitly:

- `--from-side claude --to-side codex`
- `--from-side codex --to-side claude`

Decide scope:

- `--all` for all source-side skills
- `--skills <name...>` for individual skill(s) or subset

### 3. Dry-run sync (default)

```bash
python scripts/sync_skills.py sync --from-side claude --to-side codex --all
python scripts/sync_skills.py sync --from-side claude --to-side codex --skills start-new-task get-task-details
```

Without `--apply`, script prints plan only (`create`, `replace`, `unchanged`) and makes no changes.

### 4. Apply sync

```bash
python scripts/sync_skills.py sync --from-side claude --to-side codex --all --apply
python scripts/sync_skills.py sync --from-side claude --to-side codex --skills start-new-task --apply
```

Optional pruning when syncing all:

```bash
python scripts/sync_skills.py sync --from-side claude --to-side codex --all --delete-target-extras --apply
```

This removes target-side skills absent from source.

## Behavior Notes

- Sync copies full skill directories from source to target
- Existing target skill directories are replaced when content differs
- Hidden directories inside the skills root (for example `.system`) are ignored
- Only directories containing `SKILL.md` are treated as skills
- Script fails fast if requested `--skills` are missing on source side
- Status output includes the detected repo layout (`visible` or `hidden`)

## Post-Sync Checks

After apply:

1. Re-run `status` and confirm drift decreased as expected
2. For new/updated Codex skills, run:
   `python ~/pro/botfiles/codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>`
3. Restart tool sessions if needed so refreshed skills are loaded
