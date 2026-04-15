---
name: zellij-detached-codex-launch-verification
description: Debug and fix detached Zellij launches for Codex tasks when session creation succeeds but the attached pane only shows a shell or no visible Codex UI.
---

# When to use
Use when Hermes/botfiles pickup or launcher flows claim a Zellij session was started for a Codex task, but attaching shows only an idle shell, missing task metadata, or verification based only on `zellij list-sessions`.

# Core lesson
A detached Zellij session existing is **not** sufficient evidence that Codex launched successfully. Verify a real visible pane and the Codex process/UI before treating the lane as active.

# Steps
1. **Inspect the ticket/session state**
   - Check whether the Linear ticket actually contains repo-local evidence.
   - If not, use the default project root policy (currently `~/pro/personal_os` for Arya ambiguous tickets).
   - Inspect the live session:
     - `zellij list-sessions`
     - `zellij action query-tab-names --session <session>`
     - `zellij action dump-screen --session <session> -p <pane_id> -f`

2. **Check whether the launcher is over-crediting success**
   - Look at the launcher script and verify whether it only:
     - creates a session, or
     - also creates a pane running Codex.
   - If verification only checks `zellij list-sessions`, that is insufficient.

3. **Validate `--dry-run` honestly**
   - Run:
     - `start-zellij-session-for-task --project-root <root> --dry-run <ISSUE>`
   - Confirm whether dry-run only prints the launch plan/script.
   - Do not attribute launch-time pane verification failures to `--dry-run` unless the tool truly performs launch under dry-run.

4. **Fix detached launch behavior**
   - Creating a detached session plus setting `options --default-shell <bootstrap>` may not produce a visible pane that can be inspected.
   - Preferred fix on this setup:
     1. create the detached session
     2. launch the bootstrap as a real pane command with:
        - `ZELLIJ_SESSION_NAME=<session> zellij run -- <bootstrap_path>`
   - This creates an inspectable pane like `terminal_1` that actually runs Codex.

5. **Strengthen verification**
   - After launch, inspect the real pane (`terminal_1` or returned pane) with `dump-screen`.
   - Require evidence such as:
     - `OpenAI Codex`
     - seeded task prompt like `$start-new-task <ISSUE>`
     - correct repo cwd visible in UI
   - Optionally verify process tree for the Codex child.
   - If no visible Codex evidence appears after retries, fail the launcher and do not claim activation.

6. **Normalize ticket state instead of broadening supervision**
   - If a real verified live Codex session exists for a ticket still in `Todo`, the cleaner approach is to move the ticket to `In Progress`.
   - Prefer keeping supervision cron scoped to normal active states rather than special-casing `Todo` live lanes.

# Verification checklist
- `zellij list-sessions` shows the session
- `zellij action list-panes` (or equivalent session inspection) shows a real running pane
- `dump-screen` on the active pane shows Codex UI, not just a shell prompt
- task metadata/tracker context resolves if expected
- only then post activation markers or move ticket state

# Pitfalls
- Existing stale session names can block honest relaunch; kill the stale session before retrying.
- `dump-screen` against the wrong pane can make a healthy launch look broken.
- Cron summaries may conflate dry-run and real-run output; re-run commands directly when in doubt.
- Do not treat a shell prompt in `~/pro/botfiles` as evidence of a task lane for another repo.
