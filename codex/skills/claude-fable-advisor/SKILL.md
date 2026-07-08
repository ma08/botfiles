---
name: claude-fable-advisor
description: Use Anthropic Claude Fable 5 through Claude Code as a subscription-backed external advisor, reviewer, or planner for Codex work. Use when the user asks for Fable, Claude Fable, a Claude advisor/reviewer/planner, a second-model critique, hard planning review, architecture review, debugging strategy review, adversarial completion check, or an Oracle-like consultation that must avoid Bedrock, API keys, and other usage-based routes.
---

# Claude Fable Advisor

Use Claude Code to ask Fable 5 for an external opinion only after proving the
Claude process is using first-party `claude.ai` subscription auth. Treat Fable's
answer as advisory; verify it against local code, tests, docs, and user intent.

## Route Rule

Never run a Fable request through Bedrock, Vertex, Foundry, Claude Platform on
AWS, `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, or
`claude auth login --console`.

Before every live request, use `scripts/run_fable_advisor.py`. The script:

- strips known provider/API billing variables from the child environment;
- runs `claude auth status --json`;
- refuses unless the status shows `loggedIn=true`, `authMethod=claude.ai`,
  `apiProvider=firstParty`, and a non-empty `subscriptionType`;
- runs `claude --model fable --effort max -p ...` only after the gate passes;
- disables Claude tools by default and writes reusable output artifacts.

Do not use `claude --bare` for this workflow. Bare mode skips OAuth/keychain
subscription auth and expects API-key or third-party-provider credentials.

## Workflow

1. Decide whether Fable is worth the quota. Use it for hard planning, design
   tradeoffs, proof/logic review, stuck debugging, final risk review, or an
   independent critique. Skip it for routine edits or questions a local Codex
   pass can answer cheaply.
2. Write a standalone prompt. Include the goal, constraints, relevant facts,
   what has already been tried, and desired output shape. Do not include secrets.
3. Attach only the files Fable needs. Prefer a small set of source files, diffs,
   plans, logs, or status notes over whole-repo dumps.
4. Run a route-only check when uncertain:

   ```bash
   python /home/azureuser/pro/botfiles/codex/skills/claude-fable-advisor/scripts/run_fable_advisor.py \
     --check-only \
     --output-dir /path/to/artifacts/fable-route-check
   ```

5. Run the live advisory request:

   ```bash
   python /home/azureuser/pro/botfiles/codex/skills/claude-fable-advisor/scripts/run_fable_advisor.py \
     --prompt-file /path/to/fable-prompt.md \
     --file /path/to/relevant-file \
     --output-dir /path/to/artifacts/fable-review
   ```

   Add `--dry-run` first when you want to render `prompt.md` and `status.json`
   without making a model request.

6. Read `answer.md`, `status.json`, and `stderr.txt` from the output directory.
   Summarize Fable's advice, state what you accept or reject, and verify any
   actionable recommendation locally before changing code.

## Output Contract

Each successful or failed run writes:

- `prompt.md` - exact prompt sent to Claude Code after file bundling;
- `answer.md` - stdout from the Fable request;
- `stderr.txt` - stderr from the Claude process;
- `status.json` - route-gate result, command metadata, exit code, and paths.

Dry runs omit `answer.md` and `stderr.txt` because no model request is made.

Keep these files in the active task artifact folder when the consultation
informs task decisions.

## Failure Handling

If the route gate fails, stop. Tell the user the observed `authMethod`,
`apiProvider`, and `subscriptionType`, and ask them to switch Claude Code to
subscription login before continuing. The safe target is:

```text
authMethod=claude.ai
apiProvider=firstParty
subscriptionType=<paid plan>
```

If `claude -p` fails after the route gate passes, try one non-model diagnostic
pass such as `claude --version`, `claude --model fable --effort max --help`, and
`claude auth status --json` under the cleaned environment. If those are healthy,
you may use an interactive zellij fallback, but launch Claude through the same
cleaned environment and capture the answer back into task artifacts. Do not
silently switch to Bedrock, API keys, or `--console` auth.

## Prompt Shape

Ask Fable for judgment, not another implementation agent. Good requests include:

- "Review this plan for hidden risks and missing validation."
- "Find the most likely root cause and the next three checks."
- "Challenge this architecture and propose a safer alternative if needed."
- "Act as a final reviewer; list blockers before I hand this off."

Prefer concise, outcome-oriented instructions. Fable is strongest when given the
goal and constraints rather than a long procedural script.
