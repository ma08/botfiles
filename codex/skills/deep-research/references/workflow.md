# Deep Research Workflow

## Goal
Run three independent research passes (OpenAI + Gemini + Exa), reconcile findings, and deliver a decision-grade report.

## Speed-first execution rule
- Run independent work in parallel by default.
- Use as many parallel agents as practical for independent sub-questions.
- Keep one coordinator agent responsible for claim-merging, citation integrity, and final consistency.

## Step 1: Scope
Capture:
- Decision/question to answer
- Audience and risk tolerance
- Time horizon
- Geography/domain boundaries
- Required deliverables and deadline

## Step 2: Write the prompt brief
Create a prompt file in top-level task artifacts with:
- Objective and constraints
- Required sections in final report
- Explicit citation requirement
- Confidence and uncertainty instructions
- Requirement to separate evidence vs inference

Keep raw engine outputs under `task-progress-artifacts/scratchpad/<engine>/` and reserve top-level `task-progress-artifacts/` for the final synthesized report, memo, comparison table, and other human-reviewable outputs.

## Step 3: Launch OpenAI, Gemini, and Exa in parallel
Credential loading:
- Normal botfiles shells inherit deep-research secrets through `~/pro/botfiles/.botenv`.
- Azure OpenAI settings live in `~/pro/botfiles/secrets/local/codex-azure.rc`.
- Gemini and Exa direct provider keys live in `~/pro/botfiles/secrets/local/deep-research.rc`.
- Direct OpenAI credentials live in `~/pro/botfiles/secrets/local/codex-openai.rc`, and direct OpenAI deep-research still requires explicit opt-in.
- The bundled runners also check the relevant botfiles secret files directly when the shell environment was not preloaded, while allowing `--env-file <path>` and nearest `.env` fallback.

Default quality posture:
- OpenAI/Azure uses `reasoning.effort=high` by default. This is the highest supported setting for the default o3/o4 deep-research routes; use `--reasoning-effort` only when intentionally lowering cost/latency.
- Gemini uses `deep-research-max-preview-04-2026` by default for maximum comprehensiveness.
- Exa uses `exa-research-pro` by default for strongest reasoning.
- For cheap provider health checks, explicitly lower these settings with `--max-tool-calls`, `--agent deep-research-preview-04-2026`, or `--model exa-research-fast`.

OpenAI lane:

```bash
uv run ~/.codex/skills/deep-research/scripts/run_openai_deep_research.py \
  --action submit_and_check \
  --prompt-file <prompt.md> \
  --outdir <task-progress-artifacts/scratchpad/openai>
```

If `AZURE_OPENAI_DEEP_RESEARCH_ENDPOINT` or `AZURE_OPENAI_DEEP_RESEARCH_BASE_URL` is set, the same command uses Azure Responses automatically. In Azure mode, keep `--models` aligned with Azure deployment names and prefer setting `AZURE_OPENAI_DEEP_RESEARCH_DEPLOYMENTS` when you want a durable default.
Direct OpenAI billing is disabled by default; use `--allow-direct-openai` or `OPENAI_DEEP_RESEARCH_ALLOW_DIRECT=1` only when direct OpenAI spend is intentional.
Use `--max-tool-calls <n>` for low-cost smoke tests or latency-bounded checks.
Use `--reasoning-effort medium` or `low` only when reducing cost/latency is more important than maximum quality.

Exa lane:

```bash
uv run ~/.codex/skills/deep-research/scripts/run_exa_research.py \
  --action submit_and_check \
  --prompt-file <prompt.md> \
  --outdir <task-progress-artifacts/scratchpad/exa>
```

If `EXA_API_KEY` is unavailable but Exa MCP tools are available, use the MCP deep researcher only as a degraded fallback and document that the direct Exa Research API route still needs credentials.

Gemini lane:

```bash
uv run ~/.codex/skills/deep-research/scripts/run_gemini_deep_research.py \
  --action submit_and_check \
  --prompt-file <prompt.md> \
  --outdir <task-progress-artifacts/scratchpad/gemini> \
  --timeout-minutes 180 \
  --max-timeout-retries 2
```

If you prefer unlimited wait:

```bash
uv run ~/.codex/skills/deep-research/scripts/run_gemini_deep_research.py \
  --action submit_and_check \
  --prompt-file <prompt.md> \
  --outdir <task-progress-artifacts/scratchpad/gemini> \
  --timeout-minutes 0
```

Notes:
- `--timeout-minutes <= 0` means no timeout.
- `submit_and_check` retries a timed-out submission once by default (`--max-timeout-retries 1`).
- Do not pass `--foreground` for deep-research agents (Gemini requires `background=true`).
- Default Gemini agent is `deep-research-max-preview-04-2026` with API revision `2026-05-20`.
- Use `--agent deep-research-preview-04-2026` for cheaper/faster checks.
- Resume any in-flight interaction with `--action check --interaction-id <id>`.

Expected OpenAI outputs:
- Raw submit/check JSON snapshots under `task-progress-artifacts/scratchpad/openai/`
- `openai-report-<response_id>.md` under `task-progress-artifacts/scratchpad/openai/`
- `openai-sources-<response_id>.md` under `task-progress-artifacts/scratchpad/openai/`

Expected Gemini outputs:
- Raw submit/check JSON snapshots under `task-progress-artifacts/scratchpad/gemini/`
- `gemini-report-<interaction_id>.md` under `task-progress-artifacts/scratchpad/gemini/`
- `gemini-sources-<interaction_id>.md` under `task-progress-artifacts/scratchpad/gemini/`

Expected Exa outputs:
- Raw submit/check JSON snapshots under `task-progress-artifacts/scratchpad/exa/`
- `exa-report-<research_id>.md` under `task-progress-artifacts/scratchpad/exa/`
- `exa-sources-<research_id>.md` under `task-progress-artifacts/scratchpad/exa/`

## Step 4: Reconcile
- Build a claim matrix with columns: claim, OpenAI evidence, Gemini evidence, Exa evidence, source quality, confidence.
- Mark conflict types:
  - Data mismatch
  - Date mismatch
  - Method mismatch
- Resolve by preferring higher-trust and more recent primary sources.

## Step 5: Draft final report
Follow `output-contract.md`.
- Markdown report first.
- Optional additional formats only when requested.

## Step 6: Final quality check
- Every major claim has at least one citation.
- Dates are explicit.
- Assumptions are listed.
- Risks, limitations, and "what would change" are present.
- Recommendation is tied to evidence and confidence.
