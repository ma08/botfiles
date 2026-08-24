---
name: personal-os-repo-cleanup
description: Use when the user asks to commit, clean, audit, reconcile, push, pull, or coordinate dirty personal_os changes across the VM and Mac checkouts, especially when live task-specific sessions may own folders, orphaned artifacts need curated commits, or divergent main histories must be synchronized safely.
---

# Personal OS Repo Cleanup

## Overview

Coordinate cleanup and synchronization of `~/pro/personal_os` across machines without trampling live task owners. By default, finish by reconciling committed histories with the remote, pushing the canonical merged `main`, and pulling or fast-forwarding each checkout. Preserve useful task evidence, local dirty work, and secrets.

## Workflow

1. Create or reuse a tracking task folder in `context/daily/YYYY-MM-DD/...`.
   Record the user request, scope, and running checklist in `status.md`. For complex cleanup, create a goal so progress can survive context shifts.

2. Inventory both repositories before changing anything.
   Use `git status --porcelain=v1 -uall` for the local VM checkout. For the Mac, use the configured SSH alias, usually:

   ```bash
   ssh sourya-mac 'cd ~/pro/personal_os && git status --porcelain=v1 -uall'
   ```

   Save inventories, grouped summaries, and any helper scripts under the active task's `task-progress-artifacts/scratchpad/`.

3. Group dirty paths by ownership.
   Treat `context/daily/<date>/<task-slug>/...` as task-owned. Treat root files such as `.gitignore`, `CLAUDE.md`, `scripts/`, `output/`, and root `task-progress-artifacts/` as non-task work requiring separate review. Use task metadata, transcripts, and zellij listings to decide whether a live owner exists.

4. Delegate only to clearly reachable owners.
   When a task has an active, unambiguous zellij/Codex owner, use `$cross-session-message` preview-first, then send a bounded commit instruction with `--execute --submit enter`. Record target session, tab, task group, and requested commit message. If the session is missing, ambiguous, ended, or is just a shell/gitui workspace, this cleanup session owns the commit.

5. Keep the git index safe.
   All sessions in a shared checkout share one index. Before staging, confirm `git diff --cached --name-only` is empty or contains only the scope you intend. If another session is working, prefer waiting or rechecking over committing a mixed index.

6. Stage explicitly and commit logically.
   Use pathspec files or explicit paths. Split commits by natural scope, for example delegated task artifacts, orphaned backlog artifacts, non-task utilities, Mac artifacts, and cleanup-skill/tracking files. Do not use broad `git add .` unless the status output has already been reduced to the exact intended scope.

7. Use curated-only handling for bulk artifacts.
   Commit status files, user inputs, small scripts, summaries, reports, screenshots, and other human-reviewable evidence. Leave generated checkouts, caches, archives, model weights, databases, extracted text dumps, dependency folders, and sensitive-looking scratch files local-only by adding exact paths to `.git/info/exclude`. Prefer `.git/info/exclude` over `.gitignore` for one-machine task leftovers.

8. Run staged safety checks before every commit.
   At minimum run:

   ```bash
   git diff --cached --name-only
   git diff --cached --check
   ```

   Also scan staged text for obvious secret material without printing values: private-key blocks, AWS access keys, GitHub tokens, OpenAI-style keys, and Google API keys. If a scan hits, unstage and exclude or inspect the file. Generic variable names such as `API_KEY=` are not by themselves a secret.

9. Preserve archival artifacts unless they are unsafe.
   If `git diff --cached --check` reports whitespace in captured logs, HTML, CSVs, or model output, record that and commit as-is when the secret scan is clean. Do not rewrite archived evidence merely to satisfy whitespace checks.

10. Commit tooling fixes separately in the owning repo.
    If a helper or skill bug blocks the cleanup, fix and commit the narrow tooling change in its own repository. Leave unrelated dirty files in that repo untouched.

11. Reconcile committed histories with the remote by default.
    Fetch on every participating machine before pushing. Compare `origin/main`, the canonical GCP `main`, and the Mac `main`. Never force-push or overwrite one machine's commits merely because the other machine is canonical.

    If committed histories diverge, preserve each head with an explicit temporary branch or ref, then merge them from a clean checkout. A short-lived merge worktree is an allowed exception to the normal Personal OS no-worktree default when the real checkouts contain substantial preserved dirt. State the exception before creating it. Resolve conflicts from task ownership, chronology, and saved evidence. Do not guess through a material content conflict.

12. Preserve local dirt while updating real checkouts.
    Before fast-forwarding a dirty checkout, compute the exact intersection between incoming changed paths and current dirty paths. Prefer an exact-path stash for only that intersection. Record the stash ref, update the checkout, then reapply the stash and verify that no local work disappeared. Avoid stashing large unrelated scratch trees when they do not overlap the incoming history.

13. Push and pull unless the user opts out.
    Push the reconciled canonical `main` to `origin/main`, then fetch and fast-forward the VM and Mac checkouts so their committed histories match the remote. Do not push temporary reconciliation branches unless needed for safe transport; delete them after successful verification when doing so is safe. If credentials or branch protection block synchronization, report the exact blocker.

14. Verify and report final state.
    Re-run status and divergence checks on VM, Mac, and remote. Confirm commits created, conflict resolutions, restored local changes, deliberately local-only paths, and any remaining issues.

## Human interaction budget

- Resolve routine ownership, staging, merge, and stash decisions from repository evidence.
- Ask only when a conflict or destructive choice has more than one materially different safe answer.
- Ask no more than five questions during one cleanup run. Prefer one concise question at a time and group tightly related decisions when that reduces interruption.
- If five questions are exhausted, stop before the unresolved risky action, preserve all refs and worktrees, and report the exact remaining decision.

## Useful Commands

Group current dirty paths:

```bash
git status --porcelain=v1 -uall |
  awk '{print $2}' |
  awk -F/ '$1=="context"&&$2=="daily"{print $1"/"$2"/"$3"/"$4; next}{print $1}' |
  sort | uniq -c | sort -nr
```

Commit a scoped path list:

```bash
git add --pathspec-from-file=pathspecs-to-commit.txt
git diff --cached --name-only
git commit -m "Commit curated personal OS task artifacts"
```

Mac status and commit:

```bash
ssh sourya-mac 'cd ~/pro/personal_os && git status --short --branch'
ssh sourya-mac 'cd ~/pro/personal_os && git commit -m "Record Mac personal OS task artifacts"'
```

## Completion Criteria

- VM `~/pro/personal_os` has no dirty tracked/untracked changes except the current cleanup task until its final commit.
- Mac `~/pro/personal_os` is clean or has only explicitly deferred local-only paths.
- Live task owners were messaged or ruled unreachable with evidence.
- Every commit has a clear scope and passed staged secret checks.
- The cleanup task status records commits, skipped bulk policy, validation, and follow-up maintenance such as git GC warnings.
- `origin/main` contains the reconciled committed history unless the user opted out or an explicit blocker is recorded.
- VM and Mac committed histories match `origin/main`, with all pre-existing local dirty work restored and documented.
