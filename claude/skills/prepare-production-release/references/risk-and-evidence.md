# Risk and evidence guide

Use this guide to choose a proportionate evidence set. It is a routing aid, not a universal checklist.

## Contents

1. Intake question bank
2. Risk lane selection
3. Evidence matrix
4. Lens prompts
5. Finding contract
6. Optional cleanup decision
7. Anti-overengineering test
8. Adviser and production evidence rules

## 1. Intake question bank

Inspect the repository before asking. Select only questions that require user judgment, normally 5 to 7 total.

### Release intent

- What exact candidate is being considered, and what accepted behavior defines success?
- Is the goal an internal preview, limited release, full production release, or readiness assessment only?
- Which users or business process would be harmed if it fails?

### Exposure

- Does it touch authentication, authorization, secrets, sensitive data, billing, legal records, or external integrations?
- What traffic, data volume, concurrency, and availability are actually expected over the next release horizon?
- Are old and new application versions, schemas, clients, jobs, or APIs expected to coexist?

### Recovery

- What is the fastest safe recovery: application rollback, feature disablement, forward fix, data restore, or manual repair?
- Which effects cannot be reversed by reverting code?
- What evidence would make the user comfortable approving the later release?

### Cleanup appetite

- Should the pass cover only release blockers, or also contained low-risk simplifications?
- How much human review time is available for optional decisions?

## 2. Risk lane selection

### Fast lane

All must be true:

- candidate is exact and small enough to understand as one coherent change;
- behavior is reversible through normal application rollback;
- no authorization or sensitive-data boundary changes;
- no schema, data, API, configuration, permission, or background-job migration;
- no old/new coexistence or ordered rollout requirement;
- no new critical dependency or difficult-to-detect failure mode;
- meaningful automated checks already cover the changed behavior.

Fast lane minimum:

1. candidate binding and clean pre/post status;
2. relevant native deterministic checks;
3. changed-path simplicity and architecture sanity;
4. both complementary advisers when the code or operational-risk trigger applies;
5. production-survey state and bounded evidence when a real target exists;
6. targeted smoke or E2E evidence;
7. rollback statement and concise readiness report.

### Hardening lane

Use if any fast-lane condition is false or uncertain. Common triggers:

- authn/authz, tenant isolation, secrets, sensitive or regulated data;
- schema or data changes, backfills, format changes, or imports/exports;
- external API or client contract changes;
- background workers, retries, concurrency, idempotency, or partial failure;
- ordered deploys, old/new coexistence, or irreversible side effects;
- wide blast radius or weak observability of likely failures;
- agent-generated implementation with little independent technical review;
- recovery depends on untested manual action.

Add only the evidence rows relevant to the triggers.

## 3. Evidence matrix

For each selected row, record: trigger, risk, evidence action, pass condition, artifact, and disposition.

| Area | Trigger | Proportionate evidence |
|---|---|---|
| Candidate | Always | Exact base/head or snapshot, repo instructions, pre/post status |
| Behavior | Always | Accepted spec mapped to tests and user-visible flows |
| Build/CI | Applicable native checks | Reproduce current-head install/build/type/lint/test/CI locally or through trusted current-head CI |
| Simplicity | Changed or hot code | Behavior-preserving review for needless indirection, accidental duplication, and local inconsistency |
| Architecture | Boundary or state changes | Trace request/data flow, ownership, failure propagation, transaction limits, and test seams |
| Authorization | Role or tenant changes | Positive and negative tests at the server-side enforcement point |
| Sensitive data | New collection, storage, or exposure | Data-flow and disclosure checks, retention and secret handling review |
| Schema/data | Migration or backfill | Production-shaped schema rehearsal, realistic fixtures, idempotency, interruption, and recovery |
| Compatibility | Coexistence or public contract | Old/new matrix only for combinations that can exist during rollout |
| Jobs/concurrency | Async or retry behavior | Duplicate delivery, retry, timeout, race, partial completion, and idempotency evidence |
| Dependencies | New or materially changed | Reachability and advisory triage, failure behavior, version and license fit as relevant |
| Performance | Critical path or expected load risk | Measure the actual path at expected and modest peak load; avoid hypothetical-scale benchmarks |
| Diagnostics | Failure is otherwise hard to detect | Minimum logs, health, error capture, or metric needed to identify and localize the selected failure modes |
| UX/E2E | User flow changed | Project-specific E2E or smoke test at the closest safe environment |
| Recovery | Always | Concrete rollback or forward-recovery steps, stop condition, owner, and verification |
| Production state | Real target and task permits reads | Value-safe provider identity, deployed revision, migration/schema/policy state, aggregate health, and recovery evidence through an existing approved read-only route |
| Oracle adviser | Executable code or operational risk | GPT-5.6 Sol with ChatGPT Pro review emphasizing backend, database, migration, architecture, compatibility, recovery, and tricky correctness |
| Fable adviser | Executable code or operational risk | First-party Fable read-only review emphasizing frontend, UX/accessibility, state recovery, code structure, and change safety |
| Reconciliation | Any adviser claim | Direct reproduction or corroboration, duplicate merge, contradiction check, and explicit rejection of unsupported claims |

Do not require every row.

## 4. Lens prompts

### Simplicity

- Can an abstraction be deleted without losing behavior, safety, or a real second use?
- Is the same decision encoded in multiple places that can drift?
- Does the candidate follow local conventions, or introduce a parallel pattern without need?
- Would simplification reduce comprehension or failure risk without broadening the diff?

Do not optimize for fewer lines. Do not refactor unrelated code. Understand the reason for an unusual construct before changing it.

### Architecture

- Where are state and invariants owned?
- Which boundary enforces authorization, validation, and transactionality?
- Can a partial failure leave inconsistent or misleading state?
- Does the interface expose unnecessary implementation detail or force callers to duplicate policy?
- Is the changed behavior testable through a stable public seam?
- What is the real blast radius at expected use?

A smell blocks only when it creates a current correctness, data-safety, operability, testability, or near-term change-safety risk.

### Migration and compatibility

- Which code and data shapes can coexist during the actual rollout?
- Is expand-contract needed, or would it be ceremony for a single atomic deployment?
- Are writes idempotent? Can a backfill resume after interruption?
- What happens if deployment stops halfway?
- Can code rollback safely after data has changed?
- If reversal is unsafe, is forward recovery rehearsed and bounded?

Never demand a database down migration when running it would be more dangerous than forward recovery.

### Operational readiness

- Which selected failure modes would be invisible without one additional signal?
- What smoke check confirms the release's critical behavior?
- What measurable condition should stop or reverse a rollout?
- Who performs recovery, with which access, and how is success verified?
- Are environment-specific configuration and least privilege correct for the candidate?

Add only the diagnostics needed to detect and localize plausible current failures. Do not build a telemetry program by default.

## 5. Finding contract

Use this schema:

```markdown
### [severity] Concise failure title

- Origin:
- Candidate surface:
- Plausible failure:
- Affected user/data:
- Reachability or evidence:
- Direct validation:
- Release consequence:
- Smallest sufficient control:
- Verification:
- Disposition: must fix | accepted risk | follow-up | noise
```

Severity guide:

- `critical`: likely compromise, destructive data loss, or broad outage; do not proceed.
- `high`: reachable major correctness, authorization, integrity, or recovery failure; normally `must fix`.
- `medium`: real bounded failure or operational gap; decide from likelihood, impact, and recovery.
- `low`: contained improvement with little release consequence; normally `follow-up` or optional cleanup.

Reject a finding if it lacks a current path, duplicates stronger evidence, applies only to unrelated existing code, or asks for stylistic conformity without a risk reduction.

## 6. Optional cleanup decision

When a major smell appears easy to fix, present:

```markdown
### Optional cleanup: <title>

- Situation:
- Why it may matter soon:
- Why it does not block this release:
- Smallest proposed change:
- Estimated effort:
- Regression and rollout risk:
- Verification:
- Recommendation: include now | follow up | leave as is
```

"Easy" means contained, reversible, behavior-protected, consistent with local conventions, and free of new infrastructure or dependencies. The user decides.

## 7. Anti-overengineering test

Before proposing a new mechanism, answer all five:

1. What reachable current risk does it control?
2. Why are existing controls inadequate?
3. Why is this the smallest sufficient control?
4. What verification will prove it works?
5. What maintenance and operational burden does it add?

If any answer is missing, keep it out of the hardening plan.

## 8. Adviser and production evidence rules

- Adviser output is a claim source, not proof. Do not use model agreement as the direct validation field.
- Both advisers are required for executable code or operational-risk candidates, including fast-lane code changes. Omission needs a recorded reason and material missing coverage needs `not ready` or explicit acceptance.
- The native reviewer is not an automatic third pass. Add it only for unavailable coverage or one narrow specialist question.
- Production evidence must follow `production-state-survey.md`. Preserve only value-safe metadata and aggregates selected at command time.
- Never send credentials or unsanitized production output to an adviser.
- If advisers disagree, run one targeted check. Unresolved material uncertainty remains a blocker or accepted risk.
