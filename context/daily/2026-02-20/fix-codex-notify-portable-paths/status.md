# Fix Codex Notify Hook Portable Paths

**Goal**: Keep one shared Codex notify setup working across machines while keeping `codex/config.toml` simple.
**Last Updated**: 2026-02-20 ~01:12PM PST
**Status**: Complete

## Current State

The notify complexity is now abstracted into a dedicated script: `codex/hooks/run-codex-notify.sh`. `codex/config.toml` has a short notify command plus 3 explanatory comments, while `UV_BIN` portability remains centralized in `shell/10-uv-bin.sh` (loaded via `.botrc`).

## Progress

- [x] Added shared `UV_BIN` resolution in shell extension (`shell/10-uv-bin.sh`)
- [x] Added dedicated notify runner script (`codex/hooks/run-codex-notify.sh`)
- [x] Simplified `codex/config.toml` notify block to call runner script only
- [x] Added 3 inline comments in `config.toml` explaining abstraction rationale
- [x] Updated docs with notify wrapper references
- [x] Validated TOML parse, direct runner smoke test, and config-style invocation smoke test

## Things Attempted

1. Started with inline notify logic inside TOML (functional but too verbose).
2. Moved UV lookup to shell module loaded by `.botrc`.
3. Final simplification: moved notify execution flow to runner script and reduced TOML to one short command.

## Code Changes

- `codex/hooks/run-codex-notify.sh`: New wrapper script that sources `.botrc`, validates `UV_BIN`/`BOTFILES_ROOT`, and runs `codex_notification.py`.
- `codex/config.toml`: Replaced long inline shell logic with `run-codex-notify.sh "$1"` and added 3 comments.
- `README.md`: Added note that Codex notify uses wrapper script and `shell/10-uv-bin.sh` for UV resolution.
- `AGENTS.md`: Added command to test the same notify wrapper path used by `config.toml`.

## Artifacts

| File | Description |
|------|-------------|
| `task-progress-artifacts/add-run-codex-notify.patch` | Patch for new `codex/hooks/run-codex-notify.sh` |
| `task-progress-artifacts/notify-config-runner.diff` | Diff showing simplified notify block in `codex/config.toml` |
| `task-progress-artifacts/notify-doc-updates.diff` | Diff for `README.md` and `AGENTS.md` notify documentation updates |
| `task-progress-artifacts/toml-validation-runner.txt` | TOML checks confirming runner-based notify config |
| `task-progress-artifacts/notify-smoke-test-runner.txt` | Output from direct runner and config-style invocation smoke tests (`Exit 1: 0`, `Exit 2: 0`) |
| `task-progress-artifacts/runner-permissions.txt` | `ls -l` output confirming runner script permissions |

## Next Steps

- [ ] Trigger a real Codex completion event and verify notification delivery on this machine.
- [ ] Pull this change on ML VM and verify same notify flow works unchanged.
