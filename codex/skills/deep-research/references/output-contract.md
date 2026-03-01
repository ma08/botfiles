# Output Contract

## Default behavior
Always deliver a comprehensive, easy-to-read Markdown report first.

If the user asks for another format, provide it after the Markdown report.

## Required Markdown structure

```markdown
# <Title>

## Executive Summary
- Decision-oriented summary
- Primary recommendation
- Confidence level

## Scope and Method
- Question
- Constraints
- Time horizon
- How research was done (OpenAI + Exa + validation approach)

## Key Findings
- Evidence-backed findings with citations

## Detailed Analysis
### Option/Theme 1
### Option/Theme 2
...

## Comparative Scoring
- Table with criteria, score, confidence, notes

## Scenario Analysis
- Base case
- Upside case
- Downside case

## Risks and Mitigations
- Risk
- Impact
- Mitigation

## What Would Change This Recommendation?
- Trigger events/thresholds that would alter the decision

## Limitations and Data Gaps
- Missing data, proxies, confidence caveats

## Sources
1. [Source name](URL)
2. [Source name](URL)
...
```

## Optional additional outputs (only on request)

### 1) Executive brief
- 5-10 bullets, action-oriented

### 2) JSON summary
Include keys:
- `question`
- `recommendation`
- `confidence`
- `key_findings`
- `scenarios`
- `risks`
- `sources`

### 3) Notion-ready body
- Same logical sections as Markdown
- Keep tables simple markdown tables

### 4) Table-only decision sheet
- Criteria, score, rationale, confidence, source IDs

## Consistency rule
If multiple outputs are produced:
- Keep conclusions identical unless explicitly versioned.
- Keep citation numbering consistent across formats.
