# Ralph Loop Prompt

Read AGENT.md for build/test instructions.
Read specs/ for feature specifications.
Read fix_plan.md for the task list.

Choose the most important incomplete item from fix_plan.md and implement it.

## Requirements

- Full implementations only (no placeholders, no stubs)
- Search codebase before making changes (don't assume code doesn't exist)
- After EVERY code change: run Tier 1 (static) and Tier 2 (smoke) from AGENT.md
- At milestone tasks (marked [MILESTONE] in fix_plan.md): also run Tier 3 (integration)
- If Tier 2 fails with 500/crash: fix before committing
- If Tier 2 returns connection refused: skip, rely on Tier 1 only
- Update fix_plan.md when task is complete
- Commit with descriptive message

## Signs

- After modifying code, ALWAYS run Tier 2 smoke test before committing. A crash means broken code.
<!-- Add more guidance here when Ralph goes wrong -->
<!-- Example: DO NOT modify files unrelated to the current task -->

## Promise

Keep the exact completion token below in this file only once. If you want additional wording elsewhere, paraphrase it instead of repeating the exact token.

When all items in fix_plan.md are complete, respond with:

```
TASK_COMPLETE
```
