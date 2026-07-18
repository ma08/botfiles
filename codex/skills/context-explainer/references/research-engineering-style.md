# Research / Engineering Style

Use this mode for research proposals, experiment designs, benchmark reports, architecture reviews, and pitches to senior research engineers.

## Output contract

- The source of truth is a real LaTeX document.
- Deliver the editable .tex source and a PDF compiled by lualatex or pdflatex.
- Do not use HTML-to-PDF, browser print styling, or an image of typeset text as a substitute.
- Keep generated auxiliary files and build logs in the task scratchpad.

## Typographic grammar

- Start from a conventional article class with restrained margins, Latin Modern or another installed TeX text family, microtypography, numbered sections, and ordinary page numbers.
- Use semantic title, author/audience, date, abstract, labels, cross-references, tables, equations, figures, captions, and bibliography entries.
- Prefer one-column preprint form for architecture and methodology papers unless the user requests a conference template or two-column format.
- Keep prose in normal paragraphs with real indentation or restrained paragraph spacing. Avoid web-style cards, badges, hero blocks, and dashboard navigation.
- Use color only for links and a restrained figure accent. The paper must remain legible in grayscale.

## Figures

- Default to native TikZ/PGF for architecture, data flow, state, decision, and experiment-boundary figures.
- Use PGFPlots for quantitative charts.
- Use consistent node shapes, line weights, arrowheads, type sizes, alignment, and caption conventions across the paper.
- Keep figure text selectable. Do not rasterize technical labels.
- Fit figures to the text block without tiny type. If a figure needs excessive scaling, simplify or split it.
- Use Figma only when the figure is primarily illustrative/editorial or when collaborative manual editing matters more than publication-native source.

## Tables and equations

- Use booktabs rules rather than boxed cell grids.
- Use tabularx or carefully sized columns; never shrink dense tables until text becomes unreadable.
- State objectives and gates mathematically when notation is more compact than prose, then define every symbol.
- Use footnotes sparingly and do not bury core methodology in them.

## References and evidence

- Cite external research with bibliography entries and in-text citations.
- Cite local task evidence with a stable relative path, repository path, commit, or artifact name.
- Make fact, inference, proposal, and decision status explicit.
- The first page should state the research question, proposal, evidence boundary, and requested decision.

## Compilation and QA

- Compile twice at minimum.
- Treat LaTeX errors, undefined references, missing characters, and overfull boxes as defects.
- Review underfull-box warnings for genuinely bad spacing; harmless warnings may be documented.
- Use the compile helper's --fail-on-warnings option for the final freeze unless a reviewed harmless warning is explicitly recorded.
- Render every PDF page with Poppler.
- Inspect the title page, all TikZ figures, the densest table, equation blocks, section/page transitions, and references.
- Confirm selectable text with pdftotext and document metadata/page size with pdfinfo.
