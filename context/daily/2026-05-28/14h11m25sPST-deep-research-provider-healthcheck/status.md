# Deep Research Provider Health Check

Started: 2026-05-28 ~02:11pm PST

## Goal

Run a smoke health check for each deep-research provider supported by the local skill runners:

- OpenAI deep research
- Gemini Deep Research
- Exa Research API

Report provider-by-provider outcomes, including which default path works easily and which paths are degraded or failing.

## Artifacts

- Prompt: `user_inputs/health-check-prompt.md`
- Raw OpenAI outputs: `task-progress-artifacts/scratchpad/openai/`
- Raw Gemini outputs: `task-progress-artifacts/scratchpad/gemini/`
- Raw Exa outputs: `task-progress-artifacts/scratchpad/exa/`
- Command logs: `task-progress-artifacts/scratchpad/logs/`
- Summary report: `task-progress-artifacts/provider-health-report.md`

## Outcome

Completed: 2026-05-28 ~02:16pm PST

All provider runners passed:

- Exa default `exa-research`: passed, completed in 51s.
- Gemini default `deep-research-preview-04-2026`: passed, completed in 93s.
- OpenAI Azure default `o3-deep-research`: passed, completed in about 3m45s.

Best/easiest default path from this smoke test: Exa.

No provider is outright broken. Gemini and Exa credentials are present in `secrets/local/deep-research.rc` and load through the runners, but are not present in the ambient shell after sourcing `.botenv`.
