---
name: context-explainer
description: Create source-grounded explainers for research, engineering, architecture, task, issue, PR, and implementation-plan context. Use for end-to-end mental models, technical pitches, decision briefs, or artifacts copied to a local Mac. Research/engineering mode is real LaTeX compiled to PDF with native TikZ/PGF figures; regular mode is minimal self-contained HTML.
---

# Context Explainer

Create an artifact that teaches the reader a durable mental model. Prefer quiet typography, evidence, and useful figures over interface decoration.

## 1. Resolve scope and sources

1. Resolve the canonical task folder and status file.
2. Put curated outputs under task-progress-artifacts/; put build logs, rendered pages, screenshots, and intermediate files under task-progress-artifacts/scratchpad/.
3. Inspect primary code, tests, issue/PR state, docs, results, and prior artifacts. Verify mutable external state when relevant.
4. Distinguish facts, measurements, inferences, proposals, and unresolved questions.

## 2. Select one style

- **Research / engineering** — default for experiments, benchmark methodology, system architecture, research proposals, evaluation plans, and technical pitches. Read [references/research-engineering-style.md](references/research-engineering-style.md) completely and start from [assets/research-engineering-template.tex](assets/research-engineering-template.tex).
- **Regular artifact** — default for task context, issue families, product plans, PR explanations, and general decision briefs. Read [references/regular-style.md](references/regular-style.md) completely and start from [assets/regular-template.html](assets/regular-template.html).
- Honor an explicit style or output-format request. If the audience or use case is ambiguous, choose the quieter style; do not ask merely about aesthetics.

Research mode produces editable .tex source and a PDF compiled by a real LaTeX engine. Regular mode normally produces self-contained HTML.

## 3. State the thesis before authoring

Send a concise commentary update covering:

- **Argument:** the one sentence the reader should remember.
- **Reader path:** the minimum section sequence needed to establish it.
- **Figure plan:** only relationships that materially benefit from a visual.

Do not invent an interaction thesis when a static paper or essay is clearer.

## 4. Author the artifact

### Research / engineering

1. Copy the LaTeX template into the task artifact and replace its placeholders.
2. Use semantic LaTeX structure: title, author, abstract, numbered sections, labels/references, proper tables, captions, equations, and bibliography entries.
3. Author technical diagrams natively with TikZ/PGF. Use PGFPlots for data plots. Keep labels selectable and visual language consistent with the paper.
4. Keep source reproducible and self-contained where practical. Capture any external image locally and use relative paths.
5. Compile with scripts/compile_research_explainer.py; use --fail-on-warnings for the final freeze unless a reviewed harmless warning is documented. Do not fake a LaTeX look with HTML-to-PDF.

### Regular artifact

1. Copy the HTML template into the task artifact and replace its placeholders.
2. Keep it self-contained: inline CSS, inline SVG when needed, and no build step or remote font dependency.
3. Use semantic HTML, accessible contrast, selectable text, descriptive captions, and print CSS.

For either mode, use diagrams only when they clarify sequence, hierarchy, branching, repeated mappings, or causal relationships. Prefer one strong figure to many decorated boxes. Cite primary local paths and external sources near the claims they support.

## 5. Visual constraints

- Avoid gradients, glass effects, glowing borders, metric-card walls, badge/pill overload, oversized hero text, and dense sticky navigation.
- Do not turn every paragraph into a card. Let whitespace, headings, rules, tables, captions, and ordinary prose carry structure.
- Limit the palette to text, paper/background, rules, and at most one restrained accent plus a semantic warning color.
- Research PDFs should look like authored technical papers, not web pages printed to PDF.

## 6. Verify

### Research / engineering

1. Compile at least twice so references and page numbers settle.
2. Fail on LaTeX errors. Review the compiler's final-log warning summary for overfull/underfull boxes, undefined references, missing glyphs, and duplicate labels; final artifacts should normally pass --fail-on-warnings.
3. Use pdfinfo, pdftotext, and Poppler page rendering.
4. Inspect the title page, every technical figure, the densest table, section transitions, and the final references page. Fix clipping, awkward floats, widows/orphans, and bad page breaks.

### Regular artifact

1. Use the Playwright skill/wrapper for desktop and narrow/mobile screenshots.
2. Check console output, horizontal overflow, typography, tables, figures, captions, and link behavior.

## 7. Deliver and record

- On a remote VM, use scripts/copy_explainer_to_mac.py for PDF, TeX, or HTML. Default alias: sourya-mac; default destination: /Users/sourya4/Desktop/. Use --open only when requested.
- Update the task status with curated outputs, source, QA captures/renders, copy destination, and material limitations.
- Preserve unrelated task and repository changes.

## Quality bar

- The first page/screen establishes the question, proposed answer, and why it matters.
- The artifact is pleasant to read linearly and scannable in under two minutes.
- Architecture figures expose inputs, state, decisions, outputs, and information boundaries where relevant.
- Recommendations state scope, falsification criteria, risks, and the cheapest credible next validation.
- Do not launch costly experiments merely because the explainer proposes them.
