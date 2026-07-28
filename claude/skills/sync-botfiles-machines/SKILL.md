---
name: sync-botfiles-machines
description: Safely inventory, reconcile, clean, and synchronize divergent botfiles Git checkouts and layered Codex configuration across the canonical cloud host and client machines. Use for dirty Mac/VM botfiles trees, ahead/behind main histories, machine-local Codex runtime state, generated agent artifacts, or branch-to-main integration and verification.
---

# Sync Botfiles Machines

Reconcile authored changes without committing machine state, secrets, or
generated/vendor material. Treat `research-cpu-01` as the canonical integration
host and `sourya-mac` as a synchronized client unless current instructions say
otherwise.

## Safety Contract

- Read each checkout's `AGENTS.md` before changing it.
- Inspect every machine before fetching, cleaning, switching branches, or
  updating remote `main`.
- Never assume similarly named commits are identical; use `git cherry`, patch
  IDs, and final-tree diffs.
- Never force-push, rewrite a shared branch, or run the full setup script as
  root.
- Never copy `secrets/local/`, raw user configs, credentials, auth state,
  plugin caches, marketplace materializations, or generated vendor trees
  between machines or into Git-backed task artifacts.
- Do not delete an untracked path until it is positively classified. Preserve
  unknown or authored material for review.
- Keep original dirty checkouts untouched while integrating. Use an isolated
  worktree when their state conflicts with branch operations.
- Require explicit approval before updating remote `main`.

## 1. Resolve Hosts And Task Evidence

1. Confirm canonical and client checkout paths.
2. Resolve SSH aliases from
   `~/pro/personal_os/context/machine-ssh-aliases.md` when needed.
3. Use the active task folder's `task-progress-artifacts/scratchpad/` for raw,
   redacted inventories and recovery evidence.
4. Store raw config backups only in a private machine-local directory with mode
   `0700`; keep that path out of Git.
5. Record a curated reconciliation ledger under `task-progress-artifacts/`.

## 2. Capture Every Git State

Run `scripts/capture-state.sh` locally on each host before mutation:

```bash
bash scripts/capture-state.sh \
  --repo "$HOME/pro/botfiles" \
  --output "<task-scratchpad>/snapshot-<host>-before"
```

Copy remote Git-only snapshots into the task folder when practical and verify
`sha256sums.txt`. The helper captures committed refs, a binary tracked patch,
status/history/divergence reports, and an untracked filename manifest; it does
not archive untracked contents.

Also verify live remote `main` with `git ls-remote origin refs/heads/main`.

## 3. Classify Differences

Classify every committed and worktree difference:

- **portable authored source**: retain and validate;
- **machine-local configuration**: preserve locally and keep out of Git;
- **generated/vendor state**: ignore narrowly and remove only when reproducible
  and not required at runtime;
- **unknown**: preserve and review.

Keep Codex/Claude skill counterparts synchronized unless a capability is
explicitly product-managed and surface-specific. Treat `codex/skills/.system/`
and app-injected skills as machine-managed. Do not vendor upstream curated
skills merely because a symlink made them appear inside the repository.

For overlaps, compare final hashes or stable patch IDs. Auto-resolve only
byte-identical or patch-equivalent changes. Present one focused user decision
for authored conflicts, unknown files, destructive cleanup, or a change in
canonical intent; preserve and defer when no answer is available.

## 4. Reconcile History

1. Fetch each checkout only after snapshots exist.
2. Create `codex/<tracker>-botfiles-sync` from current `origin/main` in an
   isolated worktree.
3. Run `git cherry -v origin/main <source-main>` and
   `git log --left-right --cherry-mark`.
4. Replay unique commits in original order and skip patch-equivalent commits.
5. Resolve conflicts by newest reviewed intent, not by choosing an entire side.
6. Use `git range-diff` and `git diff --check` to prove the replay.

Do not cherry-pick a temporary add/remove sequence out of order. Preserving
both commits is acceptable when provenance matters and the final net state is
correct.

## 5. Integrate Dirty Worktrees

Apply captured tracked patches with three-way context or import reviewed files
explicitly. Commit coherent groups such as wrappers, task helpers, paired
skills, instructions, layered configuration, and cleanup rules.

Before every commit:

- inspect staged filenames and the full staged diff;
- run `git diff --cached --check`;
- scan staged content for private keys and common token shapes;
- validate affected shell, Python, JSON, TOML, YAML, and skill files.

Restore ambiguous deletions unless evidence proves they were intentional.

## 6. Preserve The Codex Layer Boundary

Use native Codex configuration precedence:

- `/etc/codex/config.toml` is a root-owned symlink to the checked-out
  `codex/config.system.toml`;
- `~/.codex/config.toml` is a regular mode-`0600` machine-local file;
- the system base owns authored portable defaults, the accepted shared MCPs,
  and only plugins proven supported on every required surface;
- the user file owns project trust, notice/migration state, desktop/runtime
  tables, marketplace paths and timestamps, credentials, and host-only
  integrations;
- local or plugin-injected MCP additions are allowed;
- an enumerated Mac notification override may shadow portable `notify`.

Never union, copy, merge, delete, or compare local trust/runtime values as
content that should be identical. Never use a Git clean filter,
`skip-worktree`, `assume-unchanged`, a generated active config, implicit
profiles, or `CODEX_HOME` as production routing.

Ordinary `setup.sh` must not rewrite the active user config. Use
`bin/install-codex-system-config --apply` for the single elevated system-link
action.

## 7. Verify Layering And Runtime Support

Run the read-only verifier on each host:

```bash
python3 scripts/verify-config-layers.py \
  --repo "$HOME/pro/botfiles" \
  --machine "<machine-name>" \
  --output "<task-scratchpad>/config-layers-<machine>.json"
```

On the Mac, add `--allow-user-override notify` when its Desktop notifier is
present.

The verifier reports names, layer origins, and status only. It checks:

- portable and user TOML parsing;
- root-owned system symlink target;
- regular mode-`0600` user config;
- prohibited system/local ownership categories;
- unapproved key collisions;
- app-server layer discovery and effective origins;
- the accepted six-MCP subset while allowing local additions;
- Zotero router, credential-mode, and server launch prerequisites;
- the evidence-backed installed plugin subset.

Treat TOML plugin entries as intent, not runtime proof. Use native
`codex plugin list --json` and marketplace discovery; never copy runtime caches
between hosts.

## 8. Migrate And Exercise Rollback

1. Back up the exact legacy user symlink and dereferenced config contents in the
   host's private mode-`0700` state directory.
2. Install the system symlink while the legacy user symlink remains.
3. Prove system-layer discovery before replacing either user config.
4. Cut over the canonical GCP host first; validate, restore the exact legacy
   arrangement, then reapply and validate again.
5. Stop Mac Desktop, repeat the cutover/rollback/reapply sequence, then restart
   and validate Desktop plus CLI.
6. Compare only the accepted portable subset across hosts.

Keep rollback backups until the landed-state reviewer handoff is complete.

## 9. Validate And Request Landing

Run proportionate checks:

- `bash -n` for shell files;
- Python compilation and focused tests;
- JSON/TOML/YAML parsing;
- Codex/Claude counterpart comparison;
- skill `quick_validate.py`;
- setup idempotence and wrapper failure/success paths;
- `git diff --check`, staged secret scans, and full final diff review.

Correct reasonable task-scoped defects and rerun affected gates. Stop before
landing for a material architecture/scope change, weakened security or
rollback, destructive ambiguity, or unresolved required capability.

Present compact redacted evidence and obtain explicit landing approval.

## 10. Land, Synchronize, And Handoff

After approval:

1. Confirm the candidate is clean and based on live remote `main`.
2. Fast-forward and push `main` without force or a merge commit.
3. Preserve post-snapshot changes and fast-forward every client checkout.
4. Repoint system symlinks to each canonical landed checkout and run setup only
   where needed.
5. Run `scripts/verify-pair.sh` and the layer verifier on every host.
6. Confirm exact `HEAD == main == origin/main`, the accepted config contract,
   and only documented local state.
7. Record SHAs, retained/skipped changes, cleanup, tests, exceptions, and
   rollback locations.
8. Move the tracker to `Review`, not `Done`, with a reviewer-facing handoff.
