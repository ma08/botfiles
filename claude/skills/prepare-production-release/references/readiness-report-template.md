# Readiness report template

Use the same structure for Stage A and the final Stage B packet. Mark unexecuted sections clearly. Keep the decision summary short and put raw logs in task scratchpad artifacts.

## Contents

1. Human decision and scope
2. Candidate, intake, and risk classification
3. Production state and adviser coverage
4. Evidence and findings
5. Migration and operational handoff
6. Proposed hardening plan
7. Final verification and evidence index
8. Concision rules

```markdown
# Production-readiness report: <candidate>

## Human decision

- Recommendation: ready | ready with accepted risks | not ready
- Candidate: <base>..<head> or exact snapshot
- Risk lane: fast | hardening
- Intended release: <environment and audience>
- Production survey: completed | completed with gaps | not applicable | omitted by scope | blocked: access or authority | blocked: safety
- Adviser coverage: both complete | Oracle omitted/unavailable | Fable omitted/unavailable | both omitted
- Decision needed now: approve plan | revise plan | accept listed risk | prepare separate release task
- Top reasons: <up to five short bullets>
- Human review estimate: <minutes>

## Scope

### Accepted behavior

<spec, ticket, and concise behavior contract>

### Included surfaces

- <surface>

### Exclusions

- <explicit exclusion>

## Candidate and environment

- Repository:
- Base SHA:
- Head SHA or snapshot:
- Working-tree state before:
- Working-tree state after:
- Test environment:
- Production topology evidence source:
- Existing approved production route used: none | <value-safe route label>
- Project profile used: none | <path>

## Intake decisions

| Decision | Answer | Locked implication |
|---|---|---|
| <topic> | <answer> | <implication> |

## Risk classification

### Triggers

- <trigger and evidence>

### Minimum evidence floor

- <required check>

### Accepted omissions

- <skipped check, consequence, compensating control, approver>

## Evidence matrix

| Area | Risk | Action | Pass condition | Result | Artifact |
|---|---|---|---|---|---|
| Candidate | Moving target | Bind exact SHAs | Stable candidate | pass/fail | <path> |

## Production-state survey

- Status:
- Trigger decision:
- Cloud-access runbook consulted:
- Provider or target:
- Existing approved route:
- Value-safe identity:
- Deployed revision and health:
- Migration, schema, or policy state:
- Aggregate state:
- Recovery evidence:
- Gaps or blockers:
- Login, provider, credential, or production state changed: no

## External adviser coverage

| Adviser | Required | Route and effort | Primary lens | Result | Artifact or omission |
|---|---|---|---|---|---|
| Oracle | yes/no | GPT-5.6 Sol, ChatGPT Pro browser | Backend, DB, migration, architecture, compatibility, recovery | complete/unavailable/omitted | <path or reason> |
| Fable | yes/no | Fable, first-party claude.ai, read-only review | Frontend, UX/accessibility, state recovery, structure, change safety | complete/unavailable/omitted | <path or reason> |

### Reconciliation

- Corroborated claims:
- Rejected unsupported claims:
- Merged duplicates:
- Contradictions and targeted checks:
- Material uncovered lens:

## Findings

### Must fix

<finding contract from risk-and-evidence.md>

### Accepted risks

- <risk, consequence, compensating control, acceptance signal>

### Optional cleanup decisions

<optional cleanup contract from risk-and-evidence.md>

### Follow-ups

- <useful non-blocking improvement>

### Rejected noise

- <finding and rejection reason>

## Migration and compatibility

- Changed shapes or contracts:
- Real coexistence combinations:
- Rehearsal performed:
- Idempotency and interruption result:
- Rollback or forward recovery:
- Remaining constraint:

## Operational release handoff

- Proposed deploy order:
- Critical smoke checks:
- Observation window:
- Stop conditions:
- Rollback or forward-recovery owner and steps:
- Production access or approval needed:

## Proposed hardening plan

Status: proposed, not authorized

1. <must-fix item, smallest control, test, and verification>
2. <user-selected optional cleanup, if any>

### Explicitly excluded from implementation

- <follow-up or unrelated debt>

## Final verification

Complete only after an accepted Stage B plan.

- Accepted plan reference:
- Implemented candidate:
- Targeted checks:
- Full applicable gates:
- Corrective reviewer pass:
- Targeted corrective adviser pass:
- E2E or migration rerun:
- Residual risks:
- Final recommendation:

## Evidence index

- <curated artifact>
- <raw scratchpad log>
```

## Concision rules

- Keep `Human decision` readable in roughly 10 minutes or less.
- Link to raw evidence instead of pasting logs.
- Do not hide failed checks in prose.
- Separate candidate-introduced findings from existing debt.
- Name unavailable production evidence and access blockers explicitly.
- Separate vendor capability claims, local adviser-routing policy, and candidate evidence.
- State which adviser claims were directly validated or rejected.
