---
name: finish-task
description: >-
  Standardize end-of-task closeout when the user asks to finish, wrap up,
  merge-and-close, land, or otherwise cleanly close a tracked task or PR,
  including task-status sync, tracker notes/state changes, downstream
  heads-up checks, and local branch/worktree cleanup.
---

# Finish Task

Run the full closeout flow only when the goal is to land or close work, not when
the task still needs implementation or review fixes.

## Invocation

```text
/finish-task [optional task target]
```

If no target is provided, resolve the current task for this session with
`get-task-details`.

## Reuse Existing Helpers

- `get-task-details` for the current task metadata and status path
- `save-task-status` for status updates before and after closeout
- `pr-autoreview-loop` when the repo has a current-head reviewer/check workflow
- `gh` for GitHub PR and issue operations
- `git` for branch and worktree cleanup

## Step 1: Resolve the task and repo surfaces

1. Resolve the active task with `get-task-details` unless the user already gave
   an exact `status.md`, task folder, repo root, or tracker/PR URL.
2. Read the resolved status file and identify every repo involved:
   - the code repo or worktree that owns the implementation
   - the task-tracking repo (for example `personal_os`) when it differs from
     the code repo
   - task artifact folders such as `context/daily/.../<task-slug>/` that need
     to be committed as durable closeout context
   - whether each repo uses a dedicated task branch/PR or intentionally works
     on its default branch, such as `personal_os` tasks done directly on `main`
   - tracker surfaces such as Linear issues, GitHub issues, PRs, and any
     downstream linked tasks
3. Capture the current local state before touching anything:
   - `git status -sb`
   - `git branch --show-current`
   - `git worktree list`
   - `gh pr status` or `gh pr view <number>` when the repo uses GitHub PRs

## Step 2: Gate on closeout readiness

Do not treat `finish-task` as permission to force-close unfinished work.

- If the task still has outstanding implementation, review findings, failing
  checks, or missing human approval, stay in the active workflow and explain
  what remains.
- For PR-bearing tasks, confirm that the current-head reviewer/check sweep is
  clean before merging. If the repo already uses `pr-autoreview-loop`, prefer:

  ```bash
  pr-autoreview-loop status --repo "<repo-root>" --pr <number|url>
  ```

- If there are multiple candidate PRs, multiple repos, dirty uncommitted
  changes, or unclear merge strategy, stop and ask the smallest targeted
  question needed to disambiguate.
- For no-dedicated-branch tasks, do not require or invent a PR. Confirm the
  work is on the expected default branch, usually `main`, and that the relevant
  task context folder is included in the intended commit/push set.
- For cross-repo tasks coordinated from `personal_os`, treat uncommitted
  `context/` task artifacts as part of closeout readiness. Do not close the
  external PR or tracker while the corresponding task context folder is still
  uncommitted unless the user explicitly chooses a different bookkeeping plan.

## Step 3: Ask for explicit confirmation before destructive actions

Get an explicit yes before any action that can delete, close, or merge. Treat
these as separate toggles when the user's request did not already specify them:

- merge the PR or land the branch
- delete the remote branch
- delete local branches or remove worktrees
- move a tracker to `Done` or close a GitHub issue
- commit or push task context artifacts to a default branch such as
  `personal_os/main`
- create bookkeeping commits in a task-tracking repo such as `personal_os`
- close a dedicated zellij session

If the user explicitly asked for a full merge-and-close flow, that counts as
permission for the matching items above, but still surface any ambiguity first.

## Step 4: Execute closeout in a safe order

1. Update local task state first.
   - Refresh the task `status.md`
   - Record final validation, merge intent, and any residual risk
   - Run `save-task-status` before external writes so the task record reflects
     the pre-merge state
   - If the task does not have a dedicated branch and is meant to land on the
     current repo's default branch, keep the relevant implementation files and
     the task context folder in scoped commits on that same branch.
   - If a task-tracking repo such as `personal_os` owns closeout artifacts that
     belong in version control, commit and push that bookkeeping deliberately in
     the same closeout sequence. For cross-repo work, this is usually a separate
     `personal_os` commit/push alongside the code repo PR merge, not a hidden
     addition to the code repo PR.
2. Land the code change if applicable.
   - Ensure the working tree is intentionally clean
   - Merge with the repo's expected strategy or the user's specified strategy
   - Prefer `gh pr merge` so the PR timeline and branch deletion stay in sync
   - Run any repo-specific deploy, release, migration, or dependency follow-up
     that the PR or task explicitly requires
3. Handle downstream follow-ups.
   - Check `blocks`, `blockedBy`, related issues, linked roadmap/docs, and
     release trackers
   - Leave short heads-up notes only where the closeout changes somebody
     else's next step
4. Close the tracker surfaces.
   - Post a closing note that states what landed, what was validated, where it
     merged, and any concrete follow-up still left
   - Preserve the GitHub authorship byline on GitHub comments or issue edits
   - Move Linear or GitHub trackers to their terminal state only after the
     merge or explicit local-only closure is complete
5. Clean local state last.
   - Switch remaining checkouts back to the updated default branch when
     appropriate
   - Delete merged local branches
   - Remove task-specific worktrees only when they are clean and no longer
     needed
   - Close a dedicated zellij session only if the user asked for it or it
     clearly exists just for this finished task
6. Re-run `save-task-status` if metadata, tracker state, or artifact links
   changed during closeout.

## Step 5: Final response

Report only the concrete closeout results:

- what merged, landed, or closed
- what tracker notes or downstream heads-ups were posted
- what local cleanup ran
- what concrete next steps remain, if any

## Special cases

- No PR exists: still use this flow for local-only or tracker-only closeout;
  skip PR merge steps. If the work was intentionally done on the default branch,
  verify the scoped commit/push that lands the task, including any relevant
  `context/` folder, before closing the tracker.
- Multiple repos are involved: treat the code repo and the task-tracking repo
  as separate closeout surfaces that must both be handled in the same closeout
  sequence; do not assume one PR should contain both.
- Dirty or unrelated changes are present: do not delete branches/worktrees or
  auto-close the task until the user explicitly decides how to handle them.
- If the repo has no `gh` auth, no tracker auth, or no deterministic way to
  inspect PR state, stop after the local status update and ask for the missing
  access.
