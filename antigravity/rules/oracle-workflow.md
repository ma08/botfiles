---
trigger: model_decision
description: "Oracle CLI and GPT-6 Astra Pro browser review workflow, GPU-local vs oracle-vm routing, pinned Oracle 0.21.4 wrapper policy, no-silent-downgrade rules, and session harvesting. Load whenever using Oracle or reviewing/editing Oracle configs."
---

# Oracle Workflow Policy

- `~/pro/botfiles/codex/skills/oracle` and `~/pro/botfiles/claude/skills/oracle` are protected local workflow forks derived from `steipete/oracle/skills/oracle` carrying local GPT-6 Astra + Pro browser defaults. Do not overwrite them from upstream without reapplying local policy, and keep the skills, global instructions, Oracle awaiter agents, and shell wrappers aligned.

## Host Routing (GPU-local vs `oracle-vm`)

- **On `research-gpu-01`:** Run plain `oracle` locally using its own pinned Oracle 0.21.4 build and local browser profile, keeping GPT-6 Astra + Pro defaults and local `oracle session` recovery. Treat `oracle-vm` only as an explicit CPU-dependent alternative there, never the GPU default.
- **On other machines (for example `sourya-mac`) when `research-cpu-01-ts` is healthy:** For agent-driven Oracle reviews with prompts plus literal text or source files, prefer `~/pro/botfiles/bin/oracle-vm` to keep long browser automation on the GCP VM. Keep plain `oracle` host-local for manual use, explicit local requests, VM outages, and Mac-only context.
- Never transparently redirect arbitrary plain `oracle` invocations. `oracle-vm` must preflight the remote route, refuse ambiguous directories, globs, secrets, and binary attachments, preserve explicit model/engine choices, and return the remote slug plus reattach or harvest commands. Surface any pre-submission failure before deliberately falling back to the local wrapper.

## Wrappers and Pinned Version

- Always use the local `oracle` and `oracle-mcp` wrappers from `~/pro/botfiles/bin/` (symlinked into `~/.local/bin` by `setup.sh`) instead of raw `npx -y @steipete/oracle`, especially on machines where default Node is below 24.
- Local wrappers prefer released Oracle 0.21.4 at `~/pro/lab/tools/oracle-0.21.4` (pinned to `5dd3cd855e14dce996038004f4c5b92b47eb19f9`), falling back to `@steipete/oracle@0.21.4`. Use `ORACLE_SOURCE_MAIN=0` for npm release, `ORACLE_SOURCE_MAIN=require` to require source build, and `ORACLE_SOURCE_MAIN_VERBOSE=1` to print the route. Keep `~/pro/lab/tools/oracle-main` for rollback; do not vendor either build into `botfiles`.

## Model Defaults and Execution Rules

- Default Oracle requests with no explicit engine/model must use ChatGPT GPT-6 Astra with the Pro tier verified via the local wrapper (`gpt-6-pro` is Oracle's browser-only alias, not an API model ID). Plain `oracle -p "<prompt>" [--file ...]` expands to `--engine browser --model gpt-6-pro --browser-thinking-time pro --browser-model-strategy select`, reusing `127.0.0.1:9223` when available and otherwise using manual-login mode with `"$HOME/pro/botfiles/bin/oracle-chrome-linux"`.
- Honor explicit user requests for another model, engine, multi-model run, or faster/cheaper pass. Otherwise never silently downgrade the no-model default from GPT-6 Astra + Pro to GPT-5.6/5.5/5.4 or an API route; fix or surface browser/profile/canary issues and retry the same target.
- Prefer compact prompts or inline file delivery (`--browser-inline-files` / `--browser-attachments never`) for text/source context; reserve upload/bundle mode for PDFs, images, binaries, or file sets that truly cannot fit inline.
- Allow up to 60 minutes for a GPT-6 Astra Pro browser run. `in_progress` alone is not failure, and a closed polling shell is not Oracle failure (reattach to the same slug). Quote local Oracle evidence (`oracle status`, `meta.json`, `output.log`) for timing claims instead of guessing.
- Wait or reattach until `completed` or `error` whenever the result is needed for the next step (skip waiting only if the user explicitly says not to wait). If a foreground waiter misses a visibly completed response, run `oracle session <slug> --harvest` against the same bound tab before treating the run as failed or starting another run.
- On Linux/SSH shells without `DISPLAY`, the local `oracle` wrapper auto-runs explicit browser mode under `xvfb-run` (still requires a signed-in ChatGPT Chrome profile, inline cookies, or remote browser host).
- For shell-wide API auth outside repos with their own `.env`, keep the default Azure Oracle route in `~/pro/botfiles/secrets/local/codex-azure.rc` and direct OpenAI fallback in `~/pro/botfiles/secrets/local/codex-openai.rc`. On non-Pro models, pass an explicit `--timeout` or use background mode instead of `auto`.
