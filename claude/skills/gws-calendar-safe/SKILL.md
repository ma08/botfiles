---
name: gws-calendar-safe
description: Safely read, create, edit, split, cancel, or delete Google Calendar events through the named work, personal, or columbia gws aliases. Use for any agent-driven Calendar write, recurring-event change, exact event preview, writable-calendar inventory, or Calendar OAuth scope planning.
---

# Safe Google Calendar

Use `gws-calendar-safe` as the only Calendar write path. Leave the native Codex Google Calendar connector and the `jiffy` alias untouched.

## Required workflow

1. Require one explicit alias and one explicit calendar ID. Never infer either.
2. Read the exact calendar or event before proposing a write.
3. Generate a preview and show the user:
   - title;
   - exact start and end;
   - timezone or all-day dates;
   - account and calendar;
   - location;
   - visibility;
   - conferencing;
   - resolved reminders;
   - attendee state;
   - organizer state;
   - recurrence scope;
   - exact diff;
   - notification behavior and risk.
4. Wait for explicit approval of that exact preview. Do not treat a general request as approval of a generated hash.
5. Apply the unexpired preview with its approval hash. For deletion, also pass the exact destructive confirmation from the preview.
6. Return the structured audit receipt.

## Commands

Inventory and exact reads:

```bash
gws-calendar-safe accounts
gws-calendar-safe calendars --account work
gws-calendar-safe event-read --account work --calendar-id <calendar-id> --event-id <event-id>
```

Create from a local JSON request:

```bash
gws-calendar-safe create-preview \
  --account work \
  --calendar-id <calendar-id> \
  --input <request.json>
```

The request must contain a title plus exact `start` and `end` objects. A new event always includes only the selected account as attendee and uses `sendUpdates=none`. Primary calendars use default visibility. Secondary calendars default to private. Calendar-default reminders are inherited and resolved in the preview. Google Meet is opt-in with `"conference": "googleMeet"`.

Edit one occurrence, a whole series, or this-and-following:

```bash
gws-calendar-safe update-preview \
  --account work \
  --calendar-id <calendar-id> \
  --event-id <event-id> \
  --scope occurrence|series|following \
  --patch <patch.json> \
  [--send-updates none|all]
```

Use an exact recurring instance ID for `following`. The helper rejects unsafe recurrence forms instead of guessing. If the source series has conferencing, a following split requires an explicit `"conference": "googleMeet"` for a new unique Meet or `"conference": "remove"`; existing conference data cannot be safely reused on a new series. Existing attendee lists are immutable. A non-organizer event can be previewed but cannot be applied. Attendee-bearing events require an explicit `none` or `all` notification choice.

Destructive preview:

```bash
gws-calendar-safe delete-preview \
  --account work \
  --calendar-id <calendar-id> \
  --event-id <event-id> \
  --scope occurrence|series|following \
  [--send-updates none|all]
```

Apply only after approval:

```bash
gws-calendar-safe apply \
  --preview <preview.json> \
  --approval-hash <approval-hash> \
  [--confirm-destructive 'DELETE:<event-id>:<scope>']
```

## OAuth gate

Never start reauthorization silently. First show the exact scope-preserving plan:

```bash
gws-calendar-safe auth-plan --account work
```

After the user approves that exact plan, run only its returned `authorizationCommand`. The command stages the new login in a private machine-local directory, verifies the selected Google identity and exact scope set before replacing the alias, keeps a mode-`0600` backup, verifies the installed alias, and restores the backup if post-install verification fails. Do not substitute `gws-account <alias> auth login`; derived alias state can be regenerated from the old saved credential.

The approved Calendar scope set is exactly:

- `https://www.googleapis.com/auth/calendar.events`
- `https://www.googleapis.com/auth/calendar.calendarlist.readonly`

Preserve non-Calendar scopes. Do not grant Calendar ACL, settings, full-calendar, Gmail-send, or unrelated access. Keep every token machine-local and verify the returned account immediately after the human OAuth step.

## Safety rules

- Never add or remove another person.
- Never apply a non-organizer edit.
- Preserve unspecified fields, attendees, and conferencing.
- Use the previewed ETag with `If-Match`; stop on drift.
- Treat cancellation, deletion, whole-series changes, this-and-following splits, guest notifications, and conference changes as visibly high impact.
- Test live behavior only with clearly labeled future self-only fixtures. Never contact guests or delete a live fixture.
- Do not commit preview files, audit files containing private event content, credentials, or generated account state.
