# Hermes Shared Skills

Public-safe shared Hermes workflow assets.

Purpose:
- provide one canonical skill source for main Hermes and all Hermes profiles
- keep universal workflow/task skills in a single maintained copy
- avoid copy drift across profiles
- keep private context and secrets out of the public botfiles repo

Conventions:
- only public-safe reusable workflow artifacts belong here
- keep secrets and private runtime values out of this tree
- prefer Hermes-native skills that reuse shared task/status contracts rather than copying Codex/Claude behavior verbatim
- keep task/artifact/status skills agent-agnostic where possible so Hermes, Codex, and Claude Code can share filesystem contracts

Layout:
- `skills/` — shared Hermes skills
- `docs/` — Hermes-specific workflow docs/contracts
- `templates/` — reusable public-safe templates

Initial scope:
- continue-task
- get-task-details
- cross-session-context
- cross-session-message
- grill-me

Planned next:
- start-task
- save-status
