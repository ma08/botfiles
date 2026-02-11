# Ralph Skill for Claude Code

A Claude Code skill encoding the Ralph Wiggum methodology for autonomous agentic software development.

## What is Ralph?

Ralph is a technique for autonomous code generation using LLMs in a deterministic loop. Instead of giving Claude complex multi-step plans, you give it:
- Clear specifications (specs)
- A simple task list (fix_plan.md)
- Build/test instructions (AGENT.md)
- A loop prompt (PROMPT.md)

Then you let Ralph iterate: generate code → run tests → commit → repeat.

## Prerequisites

- Claude Code CLI or Codex CLI
- Git repository for the target project
- Test suite for the feature being implemented

## Quick Start

### 1. Create a staging folder

```bash
# In your instructions directory
mkdir -p staging/specs
cd staging
```

### 2. Copy templates

```bash
cp ~/.claude/skills/ralph/templates/AGENT.md .
cp ~/.claude/skills/ralph/templates/PROMPT.md .
cp ~/.claude/skills/ralph/templates/fix_plan.md .
cp ~/.claude/skills/ralph/templates/spec-template.md specs/
```

### 3. Write specs (the critical step)

Talk to Claude about what you want to build:

```
Me: I need to implement a zone grounding service that uses Florence-2 to detect objects in video frames and determine if they're in defined zones.

Claude: [Asks clarifying questions about input format, output format, performance requirements...]

Me: Now write a spec for this feature.

Claude: [Generates comprehensive spec with function signatures, requirements, reference code]
```

Save the spec to `specs/feature_name.md`.

### 4. Fill AGENT.md

Add your project-specific commands:
- Environment activation (conda, venv)
- Test commands (pytest, jest, etc.)
- Type checking (mypy, pyright)
- Build commands if applicable

### 5. Run the loop

There are three execution paths:

**A) Loop script (for unattended/remote runs):**
```bash
# Generate run-ralph.sh from the template, then:
./run-ralph.sh codex           # Run with Codex CLI
./run-ralph.sh claude          # Run with Claude Code CLI
./run-ralph.sh codex 30        # Codex, 30 iterations
```

**B) Ralph-loop plugin (for interactive Claude Code sessions):**
```bash
/ralph-loop "$(cat PROMPT.md)" --max-iterations 30 --completion-promise "TASK_COMPLETE"
```

**C) Simple while loop (for learning/debugging):**
```bash
while true; do cat PROMPT.md | claude --dangerously-skip-permissions -p; sleep 2; done
```

## Directory Structure

```
staging/
├── AGENT.md          # Build/test instructions
├── PROMPT.md         # The loop prompt
├── fix_plan.md       # Task list
├── run-ralph.sh      # Loop script (generated from template)
└── specs/            # Feature specifications
    └── feature.md
```

## Tips for Success

1. **Start small**: Begin with 3-5 tasks in fix_plan.md, not 20
2. **Include reference code**: Working code in specs dramatically improves output
3. **Watch the first loop**: Observe what Ralph does wrong, add signs
4. **Commit often**: Let Ralph commit after each successful task
5. **Use type checking**: Add mypy/pyright to AGENT.md for Python projects

## Complete Example: ZonEye Backend

Here's how the orchestrator (Personal OS) prepares a Ralph task for the GPU VM:

### 1. Create staging folder
```bash
mkdir -p orchestration/instructions/daily/2026-01-04/zoneye/backend/staging/specs
```

### 2. Create files from templates
- **AGENT.md**: conda env activation, pytest commands, mypy type checking
- **PROMPT.md**: Task instructions with "ZONEYE_BACKEND_COMPLETE" promise
- **fix_plan.md**: 3 tasks (zone_grounding, vlm_client, vlm_verifier)
- **specs/*.md**: Function signatures, requirements, working reference code from tested notebooks
- **run-ralph.sh**: Generated from template with WORKDIR, promise, etc. filled in

### 3. Copy to GPU VM
```bash
scp -r staging/* ladduu-dev-ml-vm:/home/azureuser/pro/zone-analytics/
```

### 4. User runs on target machine
```bash
ssh ladduu-dev-ml-vm
cd /home/azureuser/pro/zone-analytics

# Option A: Unattended loop script
chmod +x run-ralph.sh
./run-ralph.sh codex 20

# Option B: Interactive plugin
/ralph-loop "$(cat PROMPT.md)" --max-iterations 30 --completion-promise "ZONEYE_BACKEND_COMPLETE"
```

### 5. Monitor and recover if needed
```bash
# If Ralph breaks things
git reset --hard HEAD~5

# If Ralph gets stuck
pkill -f "claude"
cat fix_plan.md  # Check what's left
```

## Troubleshooting

### Ralph keeps implementing placeholders
Add to PROMPT.md:
```
DO NOT IMPLEMENT PLACEHOLDER OR STUB IMPLEMENTATIONS.
WE WANT FULL, WORKING IMPLEMENTATIONS.
```

### Ralph changes unrelated files
Add to PROMPT.md:
```
Only modify files directly related to the current task.
Do not refactor or "improve" other code.
```

### Tests keep failing
- Check AGENT.md has correct test commands
- Add sign: "Run only tests for the feature being implemented"
- Make sure specs include expected behavior

### Ralph assumes code doesn't exist
Add to PROMPT.md:
```
Before making changes, search the codebase using parallel subagents.
Do not assume a feature is not implemented.
```

## Attribution

Based on "Ralph Wiggum as a Software Engineer" by Geoffrey Huntley and the Claude Code Ralph plugin.
