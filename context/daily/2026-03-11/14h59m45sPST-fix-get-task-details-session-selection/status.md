# Fix `get-task-details` Session Selection

**Goal**: Update the botfiles task-status helpers so `get-task-details` resolves the active task for the current session instead of picking the newest task folder.
**Last Updated**: 2026-03-11 ~03:04pm PST
**Status**: Session-aware `get-task-details` fix implemented and validated across Codex/Claude copies

## Quick Links

| Resource | URL |
|----------|-----|
| Original Input | Implement the plan to fix `get-task-details` so it resolves the current session's task instead of the newest task folder. |

<!-- TASK-METADATA:START -->
## Task Metadata
- Machine: Sourya-Macbook
- Coding Agent: codex
- Agent Session ID: 019cca7b-bc27-77e3-8f0d-33200d679162
- GitHub Issue: none
- GitHub Repo: none
- GitHub Issue Number: none
- Zellij Session: personal-os
- Zellij Link: https://souryas-macbook-pro.tailaaddce.ts.net:8443/personal-os
- Last Synced: 2026-03-11 ~03:04pm PST
<!-- TASK-METADATA:END -->

## Current State

The shared task-status helpers now resolve the active task by exact `Agent Session ID` match instead of newest-folder recency.
- `codex/skills/_shared/task_status/scripts/task_status_common.py` and the Claude mirror now expose a shared runtime-context resolver, a shared task-candidate loader, and accept `AGENT_SESSION_ID` as a valid session-id env key.
- `codex/skills/_shared/task_status/scripts/get_task_details.py` and the Claude mirror now fail closed in default no-arg mode, only print the current session task when exactly one match exists, and report ambiguity instead of silently guessing.
- Explicit `task-slug` lookup still works cross-session, but now prefers the current-session match inside the filtered set when one exists.
- The Codex and Claude `get-task-details` skill docs now explain the session-only default behavior, and the Codex skill prompt metadata was updated to stop describing the old “newest task folder” behavior.
- Regression validation passed for the real current session, broad and narrow slug lookups, no-match fail-closed behavior, `AGENT_SESSION_ID` compatibility, and a synthetic duplicate-session ambiguity case.

## Accepted Plans

### Plan v1 — 2026-03-11 ~03:00pm PST
**Accepted Signal**: explicit_text
**Supersedes**: none
**Revision Summary**: Fix `get-task-details` so default resolution is current-session-only and no longer guesses from newest-folder recency.

# Fix `get-task-details` to Resolve the Current Session’s Task, Not the Newest Folder

## Summary
- Change `get-task-details` so the default no-argument path is strictly session-scoped.
- Use the current runtime agent session ID as the primary selector for the active task; never fall back to “latest task folder” in default mode.
- Keep explicit `task-slug` lookup working as a separate cross-session mode.
- Apply the fix to both Codex and Claude copies of the task-status helpers and update the skill docs to explain the new behavior.

## Key Changes
- In the shared task-status helpers, resolve the current runtime context from env using the same metadata sources already used by `save-task-status`, and add `AGENT_SESSION_ID` to the accepted session-id env keys for consistency with `notify_utils.py`.
- Add a shared task-candidate loader in `task_status_common.py` that:
  - enumerates task folders
  - resolves `status.md` / legacy `README.md`
  - parses only the managed `TASK-METADATA` block
  - extracts exact metadata fields once per candidate
- Change `get_task_details.py` selection behavior:
  - No `task-slug`: find candidates whose `Agent Session ID` exactly matches the current runtime session ID.
  - If exactly one match exists, print that task as `Primary`.
  - If no exact match exists, print a fail-closed message for the current session and suggest `save-task-status` or `start-new-task`; do not print an unrelated primary task.
  - If multiple exact matches exist, treat that as ambiguous and print the matching task folders instead of silently picking the newest.
- Keep `task-slug` as explicit lookup mode:
  - filter candidates by slug first
  - if the filtered set contains an exact current-session match, make that `Primary`
  - otherwise preserve newest-first ordering within the filtered set
  - only show `Related` / `Stale` for that filtered set, not for the entire task root
- Change default no-argument output to `Session Only`:
  - show only the current session’s task when resolved
  - omit unrelated recent/stale tasks by default
  - include current-session diagnostics in no-match / ambiguous-match messages so it is clear what context was used
- Update both `codex/skills/get-task-details/SKILL.md` and `claude/skills/get-task-details/SKILL.md` to document:
  - default mode is current-session-only
  - `task-slug` is explicit cross-session lookup
  - legacy or unsynced task folders without a metadata block cannot be auto-resolved for the current session

## Public Interface Changes
- No new CLI flags.
- Behavior change for `get-task-details`:
  - default call now resolves only the current session’s task
  - it no longer treats the newest task folder as active
  - `task-slug` remains the opt-in way to inspect non-current tasks
- No metadata schema changes; the existing `Task Metadata` block remains the source of truth.

## Test Plan
- Reproduce the current bug with the real current session:
  - current `CODEX_THREAD_ID` is `019cca7b-bc27-77e3-8f0d-33200d679162`
  - default `get-task-details` should resolve issue `#16`, not the newer March 9 Apple Music task
- Validate explicit lookup behavior:
  - `--task-slug issue-16` still resolves the issue `#16` task
  - `--task-slug personal-os-issue` prefers the current-session match within that filtered set instead of unrelated newer issue folders
- Validate fail-closed behavior:
  - run with a non-matching session ID override and confirm the script prints “no task for current session” instead of choosing the newest folder
- Validate ambiguity handling:
  - use a temporary synthetic task root with two status files carrying the same `Agent Session ID` and confirm the script reports ambiguity rather than silently picking one
- Validate env compatibility:
  - confirm `AGENT_SESSION_ID` works the same as `CODEX_THREAD_ID`
- Validate mirror consistency:
  - Codex and Claude helper copies stay identical after the change, aside from the expected skill-wrapper doc differences

## Assumptions and Defaults
- The only trustworthy default selector for the active task is exact `Agent Session ID` match from the managed metadata block.
- Default no-argument mode fails closed when there is no exact match or when multiple matches exist.
- `task-slug` intentionally broadens scope and is the supported way to inspect non-current tasks.
- Legacy task folders without synced metadata are not auto-detectable as the active current-session task until `save-task-status` or `start-new-task` writes the managed metadata block.

## Progress

- [x] Investigated the current `get-task-details` behavior and confirmed it picks the newest task folder.
- [x] Captured the accepted fix plan in this task record.
- [x] Implement the session-aware resolver and output changes in the shared task-status helpers.
- [x] Mirror the fix across both Codex and Claude copies and update skill docs.
- [x] Run regression checks and save validation artifacts.

## Code Changes

- `codex/skills/_shared/task_status/scripts/task_status_common.py` and `claude/skills/_shared/task_status/scripts/task_status_common.py`: added shared runtime-context and task-candidate helpers, plus `AGENT_SESSION_ID` support in session-id resolution.
- `codex/skills/_shared/task_status/scripts/get_task_details.py` and `claude/skills/_shared/task_status/scripts/get_task_details.py`: replaced newest-folder primary selection with exact current-session matching, fail-closed messaging, ambiguity reporting, and slug-filtered lookup behavior.
- `codex/skills/get-task-details/SKILL.md`, `claude/skills/get-task-details/SKILL.md`, and `codex/skills/get-task-details/agents/openai.yaml`: updated the documented/default skill semantics to match the new session-scoped behavior.

## Artifacts

| File | Description |
|------|-------------|
| `task-progress-artifacts/sync-task-metadata.txt` | Output from the final metadata sync for this implementation task. |
| `task-progress-artifacts/validate_get_task_details.sh` | Saved validation harness for syntax, parity, real-session lookup, no-match behavior, `AGENT_SESSION_ID` compatibility, and ambiguity handling. |
| `task-progress-artifacts/validate-get-task-details-output.txt` | Output from the validation harness confirming the new session-aware selection behavior. |

## Next Steps

- None. Implementation and validation are complete; commit/push can be done separately if requested.
