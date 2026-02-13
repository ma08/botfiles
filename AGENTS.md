# Repository Guidelines

## Project Structure & Module Organization
- `claude/` holds the Claude Code configuration that gets symlinked into `~/.claude/`.
- `claude/hooks/` contains Python notification hooks plus `.env.example`, `pyproject.toml`, and `uv.lock` for dependencies.
- `claude/skills/` is the target for installed skills; `claude/backup_skills/` stores archived skill examples.
- `codex/` stores Codex CLI config, provider env templates, synced Codex skills, and global Codex instructions (`config.toml`, `.azure_codex_config_rc.example`, `skills/`, `AGENTS.md`).
- `codex/skills/.system/` is machine-managed and git-ignored (may vary by OS/Codex version).
- `.botrc` sources Claude/Codex env config files for your shell.
- `setup.sh` bootstraps the symlinks and installs hook dependencies.

## Build, Test, and Development Commands
- `./setup.sh` creates symlinks in `~/.claude` and `~/.codex`, then runs `uv sync` for hook deps.
- `cd claude/hooks && uv sync` refreshes Python dependencies after updates.
- `cp claude/hooks/.env.example claude/hooks/.env` sets up local secrets for WhatsApp.
- `cp codex/.azure_codex_config_rc.example codex/.azure_codex_config_rc` sets up Codex Azure credentials.
- `cd claude/hooks && uv run python test_whatsapp.py` sends a manual WhatsApp test message.
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
- Never commit `claude/hooks/.env`; update `.env.example` if new variables are needed.

## Security & Configuration Tips
- Keep secrets in local env files only; ensure `.env` and `codex/.azure_codex_config_rc` stay untracked.
- Symlinks target `~/.claude` and `~/.codex`, so validate paths before running `setup.sh`.
