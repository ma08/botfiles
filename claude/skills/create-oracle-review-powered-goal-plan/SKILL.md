---
name: create-oracle-review-powered-goal-plan
description: Create compact Codex `/goal` plan files that require an implementation loop with Oracle GPT-5.5 Pro review between iterations. Use when the user wants a goal plan that explicitly sequences implementation, strongest-model Oracle review, rework from Oracle findings, repeated review until no material changes remain, and final verification.
---

# Create Oracle Review Powered Goal Plan

## Overview

Create a concise Markdown handoff for Codex CLI `/goal <path>` that embeds an Oracle-reviewed implementation loop. This skill specializes `create-goal-plan`: the goal file remains short, but the process requires implementation, local validation, Oracle GPT-5.5 Pro review, rework, and repeated Oracle review until the remaining recommendations are empty or explicitly rejected with rationale.

## Workflow

1. Resolve the task context and full plan.
   - Prefer the active task `status.md`, accepted plan entry, and dedicated plan artifacts under `task-progress-artifacts/`.
   - If no plan is accepted yet, do not imply approval. The goal plan may say that implementation begins only after explicit human acceptance and normal task-status persistence.
   - Cite the full plan/status paths in `Context` instead of duplicating long planning detail.

2. Write a compact goal plan.
   - Use the same shape as `create-goal-plan`: first line is one concrete outcome, then exactly `Context:`, `Constraints:`, `Process:`, and `Done when:`.
   - Keep it roughly one screen. The complete architecture, plan, and rationale belong in cited artifacts.
   - Include dirty-worktree, privacy, secrets, destructive-action, and external-API boundaries when relevant.

3. Make the Oracle loop explicit in `Process`.
   - Implement in focused phases from the accepted plan.
   - Run repo-local tests, linters, validators, smoke tests, or reproductions after each meaningful phase.
   - Prepare a tight Oracle prompt with the changed files, acceptance criteria, validation commands already run, known risks, and the exact review question.
   - Run the local wrapper with GPT-5.5 Pro browser/manual-login mode:

```bash
oracle --engine browser --browser-manual-login --browser-chrome-path "$HOME/pro/botfiles/bin/oracle-chrome-linux" --model "5.5 Pro" --browser-model-strategy current -p "<review prompt>" --file "<focused paths>"
```

   - Wait or reattach until Oracle completes. Do not downgrade for normal latency, `in_progress`, prompt-size issues, polling-shell death, or browser upload friction; compact or reattach first. Fallback from GPT-5.5 Pro only after repeated availability or access failures.
   - Save Oracle prompt, response, and relevant logs under the task's `task-progress-artifacts/scratchpad/`.
   - Classify Oracle feedback as must-fix, optional, or rejected-with-rationale. Implement must-fix items, rerun local validation, and repeat Oracle review on the revised diff until no material changes remain.

4. Report the created file and invocation.
   - Tell the user the exact path.
   - Include the exact `/goal <path>` command they can paste.

## Oracle Review Rules

- Use the local `oracle` wrapper, not raw `npx`, unless debugging the wrapper itself.
- Attach the fewest files that still contain the truth. Never attach `.env`, secrets, private keys, raw tokens, or unrelated private data.
- Ask Oracle for findings, risk assessment, concrete recommendations, and test gaps. Do not ask for hidden chain-of-thought.
- Treat Oracle as advisory but high-signal. If rejecting a recommendation, write a short rationale and keep it with the review artifact or final notes.
- Repeat review only after meaningful changes. If the last Oracle response has no material changes or only rejected optional suggestions, the loop can close.

## Goal Plan Template

```markdown
<Implement/fix/build the concrete outcome, using Oracle GPT-5.5 Pro review until no material changes remain.>

Context:
- <full accepted plan/status/artifact paths>
- <files or modules to inspect first>

Constraints:
- <do not change / privacy / secrets / external API / dirty worktree boundaries>
- Use Oracle GPT-5.5 Pro browser/manual-login review; do not downgrade for normal latency.

Process:
- Implement from the accepted plan in scoped phases and run local validation.
- Prepare a focused Oracle review prompt with changed files, criteria, tests run, and known risks; run the explicit GPT-5.5 Pro browser command.
- Save Oracle prompt/response/logs, implement must-fix feedback, rerun validation, and repeat Oracle review until clean or remaining suggestions are rejected with rationale.

Done when:
- <objective verification passes>
- <tests/checks pass>
- Final Oracle GPT-5.5 Pro review has no material changes.
- Final answer summarizes implementation, validation commands, and Oracle iterations.
```
