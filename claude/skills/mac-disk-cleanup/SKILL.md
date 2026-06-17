---
name: mac-disk-cleanup
description: Safely audit and clean macOS disk space with read-only baselines, approval-gated cleanup batches, Docker/Xcode/cache/log cleanup, verification, and task artifacts. Use when the user asks to free Mac disk space, clean Mac storage, reclaim disk space on macOS, investigate a near-full Mac, audit caches or developer artifacts, or create a repeatable Mac cleanup workflow.
---

# Mac Disk Cleanup

Use this skill to reclaim macOS disk space without accidental data loss.

The default workflow is: read-only audit, trusted-tool research, action table, explicit batch approval, cleanup, verification, and durable notes.

## Safety Rules

- Do not run destructive commands until the user approves the exact batch.
- Treat user media, Documents, Downloads, browser profiles, app support data, secrets, project data, active worktrees, virtualenvs, Docker volumes, Photos libraries, and external-drive moves as protected by default.
- Do not use `/Volumes/*` as an archive destination unless the user explicitly includes archive/offload scope.
- Ask narrowly for macOS privacy permissions only when a blocked path matters to an approved cleanup branch.
- Save one-off audit and cleanup scripts under the active task's `task-progress-artifacts/scratchpad/` before running them.
- Capture before/after evidence for every cleanup batch.

## Read-Only Audit

Start with bounded checks:

```bash
df -h / /System/Volumes/Data /Volumes/* 2>/dev/null
tmutil listlocalsnapshots / 2>&1
du -sh "$HOME/.cache" "$HOME/.npm" "$HOME/Library/Caches" "$HOME/Library/Logs" "$HOME/Library/Developer" 2>&1
```

Then inspect likely candidates, keeping output bounded:

- `~/.cache` children.
- `~/Library/Caches` children.
- `~/Library/Logs` children.
- `~/Library/Developer/Xcode/DerivedData`, `Archives`, `iOS DeviceSupport`.
- `~/Library/Developer/CoreSimulator`.
- package-manager cache paths from owner commands.
- Docker state from `docker system df`.
- selected project build artifacts such as `build`, `dist`, `.next`, `target`, `node_modules`, `.venv`, and cache directories, without deleting them.
- user-facing folders such as Downloads/Documents only for size review.

Avoid broad recursive scans when the disk is critically low or macOS privacy blocks many subtrees.

## Trusted Cleanup Mechanisms

Prefer owner commands over manual deletion:

- Homebrew: `brew cleanup --dry-run --prune=all` before `brew cleanup --prune=all`.
- npm: `npm config get cache`; `npm cache clean --force` only with approval.
- pnpm: `pnpm store path`; `pnpm store prune`.
- uv: `uv cache dir`; prefer `uv cache prune` over `uv cache clean`.
- pip: `pip3 cache info`; `pip3 cache purge`.
- Docker: `docker system df`; `docker system prune -af` only when volumes should be preserved.
- Xcode simulators: `xcrun simctl list devices unavailable`; `xcrun simctl delete unavailable` only if useful.

For current behavior, check installed help (`<tool> --help`) and official docs when needed. Record what was reused, avoided, or adapted.

## Action Table

Before cleanup, write an action table with:

- path or command
- size/evidence
- risk
- exact proposed action
- reversibility
- approval status

Recommended batch categories:

- High-dividend generated data: Docker unused images/build cache without volumes, Xcode DerivedData, large app logs.
- Smaller package caches: Homebrew, npm, pnpm, uv, pip.
- Developer project artifacts: generated build outputs and dependency directories, only after repo/worktree review.
- User-facing files: Downloads/Documents/media, only with path-level approval.
- Browser/app support data: usually defer; browser profiles are not cache.

## Proven High-Dividend Pattern

On a near-full Mac, this approved batch reclaimed meaningful space:

```bash
docker system prune -af
rm -rf "$HOME/Library/Developer/Xcode/DerivedData"/*
rm -rf "$HOME/Library/Logs/activitywatch"
```

Important constraints:

- Do not add `--volumes` to Docker prune unless the user explicitly approves volume deletion.
- `docker system prune -af` removes stopped containers, unused networks, unused images, and build cache; images may need rebuild or re-pull later.
- Xcode DerivedData is generated build data and will be recreated.
- Running apps may recreate log directories during deletion; verify final size rather than treating a tiny leftover log directory as failure.

## Verification

After each approved batch:

```bash
df -h / /System/Volumes/Data
du -sh <approved-targets> 2>&1
docker system df 2>&1
```

Record:

- before and after free-space numbers
- command transcript
- target sizes before/after
- nonzero exit statuses and whether they are material
- skipped/deferred items
- recovery notes, such as "rebuild Docker image" or "Xcode will recreate DerivedData"

For tracked tasks, update `status.md`, save curated summaries under `task-progress-artifacts/`, and keep raw logs in `task-progress-artifacts/scratchpad/`.
