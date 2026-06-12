# Deep Research Provider Health Report

Checked: 2026-05-28 ~02:16pm PST

## Scope

This was a smoke health check for the local `deep-research` skill runners, not a full research-quality benchmark.

I used each provider's default runner path with no explicit `--env-file`, model override, or agent override:

- OpenAI: `run_openai_deep_research.py`, Azure route, default deployment from `AZURE_OPENAI_DEEP_RESEARCH_DEPLOYMENTS`
- Gemini: `run_gemini_deep_research.py`, default agent
- Exa: `run_exa_research.py`, default model

Smoke-test bounds:

- `--timeout-minutes 8`
- `--poll-seconds 10`
- OpenAI only: `--max-tool-calls 1` to keep the provider check bounded

## Result Summary

| Provider | Default route tested | Result | Time to complete | Default-path health |
|---|---:|---:|---:|---|
| Exa | `exa-research` | Passed | 51s | Best/easiest default path |
| Gemini | `deep-research-preview-04-2026` | Passed | 93s | Healthy default path |
| OpenAI | Azure `o3-deep-research` | Passed | ~3m45s | Healthy, slower |

## Provider Outcomes

### Exa

Status: passed.

Evidence:

- Submitted `research_id=r_01ksr6x92gbb49pqyjjdyy5xsd`
- Default model used: `exa-research`
- Terminal status: `completed`
- Report saved to `task-progress-artifacts/scratchpad/exa/exa-report-r_01ksr6x92gbb49pqyjjdyy5xsd.md`
- Cost file reported total estimated cost: `$0.01667125`

Notes:

- This was the easiest working default path in the smoke test.
- It completed fastest and generated a cited response.
- Minor output caveat: the runner saved the report as JSON-fenced content rather than plain Markdown, and source extraction included some trailing punctuation in URLs.

### Gemini

Status: passed.

Evidence:

- Submitted `interaction_id=v1_Chd4NjhZYXNMN0E1bTNxdHNQdWZqWW9RMBIXeDY4WWFzTDdBNW0zcXRzUHVmallvUTA`
- Default agent used: `deep-research-preview-04-2026`
- Terminal status: `completed`
- Report saved to `task-progress-artifacts/scratchpad/gemini/gemini-report-v1_Chd4NjhZYXNMN0E1bTNxdHNQdWZqWW9RMBIXeDY4WWFzTDdBNW0zcXRzUHVmallvUTA.md`

Notes:

- Healthy default path.
- It completed within roughly a minute and a half.
- Caveat: the extracted report includes the original prompt echoed above the answer, and citations are Vertex grounding redirect URLs rather than clean destination URLs.

### OpenAI

Status: passed.

Evidence:

- Submitted `response_id=resp_05738fd97492cc8b006a18afc6cf9481978d6c2feefe7f2a1f`
- Provider used: `azure`
- Default deployment/model used: `o3-deep-research`
- Terminal status: `completed`
- Report saved to `task-progress-artifacts/scratchpad/openai/openai-report-resp_05738fd97492cc8b006a18afc6cf9481978d6c2feefe7f2a1f.md`

Notes:

- Healthy default path, using the Azure deep-research route.
- It completed successfully but was slower than Exa and Gemini for the same small prompt.
- Because stdout was redirected to a log file and Python buffered output, the OpenAI log appeared empty until process exit; this was logging buffering, not a provider submission failure.

## Credential Loading Notes

Observed without printing secret values:

- Azure OpenAI deep-research variables were already present in the shell environment.
- `GEMINI_API_KEY` and `EXA_API_KEY` were not present after sourcing `.botenv`, but both were present in `secrets/local/deep-research.rc`.
- The Gemini and Exa runners successfully loaded `secrets/local/deep-research.rc` directly, so the skill runners work by default.
- Caveat: raw SDK calls outside these runners may not see Gemini or Exa credentials unless `.botenv` is fixed to export them or the caller sources `secrets/local/deep-research.rc`.

## Bottom Line

All three provider runners are working right now.

Default ease ranking from this smoke test:

1. Exa: best/easiest.
2. Gemini: healthy and reasonably quick.
3. OpenAI Azure: healthy but slower.

No provider is outright broken. The main follow-up is configuration hygiene: decide whether `.botenv` should preload `GEMINI_API_KEY` and `EXA_API_KEY`, since the runners recover by loading `deep-research.rc` directly but the ambient shell does not expose those variables.

