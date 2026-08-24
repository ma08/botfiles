---
name: apple-reminders-safe
description: Safely read, search, create, update, complete, reopen, or explicitly delete Apple Reminders through a bounded Mac-native EventKit bridge. Use for any agent-driven Apple Reminders access, macOS Reminders TCC check, exact reminder preview, or owner-only Deep Feed collection.
---

# Safe Apple Reminders

Use `apple-reminders-safe` as the policy boundary for Apple Reminders. It calls the verified native helper locally on macOS and reaches `sourya-mac` through bounded SSH from GCP. Do not invoke the native helper directly for normal work.

## Safety rules

- Treat status, authorization, reads, and writes as separate actions. A pre-existing `full-access` TCC state does not authorize an agent to read or change reminders.
- Keep reminder contents out of Git, task artifacts, reusable caches, and broad logs. Exact reads and previews may exist only in the user's machine-local state.
- Require one explicit list ID for create and list moves. Never choose a default list implicitly.
- Preserve every field omitted from an update. Use explicit `clear` entries to remove supported optional fields.
- Preview every write and obtain approval for its exact `approvalHash` before `apply`.
- Delete only one exact reminder, only after a fresh preview, and only with the preview's separate `DELETE:<local-id>` confirmation. Do not delete a live fixture.
- Reject list creation, rename, deletion, bulk writes, bulk deletes, and broad exports.
- Report Mac offline, SSH failure, fetch timeout, TCC state, hard-cap truncation, ambiguous identity, and unverified cloud freshness. Never interpret these states as an empty result.
- Passive Deep Feed collection is read-only. It must never call create, update, complete, reopen, or delete.

## Check health and permission

Run:

```bash
apple-reminders-safe status
```

The response must show `macReachable`, the exact `tccStatus`, `fetchComplete`, `truncated`, and `cloudFreshness`. `cloudFreshness` remains `unverified` because EventKit does not prove that iCloud sync is current.

Do not trigger a macOS permission request without separate user approval. First save a permission preview outside any repository:

```bash
mkdir -p ~/.local/state/apple-reminders-safe/previews
apple-reminders-safe authorize-preview \
  --output ~/.local/state/apple-reminders-safe/previews/authorize.json
```

Show the exact `currentTccStatus`, `willPrompt`, bundle identifier, expiry, and `approvalHash`. After explicit approval, apply only that unexpired preview:

```bash
apple-reminders-safe authorize \
  --preview ~/.local/state/apple-reminders-safe/previews/authorize.json \
  --approval-hash '<exact-hash>'
```

If status is already `full-access`, this command should not prompt. The user approval still gates first use. If status is denied, restricted, or write-only, stop and guide the user through macOS Privacy & Security rather than bypassing TCC.

## Read workflow

List Reminder lists with a bound:

```bash
apple-reminders-safe lists --limit 100
```

Search results redact note text. Use an exact read only after selecting one result:

```bash
apple-reminders-safe search --query 'renew' --limit 25
apple-reminders-safe get --local-id '<calendarItemIdentifier>'
```

An external ID lookup must include the exact list ID:

```bash
apple-reminders-safe get \
  --external-id '<calendarItemExternalIdentifier>' \
  --list-id '<list-id>'
```

## Create and update workflow

Keep request and preview files under `~/.local/state/apple-reminders-safe/`, mode `0600`, never in a repository. A create request uses one explicit list and may include title, notes, URL, due state, priority, simple recurrence, and alarms:

```json
{
  "listId": "<exact-list-id>",
  "title": "ZON-325 self-only Reminders fixture",
  "due": {
    "kind": "timed",
    "value": "2026-09-18T09:00:00",
    "timeZone": "America/Los_Angeles"
  }
}
```

Preview it:

```bash
apple-reminders-safe create-preview \
  --input ~/.local/state/apple-reminders-safe/requests/create.json \
  --output ~/.local/state/apple-reminders-safe/previews/create.json
```

For an update, include only fields to set, fields to clear, and an explicit move target when needed:

```json
{
  "set": {"title": "Updated title"},
  "clear": [],
  "moveToListId": "<exact-list-id>"
}
```

```bash
apple-reminders-safe update-preview \
  --local-id '<local-id>' \
  --patch ~/.local/state/apple-reminders-safe/requests/update.json \
  --output ~/.local/state/apple-reminders-safe/previews/update.json
```

Before asking for approval, show the exact list, title, notes-change digest, due kind and timezone, all-day or floating state, priority, completion, recurrence, alarms, URL, last modified value, diff, expiry, and approval hash. System-generated creation, modification, and completion timestamps are explicitly marked as set by EventKit on apply.

Apply one approved preview:

```bash
apple-reminders-safe apply \
  --preview ~/.local/state/apple-reminders-safe/previews/update.json \
  --approval-hash '<exact-hash>'
```

The wrapper rereads the reminder, rejects drift, applies only the previewed operation, rereads for verification, and writes a content-free machine-local audit record.

## Complete, reopen, and delete

Use the same exact-target workflow:

```bash
apple-reminders-safe complete-preview --local-id '<local-id>' \
  --output ~/.local/state/apple-reminders-safe/previews/complete.json
apple-reminders-safe reopen-preview --local-id '<local-id>' \
  --output ~/.local/state/apple-reminders-safe/previews/reopen.json
apple-reminders-safe delete-preview --local-id '<local-id>' \
  --output ~/.local/state/apple-reminders-safe/previews/delete.json
```

Deletion needs both the approval hash and exact destructive token:

```bash
apple-reminders-safe apply \
  --preview ~/.local/state/apple-reminders-safe/previews/delete.json \
  --approval-hash '<exact-hash>' \
  --confirm-destructive 'DELETE:<local-id>'
```

## Deep Feed collection

The owner-only Deep Feed collector may request bounded pages with full notes:

```bash
apple-reminders-safe collect-page \
  --limit 100 \
  --owner-only-deep-feed
```

Follow `nextCursor` until `truncated` is false. A partial, timed-out, offline, denied, or truncated final scan is not authoritative and must leave source health visibly degraded. Do not enable recurring collection until Sourya separately approves the all-list, all-open, notes-copy, and scheduling policy.

## Native installation

The native helper source is under `macos/apple-reminders-native/`. On `sourya-mac`, first install with:

```bash
install-apple-reminders-native
```

The installer builds with Swift, ad-hoc signs the fixed bundle identifier, records a mode-`0600` hash manifest, and installs at a fixed path. Rebuilds can change the code requirement, so replacement requires explicit `--replace` and may require a new TCC grant. Never copy TCC databases or iCloud credentials to GCP.
