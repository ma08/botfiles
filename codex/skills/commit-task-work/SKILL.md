---
name: commit-task-work
description: Commit task-scoped work across personal_os task artifacts and any external codebases touched by the task. Use when the user asks to commit relevant files, save task work in git, commit personal_os context files, commit a task folder, or commit changes spanning personal_os plus another repo. Infer the active task and branches from context; stage only related paths; ask before committing an external repo when the branch or ownership is ambiguous.
---

# Commit Task Work

Commit only the work that belongs to the current task, even when several repos have unrelated dirty state.

## Workflow

1. Resolve the task scope.
   - Prefer an explicit task folder, status file, tracker id, branch name, or paths from the conversation.
   - If unclear, run `get-task-details` or inspect recent task folders under `context/daily/`.
   - Treat the task folder in `personal_os` as the durable notes/artifacts scope.

2. Identify repos touched by the task.
   - Always check `personal_os` when task notes or artifacts were created there.
   - Check external codebases mentioned in the status file, task artifacts, current branch, recent commands, or user prompt.
   - Use `git -C <repo> status --short --branch` for each repo.

3. Classify each repo before staging.
   - `personal_os`: usually commit task folders and task-specific support files on `main`; do not stage unrelated dirty files elsewhere in the repo.
   - External code repo with a task-specific feature branch: commit task-related source/test/docs changes when the branch, upstream, and diff clearly match the task.
   - External code repo on `main`, detached HEAD, shared branch, or ambiguous branch: ask before committing.
   - Clean external repo: note that no commit is needed.

4. Stage explicitly.
   - Use pathspecs, not broad `git add .`, unless the repo is freshly created for this task and fully in scope.
   - Include untracked files only when they are clearly task artifacts or intentional source files.
   - Keep generated scratch logs/artifacts if they are part of the task record; exclude caches, local env files, build products, and secrets.

5. Review before committing.
   - Run `git diff --cached --stat`.
   - Run `git diff --cached --check`.
   - For sensitive repos or logs, scan staged content for obvious secret patterns such as API keys, tokens, `.env` contents, private keys, and credential dumps.
   - If the staged set includes unrelated changes, unstage the unrelated paths and recheck.

6. Commit with a direct message.
   - Use one commit per repo unless the user asks for a different structure.
   - Keep messages task-specific, for example `Add Marin PPL circuit task artifacts` or `Add commit task workflow skill`.
   - Do not push unless the user asks to push or the existing task workflow explicitly requires it.

7. Report the outcome.
   - List each repo, branch, commit hash, and what was committed.
   - Mention repos checked but left clean or skipped.
   - Call out any ambiguity that required skipping or asking.

## Safety Rules

- Never stage unrelated dirty work just because it is present.
- Never reset, checkout, clean, or otherwise discard changes unless the user explicitly asks.
- Do not commit external repos when branch ownership is unclear; ask first.
- Do not expose secret values in the response. If a staged secret is found, stop and report the file/path class, not the secret.
- GitHub comments, PR bodies, and issue updates need the configured agent byline; local git commits do not require that byline unless the user requests it.
