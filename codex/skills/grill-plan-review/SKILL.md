---
name: grill-plan-review
description: Review a long or cognitively heavy plan through a concise, one-decision-at-a-time interview, recommend each choice with rationale, and turn the user's answers into a persisted accepted plan and execution authorization when requested. Use when the user cannot or does not want to read a plan document, asks for a grill-me-style plan review, or wants interactive confirmation before implementation.
---

# Grill Plan Review

Replace document reading with a decision interview while preserving a precise
approval trail.

1. Read the complete proposed plan, task status, and material evidence first.
   Resolve discoverable facts yourself instead of asking the user.
2. Extract only decisions that materially change scope, safety, cost,
   reversibility, sequencing, validation, or stopping conditions.
3. Use `request_user_input` for one focused decision at a time with 2-3
   concrete options. Put the recommended option first, label it
   `(Recommended)`, and explain its rationale and tradeoff in the description.
4. After every answer, state the locked implication in one or two sentences,
   then ask the next unresolved decision. Keep an explicit decision ledger.
5. Before the final confirmation, summarize the accumulated safeguards
   concisely. Ask whether to save only or save and execute unless the user has
   already made the intended post-review action unambiguous.
6. Treat the answers as review/confirmation only when the user explicitly said
   they should count that way. Preserve the exact answers as immutable task
   input.
7. If the final selection authorizes execution:
   - persist the full accepted plan in the canonical task status file before
     implementation;
   - include timestamp, accepted signal, supersedes value, revision summary,
     full plan, acceptance criteria, and hard boundaries;
   - create or update the requested goal;
   - execute without another redundant approval prompt.
8. Stop for clarification instead of inferring approval when the interview
   exposes a new action outside the reviewed scope.

Keep the interaction easy to scan: lead with the current decision, avoid
repeating the long source document, and make costs and failure behavior
concrete.
