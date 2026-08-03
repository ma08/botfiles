---
name: deep-feed-handoff-consumer
description: Accept, acknowledge, and work a Deep Feed handoff that was routed to this exact existing Codex task. Use when invoked by the compact Deep Feed consumer command containing the handoff, revision, route generation, and destination task IDs.
---

# Deep Feed handoff consumer

## Purpose

Make the routed destination—not the disposable router—the owner of the actual
work. Fetch canonical private evidence, acknowledge only an exact dispatch, and
return truthful work status and outcomes to Deep Feed.

Use only the portable `deep-feed-handoff` helper and its narrow consumer
capability. It cannot ingest cards, assign routes, or approve external actions.

## Invocation contract

Require these exact positional values:

```text
accept <handoff-id> <revision> <route-generation> <destination-thread-id>
```

Reject missing or malformed values. Do not accept a handoff addressed to a
different task, revision, or route generation.

## Accept safely

1. Briefly tell the user this skill is verifying and accepting a routed Deep
   Feed handoff.
2. Fetch the canonical record:

   ```bash
   deep-feed-handoff get <handoff-id> --role consumer
   ```

3. Verify all of the following before acknowledging:
   - `revision` and `routeGeneration` equal the invocation;
   - `routingStatus` is `dispatch_accepted` (or already `acknowledged` for an
     idempotent replay);
   - `destinationThreadId` equals the invocation's destination task ID;
   - the handoff is not canceled, stale, or completed.
4. Acknowledge this exact destination:

   ```bash
   deep-feed-handoff status <handoff-id> acknowledged --role consumer \
     --revision <revision> --route-generation <route-generation> \
     --task-thread-id <destination-thread-id>
   ```

Do not acknowledge merely because a scheduled scan saw the queue.

### Hourly fallback only

The persistent Chief-of-Staff task may take over a handoff only when the
canonical record is still `launch_requested`, `routing_started`, or
`choice_required` and its `reservationExpiresAt` is in the past. Use the
returned revision and generation exactly:

```bash
deep-feed-handoff fallback <handoff-id> --role consumer \
  --revision <revision> --route-generation <route-generation> \
  --idempotency-key fallback:<handoff-id>:<revision>:<route-generation>
```

The server advances the generation, clears the expired router lease, and fixes
the destination to the configured persistent Chief-of-Staff task. Refetch and
then acknowledge that new generation. Never take over `dispatch_started`,
`dispatch_unknown`, or `dispatch_accepted`; those states require exact dispatch
reconciliation or destination acknowledgment.

## Work and report truthfully

- Read the canonical `request`, `constraints`, evidence, and links from the API.
  Do not ask the user to repaste the card.
- Move to `working` only when this task actually begins investigation or
  execution. Use the same revision, generation, and destination arguments.
- Collaborate normally with the user. For consequential or external effects,
  prepare the exact preview and obtain fresh approval before acting.
- If a user decision is required, record `waiting_user` and put the specific
  question in `--result` before asking it interactively.
- When a concrete result is ready, record `outcome_ready` with a concise result.
  Record `completed` only when the requested work and relevant verification are
  actually complete.
- Never resolve or hide the originating card; only the owner performs that
  separate Deep Feed action.

Examples:

```bash
deep-feed-handoff status <handoff-id> working --role consumer \
  --revision <revision> --route-generation <route-generation> \
  --task-thread-id <destination-thread-id>

deep-feed-handoff status <handoff-id> waiting_user --role consumer \
  --revision <revision> --route-generation <route-generation> \
  --task-thread-id <destination-thread-id> \
  --result 'Waiting for your choice between the two verified options.'

deep-feed-handoff status <handoff-id> outcome_ready --role consumer \
  --revision <revision> --route-generation <route-generation> \
  --task-thread-id <destination-thread-id> \
  --result 'Prepared the verified change and exact approval preview; no external action was taken.'
```

If a status call returns a conflict, refetch once and reconcile the canonical
state. Never overwrite a newer revision, generation, destination, or outcome.
