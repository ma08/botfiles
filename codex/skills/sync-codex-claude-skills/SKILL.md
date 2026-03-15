---
name: sync-codex-claude-skills
description: Compare, audit drift, and sync skills between `claude/skills` and `codex/skills`, and sync local Codex skills against the OpenAI curated skills repo with protected local forks. Use when the user asks to keep skills aligned across Claude and Codex, compare local skills to `openai/skills`, sync all or selected skills, or identify where drift exists.
---

# Sync Codex Claude Skills

Compare skill directories across Claude and Codex, and compare local Codex skills against the upstream OpenAI curated skills catalog. Use dry-run first, then apply only the changes you intend.

## Script

Use:

```bash
python ~/pro/botfiles/codex/skills/sync-codex-claude-skills/scripts/sync_skills.py ...
```

For upstream curated sync:

```bash
python ~/pro/botfiles/codex/skills/sync-codex-claude-skills/scripts/sync_upstream_skills.py ...
```

The script auto-discovers repo root from the current directory. It supports both standard skill directories (`claude/skills`, `codex/skills`) and hidden project skill directories (`.claude/skills`, `.codex/skills`). If needed, pass an explicit root:

```bash
python scripts/sync_skills.py --repo-root ~/pro/botfiles ...
```

The upstream sync script uses `upstream_sync_policy.json` in this skill directory by default.

## Workflow A: Claude <-> Codex

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

## Workflow B: OpenAI Curated -> Codex -> Claude

### 1. Check upstream drift first

```bash
python scripts/sync_upstream_skills.py --repo-root ~/pro/botfiles status
```

This reports:

- `tracked_identical` - overlapping curated skills that already match upstream
- `tracked_drifted` - overlapping curated skills safe to update from upstream
- `protected_drifted` - overlapping skills intentionally protected from overwrite
- `local_only` - local skills with no upstream curated counterpart
- `upstream_only` - curated skills available upstream but not yet vendored locally

### 2. Dry-run the default tracked sync

```bash
python scripts/sync_upstream_skills.py --repo-root ~/pro/botfiles sync
```

Default sync scope is `update existing only`: it considers overlapping curated skills except those protected by policy.

### 3. Apply the tracked sync

```bash
python scripts/sync_upstream_skills.py --repo-root ~/pro/botfiles sync --apply
```

By default this:

- updates changed overlapping curated skills in `codex/skills`
- keeps protected drifted skills untouched
- mirrors the changed skill names into `claude/skills` after the Codex apply

### 4. Add a missing curated skill explicitly

```bash
python scripts/sync_upstream_skills.py --repo-root ~/pro/botfiles sync --skills screenshot --apply
```

Use `--skills <name...>` when you want to vendor a curated skill that currently appears under `upstream_only`.

### 5. Force a protected skill only when intentional

```bash
python scripts/sync_upstream_skills.py --repo-root ~/pro/botfiles sync --skills transcribe --force-protected --apply
```

Without `--force-protected`, a protected drifted skill is reported as `skip-protected` and is not overwritten.

## Behavior Notes

- Sync copies full skill directories from source to target
- Existing target skill directories are replaced when content differs
- Hidden directories inside the skills root (for example `.system`) are ignored
- Only directories containing `SKILL.md` are treated as skills
- Script fails fast if requested `--skills` are missing on source side
- Status output includes the detected repo layout (`visible` or `hidden`)
- Upstream defaults come from `upstream_sync_policy.json`
- Protected skills are for intentional local forks or local-only workflows that should not be overwritten by upstream drift checks

## Post-Sync Checks

After apply:

1. Re-run `status` and confirm drift decreased as expected
2. For new/updated Codex skills, run:
   `python ~/pro/botfiles/codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>`
3. Restart tool sessions if needed so refreshed skills are loaded
