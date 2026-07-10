---
name: goal-traceability-loop
description: Use for long-horizon Codex implementation work where an accepted spec must be converted into a goal-driven execution loop with a durable feature/test traceability matrix. Trigger when the user asks for a Ralph-style loop, full MVP/V1 implementation, comprehensive feature checklist, requirements-to-tests tracking, Codex goal-backed iteration, or spec-to-implementation workflow with validation evidence.
---

# Goal Traceability Loop

Use this skill to keep large implementation efforts grounded in an explicitly accepted spec. The controlling artifacts separate immutable requirements from mutable execution state so an autonomous goal cannot silently reinterpret scope.

## Operating Principles

- Treat accepted requirements as the source of truth; do not silently expand scope.
- Preserve source authority: distinguish stakeholder requirements, user overrides, and implementation-derived defaults.
- Classify every discovered requirement by `decision state`, `release`, and `fidelity`; do not overload one scope/status field.
- Keep scope decisions durable in task artifacts/status, not only chat.
- Use Codex goal mode only after the user has reviewed the implementation plan from file, explicitly accepted it, and the accepted plan has been persisted in the active task status file.
- An agent without native Codex goal tools may prepare or review the artifacts, but must hand goal creation, status changes, and completion back to the Codex goal owner; never simulate goal state in prose or files.
- Use one active goal owner at a time. The owner alone controls the goal, integration branch, execution matrix, leases, exceptions, and completion decision.
- Validate after each feature cluster and repair failures before moving to the next cluster.
- Record evidence continuously: commands, screenshots, exported files, manual flows, logs, and known gaps.
- State the harness trust model. Default to honest-but-fallible supervised agents unless the user explicitly requests a cryptographic/adversarial boundary; do not add OS-user/signing infrastructure for ordinary orchestration correctness.
- Treat manifest-pinned accepted plans, locks, catalogs, human matrices, briefs, appendices, and readiness documents as immutable accepted planning inputs during the goal. Track runtime progress in separate mutable/append-only controls; emit as-built stakeholder documents under new dated versions after control closeout.
- Do not mark the goal complete until every accepted in-scope row has implementation, validation, documentation, risk, test, integrated-SHA, and evidence fields in a terminal state.
- Completion means the locally agreed handoff state (normally `review_ready`), not merged, deployed, or production-approved unless the accepted plan explicitly says otherwise.

## Required Artifacts

Create or update these human-readable artifacts in the active task folder unless the user gives a different location:

- `requirements-brief.md`: concise stakeholder-facing review brief.
- `requirements-appendix.md`: detailed V1/V2 requirements and decisions.
- `traceability-matrix.md`: engineering matrix used to drive implementation.
- `goal-runbook.md`: compact Codex goal/runbook that points to the matrix and states the done criteria.
- `validation-log.md`: ongoing evidence log for commands, screenshots, manual checks, known gaps, and fixes.

If a repo already has equivalent artifacts, update the existing files instead of creating duplicates.

For high-assurance or long-running goals, also maintain:

- `source-decision-ledger.md`: source clauses, authority, supersession, and accepted overrides.
- `requirements-lock.json`: immutable accepted atomic requirements and acceptance criteria.
- `execution-matrix-template.json`: immutable launch template generated from the accepted lock/catalog.
- `goal-execution-matrix.json`: mutable schema-validated implementation/validation/documentation/risk state with separate integrated SHAs per repository.
- `goal-run-manifest.json`: accepted hashes, repositories, base SHAs, branch/worktree, model policy, prohibited actions, and exact validation commands.
- `goal-run-launch-anchor.json`: separately committed external binding from accepted status/control commit to the literal manifest hash and launch SHAs; never embed a manifest's own commit/hash inside itself.
- `goal-run-state.json`: current packet/cluster, owner, HEAD, checkpoints, and resume data.
- `leases.json`: owner-controlled path and singleton-resource leases.
- `validation-evidence.jsonl`: append-only evidence records with requirement/test/scenario/packet IDs, command, result, environment, exact code SHAs, and SHA-256-pinned artifacts.
- `coverage-catalog.json`: accepted contextual-help targets, role tutorial steps, browser semantic/color cues, explicit self-evident exemptions, and their allowed requirement/test mappings when these surfaces are part of acceptance.
- `exceptions.json`: explicitly accepted deviations, baseline failures, and deferrals.
- `work-packets/`: write-once packet definitions and superseding revisions constrained by manifest-owned profiles.
- `work-packet-results/`: write-once terminal worker outcomes bound to exact packet bytes.
- `work-packet-dispositions/`: write-once owner decisions bound to exact packet/result bytes; latest revisions become `integrated`, while every earlier unintegrated revision becomes contiguously `superseded`.
- `human-gate-receipt.json` and `human-gate-snapshots/`: pre-human proof that pins exact awaiting-human run state, execution matrix, pre-human evidence, final automated/review artifacts, packet/result/disposition/lease/exception inventory, repository heads, hashes, actor, and chronology. The verifier, not prose or an agent edit, stamps durable `validatedAt` only after all receipt/runtime checks pass.
- `completion-report.json`: machine-checkable final coverage and exact-final-SHA result.
- `control-schemas.json`: closed schemas for manifest, launch anchor, run state, leases, exceptions, evidence, packets/results/dispositions, human-gate receipt, and completion. Validate them with a pinned executable checker and negative runtime cases; prose-only schemas do not constitute a gate.
- a pinned cross-document semantic verifier that reconciles the exact requirement/test/scenario sets, packet/result bytes and allowlists, git commits, leases, checkpoints, evidence files/hashes, accepted exceptions, completion arrays, and final repository heads. JSON-schema validity alone cannot authorize completion.
- `domain-fixture-manifest.json`: pinned fixture/profile/style/count oracle when file or transformation fidelity is part of acceptance.
- a task-local bootstrap preflight that exists before repo-owned safety scripts and attests every mutation-capable endpoint before goal creation.

Do not create high-assurance machinery for a narrow task. Use it when scope, duration, blast radius, or autonomous runtime justifies the overhead.

## Traceability Matrix Columns

Use these columns unless the task has stronger local conventions:

| Column | Meaning |
| --- | --- |
| `ID` | Stable short id, grouped by feature area. |
| `Requirement` | Concrete behavior to build or verify. |
| `Source` | Meeting/doc/code source. |
| `Decision state` | `Proposed`, `Locked`, `Needs decision`, `Superseded`, or `Deferred`. |
| `Release` | `V1`, `V2`, or `Out`. |
| `Fidelity` | `Full`, `Basic`, or `N/A`. |
| `Owner surface` | Admin, consultant, API, schema, export, docs, etc. |
| `Data/schema impact` | Tables, fields, migrations, policies, or `None`. |
| `UI/API work` | Main implementation tasks. |
| `Test IDs` | Stable test-catalog IDs that verify this requirement. |
| `Implementation` | `Not started`, `In progress`, `Implemented`, `Blocked`, or `Deferred`. |
| `Validation` | `Not started`, `Failing`, `Passed`, `Blocked`, or `N/A`. |
| `Documentation` | `Not started`, `Current`, `Blocked`, or `N/A`. |
| `Risk` | `Open`, `Accepted`, `Closed`, or `N/A`. |
| `Integrated SHA` | Commit containing the integrated implementation, or `N/A`. |
| `Evidence` | Exact paths/records for commands, screenshots, tests, exports, reviews, and docs. |
| `Notes/open questions` | Any caveat or decision still needed. |

## Workflow

1. **Ground sources**
   - Read the current accepted plan, task status, requirements docs, meeting notes, and relevant code/schema.
   - If a material source link cannot be accessed, record the limitation and ask for content or permission before treating it as known.

2. **Inventory requirements**
   - Extract all explicit requirements and repeated meeting themes.
   - Preserve minor UI and workflow requirements; do not filter them out just because they are small.
   - De-duplicate while keeping source references.

3. **Lock decisions**
   - Make each requirement atomic and classify decision state, release, and fidelity.
   - Use `grill-me` or concise user questions only for decisions that cannot be safely inferred and materially affect scope.
   - Record each decision in the source/decision ledger, appendix, requirements lock, and matrix.
   - Keep delivery controls and test-catalog rows separate from product requirements.

4. **Authorize implementation**
   - Write the proposed implementation plan to the active task artifacts.
   - Ask the user to review it from file and make changes.
   - After explicit approval, append the accepted plan to the active task status file before any product implementation.
   - Freeze the requirements-lock hash, repository base SHAs, and run-manifest hash.

5. **Prepare the goal**
   - Check whether a Codex goal is already active.
   - Run the anchored T0 launch/baseline checks before creating the goal. High-assurance runs use an evidence-empty `launch` probe, append its exact passed evidence, and then require an evidence-bound `launch-finalize`; neither phase may authorize itself. Validate executable closed schemas, a separately committed launch anchor/control chain, exact code/control SHAs, and every mutation-capable local runtime identity.
   - When a high-assurance manifest pins Codex and Claude skill counterparts, require byte-identical blobs in one dedicated botfiles commit that changes exactly those two paths, then bind that single commit in the manifest and launch anchor.
   - If the accepted plan explicitly requires goal-backed execution and no active goal exists, create one with a compact objective containing the literal frozen run-manifest hash and launch-anchor commit.
   - Keep detailed instructions in files; do not paste a second mutable plan into the goal objective.

6. **Implement by work packet**
   - Pick one invariant or 1-3 tightly coupled accepted rows within the current dependency-ordered cluster. Only an explicitly frozen control bootstrap may contain zero product requirements.
   - Freeze a write-once `issued` packet with a manifest profile, assigned worker ID, revision-specific deterministic branch/worktree, requirement IDs, both current integration heads, repository base SHA, acceptance criteria, packet-narrowed paths, dependencies, revision-bound leases, catalog-derived tests, safety class, preflight mode, and stop conditions. Record one write-once terminal result bound to exact packet bytes and assigned worker; never overload it with integration/supersession state.
   - Record a separate write-once owner disposition bound to exact packet/result bytes after review: `integrated` names the containing integration SHA; `superseded` points to the immediately following revision. A new revision preserves the original profile/scope and requires terminal results plus a contiguous superseded chain. An integrated packet is never revised.
   - A dependency is authorized only when its latest revision has a completed result, integrated disposition, and commit in the dependent packet's frozen integration ancestry.
   - When the accepted run starts before a repo-owned wrapper exists, pin known-good wrapper source bytes in the accepted manifest. Permit exactly one control-only first bootstrap packet to install those exact bytes and the one package script; it may not claim product requirements or revise itself. Every later packet invokes the argument-bound absolute wrapper command and verifies the package script plus accepted source hash at frozen/final heads.
   - The test catalog separates a logical test from one or more execution definitions. Each execution fixes its ID, gate scope, repository, earliest cluster, execution worktree, method kind, and exact method. The manifest, not a packet author, owns cluster, repository, path scope, hard-deny paths, caps, primary requirement cluster, and eligible executions. Packet fields may narrow this authority only. Reject traversal/unsafe paths, symlinks/submodules, profile escalation, self-selected executions, skipped/reversed checkpoints, and work issued before the wrapper is integrated.
   - Before editing, state the files/surfaces being changed.
   - Use explicit packet phases: `packet-prewrite` has no candidate commit, result, or packet evidence; after one worker commit, `packet-postcommit` binds that candidate and permits exact required evidence to accumulate; `packet-preintegration` requires the complete write-once result and exact evidence set before owner integration. If a stop condition is discovered before mutation, write a commitless failed/blocked prewrite result, validate it through `packet-terminal-prewrite`, then write a superseded disposition before issuing the next contiguous same-scope revision. Never fabricate a commit or make a completed result depend on the pre-integration check that consumes it.
   - Keep diffs inside the packet. If scope crosses a frozen boundary, stop and supersede the packet rather than expanding it silently.
   - Update implementation state before and after integration.

7. **Validate and repair**
   - Run the packet's exact focused checks, then the current cluster gate.
   - Save important logs/artifacts under the task artifact folder.
   - If validation fails, repair before advancing.
   - Mark validation `Passed` only when exact-SHA evidence is recorded.

8. **Review at major milestones**
   - Use Oracle, a reviewer agent, or another external review only at agreed major checkpoints or when design risk is high.
   - Feed the reviewer the matrix, changed files, validation evidence, and specific risks.
   - Record accepted/rejected review guidance and resulting changes.
   - Any subsequent code change invalidates approval for affected surfaces until review/checks are rerun.

9. **Close the loop**
   - Ensure every accepted contextual-help target, tutorial step, browser semantic/color cue, and other runtime-owned document matches implemented behavior without mutating manifest-pinned planning inputs. Create new dated as-built stakeholder artifacts only after control closeout.
   - Confirm every accepted in-scope row is implemented or explicitly changed by an accepted plan revision.
   - Run the agreed automated final suite and independent exact-SHA review, then stop in an explicit `awaiting_human` state when the accepted plan requires human validation.
   - Validate the pre-human state, freeze exact readiness snapshots, write the draft immutable receipt, and have the verifier atomically stamp `validatedAt` in a separate receipt phase only after all runtime checks pass. A named human may begin only afterward and must personally provide a separately pinned attestation whose statement and artifact bind the exact run ID, final code SHAs, procedure hash, and completion time; an agent may capture supplied words but cannot invent, reuse, or self-author this evidence. Every scenario result binds the scenario catalog's exact test IDs and a scenario-specific checklist artifact.
   - Only after the human gate validates should the owner produce `review_ready` completion and mark the Codex goal complete.

## Subagent Protocol

Subagents are bounded workers, not co-owners of the goal.

- The primary goal owner retains the integration branch, control artifacts, goal tools, and completion authority.
- Default high-assurance concurrency is one writing subagent plus one read-only scout/reviewer. Increase writer count only when the run manifest explicitly proves disjoint paths and singleton resources.
- Writing agents work in deterministic revision-specific packet worktrees/branches. They receive one write-once packet, make one commit, run packet checks, and report one terminal result bound to exact packet bytes/revision/worker. The owner alone creates the integration/supersession disposition.
- Prefer a separate read-only/test-runner subagent to execute or independently inspect packet checks after the writer finishes. Its result is supervisory correctness evidence under the stated trust model, not a cryptographic identity claim.
- Subagents may not edit the requirements lock, execution/control artifacts, shared migrations/contracts/lockfiles outside their lease, integrate commits, push, deploy, create tunnels, or call goal tools.
- The owner acquires path and singleton-resource leases before delegation. Database, dev server, ports, migrations, lockfiles, generated schemas, snapshots, and navigation are singleton resources unless the manifest says otherwise.
- Compare lease expiry with verifier wall-clock time, not stale run-state time. Expiry never permits blind takeover: inspect processes, worktree state, diff, and packet status first.
- A `stale_pending_inspection` lease is still blocking state: every mutation-capable preflight must fail until inspection ends with an explicit release; it cannot coexist with a replacement lease on the same target.
- Database- or service-mutating test runners require an exclusive resource lease and do not overlap a writer.
- Reviewers use fresh context and read-only scope. Prefer the strongest current native reasoning model at a controlled reasoning level; do not hard-code a stale model as permanent frontier policy.
- When using native GPT-5.6 Sol, Terra, or Luna subagents, always select `max` reasoning effort for workers, explorers, and reviewers.
- Oracle or cross-provider review is optional diversity/tie-breaking unless the accepted plan makes it mandatory.

## Safety And Recovery

- A task-local bootstrap preflight must exist and pass before goal creation; one pre-pinned shared wrapper may be installed only through one explicit bootstrap packet. Keep phases distinct: `launch` requires empty packet/result/disposition directories, no launch evidence, active G0, and free future app ports; only after that probe passes may its exact evidence be appended and `launch-finalize` require exactly that evidence plus the evidence-bound G0 checkpoint. Packet-prewrite requires one active exact revision and no candidate/result/evidence; packet-terminal-prewrite validates a commitless failed/blocked result; packet-postcommit validates the ordinary candidate's exact diff, path leases, hard-deny set, file/line caps, and file modes before evidence-producing tests; packet-preintegration requires the complete exact result/evidence set. Freeze one owner identity in manifest and anchor; only that owner issues packets, decides dispositions, and creates the human receipt, while workers remain distinct. Integration is fast-forward-only so `integrationSha` equals the worker `commitSha`; verify the integration worktree directly and prove integrated commits remain in current, relevant checkpoint, human-gate/receipt, and completion ancestry. Every passed checkpoint binds its exact catalog executions, evidence paths, repository heads, completion time, and the latest completed/integrated primary-cluster packet for each requirement due by that checkpoint. Derive mandatory exclusive resources from frozen test/execution metadata rather than packet requests, and compare canonical lease timestamps numerically. All packet phases require prior checkpoints Passed/current Active/future Pending. Human-gate requires every G0/C0-C6 checkpoint Passed, all revisions terminal/dispositioned, latest revisions integrated, non-manual executions complete, and no receipt/manual result; human-receipt binds frozen readiness snapshots, runtime-record inventory, exact heads, and verifier-stamped `validatedAt` before manual work. Receipt authorization is atomic and idempotent: rerunning after an interrupted write or already-authorized receipt revalidates the same bytes rather than creating a second authorization. Completion requires valid receipt chronology, preserved inventory, exact scenario/coverage results, and one distinct exact-run/head checklist artifact per scenario.
- Hosted/live writes, push, deploy, tunnel creation, schema refresh from hosted systems, and secret reads are prohibited unless explicitly authorized by the accepted run manifest.
- Unexpected dirty state stops writes. Never automatically reset, stash, clean, amend, rebase, or discard changes.
- Checkpoint after preflight, packet commit, integration, validation evidence, and cluster completion.
- Resume only when owner, run ID, manifest hash, launch-anchor ancestry, branch, current HEAD, packet hash, and leases reconcile. In a shared task repository, unrelated descendant commits are allowed only when the anchor remains an ancestor and no active-task pinned path changed. Otherwise stop for investigation.
- Use bounded retries. Repeating the same failure without new evidence is not progress.

## Validation Tiers

- `T0 Safety`: worktree/branch/target/env/lease checks; no product mutation.
- `T1 Focused`: static checks and packet-level unit/contract tests.
- `T2 Domain`: local migrations, RLS, API, transactions, concurrency, import/export, and storage contracts.
- `T3 Cluster`: integrated runtime and named browser/workbook scenarios.
- `T4 Final`: clean worktree, exact final SHA, full suites, coverage audit, fresh-context review, docs, and demo dry run.

## Status Discipline

- Update execution state before and after every packet and cluster.
- Keep `validation-log.md` chronological.
- Evidence records include run ID, packet/revision/logical-test/execution/requirement/scenario/coverage IDs, gate scope, exact catalog method, declared working directory, performer, environment, timestamps, result/exit code, exact code SHAs, and SHA-pinned artifacts. Packet evidence binds exact packet requirements/worker; mutated-repository SHA equals packet commit and the other SHA equals the concurrent integration head. Result and evidence outcomes agree; completed authorization requires passed evidence and exit code zero. Manual evidence starts after receipt `validatedAt`, binds exact per-scenario test/checklist evidence and accepted coverage IDs, and uses a separately pinned named-human attestation. Evidence paths cannot be reused across packet revisions, dependency checks require latest integrated dispositions, released/stale/wrong-revision leases cannot authorize work, and completion enumerates exact accepted ID sets rather than counters.
- If implementation reveals a material requirement-interpretation change, stop the affected packet/cluster. Revise the source ledger, appendix, requirements lock, tests, matrix, and plan; obtain explicit user acceptance and freeze a new manifest before resuming. Documentation-only clarification that does not change behavior may update in the same cluster.
- Keep `V2` and `Out` rows visible so reviewers can see what is intentionally excluded.
- Never downgrade, defer, or remove an accepted requirement without a reviewed and accepted plan revision.

## Done Criteria Template

Use this shape in `goal-runbook.md`:

```markdown
Done when:
- Every accepted V1 requirement has terminal implementation, validation, documentation, risk, integrated-SHA, test, and evidence fields.
- Every high-risk requirement has positive and negative validation where applicable.
- Every requirement maps to tests and every test maps to at least one requirement.
- Every `Needs decision` row is resolved through an accepted plan revision.
- Final automated checks pass or known unrelated failures are documented with evidence.
- The loop stops at `awaiting_human` before manual evidence exists; then a named human personally attests that the manual demo flows pass for the named stakeholder scenarios.
- Product help/tutorials and runtime validation state are current; immutable accepted planning inputs are unchanged, and any as-built brief/appendix/traceability package is a new dated post-run artifact.
- Final review and validation match the exact final SHA.
- Completion report says `review_ready`; no claim of merge/deploy/production approval is implied.
```
