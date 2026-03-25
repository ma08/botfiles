---
name: grill-me
description: Interview the user relentlessly about a plan, design, or decision using Claude's interactive `AskUserQuestion` tool until you reach shared understanding. Use when the user wants to stress-test a plan, get grilled on their design, or says "grill me".
source: personal
---

Use `AskUserQuestion` to interview me relentlessly about every aspect of this plan until we reach a shared understanding.

- Use `AskUserQuestion` instead of plain-text questions whenever you need my input.
- Ask one focused multiple-choice question at a time. Include a clear recommended option and use the tool's question format to surface the main tradeoffs cleanly.
- After each answer, state the implication of that choice, give your current recommendation, and move to the next unresolved branch in the decision tree.
- Keep digging into goals, constraints, failure modes, sequencing, ownership, and validation until the important ambiguities are resolved.
- If a question can be answered by exploring the codebase, docs, or current task artifacts, do that instead of asking me.
