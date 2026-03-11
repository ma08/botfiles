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
OpenAI lane:

```bash
uv run ~/.codex/skills/deep-research/scripts/run_openai_deep_research.py \
  --action submit_and_check \
  --prompt-file <prompt.md> \
  --outdir <task-progress-artifacts/scratchpad/openai>
```

Exa lane:
- Start with `mcp__exa__deep_researcher_start`.
- Poll with `mcp__exa__deep_researcher_check` until completed.
- Persist raw Exa report output in `task-progress-artifacts/scratchpad/exa/`, then promote only the synthesized final deliverable to top-level task artifacts.

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
- Resume any in-flight interaction with `--action check --interaction-id <id>`.

Expected OpenAI outputs:
- Raw submit/check JSON snapshots under `task-progress-artifacts/scratchpad/openai/`
- `openai-report-<response_id>.md` under `task-progress-artifacts/scratchpad/openai/`
- `openai-sources-<response_id>.md` under `task-progress-artifacts/scratchpad/openai/`

Expected Gemini outputs:
- Raw submit/check JSON snapshots under `task-progress-artifacts/scratchpad/gemini/`
- `gemini-report-<interaction_id>.md` under `task-progress-artifacts/scratchpad/gemini/`
- `gemini-sources-<interaction_id>.md` under `task-progress-artifacts/scratchpad/gemini/`

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
