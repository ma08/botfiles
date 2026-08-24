# Bounded production-state survey

Use this reference only for Stage A readiness evidence. It authorizes no production mutation and no new access.

## Contents

1. Decision rule
2. Authority check
3. Value-safe evidence
4. Survey procedure
5. Prohibited actions
6. Result states and blocker contract

## 1. Decision rule

Run the survey without another user prompt only when all three conditions are true:

1. A real production target exists.
2. The current task permits readiness-oriented production reads.
3. A pre-existing approved read-only route is already usable.

| Production target | Task permits reads | Approved route usable | Result |
|---|---|---|---|
| No | Any | Any | `not applicable` |
| Yes | No | Any | `omitted by scope` |
| Yes | Yes | No or uncertain | `blocked: access or authority` |
| Yes | Yes | Yes | Run the bounded survey |

The skill invocation supplies no authority beyond this table. A broadly privileged identity may be used only for commands that are clearly read-only and already within task scope.

## 2. Authority check

Before any cloud, database, or provider command:

1. Read `~/pro/personal_os/context/cloud-access.md`.
2. Read the repository instructions and applicable task or provider runbook.
3. Record the intended provider, target, identity or configuration, and exact evidence question.
4. Confirm the route is already authenticated and approved for read-only use.
5. Inspect command help or provider documentation when side effects are not obvious.

Do not log in, refresh a human session, switch account or provider configuration, select a different cloud profile, create or retrieve tokens, copy credential caches, grant roles, or change the active project. Missing or ambiguous authority is a blocker, not a setup task.

An identity check may retain a value-safe account, project, workspace, or service label. Never retain tokens, credential paths containing secret material, raw auth responses, or private keys.

## 3. Value-safe evidence

Retain only fields needed for the release decision.

| Area | Allowed retained evidence | Never retain |
|---|---|---|
| Provider identity | Provider, value-safe workspace/project/service name, read-only route used | Tokens, keys, cookies, auth headers, credential payloads |
| Deployment | Revision, commit, version, deployment time, status, readiness or health | Environment values, build secrets, private payloads |
| Schema and migrations | Migration ID, version, checksum, applied or pending status, schema fingerprint | Connection strings, passwords, row contents, database dumps |
| Policy and configuration | Policy existence, version, status, target, retention or protection state | Secret values, full environment exports, sensitive policy payloads |
| Aggregate state | Counts, sizes, rates, bounded error totals, queue depth, status summaries | Raw records, user identifiers, request bodies, response bodies, unbounded logs |
| Recovery | Backup or snapshot status, age, retention, restore-test status, rollback or forward-recovery readiness | Backup contents, exported data, recovery secrets |

Project fields at command time. Do not fetch a broad response and redact it later. Prefer provider-side query, filter, field selection, aggregation, and bounded time windows.

Raw application logs are out of scope by default because they may contain business records or personal data. Use aggregate error counts, health signals, or already-sanitized summaries. If a raw event is truly required, stop and obtain a separate explicit scope decision before retrieval.

## 4. Survey procedure

1. **Define the questions.** Select only candidate-relevant facts, such as deployed revision, migration parity, health, error aggregate, and recovery readiness.
2. **Build a command inventory.** Mark every command `read-only`, `ambiguous`, or `mutating`. Run only the read-only set.
3. **Constrain output before execution.** Select safe fields, bounded time ranges, and aggregates in the command itself.
4. **Run the minimum queries.** Stop when each selected evidence row has an answer.
5. **Scan before saving.** Confirm output contains no credentials, environment values, connection strings, business records, user identifiers, raw payloads, or broad logs.
6. **Save curated evidence.** Keep sanitized conclusions at the task-artifact top level and only value-safe raw metadata in scratchpad when needed.
7. **Record omissions and uncertainty.** Name unavailable providers, missing roles, stale auth, unrehearsed recovery, and any fact inferred rather than directly observed.

Do not give Oracle or Fable provider access. If adviser context needs operational evidence, provide only the curated value-safe conclusions.

## 5. Prohibited actions

- deploy, rollback, restart, scale, enable, disable, promote, or delete;
- run a migration, backfill, repair, restore, or production test that writes state;
- change a flag, environment variable, domain, policy, permission, role, provider, account, or project;
- create, retrieve, rotate, revoke, export, or copy credentials;
- open an interactive login or refresh authentication;
- query raw table rows, export data, retrieve secret values, or fetch broad logs;
- run a command whose side effects are unclear;
- attach production credentials or unsanitized output to an external adviser.

Read-only evidence does not authorize a later write. Put every production action in a separate release-control handoff with its own approval.

## 6. Result states and blocker contract

Use exactly one survey state:

- `completed`: bounded value-safe evidence collected;
- `completed with gaps`: safe evidence collected, but named facts remain unavailable;
- `not applicable`: no real production target;
- `omitted by scope`: task explicitly forbids production reads;
- `blocked: access or authority`: no existing approved route, stale auth, insufficient role, or ambiguous provider identity;
- `blocked: safety`: needed evidence cannot be obtained without retrieving prohibited data or risking mutation.

For a blocker, report:

```markdown
- Provider or target:
- Evidence question:
- Existing route checked:
- Exact gap:
- Why it matters to readiness:
- Who must decide or provide access:
- What resumes afterward:
- Login or provider state changed: no
```

Do not mark the overall candidate ready when a missing production fact leaves a material migration, compatibility, health, authorization, or recovery risk unresolved.
