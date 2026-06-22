---
name: context-explainer
description: Create self-contained HTML explainers that help a human understand the full context of a task, issue family, PR, architecture, or implementation plan. Use when the user asks for an HTML/webpage/visual explainer, wants background plus diagrams, asks whether related issues are worth taking up, needs an end-to-end mental model, or wants the artifact copied/opened on a local Mac from a remote VM.
---

# Context Explainer

Build a readable, source-grounded HTML artifact that explains context, decisions, architecture, and next steps. The output is a local artifact for human review, not production app code.

## Workflow

1. Resolve the active task folder.
   - Prefer an existing task folder/status file when the request continues an active task.
   - Put curated HTML at `task-progress-artifacts/<slug>.html`.
   - Put screenshots, raw logs, and intermediate captures in `task-progress-artifacts/scratchpad/`.

2. Gather truth from primary sources.
   - Inspect current code, tests, issue/PR state, docs, and prior task artifacts.
   - For GitHub issues/PRs, verify current state with `gh` or the GitHub app; stale issue text is common.
   - If the user asks for public inspiration or latest external context, browse and cite the sources used.
   - If the user explicitly asks for Oracle or the decision is broad/risky, run Oracle with a tight file bundle and record the engine/model evidence.

3. Write the explanation thesis before editing HTML.
   - State a visual thesis: mood, material, and energy.
   - State a content plan: background, source map, architecture, decision matrix, next actions.
   - State an interaction thesis: sticky navigation, expandable evidence, hover/focus diagrams, or lightweight scroll structure.

4. Create a self-contained HTML page.
   - Use inline CSS and inline SVG diagrams; avoid external build steps.
   - Include a first-screen overview, a section map, issue/PR relationship diagrams, architecture/data-flow diagrams, a decision matrix, risks/traps, validation commands, and source references.
   - Distinguish facts from inferences. Mark stale or ambiguous issue state clearly.
   - Keep prose scannable: dense enough for technical context, but not a wall of markdown.

5. Verify visually.
   - Use the Playwright skill/wrapper for desktop and mobile screenshots.
   - Check browser console output and fix real errors.
   - Inspect screenshots for text overlap, illegible diagrams, horizontal overflow, and broken responsive layout.

6. Make it easy for the user to open.
   - If running on the user's Mac, provide the local HTML path and optionally open it.
   - If running on a remote VM, copy the HTML to the Mac with `scripts/copy_explainer_to_mac.py` or an equivalent `scp` command.
   - Default remote alias: `sourya-mac`.
   - Default destination: `/Users/sourya4/Desktop/`.

7. Update task status.
   - Add the HTML and verification screenshots to the artifact list.
   - Mention where it was copied for local viewing.
   - Preserve unrelated status content.

## Helper Script

Use the bundled helper after generating an HTML artifact:

```bash
python /home/azureuser/pro/botfiles/codex/skills/context-explainer/scripts/copy_explainer_to_mac.py \
  path/to/explainer.html \
  --machine sourya-mac \
  --dest-dir /Users/sourya4/Desktop \
  --open
```

The script prints the destination path and verifies the remote file exists. Use `--open` only when the user wants it opened on the Mac.

## Quality Bar

- The page should teach the user's mental model, not just summarize files.
- Diagrams should explain relationships that prose alone makes hard to hold.
- Recommendations should be candid about scope, cost, duplication risk, and validation.
- Do not launch expensive model/cloud jobs just because the explainer describes them.
- Do not silently skip inaccessible material links; record the limitation or ask for input.
