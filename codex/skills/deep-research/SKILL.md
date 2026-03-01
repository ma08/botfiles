---
name: deep-research
description: Run end-to-end deep research using OpenAI Responses API deep-research models plus Exa Deep Research, then synthesize results into a comprehensive, easy-to-read, citation-backed Markdown report by default. Use for due diligence, investment research, market/competitor analysis, technical investigations, policy analysis, and any high-stakes question where cross-checking sources across both OpenAI and Exa improves confidence; generate alternate formats only when the user explicitly requests them.
---

# Deep Research

Produce decision-grade research outputs with dual-engine evidence gathering:
- OpenAI deep research via bundled script (`scripts/run_openai_deep_research.py`)
- Exa deep research via MCP tools (`mcp__exa__deep_researcher_start` + `mcp__exa__deep_researcher_check`)

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

1. Run OpenAI and Exa research in parallel whenever both are required.
2. Parallelize independent sub-questions with multiple agents (market, technical, legal, risks, benchmarks).
3. Start synthesis only after minimum evidence is available from both engines, then continue ingesting late-arriving evidence in parallel.
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
- Exa track: call `mcp__exa__deep_researcher_start`, then poll to completion.
- Persist both tracks' artifacts as they complete.

4. Triangulate and resolve conflicts
- Cross-check overlapping claims between OpenAI and Exa outputs.
- Prefer higher-trust sources when claims conflict.
- Mark unresolved conflicts and confidence level.

5. Synthesize and deliver
- Produce the comprehensive Markdown report first.
- If requested, append alternate output(s) after the Markdown report.

## OpenAI Execution

Use the bundled script for deterministic runs and durable artifacts.

```bash
uv run ~/.codex/skills/deep-research/scripts/run_openai_deep_research.py \
  --action submit_and_check \
  --prompt-file <path/to/research-prompt.md> \
  --outdir <path/to/task-progress-artifacts>
```

Useful variants:

```bash
# Submit only
uv run ~/.codex/skills/deep-research/scripts/run_openai_deep_research.py \
  --action submit \
  --prompt-file <path/to/research-prompt.md> \
  --outdir <path/to/task-progress-artifacts>

# Check an existing response id
uv run ~/.codex/skills/deep-research/scripts/run_openai_deep_research.py \
  --action check \
  --response-id <resp_id> \
  --outdir <path/to/task-progress-artifacts>
```

Model guidance:
- Default fallback order is `o3-deep-research,o4-mini-deep-research`.
- Override with `--models` when needed.

## Exa Execution

Use Exa deep researcher for a second independent pass.

1. Start research with `mcp__exa__deep_researcher_start`.
- `model=exa-research` for most tasks.
- `model=exa-research-pro` for high-stakes or complex investigations.

2. Poll with `mcp__exa__deep_researcher_check`.
- Reuse the same `researchId`.
- Continue polling until status is `completed`.

3. Persist the returned report in task artifacts.

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
