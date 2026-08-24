# Source notes

This skill is a local synthesis. It paraphrases selected patterns and does not install or reproduce either upstream skill collection wholesale.

## Pinned source snapshots

### Matt Pocock

- Repository: https://github.com/mattpocock/skills
- Inspected commit: `84fdeffd12f2ee307994d1eb6feb48173b6e0502`
- Relevant collection: `skills/engineering`
- Adapted ideas: specification-aware review, behavior through public seams, minimal diagnostic loops, regression tests, vertical slices, migration ordering, and architecture lenses used as judgment prompts.
- Deliberately omitted as defaults: exhaustive smell enumeration, broad architecture-improvement sweeps, long specification expansion, and multiple overlapping reviewers.

### Addy Osmani

- Repository: https://github.com/addyosmani/agent-skills
- Inspected commit: `d2478bf0c73a6357df39a3ed6aff16acaa218843`
- Adapted ideas: changed-scope behavior-preserving simplification, incremental and rollback-friendly implementation, expand-contract migrations where actual coexistence requires them, reachable trust-boundary review, minimal launch controls, and high-confidence findings.
- Deliberately omitted as defaults: fixed line-count limits, a flag or kill switch for every feature, full telemetry for every endpoint, mandatory down migrations, fixed rollout thresholds, and repeated adversarial review cycles.

## Supporting primary guidance

- Anthropic, verification loops with skills: https://claude.com/blog/building-verification-loops-in-claude-code-with-skills
- Anthropic, securing an AI-native software development lifecycle: https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle
- OpenAI, building code review with the Codex SDK: https://developers.openai.com/cookbook/examples/codex/build_code_review_with_codex_sdk

## Current adviser capability and permission sources

Evidence last reviewed 2026-08-07:

- OpenAI GPT-5.6 Sol model documentation: https://developers.openai.com/api/docs/models/gpt-5.6-sol
- OpenAI GPT-5.6 in ChatGPT, including Pro effort: https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt
- Anthropic Claude Fable 5: https://www.anthropic.com/claude/fable
- Anthropic Transparency Hub: https://www.anthropic.com/transparency/model-report
- Claude Code CLI reference: https://code.claude.com/docs/en/cli-usage
- Claude Code permission modes: https://code.claude.com/docs/en/permission-modes
- Claude Code permissions and sandbox distinction: https://code.claude.com/docs/en/permissions

These sources establish broad vendor-described capabilities and supported harness controls. They do not establish a neutral model ranking. The Oracle-backend and Fable-frontend emphasis is a local workflow policy accepted under ZON-196 Plan v4, not an official comparative claim.

The local synthesis follows the shared theme: combine deterministic checks with focused agent judgment, scale controls by reachable risk, give findings evidence, keep humans at high-leverage decision points, and bound reviewer loops.

## Local design decisions

- One short adaptive intake, normally fewer than 10 decisions.
- A risk-triggered minimum evidence floor with explicit accepted-risk overrides.
- Two complementary external advisers for executable code or operational-risk candidates, with no automatic third reviewer.
- Oracle GPT-5.6 Sol with ChatGPT Pro effort emphasizes backend, database, migration, architecture, compatibility, recovery, and tricky correctness.
- Claude Fable 5 emphasizes frontend, UX/accessibility, state and error recovery, codebase structure, and change safety through a bounded read-only preset.
- Codex must reproduce, corroborate, or reject adviser claims against direct evidence.
- Current release risk is the only architecture-blocking threshold.
- Contained low-risk cleanup remains a user decision.
- Stage A assessment precedes any Stage B code modification.
- Stage A may use an already-approved read-only production route for value-safe readiness metadata after consulting `cloud-access.md`; login changes, credential retrieval or inheritance, and production mutation remain outside the skill.
- Deployment remains outside the skill.

Recheck the adviser sources and wrappers when model aliases, effort controls, routes, or permission flags change; when either adviser repeatedly fails its assigned lens; or at least quarterly while the workflow is active. Do not silently change the routing policy without a newly accepted maintenance plan.

When changing this skill, preserve these decisions unless a newly accepted plan explicitly supersedes them.
