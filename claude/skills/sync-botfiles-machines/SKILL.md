---
name: sync-botfiles-machines
description: Safely inventory, reconcile, clean, and synchronize divergent botfiles Git checkouts across the canonical cloud host and one or more client machines. Use for dirty Mac/VM botfiles trees, ahead/behind main histories, machine-specific Codex configuration churn, generated agent artifacts, or branch-to-main integration and verification.
---

# Sync Botfiles Machines

Reconcile every authored change without committing machine state, secrets, or
generated/vendor material. Treat `research-cpu-01` as the canonical integration
host and `sourya-mac` as a synchronized client unless current instructions say
otherwise.

## Safety Contract

- Read each checkout's `AGENTS.md` before changing it.
- Inspect both machines before fetching, cleaning, switching branches, or
  updating remote `main`.
- Never assume that similarly named commits are identical; use `git cherry`,
  patch IDs, and final-tree diffs.
- Never force-push or rewrite a shared branch.
- Never copy `secrets/local/`, credentials, auth state, editor swap files, or
  generated vendor trees into a recovery archive.
- Do not delete an untracked path until it is positively classified. Preserve
  unknown or authored material and stop for review when material ambiguity
  remains.
- Keep original dirty checkouts untouched while integrating. Use an isolated
  worktree when their state conflicts with branch operations.
- Update remote `main` only after both source states are captured, the complete
  integration diff is reviewed, and validation passes.

## 1. Resolve Hosts And Task Evidence

1. Confirm the canonical and client checkout paths.
2. Resolve SSH aliases from
   `~/pro/personal_os/context/machine-ssh-aliases.md` when needed.
3. Use the active task folder's `task-progress-artifacts/scratchpad/` for raw
   inventories and recovery files.
4. Record a curated reconciliation ledger under `task-progress-artifacts/`.

## 2. Capture Both States

Run `scripts/capture-state.sh` locally on each host before mutation:

```bash
bash scripts/capture-state.sh \
  --repo "$HOME/pro/botfiles" \
  --output "<task-scratchpad>/snapshot-<host>-before"
```

Copy remote snapshot outputs into the task folder when practical. Verify
`sha256sums.txt`. The script captures committed refs in a Git bundle, a binary
tracked patch, status/history/divergence reports, and an untracked filename
manifest; it does not archive untracked contents.

Also verify live remote `main` with `git ls-remote origin refs/heads/main`.

## 3. Classify Differences

Classify every committed and worktree difference:

- **portable authored source**: retain and validate;
- **machine-local configuration**: keep out of the canonical Git
  representation and document;
- **generated/vendor state**: ignore narrowly and remove only when reproducible
  and not required at runtime;
- **unknown**: preserve and review.

Keep Codex/Claude skill counterparts synchronized unless the capability is
explicitly product-managed and surface-specific. Treat `codex/skills/.system/`
and app-injected runtime skills as machine-managed. Do not vendor upstream
curated skills merely because a symlink caused them to appear inside the repo.

For overlapping worktree files, compare final hashes or stable patch IDs before
choosing a copy. Import only the unique side when content is identical.

## 4. Reconcile History

1. Fetch each checkout after snapshots exist.
2. Create `codex/<tracker>-botfiles-sync` from current `origin/main` in an
   isolated worktree.
3. Run `git cherry -v origin/main <source-main>` and
   `git log --left-right --cherry-mark`.
4. Replay unique commits in original order. Skip patch-equivalent commits.
5. Resolve conflicts by newest reviewed intent, not by choosing an entire side.
6. Use `git range-diff` and `git diff --check` to prove the replay.

Do not cherry-pick a temporary add/remove sequence out of order. Preserving
both commits is acceptable when provenance matters and their final net state is
correct.

## 5. Integrate Dirty Worktrees

Apply each captured tracked patch with three-way context or import reviewed
files explicitly. Keep configuration changes separate until their portability
strategy is settled.

Commit in coherent groups such as wrappers, shared task helpers, paired skills,
instructions, configuration, cleanup rules, and this synchronization workflow.
Before each commit:

- inspect the staged filenames and diff;
- run `git diff --cached --check`;
- scan staged content for private keys and common token shapes;
- validate the affected shell, Python, JSON, TOML, YAML, or skill files.

Restore ambiguous deletions unless evidence proves they were intentional.

## 6. Handle Codex Configuration

Prefer one reviewed portable configuration where feasible. Exhaustive
machine-specific project trust entries can coexist.

Separate durable preferences from runtime-owned state such as marketplace
cache paths/timestamps, app-bundled executable paths, app-versioned hashes,
desktop runtime tables, or machine-specific notification wrappers. If the repo
uses a canonicalizing Git clean filter:

- make the filter deterministic and fail closed;
- declare it in `.gitattributes`;
- install it with `filter.<name>.required=true` from `setup.sh`;
- preserve the raw active file for the local app while ensuring the index
  contains only canonical portable content;
- provide a verifier and a raw-config diagnostic path;
- test status cleanliness after realistic app regeneration on every host.

Do not use `skip-worktree` or `assume-unchanged` for the shared config. Manual
stash/pop is a recovery tool, not a durable synchronization design.

## 7. Clean And Validate

Use repository ignores for universally generated artifacts and
`.git/info/exclude` for documented host-local vendor/runtime directories that
should remain installed. Avoid broad patterns that can hide authored source.

Run proportionate checks:

- `bash -n` for changed shell files;
- Python compilation and focused tests for changed scripts;
- JSON/TOML/YAML parsing;
- Codex/Claude counterpart comparison;
- skill `quick_validate.py`;
- config-filter index and regeneration tests when applicable;
- `git diff --check`, staged secret scans, and full final diff review.

Confirm the pre-change bundles and patches remain readable.

## 8. Land And Synchronize

1. Confirm the integration branch is clean and based on current remote `main`.
2. Fast-forward local `main` to the validated integration head.
3. Push `main` without force.
4. On every client, preserve any post-snapshot changes, fetch, and fast-forward
   `main`.
5. Reapply only reviewed local runtime state or run setup as required.
6. Run `scripts/verify-pair.sh` from the canonical host:

```bash
bash scripts/verify-pair.sh \
  --local-repo "$HOME/pro/botfiles" \
  --remote-host sourya-mac \
  --remote-repo '$HOME/pro/botfiles'
```

Success requires both checkouts on `main`, identical to live remote `main`, and
clean except for explicitly documented ignored local state.

## 9. Handoff

Record:

- original and final SHAs for every machine and remote;
- retained commits and worktree groups;
- skipped patch-equivalent commits;
- ignored/removed generated paths;
- tests and secret scans;
- remaining local-only exceptions and rollback locations.

Move the tracker to `Review`, not `Done`, and leave a reviewer-facing comment
covering changes, verification, risks, and reviewer asks.
