---
name: sync-codex-claude-skills
description: Compare, audit drift, and sync skills between botfiles-style visible skill trees (`claude/skills`, `codex/skills`) or hidden project-local skill trees (`.claude/skills`, `.codex/skills`), and sync local Codex skills against upstream skill repositories such as OpenAI curated skills or the Oracle skill with protected local forks. Use when the user asks to keep skills aligned across Claude and Codex, compare local skills to upstream, sync all or selected skills, or identify where drift exists.
---

# Sync Codex Claude Skills

Compare skill directories across Claude and Codex, and compare local Codex skills against upstream skill repositories. Use dry-run first, then apply only the changes you intend.

## Script

Use:

```bash
python ~/pro/botfiles/codex/skills/sync-codex-claude-skills/scripts/sync_skills.py ...
```

For upstream curated sync:

```bash
python ~/pro/botfiles/codex/skills/sync-codex-claude-skills/scripts/sync_upstream_skills.py ...
```

The script auto-discovers repo root from the current directory. It supports both the botfiles/global visible layout (`claude/skills`, `codex/skills`) and the normal hidden project-local layout (`.claude/skills`, `.codex/skills`). If needed, pass an explicit root:

```bash
python scripts/sync_skills.py --repo-root ~/pro/botfiles ...
```

The upstream sync script uses `upstream_sync_policy.json` in this skill directory by default. Pass `--policy` for other upstreams, such as the Oracle skill.

## Layout Convention

- For ordinary project-local skills, prefer `.claude/skills` and `.codex/skills`.
- Treat visible `claude/skills` and `codex/skills` as the botfiles/global exception unless a repo clearly documents a different convention.
- Botfiles uses visible skill directories because user-level global skill paths are symlinked there for source control and easier inspection.

## Workflow A: Claude <-> Codex

### 1. Check drift first

```bash
python scripts/sync_skills.py status
```

This reports:

- skills only in the active Claude skill root (`claude/skills` or `.claude/skills`)
- skills only in the active Codex skill root (`codex/skills` or `.codex/skills`)
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

## Workflow C: Oracle Upstream Drift Check

The Oracle skill is derived from `steipete/oracle:skills/oracle`, but it is a protected local workflow fork because it carries local GPT-5.5 Pro browser defaults and fallback policy. Use this workflow to check drift against upstream. Do not overwrite the local Oracle skill unless you are intentionally refreshing from upstream and then reapplying the local policy.

### 1. Check Oracle drift

```bash
python scripts/sync_upstream_skills.py \
  --repo-root ~/pro/botfiles \
  --policy upstream_oracle_policy.json \
  status
```

### 2. Dry-run Oracle refresh

```bash
python scripts/sync_upstream_skills.py \
  --repo-root ~/pro/botfiles \
  --policy upstream_oracle_policy.json \
  sync --skills oracle
```

### 3. Apply Oracle refresh

```bash
python scripts/sync_upstream_skills.py \
  --repo-root ~/pro/botfiles \
  --policy upstream_oracle_policy.json \
  sync --skills oracle --force-protected --apply
```

This replaces `codex/skills/oracle` from upstream and mirrors the changed Oracle skill into `claude/skills/oracle`. Afterward, reapply the local GPT-5.5 Pro browser defaults, validate both skill copies, and re-check the Oracle awaiter agents and global instructions for drift.

## Post-Sync Checks

After apply:

1. Re-run `status` and confirm drift decreased as expected
2. For new/updated Codex skills, run:
   `python ~/pro/botfiles/codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>`
3. Restart tool sessions if needed so refreshed skills are loaded
