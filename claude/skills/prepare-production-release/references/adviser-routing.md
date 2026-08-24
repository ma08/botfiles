# External adviser routing

- Last evidence review: 2026-08-07
- Policy owner: local `prepare-production-release` workflow
- Purpose: obtain complementary judgment without treating model output as release authority

## Contents

1. Trigger and omission rule
2. Official capability facts
3. Local routing policy
4. Evidence packet
5. Invocation controls
6. Reconciliation contract
7. Failure handling
8. Refresh policy

## 1. Trigger and omission rule

Invoke both advisers when the exact candidate changes executable source, schemas, migrations, infrastructure, runtime configuration, permissions, dependencies, user flows, data handling, background processing, or release behavior, or when the production-state survey identifies plausible operational risk.

Omit them only when the candidate is genuinely non-code and non-operational, such as documentation-only or task-metadata-only work. Record the omission and evidence. Do not call a code candidate "fast lane" to bypass the advisers.

If a route is unavailable, record the exact failure. Do not silently substitute another model, provider, API, or effort level. Continue only when direct evidence covers the missing lens. Otherwise recommend `not ready` or request an explicit accepted omission.

## 2. Official capability facts

These are vendor claims and documented product capabilities, not a neutral head-to-head ranking.

### OpenAI

- [GPT-5.6 Sol model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol) describes Sol as a frontier model for complex professional work and documents its large context window and tool support.
- [GPT-5.6 in ChatGPT](https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt) describes Sol as designed for complex coding and related professional work, and identifies Pro as the highest-capability ChatGPT option for difficult and longer-running workflows.

### Anthropic

- [Claude Fable 5](https://www.anthropic.com/claude/fable) describes Fable as Anthropic's most capable model for ambitious coding projects, including migrations, complex implementations, self-authored tests, high-fidelity design implementation, and vision-based comparison to goals.
- [Anthropic's Transparency Hub](https://www.anthropic.com/transparency/model-report) describes Fable as strong in software engineering, knowledge work, and vision, and confirms availability through Claude.ai and Claude Code.
- [Claude Code CLI reference](https://code.claude.com/docs/en/cli-usage), [permission modes](https://code.claude.com/docs/en/permission-modes), and [permissions](https://code.claude.com/docs/en/permissions) document tool restriction, scoped pre-approval, non-interactive turn limits, `dontAsk`, permission bypass, and the distinction between permissions and sandboxing.

No official source establishes that Sol is categorically superior for backend work or Fable for frontend work. The division below is a local workflow choice based on Sourya's requested review pattern and observed usefulness.

## 3. Local routing policy

| Adviser | Primary emphasis | Secondary emphasis |
|---|---|---|
| Oracle GPT-5.6 Sol with ChatGPT Pro effort | Backend, database, migrations, architecture, compatibility, recovery, cross-layer failure, tricky correctness | Security boundaries and systemic failure paths |
| Claude Fable 5 | Frontend behavior, UX and accessibility, state and error recovery, codebase structure, design coherence, change safety | Cross-layer design holes and implementation consistency |

Both advisers may identify issues outside their primary emphasis. Overlap increases attention, not truth. Codex must still validate the claim.

The two advisers are the default independent review set. Do not automatically add the native reviewer as a third pass. Use it only when one route is unavailable or a narrowly defined specialist question remains.

## 4. Evidence packet

Run deterministic checks before adviser calls. Give each adviser a standalone packet containing only what it needs:

1. exact repository, base and head, or authorized snapshot;
2. accepted behavior and explicit exclusions;
3. changed-file inventory and relevant diff or source files;
4. risk lane, topology, realistic use, and triggered evidence rows;
5. deterministic check results and migration or E2E evidence;
6. value-safe production conclusions, never raw production output;
7. the finding contract and a request to omit style-only advice.

Exclude secrets, credentials, environment values, connection strings, business records, user identifiers, raw payloads, and broad logs. Prefer compact source and evidence over whole-repository uploads.

## 5. Invocation controls

### Oracle

Read and follow `$oracle` before calling it. Use the supported local `oracle` wrapper. The required route is ChatGPT browser mode with GPT-5.6 Sol and the account's Pro effort. Pro is a ChatGPT effort, not an API model identifier.

Preflight the prompt and files first:

```bash
oracle --dry-run \
  -p "$(< /path/to/oracle-review-prompt.md)" \
  --file /path/to/relevant-file
```

Then run the same bounded request through the wrapper:

```bash
oracle \
  -p "$(< /path/to/oracle-review-prompt.md)" \
  --file /path/to/relevant-file
```

Do not attach secrets. Do not switch to an API route or a lower model when the browser route is slow or unavailable. Reattach to the same Oracle session until it completes or errors.

### Fable

Read and follow `$claude-fable-advisor` before calling it. Use the first-party subscription runner with the bounded preset:

```bash
uv run python "$HOME/pro/botfiles/codex/skills/claude-fable-advisor/scripts/run_fable_advisor.py" \
  --cwd /path/to/repository \
  --prompt-file /path/to/fable-review-prompt.md \
  --read-only-review \
  --output-dir /path/to/task-scratchpad/fable-review
```

The preset uses `Read`, `Glob`, `Grep`, and selected read-only Git commands, defaults to 12 turns, strips ambient credentials, requires first-party `claude.ai` routing, and rejects `--yolo` and credential inheritance. Its permission allowlist is procedural, not an OS-level sandbox. Verify unchanged pre/post repository state for release-critical reviews.

If Claude reports safeguard rerouting or the output does not establish that the requested Fable route was available, record Fable coverage as unavailable. Do not count a substituted model as Fable review.

## 6. Reconciliation contract

Require each proposed finding to name:

- origin and candidate surface;
- plausible failure and affected user or data;
- reachability evidence;
- release consequence and severity;
- smallest sufficient control;
- verification method.

Codex then:

1. maps the claim to code, tests, migration evidence, or value-safe operational evidence;
2. reproduces or corroborates it;
3. merges genuine duplicates;
4. rejects unsupported, stylistic, unrelated, or hypothetical-scale advice;
5. resolves contradictions through one targeted check;
6. preserves unresolved material uncertainty as a blocker or accepted risk.

Record accepted and rejected adviser claims in the readiness report. An adviser label is not evidence by itself.

## 7. Failure handling

| Failure | Required response |
|---|---|
| Oracle browser route unavailable | Record the route error; do not use API or lower-model fallback |
| Oracle still in progress | Wait or reattach to the same session; do not create a duplicate run |
| Fable first-party gate fails | Record `authMethod`, `apiProvider`, and `subscriptionType`; do not change login state inside the assessment |
| Fable preset needs broader tools | Stop and report the exact missing evidence; do not add write tools or permission bypass |
| Adviser contradicts deterministic evidence | Run one targeted reproduction and reject the claim if unsupported |
| Material lens remains uncovered | Recommend `not ready` or request an explicit accepted omission |

## 8. Refresh policy

Recheck the official sources and local wrappers when a model alias, effort control, route, Claude Code permission flag, or adviser script changes; when either adviser repeatedly fails its assigned lens; or at least once per quarter while the workflow is active.

Do not silently rewrite the local routing policy when a model changes. Changing the default division or authority requires a newly accepted skill-maintenance plan.
