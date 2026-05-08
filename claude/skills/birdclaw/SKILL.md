---
name: birdclaw
description: Use Birdclaw for cache-first X/Twitter data workflows, especially followers/following, unfollowers, mutuals, non-mutual following, top followers, leadgen lists, local timeline/DM/search analysis, backups, or PR/code work in the Birdclaw repo. Prefer this skill over direct xurl whenever Birdclaw can answer from its local SQLite cache or explicit sync workflow; use xurl only for auth setup, unsupported endpoints, or intentional live API calls.
---

# Birdclaw

Birdclaw is the preferred interface for X/Twitter analysis because it stores local SQLite data and avoids unnecessary live API reads. Use direct `xurl` only when Birdclaw cannot answer the task or when the user explicitly wants raw X API behavior.

## Core Rule

- Prefer `birdclaw` / `pnpm cli` cache reads before any live X API call.
- Treat `birdclaw graph *` commands as cache-only and safe for repeated analysis.
- Treat `birdclaw sync followers|following --yes` as a live-read operation unless it clearly reuses fresh cache.
- Do not pass `--refresh` unless the user asked for a live refresh or current data is required.
- Ask before any social write action. Birdclaw follow-graph work is read-only; posting, following, unfollowing, blocking, muting, liking, reposting, DMing, and media upload still need explicit approval.
- Never read or print `~/.xurl`, app secrets, tokens, or repo `.env` values.

## Local Setup

- Canonical checkout on this machine: `~/pro/birdclaw`.
- Run Birdclaw commands from that checkout.
- Use the repo-pinned runtime before validation or development:

```bash
source ~/.nvm/nvm.sh && nvm use 25.8.1 >/dev/null
```

- Use `pnpm cli ...` in the repo. In installed contexts, `birdclaw ...` may also exist; prefer the repo command when working from the checkout.

## Cache-First Workflow

1. Inspect existing local state first:

```bash
cd ~/pro/birdclaw
pnpm cli graph summary --json
pnpm cli graph top-followers --limit 20 --json
pnpm cli graph events --direction followers --kind ended --limit 100 --json
pnpm cli graph non-mutual-following --sort followers --limit 100 --json
pnpm cli graph mutuals --limit 100 --json
```

2. If account targeting matters and the default account is uncertain, inspect local accounts without live API calls:

```bash
sqlite3 ~/.birdclaw/birdclaw.sqlite \
  "select id, handle, name, is_default from accounts order by is_default desc, id;"
```

3. Use `--account <account_id>` for personal/account-specific analysis once the account is known.

4. Save CSV/Markdown exports under the active task folder, not inside the Birdclaw repo, unless the user explicitly asks for repo changes.

## Live Sync Workflow

Use live sync only when the user asks for a fresh/live check, or when local cache is missing/stale and the user’s task requires current data.

Dry-run first when cost or scope is unclear:

```bash
pnpm cli sync followers --json
pnpm cli sync following --json
```

Run live sync intentionally:

```bash
pnpm cli sync followers --yes --json
pnpm cli sync following --yes --json
```

For a forced fresh check, add `--refresh` only when needed:

```bash
pnpm cli sync followers --yes --refresh --json
```

For cheap inspection, use caps and acknowledge incomplete snapshots:

```bash
pnpm cli sync followers --yes --max-pages 1 --allow-partial --json
```

Incomplete snapshots are recorded for audit but do not create churn events or update current edges.

## Common Tasks

**People who unfollowed me**

```bash
pnpm cli sync followers --yes --refresh --json
pnpm cli graph events --direction followers --kind ended --limit 1000 --json
```

**Top followers by follower count**

```bash
pnpm cli graph top-followers --limit 100 --json
```

**People I follow who do not follow me back**

```bash
pnpm cli graph non-mutual-following --sort followers --limit 1000 --json
```

**Mutuals**

```bash
pnpm cli graph mutuals --limit 1000 --json
```

**Backup portability**

Follow graph state should round-trip through Birdclaw text backup:

```bash
pnpm cli backup export --repo <path> --json
pnpm cli backup import <path> --json
pnpm cli backup validate <path> --json
```

## Development And PR Work

- Check `README.md`, `docs/`, `.node-version`, `package.json`, and `.github/workflows/ci.yml` before changing Birdclaw.
- Keep tests fake-data only; never commit real follower data, raw API payloads, screenshots, tokens, local DBs, or task artifacts.
- Validate under Node `25.8.1`:

```bash
pnpm run check
pnpm run typecheck
pnpm run coverage
pnpm run build
pnpm run e2e
```

## When To Use xurl Instead

Use the `xurl` skill only for:

- OAuth/app setup and auth troubleshooting.
- X API endpoints Birdclaw does not support.
- A user-requested raw API read.
- Social write actions after explicit approval.

When a task can be answered by Birdclaw cache or by Birdclaw’s explicit sync/query workflow, use Birdclaw instead of direct `xurl`.
