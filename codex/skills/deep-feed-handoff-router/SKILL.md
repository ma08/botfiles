---
name: deep-feed-handoff-router
description: Safely inspect an old Deep Feed router invocation without dispatching it. This compatibility guard prevents retired protocol-v1 links from routing into scheduled tasks; new Deep Feed work must use $deep-feed-work.
---

# Deep Feed handoff router compatibility guard

## Purpose

The standalone router entrypoint is retired. Protocol v2 handles routing as an
optional, owner-confirmed branch inside the dedicated `$deep-feed-work` task.
This skill exists only so an old prefilled router command fails safely.

## Workflow

1. Accept exactly one opaque `handoff-...` ID.
2. Fetch it read-only:

   ```bash
   deep-feed-handoff get <handoff-id> --role router
   ```

3. Never claim, dispatch, queue, acknowledge, or update the record.
4. For protocol v2, tell the user to run `$deep-feed-work <handoff-id>` in the
   newly opened task. Do not create or send another task automatically.
5. For protocol v0/v1, explain that the old router/fallback path is frozen as
   readable history. If the record already has an exact destination URL, offer
   that only for reviewing its existing result; do not revive work.

## Hard boundary

Never use `left_queued`, `take_fallback`, `send_message_to_thread`, or any
scheduled task as a destination. A closed or expired router is not permission
to choose another owner.
