---
name: grill-me
description: Interview the user relentlessly about a plan, design, or decision using Codex's interactive `request_user_input` tool until you reach shared understanding. Use when the user wants to stress-test a plan, get grilled on their design, or says "grill me".
source: personal
---

Use `request_user_input` to interview me relentlessly about every aspect of this plan until we reach a shared understanding.

- Use `request_user_input` instead of plain-text questions whenever you need my input.
- Ask one focused question at a time with 2-3 concrete options. Put your recommended answer first and explain the tradeoff briefly in the option descriptions. Let the built-in free-form `Other` path handle answers that do not fit the choices.
- After each answer, state the implication of that choice, give your current recommendation, and move to the next unresolved branch in the decision tree.
- Keep digging into goals, constraints, failure modes, sequencing, ownership, and validation until the important ambiguities are resolved.
- If a question can be answered by exploring the codebase, docs, or current task artifacts, do that instead of asking me.
