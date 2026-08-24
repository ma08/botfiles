---
name: gws-account-switch
description: Choose a named Google Workspace account alias (`work`, `personal`, `columbia`) for `gws` and switch agents onto the matching exported credentials file. Use when a user wants Gmail, Drive, or guarded Calendar access from a specific account or needs the multi-account googleworkspace/cli workflow on this machine.
---

# gws Account Switch

Use this alongside `gws-shared`, `gws-gmail`, `gws-drive`, and `gws-calendar-safe` when the user cares about which account `gws` should target.

## Aliases

- `work` -> `sourya4@trymyzone.com`
- `personal` -> `sourya4@gmail.com`
- `columbia` -> authenticated mailbox `sk5057@columbia.edu`; normal outbound From identity `sourya.kakarla@columbia.edu`

## Workflow

1. Confirm which alias the user wants if it is not already clear.
2. Check whether `~/.config/gws/accounts/<alias>.json` exists.
3. If the alias file is missing, tell the user the account must be initialized first:
   - `gws auth login --scopes https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.compose`
   - `gws-save-account <alias>`
4. For commands against a specific mailbox, use:
   - `gws-account <alias> gmail +triage`
   - `gws-account <alias> gmail +read --id <message-id>`
   - `gws-gmail-draft <alias> --to <address> --subject <subject> --body-file <path>`
   - `gws-account <alias> drive files list --params '{"pageSize": 5, "q": "trashed=false"}' --format json`
   - `gws-calendar-safe calendars --account <alias>` for Calendar inventory
   - `gws-calendar-safe auth-plan --account <alias>` before Calendar reauthorization
   - `gws-account <alias> <service> <resource> ...` for raw commands

## Notes

- `gws-account` works by setting `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` to the alias file before executing `gws`.
- Named alias state uses a private file-backed token cache by default so non-interactive Mac SSH sessions do not depend on GUI keychain access. Set `GWS_ACCOUNT_KEYRING_BACKEND=keyring` only when an interactive keychain is available.
- `gws-save-account` exports the currently active decrypted credentials into `~/.config/gws/accounts/<alias>.json`.
- On this machine, the saved aliases are expected to carry both Gmail read and Drive read scopes.
- Draft-enabled aliases additionally need `gmail.compose`; this scope also technically permits sending.
- After the alias exists, Calendar-enabled aliases use exactly `calendar.events` plus `calendar.calendarlist.readonly`; preserve all existing non-Calendar scopes through `gws-calendar-safe auth-plan`.
- Calendar writes must use `gws-calendar-safe`, never a raw `gws calendar` mutation.
- The `columbia` credential still targets the `sk5057@columbia.edu` mailbox, while new drafts should normally use its accepted default send-as address `sourya.kakarla@columbia.edu` in the From header.
- Prefer read-only Gmail and Drive flows unless the user explicitly asks to create a Gmail draft or perform another mutation.
- A vague request to “draft an email” means local text only. Gmail creation requires explicit Gmail-draft intent.
- Sending remains separate and always requires explicit confirmation.
- Never expose raw credential contents in chat or logs.
