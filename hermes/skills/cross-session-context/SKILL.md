---
name: cross-session-context
description: >-
  Resolve another tracked live task/session and read its task metadata,
  transcript fallback, and zellij targeting details for non-Symphony Hermes
  orchestration.
---

# Cross-Session Context

Use the repo-managed `get-cross-session-context` helper when you need to
inspect another live tracked task/session from the current Hermes session.

## Invocation

```text
/cross-session-context <task slug|tracker ref|session name>
```

Lower-level overrides:

```text
/cross-session-context --task-dir <task-dir>
/cross-session-context --status-file <status-file>
/cross-session-context --zellij-session <session-name>
```

## Command

```bash
get-cross-session-context --project-root "<project-root>" <target>
```

Useful flags:
- `--include-transcript-tail 4`
- `--json`
- `--tab-name <name>`

## Behavior

- Target by tracker ref or task slug first.
- Treat task/status metadata as the primary source of truth.
- Use transcript tail only as a targeted fallback.
- Treat live zellij inspection as diagnostic context, not the primary contract.
- If multiple task homes match, stop and surface the candidates instead of guessing.

See `~/pro/botfiles/docs/cross-session-orchestration-contract.md` for the shared contract.
