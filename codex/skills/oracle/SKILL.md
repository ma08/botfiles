---
name: oracle
description: Use the @steipete/oracle CLI to bundle a prompt plus the right files and get a second-model review (API or browser) for debugging, refactors, design checks, or cross-validation.
---

# Oracle (CLI) — best use

Oracle bundles your prompt + selected files into one “one-shot” request so another model can answer with real repo context (API or browser automation). Treat outputs as advisory: verify against the codebase + tests.

## Main use case (browser, ChatGPT GPT‑5.6 Sol + Pro)

Default workflow here: use the local `oracle` wrapper with ChatGPT GPT‑5.6 Sol and the account/UI Intelligence effort set to Pro. Pro is a separate ChatGPT effort, not a `gpt-5.6-pro` CLI identifier. This is the “human in the loop” path: it can take ~10 minutes to ~1 hour; expect a stored session you can reattach to or harvest.

Recommended defaults:

- Engine: browser (`--engine browser`)
- Model: `--model gpt-5.6-sol` with `--browser-model-strategy select`; the signed-in ChatGPT profile supplies the separate Pro effort.
- Browser mode: reuse `--remote-chrome 127.0.0.1:9223` when the supported login desktop is already running; otherwise use manual login with `--browser-manual-login --browser-chrome-path "$HOME/pro/botfiles/bin/oracle-chrome-linux"`.
- Local package route: for no-model browser requests, the wrapper prefers the pinned source build at `~/pro/lab/tools/oracle-main` commit `ea8b1b57f140f2c641a2a8a9cc1dd10bd03bdb18` (upstream PR #320) when it is present and verified. If unavailable, npm latest may be used only with the same GPT-5.6 Sol target. Use `ORACLE_SOURCE_MAIN=0` to force npm, `ORACLE_SOURCE_MAIN=require` to require the pinned build, and `ORACLE_SOURCE_MAIN_VERBOSE=1` to print the selected route.
- Verification: confirm the browser/session evidence shows GPT-5.6 Sol and Pro. If the foreground detector misses a visibly completed answer, run `oracle session <slug> --harvest` against the same bound tab before declaring failure.
- Attachments: directories/globs + excludes; avoid secrets. For text/code-heavy context, prefer compact prompts or inline delivery (`--browser-inline-files` / `--browser-attachments never`) before upload mode; reserve uploads/bundles for PDFs, images, binaries, or file sets that truly cannot fit inline.
- Fallback: do not silently downgrade no-model work to GPT-5.5/5.4 or switch it to an API route. Fix or surface browser/profile/canary issues and retry GPT-5.6 Sol + Pro. Honor another model or engine only when the user explicitly requests it.

## Golden path (fast + reliable)

1. Pick a tight file set (fewest files that still contain the truth).
2. Preview what you’re about to send (`--dry-run` + `--files-report` when needed).
3. Run with the local `oracle` wrapper so it selects ChatGPT GPT‑5.6 Sol + Pro by default; use API only when explicitly requested.
4. If the run detaches/timeouts, reattach to or harvest the stored session; don’t start a duplicate run.

## ChatGPT Project routing

Oracle can create a new browser conversation inside an existing ChatGPT Project by passing that project's exact `/project` URL through `--chatgpt-url`. Treat the project URL as a context scope: the new chat inherits the project's available files and instructions, subject to that project's ChatGPT memory/settings.

Private project names, aliases, and URLs must not be stored in this public skill repository. Before a project-scoped Oracle request, inspect `~/pro/personal_os/context/projects.md` for a matching entry under its private Oracle/ChatGPT project-route registry.

Routing rules:

- When the user names a project and exactly one private registry entry matches, automatically add that entry's project URL; do not ask the user to repeat it.
- Do not set a project URL as a shell-wide or wrapper-wide default. Unrelated or ambiguous Oracle work must use the normal non-project route unless the user supplies a URL.
- Do not copy private project identifiers or URLs from the registry into botfiles, logs intended for publication, or public issue/commit text.
- Project placement does not guarantee that prior chats are available as memory. When project context materially affects the answer, ask Oracle to identify whether supporting context came from a project file, project instruction, or prior project chat, and verify distinctive facts rather than accepting a generic claim.
- Project conversations are intentionally not auto-archived by Oracle's default browser archive policy.

Project-scoped GPT-5.6 Sol route on the VM (account/browser default supplies the Pro effort; Oracle does not expose `pro` as a CLI thinking-time selector):

```bash
ORACLE_SOURCE_MAIN=require ORACLE_SOURCE_MAIN_VERBOSE=1 oracle \
  --engine browser \
  --remote-chrome 127.0.0.1:9223 \
  --chatgpt-url '<project-url-from-private-registry>' \
  --model gpt-5.6-sol \
  --browser-model-strategy select \
  --browser-attachments never \
  --slug project-oracle-consult \
  -p '<task>'
```

Before using that VM route, probe `http://127.0.0.1:9223/json/version`. If unavailable, start and keep the existing `~/pro/botfiles/bin/oracle-browser-login-vm` desktop alive, use its localhost-only noVNC tunnel for login/Cloudflare if needed, and then retry the same `--remote-chrome` route. Do not silently switch to an API run.

## Commands (preferred)

- Show help (once/session):
  - `oracle --help`
  - `ORACLE_SOURCE_MAIN_VERBOSE=1 oracle --version`

- Preview (no tokens):
  - `oracle --dry-run summary -p "<task>" --file "src/**" --file "!**/*.test.*"`
  - `oracle --dry-run full -p "<task>" --file "src/**"`

- Token/cost sanity:
  - `oracle --dry-run summary --files-report -p "<task>" --file "src/**"`

- Browser run through the local wrapper (main path; long-running is normal):
  - `oracle -p "<task>" --file "src/**"`

- Text/code browser run that avoids ChatGPT attachment upload readiness:
  - `oracle -p "<task>" --browser-inline-files --file "src/**"`

- Explicit default browser run:
  - `oracle --engine browser --remote-chrome 127.0.0.1:9223 --model gpt-5.6-sol --browser-model-strategy select -p "<task>" --file "src/**"`

- Explicit GPT‑5.4 Pro API override (only when the user requests it):
  - `oracle --engine api --model gpt-5.4-pro -p "<task>" --file "src/**"`

- Manual paste fallback (assemble bundle, copy to clipboard):
  - `oracle --render --copy -p "<task>" --file "src/**"`
  - Note: `--copy` is a hidden alias for `--copy-markdown`.

- Inspect or require the pinned source route:
  - `ORACLE_SOURCE_MAIN=1 ORACLE_SOURCE_MAIN_VERBOSE=1 oracle --version`
  - `ORACLE_SOURCE_MAIN=require ORACLE_SOURCE_MAIN_VERBOSE=1 oracle --version`

## Attaching files (`--file`)

`--file` accepts files, directories, and globs. You can pass it multiple times; entries can be comma-separated.

- Include:
  - `--file "src/**"` (directory glob)
  - `--file src/index.ts` (literal file)
  - `--file docs --file README.md` (literal directory + file)

- Exclude (prefix with `!`):
  - `--file "src/**" --file "!src/**/*.test.ts" --file "!**/*.snap"`

- Defaults (important behavior from the implementation):
  - Default-ignored dirs: `node_modules`, `dist`, `coverage`, `.git`, `.turbo`, `.next`, `build`, `tmp` (skipped unless you explicitly pass them as literal dirs/files).
  - Honors `.gitignore` when expanding globs.
  - Does not follow symlinks (glob expansion uses `followSymbolicLinks: false`).
  - Dotfiles are filtered unless you explicitly opt in with a pattern that includes a dot-segment (e.g. `--file ".github/**"`).
  - Default cap: files > 1 MB are rejected unless you raise `ORACLE_MAX_FILE_SIZE_BYTES` or `maxFileSizeBytes` in `~/.oracle/config.json`.

## Budget + observability

- Target: keep total input under ~196k tokens.
- Use `--files-report` (and/or `--dry-run json`) to spot the token hogs before spending.
- If you need hidden/advanced knobs: `oracle --help --verbose`.

## Engines (API vs browser)

- The local wrapper forces no-model requests onto the GPT-5.6 Sol + Pro browser route. Explicit engine/model requests remain authoritative.
- Browser engine supports GPT + Gemini only; use `--engine api` for Claude/Grok/Codex or multi-model runs.
- **API runs require explicit user consent** before starting because they incur usage costs.
- Browser attachments:
  - `--browser-attachments auto|never|always` (auto pastes inline up to ~60k chars then uploads).
  - Use `--browser-inline-files` / `--browser-attachments never` for text and source-code context when upload readiness is flaky. If you see `Attachments did not finish uploading before timeout`, retry with inline files or a compact prompt before changing models.
- Remote browser host (signed-in machine runs automation):
  - Host: `oracle serve --host 0.0.0.0 --port 9473 --token <secret>`
  - Client: `oracle --engine browser --remote-host <host:port> --remote-token <secret> -p "<task>" --file "src/**"`

## Sessions + slugs (don’t lose work)

- Stored under `~/.oracle/sessions` (override with `ORACLE_HOME_DIR`).
- Browser runs save durable files under `~/.oracle/sessions/<id>/artifacts/`, including `transcript.md`, Deep Research reports, and downloaded ChatGPT-generated images when available.
- Runs may detach or take a long time (browser + GPT‑5.6 Sol + Pro often does). If the CLI times out: don’t re-run; reattach or harvest.
  - List: `oracle status --hours 72`
  - Attach: `oracle session <id> --render`
  - Harvest: `oracle session <id> --harvest`
- Use `--slug "<3-5 words>"` to keep session IDs readable.
- Duplicate prompt guard exists; use `--force` only when you truly want a fresh run.

## Prompt template (high signal)

Oracle starts with **zero** project knowledge. Assume the model cannot infer your stack, build tooling, conventions, or “obvious” paths. Include:

- Project briefing (stack + build/test commands + platform constraints).
- “Where things live” (key directories, entrypoints, config files, dependency boundaries).
- Exact question + what you tried + the error text (verbatim).
- Constraints (“don’t change X”, “must keep public API”, “perf budget”, etc).
- Desired output (“return patch plan + tests”, “list risky assumptions”, “give 3 options with tradeoffs”).

### “Exhaustive prompt” pattern (for later restoration)

When you know this will be a long investigation, write a prompt that can stand alone later:

- Top: 6–30 sentence project briefing + current goal.
- Middle: concrete repro steps + exact errors + what you already tried.
- Bottom: attach _all_ context files needed so a fresh model can fully understand (entrypoints, configs, key modules, docs).

If you need to reproduce the same context later, re-run with the same prompt + `--file …` set (Oracle runs are one-shot; the model doesn’t remember prior runs).

## Safety

- Don’t attach secrets by default (`.env`, key files, auth tokens). Redact aggressively; share only what’s required.
- Prefer “just enough context”: fewer files + better prompt beats whole-repo dumps.
