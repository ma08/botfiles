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
- runs Claude in safe mode with an explicit empty strict MCP configuration;
- strips common cloud, GitHub, and app credential environment variables from
  tool-enabled runs unless `--inherit-credentials` is explicitly supplied;
- runs `claude auth status --json`;
- loads a runner-only long-lived subscription token from
  `$BOTFILES_ROOT/secrets/local/claude-fable-oauth-token` when present, without
  exporting it to ordinary Claude Code sessions;
- refuses unless the status shows `loggedIn=true`, `apiProvider=firstParty`,
  and either a paid `claude.ai` stored login or an `oauth_token` credential
  loaded from the runner-only subscription token source;
- runs `claude --model fable --effort max -p ...` only after the gate passes;
- disables Claude tools by default and writes reusable output artifacts;
- provides `--read-only-review` for credential-stripped repository inspection
  with `Read`, `Glob`, `Grep`, and narrowly pre-approved read-only Git commands;
- can opt into all default tools with `--with-tools`, a bounded allowlist with
  `--tools "Read,Bash"`, and full permission bypass with `--yolo`.

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
   uv run python "$HOME/pro/botfiles/codex/skills/claude-fable-advisor/scripts/run_fable_advisor.py" \
     --check-only \
     --output-dir /path/to/artifacts/fable-route-check
   ```

   For more stable non-interactive authentication, configure the runner-only
   long-lived token once from a private terminal:

   ```bash
   uv run python "$HOME/pro/botfiles/codex/skills/claude-fable-advisor/scripts/setup_fable_oauth_token.py"
   ```

   This invokes `claude setup-token`, accepts the resulting token through a
   hidden prompt, and stores it in the git-ignored machine-local secret file at
   mode `0600`. Never paste the token into Codex, task artifacts, shell history,
   or tracked files. The runner records only `oauthCredentialSource`, never the
   token value.

5. Run the live advisory request:

   ```bash
   uv run python "$HOME/pro/botfiles/codex/skills/claude-fable-advisor/scripts/run_fable_advisor.py" \
     --prompt-file /path/to/fable-prompt.md \
     --file /path/to/relevant-file \
     --output-dir /path/to/artifacts/fable-review
   ```

   Add `--dry-run` first when you want to render `prompt.md` and `status.json`
   without making a model request.

6. Choose the tool mode deliberately:

   - No tools (default): omit both `--with-tools` and `--tools`.
   - Comprehensive read-only repository review: add `--read-only-review`.
     This is the preferred mode for assessment and code review. It defaults to
     12 turns, strips ambient credentials, uses `dontAsk`, excludes edit tools,
     and pre-approves only built-in reads plus selected inspection-only Git
     commands.
   - Full default tool set with normal permission handling: add
     `--with-tools`.
   - Bounded tool set: add a quoted allowlist such as
     `--tools "Read,Bash"`.
   - Full default tools with all permission checks bypassed: add
     `--with-tools --yolo`.

   `--yolo` maps to Claude Code's `--dangerously-skip-permissions` and is
   rejected unless tools are enabled. Use it only with explicit user approval
   or an already-approved implementation scope, from a trusted working
   directory, with a narrowly bounded prompt. It does not weaken the
   subscription route gate and never enables a cloud-provider fallback.
   Safe mode and environment stripping reduce ambient authority but are not a
   filesystem or network sandbox. Use `--inherit-credentials` only when the
   approved task explicitly needs those credentials.
   Tool-enabled runs default to three agentic turns so Fable can call a tool
   and then return its judgment; override with `--max-turns` when needed.
   `--read-only-review` has its own 12-turn default and rejects `--yolo`,
   `--inherit-credentials`, `--with-tools`, and a custom `--tools` list.
   Its Bash allowlist is a procedural permission control, not an operating-
   system sandbox. The runner also prepends a strict no-write, no-network,
   no-provider-access boundary to the prompt.

7. Read `answer.md`, `status.json`, and `stderr.txt` from the output directory.
   Summarize Fable's advice, state what you accept or reject, and verify any
   actionable recommendation locally before changing code.

## Output Contract

Each successful or failed run writes:

- `prompt.md` - exact prompt sent to Claude Code after file bundling;
- `answer.md` - stdout from the Fable request;
- `stderr.txt` - stderr from the Claude process;
- `status.json` - route-gate result, command metadata, exit code, and paths.

`status.json` records whether authentication came from `token-file`,
`environment`, or `stored-login`, without recording the credential itself.

For read-only reviews, `status.json` also records the permission mode and exact
pre-approved tool rules.

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

For the official long-lived token generated by `claude setup-token`, the safe
target is `loggedIn=true`, `authMethod=oauth_token`, and
`apiProvider=firstParty`. Claude Code currently omits `subscriptionType` for
this credential form, so accept it only when the runner loaded the explicit
OAuth environment or token-file source.

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
