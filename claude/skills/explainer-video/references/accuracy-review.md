# Accuracy reviews

Two reviews by a second strong model (a different model or a fresh subagent), each against the evidence files, not against your summary of them. Give the reviewer the files and ask for a table of findings with a concrete replacement for each. Apply every must-fix; take should-fix unless you can say why not.

## 1. Script review (before voicing)

Prompt shape:

> You are the accuracy reviewer for a narrated explainer about <topic> for <audience>. Decisions already made: <framing rules, e.g. the narrator never says "proved" in its own voice>. Review `script/script.json` line by line against: <primary source>, <decode with source/background/reading labels>, <status snapshot>. For each line give a verdict (ok / fix / optional), the problem, and a replacement of similar length in plain spoken English. Check specifically: <numbers and dates>, <claims that are the source's analogy, not a theorem>, <anything only the author can vouch for>, <time-sensitive status lines>. Also list the on-screen labels and footnotes the visuals need for honesty. Keep the total word count within 5% of the current one.

What it caught last time:
- Past tense implying a result: "nobody could prove it" suggests someone now has. Fixed to "checking trillions isn't proving it for every one".
- Narrator-voice attribution leaks: "Claude suggested ..." must be "he says Claude suggested ...". Attribution doesn't carry across two sentences when heard.
- Superlatives: "the first major proof ..." became "one of the first ..." once a counterexample surfaced.
- Overcounting: "six separately written checkers" became "six independent checkers", the wording the sources actually use.
- A clause that sounds backwards aloud ("opposite signs can't cancel") was cut instead of explained.

## 2. On-screen review (after building, before the final render)

The reviewer can't watch video. Give it the scene source files and one still per narration line (`node scripts/stills.mjs` writes `out/lines/` and `out/linesheets/`).

Prompt shape:

> Review the ON-SCREEN text and visual claims. Read every scene file (visible strings live in JSX text, string constants and SVG text) and look at every still. Flag: factual errors or claims stronger than the evidence; missing honesty labels from the brief; wrong numbers, notation, axis labels or function names; a still that contradicts its caption; text under the captions, clipped or illegible; hard-coded status text that should come from status.json. Output a table: severity (must-fix / should-fix / nit), file:line or still filename, the issue, and the exact replacement. Don't edit files.

What it caught last time:
- A data bug: a filter dropped the prime 3 from a last-digit count (19,664 shown instead of 19,665).
- A headline ("41 days") overread a timeline the narration had already softened.
- Kickers stating things the narration had been fixed to avoid ("What nobody has yet" vs "What's still missing").
- A chart titled "Generalized RH" over an even split of last digits, which is already proven; it needed "even split: proven, GRH: how fast the gaps shrink".
- A "½" glyph that rendered as a smudge in a mono font; use "1/2".
- Honesty captions at 15 px that nobody could read; 21 px minimum.

## 3. Final checks you do yourself

- Transcribe the final mix (`python3 scripts/check_audio.py --file out/explainer.mp4`) and diff it against the script.
- Re-read live status sources and update status lines (live-claims.md).
- Re-check any "first", "only", "never" claim against what you've read since writing it.
