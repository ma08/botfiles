# Deep Research Workflow

## Goal
Run two independent research passes (OpenAI + Exa), reconcile findings, and deliver a decision-grade report.

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
Create a prompt file in task artifacts with:
- Objective and constraints
- Required sections in final report
- Explicit citation requirement
- Confidence and uncertainty instructions
- Requirement to separate evidence vs inference

## Step 3: Launch OpenAI and Exa in parallel
OpenAI lane:

```bash
uv run ~/.codex/skills/deep-research/scripts/run_openai_deep_research.py \
  --action submit_and_check \
  --prompt-file <prompt.md> \
  --outdir <task-progress-artifacts>
```

Exa lane:
- Start with `mcp__exa__deep_researcher_start`.
- Poll with `mcp__exa__deep_researcher_check` until completed.
- Persist Exa report output in task artifacts.

Expected OpenAI outputs:
- Raw submit/check JSON snapshots
- `openai-report-<response_id>.md`
- `openai-sources-<response_id>.md`

## Step 4: Reconcile
- Build a claim matrix with columns: claim, OpenAI evidence, Exa evidence, source quality, confidence.
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
