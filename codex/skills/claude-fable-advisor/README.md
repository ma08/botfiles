# Claude Fable Advisor

Use Claude Fable 5 as a subscription-backed external advisor for plans,
architecture, debugging strategy, reviews, and completion checks.

The bundled runner refuses to call Fable unless Claude Code reports:

```text
authMethod=claude.ai
apiProvider=firstParty
subscriptionType=<paid plan>
```

It runs Claude in safe mode with an explicit empty MCP configuration and strips
API-key and third-party provider variables from the child process. Tool-enabled
runs also strip common cloud, GitHub, and app credential environment variables
by default. It does not fall back to Bedrock, Vertex, Foundry, Claude Platform
on AWS, or Console/API billing.

## Choose a mode

| Mode | Flags | Good for |
| --- | --- | --- |
| No tools | none | Plans, decisions, attached documents, independent critique |
| Selected tools | `--tools "Read,Bash"` | Code review, diagnostics, targeted repository inspection |
| Full tools | `--with-tools` | Broad repository exploration with normal permission handling |
| Full tools + yolo | `--with-tools --yolo` | Approved work in an isolated, trusted environment |

No tools is the default. Tool-enabled runs default to three agentic turns;
no-tool runs default to one. Override either with `--max-turns`.

## Ask Codex conversationally

You normally do not need to invoke the runner yourself. Tell Codex what
judgment you want, what evidence Fable may inspect, and which tool mode to use.

### Review a plan

> Use `$claude-fable-advisor` without tools to review Plan v16. Identify hidden
> risks, missing validation, and any reason implementation should not proceed.
> Return only blockers and recommended changes.

### Get an independent decision

> Ask Fable without tools whether we should consolidate these services.
> Challenge my assumptions and recommend one option with rationale.

### Review code

> Use Fable with `Read,Bash` tools to review this branch for correctness,
> security regressions, behavior changes, and missing tests. It may inspect
> files and run tests, but must not edit anything.

### Diagnose a difficult bug

> Ask Fable with `Read,Bash` tools to investigate this failure. Inspect the
> relevant code and logs, reproduce it if safe, and give the three most likely
> root causes plus the next diagnostic step. Do not edit code.

### Challenge an architecture

> Use Fable with full tools and normal permissions to inspect the repository
> and challenge this architecture. Focus on unnecessary complexity, failure
> modes, data-loss risks, and a simpler robust alternative.

### Perform an adversarial completion check

> Have Fable inspect the implementation and evidence with bounded tools. Act
> as a skeptical final reviewer and list anything that prevents us from
> confidently calling the task complete.

### Critique research or thesis work

> Ask Fable without tools to critique this thesis argument. Identify
> unsupported claims, methodological weaknesses, alternative interpretations,
> and the strongest revision strategy.

If Fable needs surrounding files:

> Use Fable with `Read` tools to inspect the manuscript and results files, then
> provide a reviewer-style critique. Do not modify anything.

### Analyze a production incident

> Use Fable with bounded `Read,Bash` tools to inspect the last two hours of
> logs and relevant code. Do not mutate production. Determine the likely
> failure sequence and recommend the safest next action.

### Execute in an isolated environment

> Use Fable with full tools and yolo in this isolated worktree. Run the
> relevant tests and perform an adversarial completion check. Do not access
> cloud resources, secrets, or production. Do not commit or push.

For a narrowly approved implementation:

> Use Fable with full tools and yolo to implement and validate this approved
> change in the isolated worktree. It may edit files and run tests, but must
> not commit, push, deploy, or access production.

## Run it directly

Set a short runner variable:

```bash
RUNNER="$HOME/pro/botfiles/codex/skills/claude-fable-advisor/scripts/run_fable_advisor.py"
```

Check the subscription route without using Fable quota:

```bash
uv run python "$RUNNER" \
  --check-only \
  --output-dir /path/to/artifacts/fable-route-check
```

Render and inspect the prompt without making a model request:

```bash
uv run python "$RUNNER" \
  --prompt-file /path/to/fable-prompt.md \
  --file /path/to/relevant-file \
  --dry-run \
  --output-dir /path/to/artifacts/fable-dry-run
```

Run without tools:

```bash
uv run python "$RUNNER" \
  --prompt-file /path/to/fable-prompt.md \
  --file /path/to/relevant-file \
  --output-dir /path/to/artifacts/fable-review
```

Run with selected tools:

```bash
uv run python "$RUNNER" \
  --prompt-file /path/to/fable-prompt.md \
  --tools "Read,Bash" \
  --output-dir /path/to/artifacts/fable-review
```

Run with the full default tool set and normal permissions:

```bash
uv run python "$RUNNER" \
  --prompt-file /path/to/fable-prompt.md \
  --with-tools \
  --output-dir /path/to/artifacts/fable-review
```

Run with the full tool set and permission checks bypassed:

```bash
uv run python "$RUNNER" \
  --cwd /path/to/trusted-isolated-worktree \
  --prompt-file /path/to/fable-prompt.md \
  --with-tools \
  --yolo \
  --output-dir /path/to/artifacts/fable-review
```

Use `--tools "Read"` when Fable only needs file access. Adding `Bash` permits
arbitrary shell commands; it is not a read-only guarantee.

If a tool-enabled task deliberately needs ambient credentials, add
`--inherit-credentials`. This is an explicit opt-in and should be paired with a
narrow allowlist and prompt boundary.

## Yolo safety

`--yolo` maps to Claude Code's `--dangerously-skip-permissions`. The runner
rejects it unless tools are enabled. Safe mode, an empty strict MCP config, and
credential-environment stripping reduce ambient authority, but they are not a
sandbox: files and locally authenticated CLIs can still expose capabilities.

Before using it:

1. Obtain explicit approval or stay inside an already-approved implementation
   scope.
2. Use a trusted isolated worktree or disposable scratch directory.
3. State exact mutation boundaries in the prompt.
4. Exclude secrets, cloud resources, production, deploys, commits, and pushes
   unless each is deliberately authorized.
5. Verify Fable's changes and conclusions independently.

Prompt restrictions guide the model; filesystem, network, and credential
isolation provide the real safety boundary.

## Output artifacts

Every live run writes:

- `prompt.md` — exact bundled prompt
- `answer.md` — Fable's response
- `stderr.txt` — Claude Code diagnostics
- `status.json` — route gate, model, effort, tools, yolo state, command
  metadata, exit code, and artifact paths

Keep these in the active task's artifact folder when Fable informs a durable
decision.

## Troubleshooting

If the route check fails, run:

```bash
claude auth status
```

The safe target is a paid Claude subscription using `claude.ai` and the
first-party provider. Reauthenticate with:

```bash
claude auth login --claudeai
```

Do not use `claude --bare`, `claude auth login --console`, or a cloud-provider
fallback for this workflow.

The agent-facing operational contract remains in [`SKILL.md`](SKILL.md).
