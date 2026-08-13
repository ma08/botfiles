---
name: cross-session-context
description: >-
  Resolve another tracked live task/session or Codex Desktop thread and read
  task metadata, transcript fallback, zellij diagnostics, or Codex Desktop
  thread context for non-Symphony orchestration.
---

# Cross-Session Context

Use the repo-managed `get-cross-session-context` helper when the user wants to
inspect another live tracked task/session from the current session. When running
inside Codex Desktop and the target is a Codex Desktop thread, use the app
thread tools as the Desktop transport.

If the purpose is to inspect or recover a Mac UI worker result, use the exact
worker host and task IDs recorded by `mac-ui-worker`; never resolve that worker
by title alone. The receipt must also match the declared `iab` or
`computer-use` surface.

## Invocation

```text
$cross-session-context <task slug|tracker ref|session name>
/cross-session-context <task slug|tracker ref|session name>
```

Lower-level overrides:

```text
$cross-session-context --task-dir <task-dir>
$cross-session-context --status-file <status-file>
$cross-session-context --zellij-session <session-name>
```

## Command

```bash
get-cross-session-context --project-root "<project-root>" <target>
```

Useful flags:
- `--include-transcript-tail 4`
- `--json`
- `--tab-name <name>`

Codex Desktop thread path, when `codex_app` tools are available:

0. If the thread tools are not already visible, use the runtime's tool
   discovery to load `list_threads` and `read_thread`.
1. Use `list_threads` with the tracker id, task slug, or visible title.
2. If the result is ambiguous, stop and surface the candidates.
3. Use `read_thread` with the chosen `threadId` and `hostId`.
4. If task metadata also exists, still run `get-cross-session-context` for the
   status file, tracker metadata, transcript path, and zellij diagnostics.

## Behavior

- Target by tracker ref or task slug first. Use explicit session overrides only
  for lower-level or debug work.
- Treat task/status metadata as the primary source of truth.
- Use transcript tail only as a targeted fallback for fuller deterministic
  context.
- Treat live zellij inspection as diagnostic context, not the primary contract.
- Treat Codex Desktop `read_thread` output as app-thread context: useful for
  recent turn status and summaries, but not a substitute for task status files
  when a tracked task exists.
- If no zellij session exists but a unique Codex Desktop thread is found, the
  Desktop thread is a valid context target.
- Codex CLI and Claude Code do not automatically have Codex Desktop thread
  tools. If `codex_app` tools are unavailable, do not fake thread context by
  editing or scraping local app state; use task metadata, transcript files, and
  zellij diagnostics, or ask the user to run the Desktop-thread operation from a
  Codex Desktop thread.
- If multiple task homes match, stop and surface the candidates instead of
  guessing.
- A Mac UI worker is bound to one exact source task. Reading it for result
  recovery does not authorize rebinding it or sending unrelated work.

See `~/pro/botfiles/docs/cross-session-orchestration-contract.md` for the
shared contract.
