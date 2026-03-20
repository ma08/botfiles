# Repository Guidelines

## Project Structure & Module Organization
- `claude/` holds the Claude Code configuration that gets symlinked into `~/.claude/`.
- `claude/hooks/` contains Python notification hooks plus `pyproject.toml` and `uv.lock` for dependencies.
- `claude/skills/` is the target for installed skills; `claude/backup_skills/` stores archived skill examples.
- `codex/` stores Codex CLI config, synced Codex skills, and global Codex instructions (`config.toml`, `skills/`, `AGENTS.md`).
- `secrets/` contains centralized secret templates (`templates/`) and local runtime secret files (`local/`, git-ignored).
- `codex/skills/.system/` is machine-managed and git-ignored (may vary by OS/Codex version).
- `.botrc` sources centralized secrets from `secrets/local/*.rc` for your shell.
- `setup.sh` bootstraps the symlinks and installs hook dependencies.

## Build, Test, and Development Commands
- `./setup.sh` creates symlinks in `~/.claude` and `~/.codex`, then runs `uv sync` for hook deps.
- `cd claude/hooks && uv sync` refreshes Python dependencies after updates.
- `mkdir -p secrets/local` ensures the centralized local secret directory exists.
- `cp secrets/templates/claude-hooks.rc.example secrets/local/claude-hooks.rc` sets up WhatsApp notification secrets.
- `cp secrets/templates/codex-azure.rc.example secrets/local/codex-azure.rc` sets up Codex Azure credentials.
- `cp secrets/templates/linear.rc.example secrets/local/linear.rc` sets up the default `LINEAR_API_KEY` export for shells, hooks, and tracker tooling.
- `cd claude/hooks && uv run python test_whatsapp.py` sends a manual WhatsApp test message.
- `cd claude/hooks && uv run python ~/pro/botfiles/codex/hooks/codex_notification.py '{"type":"agent-turn-complete","last-assistant-message":"Codex test message"}'` sends a Codex-style test notification.
- `~/pro/botfiles/codex/hooks/run-codex-notify.sh '{"type":"agent-turn-complete","last-assistant-message":"Codex test message"}'` tests the same notify wrapper used by `codex/config.toml`.
- `source ~/pro/botfiles/.botrc` loads shared Claude/Codex environment variables.

## Coding Style & Naming Conventions
- Python: 4-space indents, `snake_case` functions/modules, small single-purpose scripts.
- Shell: bash scripts with explicit quoting and clear error handling (see `setup.sh`).
- Files: `snake_case.py` for Python, `kebab-case.sh` for shell utilities, uppercase for env vars.

## Testing Guidelines
- No automated test suite today; use `test_whatsapp.py` for manual verification.
- If you add new hooks, document a quick manual test command in the README or this file.

## Commit & Pull Request Guidelines
- Commit messages follow imperative sentence case (e.g., "Add custom Notion skill...").
- PRs should describe changes, mention any new dependencies, and note required config steps.
- This is a public repository; before every commit, verify no secrets or sensitive PII are being committed.
- Never commit files under `secrets/local/`; update templates in `secrets/templates/` if new variables are needed.

## Security & Configuration Tips
- Keep secrets in `secrets/local/*.rc` only; all runtime secret files must remain untracked.
- Keep the Linear API key in `secrets/local/linear.rc`; do not read it out of another repo's `.env` at runtime.
- `.botrc` uses strict cutover and only loads provider/hook secrets from `secrets/local/`.
- Symlinks target `~/.claude` and `~/.codex`, so validate paths before running `setup.sh`.

## Multiple Machine Support
One of the primary use cases for this repository is to support multiple machines.
Here are some relevant files that provide context about the different machines:
- `~/pro/personal_os/context/projects.md`
- `~/pro/personal_os/README.md`

## Design & Architecture Reuse
- When making design or architecture decisions, prefer approaches that are easy for other users to reuse on their own machines with different local setups.
