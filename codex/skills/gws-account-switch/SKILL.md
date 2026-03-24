---
name: gws-account-switch
description: Choose a named Google Workspace mailbox alias (`work`, `personal`, `columbia`) for `gws` and switch agents onto the matching exported credentials file. Use when a user wants Gmail read flows from a specific account or needs a practical multi-account workaround for googleworkspace/cli on this machine.
---

# gws Account Switch

Use this alongside `gws-shared` and the Gmail skills when the user cares about which mailbox `gws` should target.

## Aliases

- `work` -> `sourya4@trymyzone.com`
- `personal` -> `sourya4@gmail.com`
- `columbia` -> `sk5057@columbia.edu`

## Workflow

1. Confirm which alias the user wants if it is not already clear.
2. Check whether `~/.config/gws/accounts/<alias>.json` exists.
3. If the alias file is missing, tell the user the account must be initialized first:
   - `gws auth login --readonly --services gmail`
   - `gws-save-account <alias>`
4. For commands against a specific mailbox, use:
   - `gws-account <alias> gmail +triage`
   - `gws-account <alias> gmail +read --id <message-id>`
   - `gws-account <alias> <service> <resource> ...` for raw commands

## Notes

- `gws-account` works by setting `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` to the alias file before executing `gws`.
- `gws-save-account` exports the currently active decrypted credentials into `~/.config/gws/accounts/<alias>.json`.
- Prefer read-only Gmail flows unless the user explicitly asks for send or mailbox mutation actions.
- Never expose raw credential contents in chat or logs.
