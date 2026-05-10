---
name: create-goal-plan
description: Create a short Markdown goal-plan file for Codex CLI `/goal` usage. Use when the user asks to create, distill, or prepare a Codex goal plan from an existing task, accepted plan, status file, grill-me result, bug report, implementation plan, or when they want a crisp objective file for a long-running Codex goal.
---

# Create Goal Plan

Create a compact Markdown file that Codex can consume with `/goal <path>`. The file is a goal handoff, not the canonical planning document.

Keep heavy planning in the active task `status.md`, `## Accepted Plans`, or dedicated plan artifacts. The goal plan should cite those paths and compress the work into one concrete outcome plus the minimum context, constraints, process, and verification criteria.

## Workflow

1. Resolve the active task context.
   - Prefer the current task status file from task metadata or `get-task-details`.
   - If no task context exists, use a user-specified output path or create `goal-plan.md` in the current repo root.
   - Default output path when a task folder exists: `task-progress-artifacts/goal-plan.md`.

2. Look for an already-finalized plan.
   - Inspect `status.md` for `## Accepted Plans`, recent `## Proposed Plan`, notes, and validation sections.
   - Also inspect obvious dedicated plan artifacts under `task-progress-artifacts/`.
   - If a concrete plan is accepted or otherwise clearly finalized, ask no extra questions unless a critical gap would make the goal unsafe or ambiguous.

3. If no concrete plan is finalized, finalize one first.
   - Use `$grill-me` when meaningful product, architecture, scope, safety, or sequencing decisions remain.
   - Persist the resulting full plan in the regular task status file or a dedicated plan artifact before creating the goal plan.
   - The goal plan should reference that full plan by path instead of duplicating it.

4. Write the goal plan.
   - Keep it roughly one screen: normally 150-300 words.
   - Start with one concrete outcome, not a heading.
   - Use short bullets under exactly these sections:

```markdown
<one concrete outcome>

Context:
- <files/modules/errors/docs that matter>
- <what to inspect first>

Constraints:
- <what not to change>
- <architecture/style/safety constraints>

Process:
- <run tests first / reproduce bug / inspect logs / use small commits mentally>
- <keep changes minimal>

Done when:
- <objective verification>
- <tests/checks pass>
- <diff is clean and scoped>
- <final answer includes summary + commands run>
```

5. Report the path and invocation.
   - Tell the user the exact path created.
   - Include the exact command they can paste, e.g. `/goal context/daily/.../task-progress-artifacts/goal-plan.md`.

## Content Rules

- Make the first line an outcome with a verb and a concrete end state.
- Cite the full plan/status path in `Context` when one exists.
- Include only context the next Codex agent needs to start correctly.
- Include explicit "do not change" constraints when the task touches a dirty worktree, live system, public content, data deletion, migrations, secrets, auth, or external APIs.
- Prefer repo-local validation commands from existing docs over invented checks.
- Mention live API/network/destructive-operation boundaries when relevant.
- Do not include long explanations, rationale, transcript summaries, or broad brainstorming in the goal plan.
- Do not mark a plan accepted unless the user explicitly accepted it through the normal task-status workflow.
