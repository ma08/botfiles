---
name: deep-research
description: Run end-to-end deep research using OpenAI Responses API deep-research models plus Gemini Deep Research plus Exa Deep Research, then synthesize results into a comprehensive, easy-to-read, citation-backed Markdown report by default. Use for due diligence, investment research, market/competitor analysis, technical investigations, policy analysis, and any high-stakes question where cross-checking sources across multiple engines improves confidence; generate alternate formats only when the user explicitly requests them.
---

# Deep Research

Produce decision-grade research outputs with multi-engine evidence gathering:
- OpenAI deep research via bundled script (`scripts/run_openai_deep_research.py`)
- Gemini deep research via bundled script (`scripts/run_gemini_deep_research.py`)
- Exa Research API via bundled script (`scripts/run_exa_research.py`)

Default output is always a comprehensive Markdown report. If the user asks for additional formats, provide them after the Markdown report.

## Non-Negotiable Output Contract

1. Deliver a comprehensive Markdown report first.
2. Make the Markdown easy to scan: clear headings, concise tables, explicit assumptions.
3. Attach citations/links for all load-bearing claims.
4. Clearly separate evidence from inference.
5. Only add alternate outputs (JSON, CSV-style table, Notion-ready, slide-outline, short brief) when explicitly requested.

Use `references/output-contract.md` for the exact structure.

## Speed Policy (Parallel-First)

Optimize for shortest end-to-end time without reducing research quality.

1. Run OpenAI, Gemini, and Exa research in parallel whenever all are required.
2. Parallelize independent sub-questions with multiple agents (market, technical, legal, risks, benchmarks).
3. Start synthesis only after minimum evidence is available from all active engines, then continue ingesting late-arriving evidence in parallel.
4. Keep at least one high-level coordinator agent to merge claims, resolve conflicts, and enforce citation quality.
5. Use sequential execution only for truly dependent steps.

## Workflow

1. Scope and clarify
- Define audience, decision to support, time horizon, and constraints.
- Confirm required output formats. If unspecified, use Markdown only.

2. Prepare research brief
- Create a prompt file in the current task artifacts folder.
- Include required deliverables, confidence handling, and citation requirements.

3. Launch research engines in parallel
- OpenAI track: run `scripts/run_openai_deep_research.py` (prefer `submit_and_check`).
- Gemini track: run `scripts/run_gemini_deep_research.py` (prefer `submit_and_check`).
- Exa track: run `scripts/run_exa_research.py` (prefer `submit_and_check`).
- Persist all track artifacts as they complete.

Default quality posture:
- OpenAI/Azure requests default to `--reasoning-effort high`, the highest supported setting for the default o3/o4 deep-research routes.
- Gemini defaults to `deep-research-max-preview-04-2026` for maximum comprehensiveness.
- Exa defaults to `exa-research-pro` for highest reasoning capability.
- Use lower/faster options explicitly only for smoke tests, latency-sensitive work, or cost-sensitive checks.

4. Triangulate and resolve conflicts
- Cross-check overlapping claims between OpenAI, Gemini, and Exa outputs.
- Prefer higher-trust sources when claims conflict.
- Mark unresolved conflicts and confidence level.

5. Synthesize and deliver
- Produce the comprehensive Markdown report first.
- If requested, append alternate output(s) after the Markdown report.

## Credential Loading

Prefer durable botfiles secrets over scraping project-local env files:
- Azure OpenAI deep-research: `~/pro/botfiles/secrets/local/codex-azure.rc`
- Gemini and Exa direct providers: `~/pro/botfiles/secrets/local/deep-research.rc`
- Direct OpenAI fallback: `~/pro/botfiles/secrets/local/codex-openai.rc`, plus explicit direct opt-in

`.botenv` sources those files for normal agent shells. The bundled runners also load the relevant botfiles secret files directly when the environment was not preloaded, while still allowing an explicit `--env-file <path>` override and nearest `.env` fallback.

## OpenAI Execution

Use the bundled script for deterministic runs and durable artifacts.
Keep the final synthesized memo/report/brief in top-level `task-progress-artifacts/`, and send raw engine-specific outputs to `task-progress-artifacts/scratchpad/openai/`.

```bash
uv run ~/.codex/skills/deep-research/scripts/run_openai_deep_research.py \
  --action submit_and_check \
  --prompt-file <path/to/research-prompt.md> \
  --outdir <path/to/task-progress-artifacts/scratchpad/openai>
```

Azure routing:
- When `AZURE_OPENAI_DEEP_RESEARCH_ENDPOINT` or `AZURE_OPENAI_DEEP_RESEARCH_BASE_URL` is set, the runner uses Azure Responses.
- Set `AZURE_OPENAI_DEEP_RESEARCH_API_KEY` when the deep-research deployment lives on a different Azure OpenAI resource than `AZURE_OPENAI_API_KEY`; otherwise the script falls back to `AZURE_OPENAI_API_KEY`.
- In Azure mode, `--models` values must be Azure deployment names. If omitted, the runner uses `AZURE_OPENAI_DEEP_RESEARCH_DEPLOYMENTS` or falls back to `o3-deep-research`.
- Direct OpenAI billing is disabled by default. Use it only with explicit opt-in via `--allow-direct-openai` or `OPENAI_DEEP_RESEARCH_ALLOW_DIRECT=1` plus `OPENAI_API_KEY`.

Useful variants:

```bash
# Submit only
uv run ~/.codex/skills/deep-research/scripts/run_openai_deep_research.py \
  --action submit \
  --prompt-file <path/to/research-prompt.md> \
  --outdir <path/to/task-progress-artifacts/scratchpad/openai>

# Check an existing response id
uv run ~/.codex/skills/deep-research/scripts/run_openai_deep_research.py \
  --action check \
  --response-id <resp_id> \
  --outdir <path/to/task-progress-artifacts/scratchpad/openai>
```

Model guidance:
- Azure fallback order comes from `AZURE_OPENAI_DEEP_RESEARCH_DEPLOYMENTS` or defaults to `o3-deep-research`.
- Direct OpenAI opt-in fallback order is `o3-deep-research,o4-mini-deep-research`.
- Override with `--models` when needed.
- Reasoning effort defaults to `high`; override with `--reasoning-effort` or `OPENAI_DEEP_RESEARCH_REASONING_EFFORT` only when you intentionally want lower cost/latency.
- Use `--max-tool-calls <n>` for low-cost smoke tests or latency-bounded checks.

## Gemini Execution

Use the bundled script for deterministic runs and durable artifacts.
For best first-pass reliability, use an explicit long timeout and retry budget.
Keep raw Gemini outputs under `task-progress-artifacts/scratchpad/gemini/`; reserve top-level task artifacts for the synthesized outputs you want humans to review quickly.
The runner defaults to the high-quality Deep Research Max agent when supported and sends the documented Deep Research `agent_config` (`type=deep-research`, `thinking_summaries=auto`, `collaborative_planning=false`) unless `--no-agent-config` is passed.

```bash
uv run ~/.codex/skills/deep-research/scripts/run_gemini_deep_research.py \
  --action submit_and_check \
  --prompt-file <path/to/research-prompt.md> \
  --outdir <path/to/task-progress-artifacts/scratchpad/gemini> \
  --timeout-minutes 180 \
  --max-timeout-retries 2
```

If you want unlimited waiting, use no-timeout mode:

```bash
uv run ~/.codex/skills/deep-research/scripts/run_gemini_deep_research.py \
  --action submit_and_check \
  --prompt-file <path/to/research-prompt.md> \
  --outdir <path/to/task-progress-artifacts/scratchpad/gemini> \
  --timeout-minutes 0
```

Useful variants:

```bash
# Submit only
uv run ~/.codex/skills/deep-research/scripts/run_gemini_deep_research.py \
  --action submit \
  --prompt-file <path/to/research-prompt.md> \
  --outdir <path/to/task-progress-artifacts/scratchpad/gemini>

# Check an existing interaction id
uv run ~/.codex/skills/deep-research/scripts/run_gemini_deep_research.py \
  --action check \
  --interaction-id <interaction_id> \
  --outdir <path/to/task-progress-artifacts/scratchpad/gemini>
```

Timeout behavior:
- `--timeout-minutes <= 0` means no timeout.
- `submit_and_check` automatically retries timed-out jobs once by default (`--max-timeout-retries 1`).
- Increase retries for unstable runs (for example `--max-timeout-retries 2`).
- Do **not** use `--foreground` with deep-research agents; Gemini Interactions API requires `background=true`.

Recovery playbook:
1. If a run exits on timeout, re-check the latest interaction id first.
2. If still `in_progress`, keep polling with `--action check`.
3. Resubmit only when needed (or let `submit_and_check` retries handle it automatically).

Agent guidance:
- Default agent is `deep-research-max-preview-04-2026` using Interactions API revision `2026-05-20`.
- Use `--agent deep-research-preview-04-2026` when speed/cost matters more than maximum comprehensiveness.
- Use `--api-revision` only when Google publishes a newer Interactions API revision or you need legacy compatibility.
- Script reads `GEMINI_API_KEY` from environment, explicit `--env-file`, nearest `.env`, or `~/pro/botfiles/secrets/local/deep-research.rc` (falls back to `GOOGLE_API_KEY`).
- Submit actions save a header-free `gemini-submit-request-*.json` payload alongside the API response so agent/config drift can be audited without exposing API keys.
- Failed, cancelled, or expired interactions write `gemini-terminal-summary-*.md` instead of `gemini-report-*.md`. A `gemini-report-*.md` file means the interaction reached `completed`.
- Completed interactions write final `model_output` text only; thought summaries and stored prompts are excluded from `gemini-report-*.md`.
- If an older artifact has a report that only repeats the original prompt, treat it as a pre-fix runner artifact and inspect the matching `gemini-check-*.json` terminal status.

## Exa Execution

Use the bundled Exa Research API runner for an additional independent pass.

```bash
uv run ~/.codex/skills/deep-research/scripts/run_exa_research.py \
  --action submit_and_check \
  --prompt-file <path/to/research-prompt.md> \
  --outdir <path/to/task-progress-artifacts/scratchpad/exa>
```

Model guidance:
- `exa-research-pro` is the default for highest quality and strongest reasoning.
- `exa-research` is acceptable when speed/cost matters more than maximum depth.
- `exa-research-fast` is acceptable for low-cost smoke tests.

The script reads `EXA_API_KEY` from environment, explicit `--env-file`, nearest `.env`, or `~/pro/botfiles/secrets/local/deep-research.rc`.
If `EXA_API_KEY` is unavailable but Exa MCP tools are available in the current agent session, the deprecated MCP deep researcher tools may be used as a temporary degraded fallback; record that in task artifacts.

3. Persist the returned report in task artifacts.
   - Default raw Exa outputs to `task-progress-artifacts/scratchpad/exa/`.
   - Promote only the final synthesized report/memo/brief to top-level `task-progress-artifacts/`.

## Source Quality and Citation Rules

Apply `references/source-quality.md`.

Minimum quality bar:
- Prefer primary and institutional sources.
- Treat forums, SEO farms, and uncited aggregators as weak evidence.
- Label confidence for every major conclusion.
- Add a "What would change this recommendation" section for decision-oriented work.

## Optional Output Modes

If requested, provide one or more of these after the Markdown report:
- Executive short brief (1-2 pages)
- Structured JSON summary
- Comparison table only
- Notion-ready page body
- Action checklist

Keep citation IDs consistent across formats.

## Reference Map

- `references/workflow.md` - end-to-end operating procedure
- `references/output-contract.md` - Markdown-first report template and optional formats
- `references/source-quality.md` - source trust tiers, conflict resolution, confidence rules
- `scripts/run_openai_deep_research.py` - reusable OpenAI deep research runner
- `scripts/run_gemini_deep_research.py` - reusable Gemini deep research runner
- `scripts/run_exa_research.py` - reusable Exa Research API runner
