---
name: deep-feed-handoff-consumer
description: Accept and work one owner-approved protocol-v2 Deep Feed dispatch in the exact existing non-scheduled Codex task named by the compact invocation. Reject scheduled, legacy, mismatched, or ambiguous destinations.
---

# Deep Feed handoff consumer

## Purpose

Make one exact existing non-scheduled task the owner only after the dedicated
`$deep-feed-work` task records the owner's destination choice and sends the
compact invocation once.

## Invocation contract

Require exactly:

```text
accept <handoff-id> <revision> <route-generation> <destination-thread-id>
```

Reject missing or malformed values.

## Verify before acknowledging

1. Read `CODEX_THREAD_ID`; it must equal the invocation destination exactly.
2. Fetch the canonical handoff:

   ```bash
   deep-feed-handoff get <handoff-id> --role consumer
   ```

3. Require protocol version 2, the exact revision and route generation,
   `destinationKind: existing`, `routingStatus: dispatch_accepted` (or an
   idempotent existing acknowledgment), and the exact destination task ID.
4. Source `~/pro/botfiles/.botenv` if needed, create a private temporary
   directory, and run:

   ```bash
   deep-feed-thread-policies --output '<temp-dir>/policies.json'
   ```

5. Reject this task if its ID appears in the protected set, if native metadata
   shows an automation or heartbeat, or if non-scheduled status cannot be
   positively verified. Do not preempt a scheduled scan. The server enforces
   the same deny independently.

Only then acknowledge:

```bash
deep-feed-handoff status <handoff-id> acknowledged --role consumer \
  --revision <revision> --route-generation <route-generation> \
  --task-thread-id "$CODEX_THREAD_ID"
```

There is no hourly fallback, `left_queued` takeover, or Chief-of-Staff
exception.

## Work and report truthfully

- Read the canonical request, constraints, evidence, and links. Do not ask the
  user to repaste the card.
- Mark `working` only when investigation actually begins.
- For a needed choice, record `waiting_user` with the exact question and two or
  three concrete options, then use `request_user_input` in the same turn.
- For a concrete result, record `outcome_ready`. Record `completed` only when
  the requested work and verification are complete.
- Use `--result-file` for long results.
- Consequential or external effects require a fresh exact preview and owner
  approval.
- Never resolve or hide the source card.

Examples:

```bash
deep-feed-handoff status <handoff-id> working --role consumer \
  --revision <revision> --route-generation <route-generation> \
  --task-thread-id "$CODEX_THREAD_ID"

deep-feed-handoff status <handoff-id> waiting_user --role consumer \
  --revision <revision> --route-generation <route-generation> \
  --task-thread-id "$CODEX_THREAD_ID" --result-file '<result-file>'

deep-feed-handoff status <handoff-id> outcome_ready --role consumer \
  --revision <revision> --route-generation <route-generation> \
  --task-thread-id "$CODEX_THREAD_ID" --result-file '<result-file>'
```

On conflict, refetch once and reconcile canonical state. Never retry an
ambiguous cross-task send or overwrite a newer destination, generation, or
outcome.
