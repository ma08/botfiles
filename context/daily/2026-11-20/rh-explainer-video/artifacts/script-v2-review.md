# Accuracy review of script-v2.json (v2.1)

Reviewed 2026-11-20 against `remark.txt`, `research-math-decode.md`, `research-reconcile-lean-decode.md`, `research-lean-archive.md`, `verify-result.json`, and `verification-status-snapshot-2026-11-20-1pm.md`. Nothing was re-fetched from the web. The status page was not re-read, so every status line is still as of 11:45am PST.

Verdicts: **ok** (leave), **fix** (must change before voicing), **optional** (better, not required).

## Word count

- Current, with status lines filled: 689.
- With all "fix" replacements below: 713 (inside the 655 to 723 window).
- With every "optional" replacement too: 727. If you take all of them, also cut "Here's why that matters." (s04) and "So what did he post?" (s10). That brings it to 718.

## Lines that must change (short list)

| Line | Problem in one phrase |
|---|---|
| s03 L4 | "nobody could prove it" (past tense) implies someone now has |
| s08 L4 | "Claude suggested" is asserted in narrator voice; "primes up to X" drops "sum" |
| s09 L1 | "a new proof of Weil's theorem" asserted as fact; the "opposite signs can't cancel" clause sounds backwards and is unverified |
| s09 L2 | "As far as anyone has found" is stronger than two forum participants |
| s09 L3 | our own reading presented as fact; "What is:" is awkward aloud; left side unexplained |
| s11 L2 (status.json) | "the afternoon" does not match the 11:45am check time |
| s11 L3 (status.json) | "a few of the slower checks" hides that the awaited comparator run is the one pending |
| s11 L4 | "the work ran from" overreads the timeline; second sentence loses its attribution |
| s12 L1 | "What nobody has yet is understanding" contradicts the note (Alpöge has part of it) |
| s12 L4 | "The key idea is" needs attribution |
| s12 L5 | presupposes it is a proof; "before any person understood it" is too absolute |

## Line by line

### s01_claim

**L1. "On November 20th, 2026, the number theorist Levent Alpöge, who works at Anthropic, posted a short note."** ok.
The affiliation is in the right place: first sentence, before the claim, stated flatly. The note supports it indirectly ("our leadership", "messaged Dario", "my miraculous colleagues") and the press reports say it directly. "Short note" is fair for four pages.

**L2. "He says that he and Claude have found a proof of the Riemann Hypothesis, and of a broader version, written entirely in Lean, a language computers can check."** optional.
Two small things. The note says "I believe I have", so "he says he believes" is closer. And "written entirely in Lean" hangs ambiguously off "a broader version"; what the note says is that he chose to release only Lean. For fairness it also helps to say once that Claude is Anthropic's product. "A broader version" is fine in speech as long as the screen says which one (see labels).
Replacement: "He says he believes that he and Claude, Anthropic's AI, have proved the Riemann Hypothesis and a broader version. He released it only as Lean code, which computers can check." (30 words, was 28)

**L3. "Here's what that means, and what's been checked."** ok.

### s02_primes

**L1. "Start with the primes. Two, three, five, seven, eleven."** ok.

**L2. "Count them up to any number x, and you get a staircase. A smooth curve tracks it closely."** ok.
The curve must be li(x) on screen. If the animation draws x / ln x, the next line's number is wrong by a factor of about 37,000.

**L3. "Up to a trillion there are about 37.6 billion primes, and the curve misses by only about thirty-eight thousand."** ok.
π(10^12) = 37,607,912,018 and li(10^12) − π(10^12) = 38,263. Both are observed values and don't depend on RH.

**L4. "Does the fit stay that tight forever?"** ok.
Loose but fair. RH allows an error up to about √x · log x, which at a trillion is far more than 38 thousand, so "that tight" means "on that scale", not "that exact margin". No change needed.

### s03_zeros

**L1. "In 1859, Bernhard Riemann tied that question to one function, called zeta."** ok.

**L2. "It's built from the whole numbers, and it encodes the primes exactly."** ok.
Euler's product makes "encodes the primes exactly" literally true. No hedge needed.

**L3. "It has infinitely many zeros in a narrow strip of the complex plane. Riemann guessed they all sit on the strip's center line."** ok.
True as stated. It leaves out the trivial zeros, which are outside the strip, so nothing is wrong. "Narrow" is fine for a strip of width one that runs forever.

**L4. "Computers have checked trillions. All on the line. But nobody could prove it for every one."** fix.
"Trillions" is right (more than ten trillion verified). The problem is "could": the past tense tells the listener that someone now can, which is a narrator-voice "proved".
Replacement: "Computers have checked trillions. All on the line. But checking trillions isn't proving it for every one." (17, was 16)

### s04_music

**L1. "Here's why that matters. Each zero adds a wave, and the waves together rebuild the prime staircase."** ok, with a label.
The clean formula is for ψ(x), which counts prime powers weighted by log p. Riemann's own formula does the same job for the plain count with more bookkeeping, so the sentence is not false. If the animation sums waves into a staircase, label the staircase as the weighted count.

**L2. "A zero's distance from the line sets how loud its wave can get."** optional.
Correct in substance: a zero with real part β gives a wave of size x^β. "Can get" is vague, and only the zero to the right of the line is louder (its mirror image on the left is quieter).
Replacement: "The farther a zero sits to the right of the line, the louder its wave grows." (16, was 13)

**L3. "All on the line means no wave drowns out the rest, and the error stays near the square root of x."** ok.

**L4. "The generalized version says the same for primes in patterns, like primes ending in 7."** ok.
Primes ending in 7 are primes that are 7 mod 10, which is exactly a Dirichlet-character question. This example fits the Dirichlet-only scope of what was released, so it does not oversell.

### s05_parallel

**L1. "There's a parallel world where this is already a theorem: polynomials over finite fields, where the question becomes counting points on curves."** ok.
It is an analogue with a different zeta function, and "parallel world" carries that.

**L2. "André Weil proved it there in the 1940s. Pierre Deligne went much further in 1974."** ok.
"It" refers to the curve version just described, which is what Weil proved (announced 1940 to 1941, full proofs 1948). Deligne's 1974 paper covers varieties of any dimension. Accurate.

**L3. "And in 1969, Sergei Stepanov found an unusually elementary proof."** optional.
Stepanov's 1969 proof handled particular families of curves. Bombieri (1973) extended it to all curves. As written, a listener hears "an elementary proof of Weil's theorem".
Replacement: "And in 1969, Sergei Stepanov found an unusually elementary proof for certain curves." (13, was 10)

### s06_stepanov

**L1 to L4.** ok.
"Helper polynomial", "zero many times over", "only so many roots, counted with multiplicity" and "multiplicity comes from derivatives" are all sound simplifications of the method.

### s07_wall

**L1. "That's where the integers push back."** ok.

**L2. "You can differentiate a polynomial. You can't differentiate the number seven."** optional.
A careful viewer will reply that the derivative of seven is zero. That is in fact the real obstruction (every derivation on the integers is zero), and saying so is just as punchy.
Replacement: "You can differentiate a polynomial. Differentiate the number seven and you just get zero." (14, was 11)

**L3. "Alpöge names exactly this gap."** ok.
The note: multiplicity is "hard to find over the integers, corresponding to something like differentiating whole numbers".

### s08_ladder

**L1. "His note describes a way around it."** ok.
The note gives a few sentences, not a description of a method. "Describes" is at the edge of fair; "points to" would be safer if you want it. Not required.

**L2. "A theta lift carries a highly symmetric object from one group of symmetries to another."** ok.
Standard background, not from the note. Don't add "larger group" in the visuals: the note only says "between totally definite unitary groups".

**L3. "According to the note, each lift mimics one more order of multiplicity. Chain them into a ladder, and every rung buys one more."** ok.
Attributed, and "mimics" is the note's own word. Nothing in the Lean that we read confirms or refutes this analogy.

**L4. "For primes up to X, Claude suggested about the square root of X rungs."** fix.
Two issues. The note's object is "the von Mangoldt sum of length X", a weighted sum over primes, not a set of primes. And "Claude suggested" is stated as fact in the narrator's voice. The "According to the note" in the previous line doesn't carry across two sentences when heard.
Replacement: "For a sum over primes up to X, he says Claude suggested about the square root of X rungs." (19, was 14)
Keep any √X counter in the animation tied to this quote. The Lean has a parameter of about that size, but it is not shown to be the chain length (reconcile memo 2.6).

**L5. "Alpöge says that line alone should make mathematicians fall out of their chairs."** ok.
Fair paraphrase of "one line which will suffice to make fellow mathematicians fall out of their chairs".

### s09_toy_and_end

**L1. "The ladder grew out of a toy he worked out first: a new proof of Weil's theorem using only signs, where two quantities with opposite signs can't cancel."** fix.
The narrator asserts that a new proof of Weil's theorem exists. It is unpublished, unverified, and the note gives it in one dense footnote. It needs "he says", and "unpublished" is a plain fact that does the hedging honestly. "Worked out first" is also shaky: the timeline dates it to October 19 or later, after other entries.
The clause "two quantities with opposite signs can't cancel" should go. Heard aloud it sounds backwards, since opposite signs are exactly what a lay listener expects to cancel. It compresses the note's "opposite signs meaning no cancellation of inverse roots", which sits in a footnote nobody on this task has decoded, so the mechanism is unverified too. "Uses nothing but signs" keeps the hook without explaining something we can't stand behind.
Replacement: "He says the ladder grew out of a toy: his new, unpublished proof of Weil's theorem that uses nothing but signs." (21, was 28)

**L2. "As far as anyone has found, that toy isn't in the formal proof."** fix.
The evidence is two participants in one Zulip thread, read second-hand, plus our own search finding no "Stepanov" and no literal "qN". The archive also has a 7,051-file directory named `WeilBound` that nobody on this task has opened. "As far as anyone has found" claims a broader search than that.
Replacement: "Early readers on the Lean forum report they can't find that toy in the released code." (16, was 13)

**L3. "What is: at the very end, a classical argument of Landau's turns a one-sided bound on a smoothed prime count into this: no zero lies right of the line."** fix.
Three problems.
1. "What is:" followed by a second colon is hard to parse by ear.
2. The Landau ending is our own reading of a handful of files, with one link in the trace established by import only. It should be marked as what we could read.
3. "No zero lies right of the line" is correct for what the Landau step gives (zeta and each family of Dirichlet L-functions, per the Lean), but a lay listener will ask about the left side. The answer is the functional equation's mirror symmetry, and it takes four words.
Replacement: "What we could read is the ending. A classical argument of Landau's turns a one-sided bound on a smoothed prime count into a ban on zeros right of the line. Symmetry covers the left." (34, was 29)
The screen should carry the two details the sentence drops: the count is weighted, and the step is applied to zeta together with families of Dirichlet L-functions (see labels). Don't say "never overshoots": on the main path the bound is only shown on long windows of x.

### s10_box

**L1. "So what did he post? Seventeen million lines of Lean, in 175,000 files, without a single comment."** ok.
Measured by us: 17,374,215 lines, 175,187 files, zero comment markers.

**L2. "At the top, five short theorems. One states the Riemann Hypothesis exactly as Lean's shared math library defines it."** ok.
`Main.lean` has five theorems, and `RiemannHypothesis` there is Mathlib's definition (our scan, and Sutherland's page says the same). Put the word "Mathlib" on screen.

**L3. "The real target is the generalized version. The original falls out as a corollary."** optional.
The corollary part is read verbatim from the Lean. "The real target" is our framing; the note presents RH first and says the method "extends". A more literal wording avoids arguing with the author.
Replacement: "In the code, the generalized version comes first. The original falls out as a corollary." (15, was 14)

**L4. "A text search finds no shortcuts: no unfinished steps, no extra axioms."** optional.
True for our scan (zero `sorry`, `axiom`, `native_decide` and similar tokens). A text search can't rule out every shortcut, so "declared" is the honest scope, and "our own" says whose search it was.
Replacement: "Our own text search finds no declared shortcuts: no unfinished steps, no added axioms." (14, was 12)

### s11_checks

**L1. "Within hours, others were checking."** ok.

**L2. "As of {asof_spoken}, independent checks report that every file compiles, the main theorems rest only on Lean's three standard axioms, and a second, independently written checker accepts the whole proof."** fix (data, not the sentence).
The three claims match the snapshot: 175,187 of 175,187 modules compile, the five main theorems use only `propext`, `Classical.choice` and `Quot.sound`, and nanoda accepts the full export. The problem is `asof_spoken`, "the afternoon of November 20th". `status.json` itself says the check time is 11:45am PST, and the snapshot's content times are 11:45am and about noon.
Fix, either one:
- Set `asof_spoken` to "late morning Pacific time on November 20th" (7 words, was 5), or
- Re-read Sutherland's page before render and set all three of `checked_at_pst`, `asof_spoken` and `asof_onscreen` from that reading.

Also note that nearly all of this comes from one person's page, with several others reporting a clean compile. "Independent checks report" is acceptable. The existing footnote ("Checks by Andrew Sutherland (MIT) and others. Some run with AI assistance; verdicts come from the proof checkers.") must be on screen during this line, not just in the credits.
The sentence runs about 35 words in one breath. If it sounds rushed, split after "compiles".

**L3. "{pending_spoken}" = "A few of the slower checks are still running."** fix (data).
What was pending is specific: the end-to-end comparator run and Lean's own kernels on the export. The comparator run is the one the Lean community said it was waiting for, so "a few of the slower checks" makes the open item sound like a formality.
Replacement for `pending_spoken`: "The end-to-end comparison run that Lean experts are waiting on is still going." (13, was 9)
If the comparator has finished by render time, this line must be rewritten from the page, pass or fail. Don't ship the old sentence.

**L4. "Per the note, the work ran from October 6th to November 16th. Alpöge supplied the guiding idea, and Claude outpaced him on the machinery."** fix.
First sentence: October 6 and November 16 are the first and last dates in a "rough timeline Claude provided". The note also talks about "recent months" together and plans going back to his student days. So the timeline runs between those dates; "the work ran from" says more than the note does.
Second sentence: by ear, "Per the note" doesn't reach it, and the division of credit is the one thing in this story that only Alpöge can vouch for. The archive can't show who wrote what. It must be "Alpöge says". "On the machinery" is our gloss; the note's words are "far outpaced me near the finish line".
Replacement: "The note's timeline runs from October 6th to November 16th. Alpöge says he supplied the guiding idea, and that Claude far outpaced him near the finish." (26, was 24)

### s12_next

**L1. "What nobody has yet is understanding. No human-readable proof has been released, and Alpöge expects the argument to shrink a lot."** fix (first sentence only).
"Nobody has understanding" is too absolute. Alpöge says he supplied the guiding idea and has not yet "mastered a massive neighbourhood" around the argument, which is partial understanding, not none. What is missing publicly is an explanation.
"No human-readable proof has been released" is right, and correctly avoids saying none exists (he mentions generating a 250,000-page document). "Expects the argument to shrink a lot" is a fair reading of "massively simplified, likely immediately".
Replacement: "What's still missing is an explanation people can follow. No human-readable proof has been released, and Alpöge expects the argument to shrink a lot." (24, was 21)

**L2. "Three takeaways."** ok.

**L3. "The Riemann Hypothesis is about how regular the primes are."** ok.

**L4. "The key idea is a stand-in for derivatives of whole numbers."** fix.
Narrator voice states what the key idea of an unread proof is. It is the note's account, and nothing we read in the Lean confirms it.
Replacement: "The note's key idea is a stand-in for derivatives of whole numbers." (12, was 11)

**L5. "And this may be the first great proof a machine checked before any person understood it."** fix.
Two problems. "The first great proof" takes for granted that it is a proof; "may" attaches to "first", not to "proof". And "before any person understood it" runs into the same objection as L1.
On precedent: with the right wording the claim survives. The four colour theorem (1976) and the Kepler conjecture (Hales 1998, formal check finished 2014) were proofs humans designed and understood in outline, with the computer doing casework, and the formal checks came years after the human proofs. The large SAT-solver results (for example Boolean Pythagorean triples, 2016) were machine-found and machine-checked with no human-readable case analysis, but they are finite searches whose strategy is fully understood, and nobody would call them the proof of a central conjecture. So "first major proof checked by machine before anyone could explain it" is defensible with "may" and a condition. "Before any person understood it" is not.
One gap in this check: it covers the older history only. The note itself mentions 2026 AI results from OpenAI (an Ehrhart conjecture result, a "Siegel argument"), and nothing in the evidence folder says how those were checked or explained. So "first" is unverified against this year's AI-assisted results. "May" has to stay. If you don't want to check, "one of the first major proofs" is the safer wording.
Replacement: "And if it holds up, this may be the first major proof a machine checked before anyone could fully explain it." (21, was 16)

## Checks requested that came back clean

- Numbers and dates: 37.6 billion, 38 thousand, trillions of zeros, 1859, Weil 1940s, Deligne 1974, Stepanov 1969, 17 million lines, 175,000 files, five theorems, October 6 to November 16 as timeline endpoints. All match the evidence.
- "It encodes the primes exactly", "infinitely many zeros in a narrow strip", "primes ending in 7", "exactly as Lean's shared math library defines it", "the original falls out as a corollary", "without a single comment": all supportable.
- No line contains a flat "solved" or "proved" in narrator voice once s03 L4, s09 L1 and s12 L5 are fixed.

## On-screen labels and footnotes needed for honesty

1. **s01:** "Generalized Riemann Hypothesis, for Dirichlet L-functions" when "a broader version" is spoken. The number-field version (which the note calls ERH) is not claimed.
2. **s02:** label the curve "li(x), the logarithmic integral". Show exact values if space allows: 37,607,912,018 primes; li(x) − π(x) = 38,263 at x = 10^12.
3. **s03:** "Checked numerically: more than 10 trillion zeros". Makes clear that "checked" is computation, not proof.
4. **s04:** if waves sum to a staircase, label it "ψ(x): primes and prime powers, weighted by log p". Under the GRH line: "primes ending in 7 = primes that are 7 mod 10".
5. **s05:** "Weil: curves over finite fields. Deligne: all dimensions. Stepanov: certain curves; Bombieri 1973, all curves."
6. **s08:** a visible quote mark or "from the note" tag on the ladder and on the √X counter. Tag the theta-lift picture "schematic". Label X as "length of the prime sum (von Mangoldt sum)".
7. **s09:** on the toy, "Author's account. Unpublished. Reported absent from the released Lean (Lean Zulip, Nov 20)". On the Landau step, "Our reading of the released code, simplified", plus "smoothed, weighted prime sum" and "applied to zeta and to families of Dirichlet L-functions". If you show the formula, use Gz(x) = Σ_{n≤x} Λ(n)(x/n − 1) − x log x + (1 + γ)x and caption it "the zeta-only version".
8. **s10:** "17,374,215 lines, 175,187 files (our count)". "Mathlib" next to "Lean's shared math library". "Text search: 0 sorry, 0 axiom, 0 native_decide (our scan; not a substitute for the kernel checks)". If any dependency chain is drawn, mark it "simplified".
9. **s11:** the `asof_onscreen` timestamp, visible for the whole status beat. The existing footnote about Sutherland and AI assistance. One more line: "A pass relies on the checkers and on Mathlib's definitions." List the pending items by name (comparator end to end; Lean kernels on the export). Tag the credit split "per Alpöge's note".
10. **s12:** "No human-readable proof released" (not "exists").

Keep off screen, per section 4.2 of the reconcile memo: the ingredient-to-directory map, any claim that named literature results "were formalized", m ≈ √x as the chain length, "weak Vandiver proved", and who wrote which part of the code.

## Other notes

- **Re-check gate.** s11 L1 to L3 and the s09 L2 report are all time-sensitive. Re-read Sutherland's page and the Zulip thread immediately before the final render and regenerate `status.json`.
- **Pronunciation.** "Alpurgay" for Alpöge is a low-confidence respelling (reconcile memo 5.1). Try to confirm from a recording of him before voicing; the name is spoken five or more times.
- **"We" in s09 L3.** The replacement uses "we" for the video's makers. If the narrator has no "we" elsewhere, use "What can be read so far is the ending."
