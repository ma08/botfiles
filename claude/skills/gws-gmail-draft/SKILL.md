---
name: gws-gmail-draft
description: Create unsent Gmail drafts through the named work, personal, or columbia gws account alias with a portable draft-only helper. Use when the user explicitly asks to save or create an email in Gmail drafts.
---

# Gmail Draft Creation

Create Gmail drafts through `gws-gmail-draft`. The helper calls only Gmail `users.drafts.create`; it never calls a send method.

## Intent Gate

- An explicit request such as “save this in Gmail drafts” or “create a Gmail draft” authorizes draft creation in the named mailbox.
- A vague request such as “draft an email” means compose text locally first. Ask before writing it into Gmail.
- Sending is a separate action. Never interpret draft approval as send approval, and always obtain explicit confirmation immediately before sending.

## Accounts

- `work` → `sourya4@trymyzone.com`
- `personal` → `sourya4@gmail.com`
- `columbia` → `sk5057@columbia.edu`

If the intended mailbox is unclear, ask which alias to use before creating the draft.

## Workflow

1. Read `../gws-shared/SKILL.md` and `../gws-account-switch/SKILL.md`.
2. Confirm `~/.config/gws/accounts/<alias>.json` exists without printing it.
3. Prefer a body file for long or sensitive content so it is not exposed in process arguments.
4. Run `--dry-run` first and review the safe summary.
5. If Gmail intent is explicit, run the same command without `--dry-run`.
6. Report the account alias, recipients, subject, and returned draft ID. State clearly that nothing was sent.

## Examples

```bash
gws-gmail-draft work \
  --to recipient@example.com \
  --subject "Follow-up" \
  --body-file ./draft.txt \
  --dry-run

gws-gmail-draft work \
  --to recipient@example.com \
  --cc teammate@example.com \
  --subject "Follow-up" \
  --body-file ./draft.txt

gws-gmail-draft personal \
  --to recipient@example.com \
  --subject "Invoice" \
  --body-file ./body.html \
  --html \
  --attach ./invoice.pdf
```

`--to`, `--cc`, `--bcc`, and `--attach` are repeatable. Address flags also accept comma-separated values. A draft may omit recipients when the message is intentionally incomplete.

## Permission Boundary

Google does not provide a general draft-only OAuth scope. The required `gmail.compose` scope also technically permits sending. The helper and this skill are workflow guardrails, not a cryptographic restriction on the credential.

Never bypass the helper with `gmail +send`, `messages.send`, or `drafts.send` while performing a draft-creation request.
