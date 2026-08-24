---
name: prepare-production-release
description: >-
  Assess and harden an exact software release candidate before production. Use
  when committed or otherwise bounded code needs risk-scaled simplification,
  architecture sanity checks, migration and compatibility review, operational
  readiness, complementary external review, an approved read-only production
  state survey, or a plan-gated hardening pass, especially after agent-first
  or vibe-coded implementation. Produces release evidence and a human decision
  packet. Does not deploy or mutate production.
---

# Prepare Production Release

Turn an exact candidate into an evidence-backed readiness decision without turning "robustness" into speculative machinery. Work in two stages: assess and propose first, then implement only an explicitly accepted plan.

## Required References

Read [`references/risk-and-evidence.md`](references/risk-and-evidence.md) before choosing the intake or evidence scope. Read [`references/adviser-routing.md`](references/adviser-routing.md) before deciding or invoking external adviser coverage. If a real production target exists, read [`references/production-state-survey.md`](references/production-state-survey.md) before any provider command or before recording why the survey is omitted. Read [`references/readiness-report-template.md`](references/readiness-report-template.md) before writing either the Stage A or final report. Read [`references/source-notes.md`](references/source-notes.md) only when auditing or changing this skill.

## Non-Negotiable Boundaries

- **Stage A is candidate-source-read-only and production-state-read-only.** It may inspect code, run non-production checks in an isolated environment, write task evidence, and use an already-approved read-only production route for the bounded survey. It must not edit application code, schemas, lockfiles, infrastructure, production data, or provider state.
- **Stage B needs an accepted saved plan.** Do not edit application code until the user has reviewed and explicitly approved or revised the Stage A plan. Persist that accepted plan in the active task status file before implementation.
- **Never deploy with this skill.** Do not mutate production, run a live migration, change provider settings, toggle production flags, or obtain new production authority. Prepare a separate release-control handoff when those actions become appropriate.
- **Keep production authority local to the assessor.** Never inherit credentials into Oracle or Fable, attach unsanitized production output, retrieve secret values, refresh login state, or switch provider identity for an assessment.
- Preserve the user's existing changes. Never broaden the diff to unrelated debt without explicit scope approval.

## Stage A: Assess and Propose

### 1. Establish the candidate

Resolve before analysis:

- repository and applicable repo instructions;
- exact base and head SHAs, or an explicitly authorized working-tree snapshot;
- accepted behavior, specification, or implementation ticket;
- target environment and deployment topology;
- whether a real production target exists and whether the task permits bounded read-only production evidence;
- expected usage, data sensitivity, reversibility, and explicit exclusions.

Record `git status` and candidate identifiers before running checks. If the candidate or intended behavior is materially ambiguous, stop and ask rather than reviewing a moving target.

Discover project facts from `AGENTS.md`, `CLAUDE.md`, README files, build/package scripts, CI, deploy configuration, and task evidence. If `docs/production-readiness-profile.md` exists, treat it as an optional project profile after repo instructions. Do not require or create a profile on first use.

### 2. Run a short decision intake

Inspect discoverable facts first. Then ask only decision questions, one at a time, in a `grill-me` style. Use `request_user_input` when available, put the recommended option first, and state the locked implication after each answer.

Normally ask 5 to 7 questions. Keep the total below 10 unless a newly discovered material risk requires one more decision. Cover:

1. intended release and user impact;
2. candidate boundary and accepted behavior;
3. traffic, sensitive data, authorization, or external-contract exposure;
4. schema, data, configuration, permission, background-job, or release-order changes;
5. rollback or forward-recovery constraints;
6. desired cleanup depth and human attention budget.

Do not ask what repository evidence can answer. Save substantive answers immutably when a task folder exists.

### 3. Set the risk lane and evidence floor

Use the **fast lane** only for a small, reversible change with no material authorization, sensitive-data, migration, external-contract, background-processing, release-order, or difficult-recovery exposure.

Use the **hardening lane** when any trigger is present, when the change has a wide blast radius, or when agent-generated code lacks meaningful independent technical review.

The user's desired depth controls emphasis, but material risk creates a minimum evidence floor. A skipped triggered check requires an explicit `accepted risk` entry containing the consequence and any compensating control.

### 4. Build the evidence matrix

Select the smallest applicable evidence set. Prefer existing deterministic controls and repository-native commands.

Always bind evidence to the exact candidate. Run applicable install, build, type, lint, unit, integration, and CI-equivalent checks. Do not add tools just to complete a generic checklist. Save raw command output under the active task's scratchpad and keep the human-readable report curated.

Apply four lenses:

- **Simplicity:** changed or demonstrably hot code only. Look for unearned abstractions, accidental duplication, needless indirection, and inconsistency with local conventions. Preserve behavior.
- **Architecture:** inspect concrete boundaries, coupling, state ownership, transaction behavior, failure propagation, test seams, and blast radius. A smell is not a blocker without a current risk path.
- **Migration and compatibility:** inspect schema, data, APIs, configuration, permissions, and deployment order. Rehearse applicable coexistence, idempotency, partial failure, backfill behavior, and rollback or forward recovery.
- **Operational readiness:** inspect reachable authorization and trust boundaries, secret handling, least privilege, measured critical paths, the minimum diagnostics needed to detect failure, smoke checks, stop conditions, and recovery steps.

Invoke project-specific E2E validation when available. Consume its evidence rather than recreating its workflow here.

### 5. Survey production state when applicable

Use the production-state reference. Run the survey without another user prompt only when a real production target exists, the task permits readiness-oriented production reads, and an already-approved read-only route is usable.

Read `~/pro/personal_os/context/cloud-access.md` and applicable repository or task provider runbooks first. Retain only value-safe provider identity, deployment revision and health, migration or schema identifiers, policy status, aggregate state, readiness, and recovery evidence. Project safe fields at command time so secrets, environment values, connection strings, business records, user identifiers, raw payloads, and broad logs never enter artifacts.

Do not log in, refresh a human session, switch account or provider configuration, create or retrieve tokens, copy credential caches, grant roles, or run any command with ambiguous side effects. Record `not applicable`, `omitted by scope`, `completed`, or the exact access blocker.

### 6. Obtain complementary external reviews

When the candidate contains executable code or plausible operational risk, invoke both advisers after deterministic evidence is available:

- **Oracle GPT-5.6 Sol with ChatGPT Pro effort:** emphasize backend, database, migrations, architecture, compatibility, recovery, cross-layer failure, and tricky correctness.
- **Claude Fable 5:** emphasize frontend behavior, UX and accessibility, state and error recovery, codebase structure, design coherence, and change safety. Use the first-party subscription wrapper with `--read-only-review`.

This split is local routing policy, not an official model ranking. Give both advisers the exact candidate, accepted behavior, relevant evidence, exclusions, and finding contract. Do not send credentials or unsanitized production evidence.

Both advisers may comment outside their primary lens. Treat their output as claims to verify, not authority. A native reviewer is a fallback for unavailable coverage or a narrowly justified specialist question, not an automatic third review.

Record a justified omission only for a genuinely non-code, non-operational candidate or an unavailable route. Do not silently substitute another provider or model. If direct evidence cannot cover a missing material lens, recommend `not ready` or request an explicit accepted omission.

### 7. Reconcile and classify findings

For every adviser claim, map it to a candidate surface and reproduce or corroborate it through code, tests, migration rehearsal, or value-safe operational evidence. Merge real duplicates. Resolve adviser contradictions with a targeted check; if material uncertainty remains, preserve it as a blocker or accepted risk.

Every actionable finding must include:

- origin and candidate surface;
- plausible failure and affected user or data;
- reachability or direct evidence;
- severity and release consequence;
- smallest sufficient control;
- verification that would prove the control.

Reject style nits, generic best-practice requests, duplicate tool output, unrelated existing debt, hypothetical-scale concerns, and unsupported adviser claims.

Classify every material finding as:

- `must fix`: reachable current release risk;
- `accepted risk`: understood risk explicitly accepted by the user;
- `follow-up`: valuable but not required for this candidate;
- `noise`: unsupported, irrelevant, duplicated, or stylistic.

Architecture blocks only for concrete current correctness, data-safety, operability, testability, or near-term change-safety risk. If a major smell appears contained and low-risk to fix, offer it as an optional decision. Explain the situation, stakes, estimated effort, regression risk, and smallest proposed change. Let the user decide whether it enters the plan.

### 8. Save the Stage A report and proposed plan

Use the report template. Include the exact candidate, production-survey status, adviser routes and coverage, corroborated and rejected claims, finding dispositions, migration and recovery proof, residual risks, and a concise recommendation: `ready`, `ready with accepted risks`, or `not ready`.

Write a bounded hardening plan containing only `must fix` findings and optional cleanup the user selects. Keep broader improvements in a separate follow-up list. Save the plan in the active task status file and stop for review.

If implementation is requested, use a one-decision-at-a-time plan review. Only an explicit accept signal authorizes Stage B.

## Stage B: Implement the Accepted Plan

Before editing:

1. verify the candidate has not changed;
2. persist the full accepted plan in the active task status file;
3. capture a fresh `git status`;
4. confirm production execution remains excluded.

Then:

1. Implement only accepted `must fix` and explicitly selected optional cleanup items.
2. Prefer a red-capable regression test and the smallest sufficient control.
3. Keep behavior-preserving cleanup separate from functional fixes when practical.
4. Run targeted checks after each coherent change, then all applicable candidate gates.
5. Run at most one targeted corrective pass for each adviser domain materially changed by Stage B. Do not repeat both advisers automatically. Further cycles require a materially changed candidate or explicit user approval.
6. Re-run applicable E2E or migration rehearsals through the project-specific workflow.
7. Produce the final readiness packet and a separate release-control handoff. Stop before deployment.

## Anti-Overengineering Contract

Do not introduce a service, framework, dependency, queue, cache, feature-flag platform, telemetry platform, abstraction layer, or broad refactor unless all five are true:

1. a current release risk is reachable or observed;
2. existing controls are inadequate;
3. the proposal is the smallest sufficient control;
4. a verification can prove it works;
5. its operational and maintenance cost is recorded.

Treat large files, duplication, sparse metrics, and missing abstractions as inquiry signals, not failures. Scale controls to expected traffic, data sensitivity, reversibility, and team size. Do not use fixed line-count thresholds, exhaustive smell inventories, blanket feature flags or telemetry, broad architecture sweeps, or mandatory unsafe database down migrations.

Stop when applicable gates pass and all `must fix` findings are resolved or explicitly moved to `accepted risk`. Do not keep inventing work to increase confidence cosmetically.

## Stop and Escalate

Stop and request input when:

- the candidate or accepted behavior cannot be fixed precisely;
- a production-shaped environment cannot support a credible decision;
- a material migration cannot be safely rehearsed;
- an authorization, data-integrity, secret, or recovery risk remains unresolved;
- required production evidence lacks an existing approved read-only route;
- an adviser route is unavailable and direct evidence cannot cover its material lens;
- the next useful action requires a login change, new credentials, production mutation, release approval, or broader scope;
- findings exceed the accepted hardening budget;
- deterministic or reviewer infrastructure is unavailable and no safe equivalent exists.

Report exactly what is missing, why it matters, who must decide or provide access, and what resumes afterward.
