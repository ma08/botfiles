---
name: guided-human-execution
description: Guide a human through a task in an interactive, human-in-the-loop execution rhythm. Use when the user asks to be walked through something step by step, wants to confirm each action before receiving the next step, says they feel overwhelmed or need help focusing, or needs coordination across agent-run checks and human-run UI/admin/credential/risky actions.
---

# Guided Human Execution

Use this skill to turn a multi-step task into a calm execution loop where the agent handles safe work and the human handles actions that require judgment, UI access, credentials, or explicit approval.

## Core Loop

1. Establish the objective and current state just enough to choose the next action.
2. Do any safe, easy, read-only, reversible, or tool-friendly checks yourself before interrupting the user.
3. Choose the next human-facing chunk with risk and cognitive load in mind.
4. Give the user only that next chunk, then wait for confirmation before giving the next human action.
5. After confirmation, verify state when possible with CLI/API/browser/screenshot/read-only checks.
6. Update the live checklist or checkpoint summary, then repeat.

## Work Split

Default to this ownership model:

- Agent does safe, easy, reversible, read-only, or tool-accessible work directly.
- Human does risky, expensive, irreversible, credential-bound, account-bound, UI-only, or tool-blocked work.
- If either route is plausible, offer a clear option: "I can do X" or "you can do Y", with the tradeoff.
- If the user asked for step-by-step focus, do not silently switch back into broad autonomous execution.

## Pacing

Use dynamic chunking:

- Use one strict step for irreversible actions, billing/admin changes, deletion, credential entry, production changes, confusing UI flows, or moments where the user may be overwhelmed.
- Use small batches only when all actions are low-risk, obvious, reversible, and easy to confirm together.
- Never give a long checklist and expect the user to execute it all before the next interaction unless they explicitly ask for a batch.

## Step Format

Keep each step short and concrete. A good step usually includes:

- **Current checkpoint:** what is true now.
- **Next step:** who acts and the exact action to take.
- **Expected result:** what the user should see or what state should change.
- **Stop condition:** what should make the user pause and report back.
- **Confirmation request:** ask the user to reply when done, or choose between options.

Use `request_user_input` when available for meaningful choices with 2-3 concrete options. For simple "do this and tell me when done" confirmations, a concise plain-text prompt is usually better.

## Safety Gates

Before irreversible, expensive, destructive, security-sensitive, or account-level actions, require explicit exact approval. State:

- the exact action
- the target account/resource
- the expected effect
- whether rollback is available
- what evidence will be checked afterward

Do not treat approval of a plan or previous step as approval for a later destructive action.

## Verification

After the user confirms a step:

- Verify independently when a safe read-only route exists.
- If verification is not possible, say so and continue from the user's confirmation.
- If verification disagrees with the user's expectation, stop the sequence, explain the mismatch, and choose a recovery step.
- For screenshots, local artifacts, support tickets, billing pages, and admin consoles, prefer durable local captures or precise summaries when task-status instructions require them.

## State And Artifacts

Maintain a lightweight running state:

- current checkpoint
- completed steps
- next unresolved decision or action
- known risks or blockers

For active tracked tasks, billing/admin work, migrations, or long workflows, save important evidence and milestones using the existing task-status/artifact conventions. For casual workflows, keep the state in chat unless persistence is useful.

## Completion

End with a concise closeout:

- final state
- what was verified
- any remaining risk
- any saved artifact or status-file path

Do not continue inventing next steps after the requested outcome is reached.
