---
name: Ralph
description: Ralph Wiggum methodology for autonomous agentic development. Use when setting up a new Ralph task, preparing specs, or troubleshooting Ralph loops.
source: personal
---

# Ralph Wiggum Methodology

Ralph is a technique for autonomous agentic software development using LLMs in a deterministic loop. Named after the naive character from The Simpsons, Ralph represents giving an AI minimal planning ability and maximum execution autonomy.

## Critical: Separation of Concerns

**The orchestrator session prepares the loop. The loop agent does the work.**

When a plan involves a Ralph loop, do NOT implement the code changes yourself. Your job is to create the Ralph infrastructure files (PROMPT.md, AGENT.md, fix_plan.md, specs/, run-ralph.sh) and hand off to the user to run the loop. The loop agent — spawned fresh each iteration by run-ralph.sh — reads PROMPT.md, picks the next incomplete task from fix_plan.md, implements it, validates, commits, and loops.

- **Orchestrator creates**: Ralph files, specs, fix_plan.md (tasks in TODO)
- **Orchestrator does NOT**: implement code, write tests, mark tasks complete, commit
- **Loop agent does**: implement code, run tests, update fix_plan.md, commit per task

## Core Philosophy

1. **Blame Yourself, Not Ralph**: If Ralph does something wrong, look at your prompts, specs, and instructions. "Tune Ralph like a guitar."

2. **One Thing Per Loop**: Ralph does ONE task per iteration. If things go off the rails, narrow to one item.

3. **Trust Eventual Consistency**: Every problem created by AI can be resolved through a different series of prompts.

4. **LLMs Are Mirrors**: The quality of Ralph's output reflects the quality of your specs and prompts.

## When to Use Ralph

- Greenfield projects (new codebases) - expect 90% completion
- Well-specified features with clear requirements
- GPU/remote machine delegation
- Tasks where you can provide working reference code

When NOT to use Ralph:
- Complex existing codebases with lots of implicit context
- Tasks requiring deep domain knowledge you can't encode in specs

---

## The Stack (4 Essential Files)

Ralph allocates these files as persistent context every loop:

### 1. PROMPT.md - The Loop Engine
The current task/instruction for Ralph. This is where you "tune Ralph" by adding guidance (signs).

Important: if your loop uses a completion promise string, include that exact string only once in `PROMPT.md`. Repeating the same promise text in multiple sections can cause false-positive completion detection when a runner echoes the prompt.

### 2. AGENT.md - The Heart
Instructions on HOW to build, run, and test the project:
- Environment setup (conda, venv, PATH)
- Build commands
- Test commands (specific test files, not whole suite)
- Type checking (mypy, pyright)

**Key**: Ralph updates this file when learning new commands.

### 3. fix_plan.md - The TODO List
Bullet-point list of items sorted by priority:
- `- [ ]` for pending tasks
- `- [x]` for completed tasks
- Notes section for learnings

Ralph keeps this updated. Delete and regenerate when stale.

### 4. specs/ - Specifications (Immutable Contract)
One file per feature/module. Each spec contains:
- Purpose statement
- Function signatures with full types
- Implementation requirements
- Working reference code (critical!)
- Expected input/output examples

**Key insight**: Specs are formed through conversation, not written in isolation.

---

## The Loop

Ralph cycles through three phases (repeat forever):

### Phase 1: Generate
- Ralph reads PROMPT.md, specs/*, and fix_plan.md
- Generates code based on specifications
- If generating wrong patterns → update specs
- If building wrong thing → specs are incorrect

### Phase 2: Backpressure (Validate at Three Tiers)
- **Tier 1 (Static)**: Type check, compile, structural grep — EVERY iteration (~5s)
- **Tier 2 (Smoke)**: Hit running service with trivial input, verify no crash — EVERY iteration if available (~5s)
- **Tier 3 (Integration)**: Real data through the feature — at [MILESTONE] tasks only (30s+)
- **Critical**: Tiers 1+2 must be fast. The wheel must turn fast. Tier 3 is for confidence checkpoints.
- If Tier 2 unavailable (service not running): fall back to Tier 1 only. Do NOT start services.

### Phase 3: Commit & Loop Back
- When tests pass, update fix_plan.md
- Git add/commit/push
- Loop back to Phase 1

---

## Writing Effective Specs

Specs are the most critical input. Bad specs = bad output.

**Process:**
1. Have a conversation with Claude about requirements
2. Claude asks clarifying questions
3. Once Claude understands, ask it to write specs
4. Include working code snippets from tested implementations

**Spec structure:**
```markdown
# Feature: [Name]

## Purpose
[What this feature does]

## Function Signatures
[Full typed signatures]

## Requirements
[Specific requirements, library versions, GPU needs, etc.]

## Reference Code
[Working code from tested notebook/implementation]

## Expected Behavior
[Input/output examples]
```

---

## Signs (Prompt Tuning)

When Ralph goes wrong, add "signs" to PROMPT.md:

| Problem | Sign to Add |
|---------|-------------|
| Placeholder implementations | "DO NOT IMPLEMENT PLACEHOLDER IMPLEMENTATIONS. WE WANT FULL IMPLEMENTATIONS." |
| Wrong assumptions | "Before making changes, search codebase using parallel subagents. Don't assume code doesn't exist." |
| Priority confusion | "Choose the most important incomplete item from fix_plan.md" |
| Forgetting context | "Capture test importance in comments explaining WHY the test exists" |
| Excessive changes | "Only modify files related to the current task" |

---

## Quick Start: Prep a Ralph Task

1. **Create staging folder** in your instructions directory:
   ```
   orchestration/instructions/daily/YYYY-MM-DD/<project>/<task>/staging/
   ```

2. **Copy templates** from `~/.codex/skills/ralph/templates/`

3. **Write specs through conversation**:
   - Describe the feature to Claude
   - Let Claude ask questions
   - Ask Claude to write the spec
   - Add working reference code

4. **Fill AGENT.md** with project-specific commands:
   - How to activate environment
   - How to run tests
   - How to type-check

5. **Keep the completion promise single-sourced**:
   - Put the exact completion string in one place in `PROMPT.md`
   - Do not repeat the same literal promise string elsewhere in the prompt
   - If you want extra wording, paraphrase around it instead of duplicating it verbatim

6. **Generate run-ralph.sh** (see Running Ralph below) or use the ralph-loop plugin

7. **Copy staging to target and run** (see Orchestrator Workflow below)

---

## Orchestrator Workflow (Personal OS → Target Codebase)

This skill is designed for the **orchestrator session** (Personal OS) to prepare Ralph tasks for execution in **target Claude Code sessions**.

### The Flow

```
┌─────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR (Personal OS)                                 │
│                                                             │
│  1. Brainstorm with user to make task ralph-able            │
│  2. Create staging/ folder with AGENT.md, PROMPT.md,        │
│     fix_plan.md, specs/                                     │
│  3. Generate run-ralph.sh (or plan to use ralph-loop)       │
│  4. Copy staging to target codebase                         │
│  5. Provide execution command to user                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  TARGET SESSION (in codebase folder)                        │
│                                                             │
│  Option A: ./run-ralph.sh codex|claude [max_iterations]     │
│  Option B: /ralph-loop "$(cat PROMPT.md)" ...               │
│  Ralph iterates: generate → test → commit → repeat          │
└─────────────────────────────────────────────────────────────┘
```

### Step 1: Brainstorm to Make Task Ralph-able

Ask the user:
- What feature/service needs to be built?
- What's the target codebase and machine?
- What are the function signatures?
- Is there working reference code (from notebooks, prototypes)?
- What are the test commands?

### Step 2: Create Staging Files

Create a staging folder in the instructions directory:
```
orchestration/instructions/daily/YYYY-MM-DD/<project>/<task>/staging/
├── AGENT.md
├── PROMPT.md
├── fix_plan.md
├── run-ralph.sh          (if using loop script)
└── specs/
    └── feature.md
```

Use templates from `~/.codex/skills/ralph/templates/` as starting point.

### Step 3: Copy Staging to Target

**Local codebase:**
```bash
cp -r staging/* /path/to/target/codebase/
```

**Remote VM (via scp):**
```bash
scp -r staging/* user@hostname:/path/to/target/codebase/

# Example for GPU VM
scp -r staging/* ladduu-dev-ml-vm:~/pro/zone-analytics/
```

### Step 4: Provide Execution Command

Based on the execution environment, provide the appropriate command:

**Option A: Loop script (unattended/remote execution)**
```bash
cd /path/to/target/codebase
chmod +x run-ralph.sh
./run-ralph.sh codex       # or: ./run-ralph.sh claude
```

**Option B: Ralph-loop plugin (interactive Claude Code session)**
```bash
cd /path/to/target/codebase
/ralph-loop "$(cat PROMPT.md)" --max-iterations 30 --completion-promise "TASK_COMPLETE"
```

---

## Running Ralph

There are three ways to execute a Ralph loop. Choose based on your environment and needs:

| Execution Path | Best For | Engine |
|---------------|----------|--------|
| **Loop script (Codex)** | Unattended remote runs, overnight execution | `codex` CLI |
| **Loop script (Claude Code)** | Unattended remote runs, overnight execution | `claude` CLI |
| **Ralph-loop plugin** | Interactive Claude Code sessions, local development | Built-in plugin |

### Path 1: Loop Script (Codex or Claude Code)

A bash script that pipes PROMPT.md to the chosen engine in a loop with promise detection.

**Generating the script:**

When the user invokes this skill to create a Ralph task, determine which variant to generate based on their phrasing:

| User says | Generate |
|-----------|----------|
| "with codex" / "using codex" | **Codex-only** script: `RUN_CMD` hardcoded, `./run-ralph.sh [max_iterations]` |
| "with claude code" / "with claude" / "using claude" | **Claude-only** script: `RUN_CMD` hardcoded, `./run-ralph.sh [max_iterations]` |
| No preference / ambiguous | **Dual-engine** script: `./run-ralph.sh <codex\|claude> [max_iterations]` |

**Dual-engine template** is at `~/.codex/skills/ralph/templates/run-ralph.sh`.

**Template variables to fill in:**
- `{{TASK_NAME}}` - Human-readable task name (e.g., "ZonEye Backend Alerts")
- `{{WORKDIR}}` - Absolute path to target codebase working directory
- `{{COMPLETION_PROMISE}}` - Promise string from PROMPT.md (e.g., "PROMISE_FULFILLED: ZONEYE_BACKEND_ALERTS_COMPLETE")
- `{{LOG_FILE}}` - Log filename (e.g., "ralph-backend.log")
- `{{MAX_ITERATIONS_DEFAULT}}` - Default iteration count (e.g., 20)

**Promise detection threshold differs by engine:**
- **Codex** echoes the prompt in its output, so the promise string appears **twice**: once in the echoed prompt text and once in the AI's response. Threshold: `PROMISE_THRESHOLD=2`.
- **Claude `-p`** does NOT echo the prompt — only the AI's response is output. The promise string appears **once**. Threshold: `PROMISE_THRESHOLD=1`.

The dual-engine template handles this automatically via the `PROMISE_THRESHOLD` variable set in the engine `case` block. For single-engine variants, hardcode the appropriate threshold.

**For single-engine variants**, simplify the template:
- Remove the engine argument and case/switch block
- Hardcode `RUN_CMD` to the appropriate command:
  - Codex: `codex --dangerously-bypass-approvals-and-sandbox exec`
  - Claude Code: `claude --dangerously-skip-permissions -p`
- Hardcode `PROMISE_THRESHOLD` to the appropriate value:
  - Codex: `PROMISE_THRESHOLD=2`
  - Claude Code: `PROMISE_THRESHOLD=1`
- Change usage to `./run-ralph.sh [max_iterations]` with `MAX_ITERATIONS="${1:-$MAX_ITERATIONS_DEFAULT}"`

### Path 2: Ralph-loop Plugin (Interactive)

For interactive Claude Code sessions, use the built-in plugin:

```bash
# In target codebase directory
/ralph-loop "$(cat PROMPT.md)" --max-iterations 30 --completion-promise "PROMISE_TEXT"
```

**Options:**
- `--max-iterations N`: Safety limit (default: 30)
- `--completion-promise "TEXT"`: Stop when Ralph outputs this text
- Press Ctrl+C or `/cancel-ralph` to stop early

This is the recommended approach when you're actively working in a Claude Code session and want plugin-level safety controls and monitoring.

---

## Troubleshooting

### Ralph is stuck in a loop
- Check if specs are clear enough
- Add more specific signs to PROMPT.md
- Reset with `git reset --hard` and restart

### Ralph generates wrong patterns
- Update specs with more reference code
- Add explicit "DO NOT do X" signs

### Tests keep failing
- Make sure AGENT.md has correct test commands
- Check if Ralph is running wrong tests
- Add sign: "Run only tests for the current feature"

### Ralph makes too many changes
- Add sign: "Only modify files directly related to the task"
- Narrow fix_plan.md to single item

### Woke up to broken codebase
- `git reset --hard` to last good commit
- Analyze what went wrong
- Add signs to prevent recurrence
- Restart Ralph

---

## Advanced Patterns

### Extend Context with Subagents
- Use parallel subagents (up to 500) for searching, analyzing, file writing
- Use only 1 subagent for builds/tests (avoid conflicts)
- Primary context operates as scheduler, not worker

### Testing Serverless / Edge Functions
- Single large files can't have individual functions imported into test harnesses
- `deno check` / `tsc` may not be available on the target machine
- Tier 2 curl-based smoke tests are the primary runtime safety net
- Design checks that distinguish "code is broken" (500) from "expected error" (400/404)
- For external SDK integration, test the key/connectivity separately from the main function

### Loop Back Is Everything
- Ralph can self-improve through the loop
- When discovering new commands → update AGENT.md
- When discovering bugs → document in fix_plan.md

### The Promise
End PROMPT.md with a "promise" - a keyword Ralph outputs when done:
```
When all items in fix_plan.md are complete, respond with: TASK_COMPLETE
```

---

## Resources

- Original article: "Ralph Wiggum as a Software Engineer" by Geoffrey Huntley
- Claude Code Ralph plugin: github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum
- Templates: See `templates/` directory in this skill
