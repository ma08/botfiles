# Secrets Layout

This repository is public. Runtime secrets must never be committed.

## Structure

- `secrets/templates/` contains safe, tracked templates (`*.rc.example`).
- `secrets/local/` contains real local secret files (`*.rc`) and is git-ignored.

`.botrc` only loads runtime secrets from `secrets/local/*.rc` (strict cutover).

## Setup

```bash
cd ~/pro/botfiles
mkdir -p secrets/local
cp secrets/templates/claude-bedrock.rc.example secrets/local/claude-bedrock.rc
cp secrets/templates/claude-vertex.rc.example secrets/local/claude-vertex.rc
cp secrets/templates/codex-azure.rc.example secrets/local/codex-azure.rc
cp secrets/templates/codex-openai.rc.example secrets/local/codex-openai.rc
cp secrets/templates/opencode-azure.rc.example secrets/local/opencode-azure.rc
cp secrets/templates/machine.rc.example secrets/local/machine.rc
cp secrets/templates/claude-hooks.rc.example secrets/local/claude-hooks.rc
```

Edit each file and replace placeholder values.

## File Map

| Template | Runtime file | Purpose |
|---|---|---|
| `secrets/templates/claude-bedrock.rc.example` | `secrets/local/claude-bedrock.rc` | Claude Code Bedrock auth (`AWS_BEARER_TOKEN_BEDROCK`) |
| `secrets/templates/claude-vertex.rc.example` | `secrets/local/claude-vertex.rc` | Claude Code Vertex config |
| `secrets/templates/codex-azure.rc.example` | `secrets/local/codex-azure.rc` | Codex Azure provider key |
| `secrets/templates/codex-openai.rc.example` | `secrets/local/codex-openai.rc` | Codex OpenAI provider key |
| `secrets/templates/opencode-azure.rc.example` | `secrets/local/opencode-azure.rc` | OpenCode Azure resource config |
| `secrets/templates/machine.rc.example` | `secrets/local/machine.rc` | Shared machine identity (`SYSTEM_NAME`) for notifications + task metadata |
| `secrets/templates/claude-hooks.rc.example` | `secrets/local/claude-hooks.rc` | Claude/Codex hook notifications (WhatsApp, Gmail, optional zellij web links) |

## Security Notes

- Never copy real secrets into templates.
- Before commit, verify `git status` does not include files under `secrets/local/`.
- If a secret was pushed to a public remote, rotate it immediately.
