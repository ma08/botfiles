# Reconciliation memo: math decode vs. the Lean archive and the verification snapshot

Written 2026-11-20, 12:17pm PST, for the scriptwriter. It supersedes `research-math-decode.md` wherever the two disagree. No final script here: audience and framing are still pending.

## Labels

- **[VERBATIM-LEAN]** I read this text in a file extracted from the archive. Path given each time.
- **[STATUS-PAGE]** From `verification-status-snapshot-2026-11-20-1pm.md` (Sutherland's page and the Lean Zulip thread, read first-hand by the main session). Time-sensitive. Note the file's title says "~1:00pm PST", but its contents are earlier: the page was last updated 19:45 UTC (11:45am PST) and Zulip was read about noon. I key every status line to those content times.
- **[NOTE]** Alpöge's four-page note says it.
- **[BG]** Standard background mathematics.
- **[READ]** My interpretation.

Three words I keep apart on purpose, because the brief blurred them:

- **defined**: a `def X : Prop := ...` exists. That is a statement, not a proof.
- **proved**: a `theorem ... : X` exists somewhere in the archive (found by grepping all 175,190 files).
- **on Main's path**: I traced identifiers from `Main.lean` to it. This is an identifier and import trace, not a kernel dependency extraction. Only Lean itself can give the true dependency cone.

## Where the evidence is

All in the original working folder (not included here; the extracted Lean files are the author's code and the grep passes were large local outputs):

- `lean-verify/extracted/`: the eight files the main session extracted.
- `lean-verify/reconcile-evidence/earlier-extract/`: 18 files from the earlier static scan that I quote here (copied out of the session temp folder so they survive).
- `lean-verify/reconcile-evidence/pass6-extract/`: all 14 files of `Formalism/BehrendSets/`.
- `lean-verify/reconcile-evidence/pass7-extract/`: 7 more chain files (`Window.lean`, `Analytic.lean`, `TopPlug.lean`, `RiemannHypothesisOfPowerBound.lean`, and others).
- `lean-verify/reconcile-evidence/pass6.py`, `pass7.py`, `pass6_hits.json`, `pass7_hits.json`: two new full-archive grep passes (each streamed all 175,190 tar members) and their hit lists. Every "N hits" claim below comes from these.

Nothing was compiled or executed. Paths below are relative to `lean/src/`.

---

## 1. The analytic endgame

### 1.1 The smoothed sum, verbatim

**[VERBATIM-LEAN]** `Formalism/Statement.lean`:

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

In ordinary notation:

> G(χ, x) = Σ_{n ≤ x} Λ(n)·(1 + Re χ(n))·(x/n − 1) − x log x + (1 + γ + Re L′/L(1, χ))·x

**[VERBATIM-LEAN]** `Formalism/StatementOC.lean` splits this into a zeta part and a character part:

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

So `G χ x = Gz x + Gchi χ x` (by unfolding; I didn't find that identity stated as a lemma, so treat it as [READ], though it is immediate).

`Gz` is, term for term, the expression in the note's item 5:

> Σ_{n≤X} Λ(n)·(X/n − 1)₊ − X log X + (1 + γ)·X   **[NOTE]**

This match is exact and is the one solid bridge between the note and the Lean. **[BG]** `Gz(x)` equals −Σ_ρ x^ρ/(ρ(ρ−1)) plus bounded terms, so "Gz(x) is at most about √x" is an RH-strength statement.

### 1.2 Three versions of the Landau step, and which ones are proved

The archive contains the same idea ("a one-sided power bound on the smoothed sum forces a zero-free half-plane") in at least three forms. They differ in what is bounded, in which direction, and in whether a proof exists.

**(a) The `G(χ, x)` form in `Statement.lean`: defined, no proof found.**

**[VERBATIM-LEAN]** `Formalism/Statement.lean`:

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

Direction: a **lower** bound, G(χ, x) ≥ −C·x^(1/2+ε). `LandauStep` and `LandauStepEps` in the same file have the same shape with a general σ₀, for a nontrivial real-valued χ, with the extra hypothesis that L(σ, χ) ≠ 0 for real σ in (σ₀, 1).

Status: the identifiers `LandauStep`, `LandauStepEps` and `RHofG` occur **only in `Statement.lean`** in the whole archive (`pass6_hits.json`; the one other `RHofG` hit is the unrelated substring `HomPullRHofGood`). So these are stated and never proved or used under those names. The same holds for `OCStep`, `OCAvg` and `RiemannHypothesisOfLowerBounds` in `StatementOC.lean`. They read like early checkpoint statements that the development moved past. `Formalism/ZetaNonvanishing/Assembly.lean` does some work with `G χ` (`def Hf (σ₀ C) (x) := G χ x + C * x ^ σ₀`, `key_identity`), but it doesn't conclude `LandauStep`.

**Do not say "Statement.lean proves".** Say "Statement.lean defines G(χ, x)".

**(b) The zeta-only `Gz` form: proved.**

**[VERBATIM-LEAN]** `Formalism/StatementU.lean` (definition) and `Formalism/ZetaNonvanishing/ZetaLandau.lean` line 258 (`theorem zetaLandau : ZetaLandau`):

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

Direction: **either** sign (s₀ = ±1). A bound on Gz from above, or from below, by C·x^θ is enough. The proof body calls `landau_Z landauEq mellinSgen mellinElem zetaRealNonvanish`, i.e. a Landau-lemma argument on a Mellin transform, using that ζ has no real zeros in (0, 1).

**[VERBATIM-LEAN]** `Formalism/SizeWindowBrackets/PowerBoundGivesRiemannHypothesis.lean` (definition) and `.../ChainSlopeWindows/RiemannHypothesisOfPowerBound.lean` line 13 (`theorem riemann_hypothesis_of_power_bound : PowerBoundGivesRiemannHypothesis`):

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

Direction: an **upper** bound on Gz. The proof is 25 readable lines: `zetaLandauEps` gives ζ(s) ≠ 0 for Re s > 1/2, then `riemannHypothesis_of_zero_free_halfPlane` (functional equation) gives Mathlib's `RiemannHypothesis`.

Also proved, same directory: `theorem proposition_final : GrowthBoundGivesRiemannHypothesis` (`ChainSlopeWindows/LipschitzWeightAndMinimum.lean` line 663). Its hypothesis, `GrowthInequalityDataExists C ε x`, bundles a long list of inequalities about arithmetic data over a finite abelian group `H`, and yields `Gz x ≤ x ^ (1/2 + (C+3)·ε)`.

Is (b) on Main's path? **Not shown.** `riemann_hypothesis_of_power_bound` has one user outside `SizeWindowBrackets` (`Formalism/SharpRestriction/GlobalSchurBounds/RamificationTwoAndConjugationAtQAndD.lean` line 1006), which I did not read. This track proves RH directly, for ζ alone, whereas `Main.lean` gets RH as a corollary of GRH. [READ] It looks like the RH-only version of the argument, kept alongside the later GRH version. Treat it as "proved in the archive, not shown to be what Main uses".

**(c) The multi-character `Gm` form: proved in two variants; the windowed variant is the one on Main's path.**

**[VERBATIM-LEAN]** `Formalism/SharpRestriction/RamificationFrobenius/TotientGaloisClasses/ExplicitFormulaErrorOfHostConditions.lean`:

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

Here `Λ` is a `Level`: a finite set `KEPT` of primitive Dirichlet characters containing the trivial one and closed under inverse (`PrimePairSizeCondition.lean`). `Nt` is `KEPT` minus the trivial character. `gChi` is the character analogue of `Gz` (**[VERBATIM-LEAN]** `.../TotientGaloisClasses/Analytic.lean`: `sumLamChi χ y + (y : ℂ) * logDerivativeAtOne χ`). `ZeroFreeAbove θ` means every L(s, ψ) with ψ in `KEPT` is nonzero for Re s > θ.

So `Gm` is the zeta sum plus a positively weighted sum of the real parts of the character sums, over a finite family of characters. Direction: an **upper** bound.

Proved: `theorem zero_free_of_Chebyshev_growth (Lv : Level) : Lv.ChebyshevGrowthImpliesZeroFree` in `.../TotientGaloisClasses/Landau.lean` line 538 (that file imports `ZetaLandau`; I read only the first lines of the proof).

The form Main's path actually calls is a "windowed" variant. **[VERBATIM-LEAN]** `.../TotientGaloisClasses/Window.lean`:

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

That is: the bound `Gm x ≤ x^θ` need not hold for all large x. It is enough that it holds on windows [Y, Y^la] starting arbitrarily far out. The matching supply statement (**[VERBATIM-LEAN]** `.../TopWin.lean`, `ChebyshevInequalityOnWindows`) ends in

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

and `theorem level_of_tiedWin` (same file, 14 lines, read in full) combines the two to get `Λ.ZeroFreeLevel`, which is `ZeroFreeAbove (1/2)`.

Be precise about which lemma does what:

- `zero_free_of_Chebyshev_growth` (the all-large-x form) is called in `level_of_tiedAll` (`TopWin.lean` line 126). I did not trace `level_of_tiedAll` to Main.
- `level_of_tiedWin`, the one Main's path reaches, takes the windowed form as a hypothesis `hB : Λ.FormBAt la`. That hypothesis is supplied by `UpperTheory.Comparison₂.formB` (call site in `ZeroFreeAllOfTopG.lean` line 29). I did not read `formB`'s proof. Its type is fixed by the call site (`(Level.cyc ψ).FormB`), and since the archive compiles with no `sorry` or `axiom`, it is a proved statement. How it is proved (presumably from the same Landau lemma) is [READ].

### 1.3 The trace from `Main.lean` down to the Landau step

Each arrow is an identifier I read in the named file.

1. `Main.lean`: `theorem riemannHypothesis : RiemannHypothesis := rhOfAll`
2. `Supplements/Kernels/MainTheorems.lean`: `rhOfAll := Formalism.VW.rh_of_every allChi`, `allChi := UpperTheory.FinalTheorems.everyCharacter`
3. `Formalism/GammaFactorNonvanishing/CritLine.lean`: `rh_of_every` applies the GRH statement to the trivial character mod 1 (`LFunction_modOne_eq` turns it into ζ), then `rh_of_right` uses the functional equation. **RH is a corollary of GRH here.**
4. `.../CharacterBoxes/MainConclusion.lean`: `everyCharacter` comes from `every_character_of_literature_of_vWin` (the 814-line bridge file).
5. The bridge file (copy in `reconcile-evidence/earlier-extract/`, import at its line 189) imports `.../ThetaCorrespondence/FockModels/EveryCharacterE`, whose line 70 calls `plugAll (...) hV` (grep hit in `pass7_hits.json`; that file itself was not extracted). **This link is import plus identifier evidence only.** The bridge's proof term is three very long lines that I did not parse.
6. `.../CharacterBoxes/EveryCharacter.lean`: `plugAll := UpperTheory.Top.imprimitive (plugWin ...)` and `plugWin := zeroFreeAll_of_topG (la := 3 / 2) ...`. (`imprimitive` passes from primitive characters to all characters.)
7. `.../CharacterBoxes/ZeroFreeAllOfTopG.lean`: `zeroFreeAll_of_topG` calls `zeroFreeOn_of_tiedWin_cyc` with `level_gm_le_on_family_scales` (the upper bound on `Gm`) and `Comparison₂.formB` (the windowed Landau step).
8. `.../TopWin.lean`: `zeroFreeOn_of_tiedWin_cyc` → `level_of_tiedWin`, applied to `Level.cyc ψ`, the cyclic group of characters generated by ψ.

Not read: the proof of `Comparison₂.formB`, and everything upstream of `level_gm_le_on_family_scales` (which is where the theta lifts, Galois representations and the rest of the 17 million lines feed in).

### 1.4 "How the proof ends": lines the script can rely on

**Plain English (one sentence), grounded in 1.2(c) and 1.3:**

> The formal proof ends with a classical move that goes back to Edmund Landau: it shows that, on long stretches of x arbitrarily far out, a smoothed, weighted count of primes does not overshoot its expected value by much more than the square root of x, and that one-sided bound alone forces the zeros of zeta and of every Dirichlet L-function out of the region to the right of the critical line.

Shorter variant for narration:

> In the end, everything funnels into one inequality: over long stretches, arbitrarily far out, a smoothed count of primes doesn't run more than about a square root above its prediction. An old argument of Landau turns that single one-sided bound into the Riemann Hypothesis.

("Never overshoots" would be wrong for Main's path: the bound is only established on windows. The zeta-only track in 1.2(b) does use an all-large-x bound.)

**Slightly more technical:**

> For each primitive Dirichlet character ψ, the Lean forms Gm(x) = Gz(x) + Σ w_ξ · Re g_ξ(x), summed over the nontrivial characters ξ in the cyclic group generated by ψ, where Gz(x) = Σ_{n≤x} Λ(n)(x/n − 1) − x log x + (1 + γ)x and g_ξ is its twist by ξ. It proves Gm(x) ≤ x^(1/2 + cε) on arbitrarily long windows of x, for every small ε. A Landau-type lemma (Mellin transform of a function of one sign) then gives L(s, ξ) ≠ 0 for Re s > 1/2 for every character in the family. An Euler-factor argument extends this to imprimitive characters, which is the GRH statement in `Main.lean`. RH follows by taking the trivial character and applying the functional equation.

**What each sentence rests on:**

| Claim | Basis |
|---|---|
| The sum is Gz, and it matches the note's item 5 | [VERBATIM-LEAN] `StatementOC.lean`; [NOTE] item 5 |
| One-sided upper bound on Gm implies zero-free half-plane | [VERBATIM-LEAN] statements `ChebyshevGrowthImpliesZeroFree` and `FormBAt`. The all-x form is proved by `zero_free_of_Chebyshev_growth` and used in `level_of_tiedAll`. The windowed form `FormBAt` is what `level_of_tiedWin` (on Main's path) consumes; it is supplied by `Comparison₂.formB`, whose proof I did not read |
| The bound has exponent 1/2 + (const)·ε, on windows | [VERBATIM-LEAN] `ChebyshevInequalityOnWindows` in `TopWin.lean` |
| Primitive to all characters | [VERBATIM-LEAN] `UpperTheory.Top.imprimitive` (statement read, proof not) |
| GRH to RH | [VERBATIM-LEAN] `rh_of_every`, `rh_of_right` |
| "Landau" as the name of the idea | [VERBATIM-LEAN] file and lemma names (`Landau.lean`, `zetaLandau`, `LandauLemma`); [BG] it is the standard Landau lemma on Dirichlet integrals with coefficients of one sign |
| "This is what Main uses" | Identifier trace in 1.3, with step 5 by import only |

**Two things the script should not say here:**

- Not "bounds the error on both sides" or "square-root cancellation is proved directly". The Lean endgame takes a one-sided bound in, and gets the two-sided statement out through the zeros.
- Not "by Weil positivity". See 3.1.

---

## 2. The open ambiguities in section 8 of the decode

Verdict labels: **resolved-by-verbatim-read**, **suggested-by-names-only**, **unresolved**. The verdict is about what the Lean contains. Whether that is what the note meant is always [READ].

| # | Ambiguity | Verdict | Evidence |
|---|---|---|---|
| 1 | "Behrend": Felix or Kai? | **resolved-by-verbatim-read: Felix Behrend** (sets avoiding arithmetic progressions) | See 2.1 |
| 2 | "μ" in items 3 and 16 | **unresolved** | Nothing I read identifies it. Not searched for specifically, since "μ" is too generic to grep. |
| 3 | "> 1 − η" (item 6), "stop at 2/3" (item 14) | **unresolved** | No match found. Do not connect `la := 3/2` in `plugWin` to "2/3": it is a window exponent, and the resemblance is a coincidence until shown otherwise. |
| 4 | "Division" (item 14), "gcd" (item 15) | **unresolved** | Not investigated. |
| 5 | "Weyl" (item 9) | **suggested** (formula shape read verbatim, no name) | See 2.2 |
| 6 | GRH and ERH scope | **resolved-by-verbatim-read** | See 2.3 |
| 7 | Path quadric: x₁x₂ + x₂x₃ + ... or x₁x₂ + x₃x₄ + ...? | **unresolved** | No literal trace. The toy proof is reportedly not in the archive (item 8). |
| 8 | Toy proof of Weil and Deligne is itself unverified | **unresolved, and now reported absent** | [STATUS-PAGE] Zulip: two participants say the sign-only qN = M^k + R proof does not appear in the released Lean. Second-hand; I didn't verify it. Consistent with our scan: 0 hits for "Stepanov" and no literal "qN". `Development/WeilBound` (7,051 files) exists by name, but its contents were not read and the name alone proves nothing. |
| 9 | Weakening of Vandiver | **suggested-by-names-only** for the identification; the statement shape is verbatim | See 2.4 |
| 10 | Page 2 references (Ehrhart, Navier-Stokes, Sussman, Bałaban, ...) | **unresolved** | Outside the Lean. Unchanged: keep out of the video. |
| 11 | Bombieri, Schmidt, Hasse derivatives, Rankin, Kurihara are my additions | n/a | Still true. They are [BG], not [NOTE]. |
| 12 | "150 years" vs 1859 | n/a | Still use 1859. |
| new | The Iwasawa tower (items 11, 19) | **resolved-by-verbatim-read** that the Lean works in 2-power cyclotomic layers | See 2.5 |
| new | Chain length √X (item 8) | **unresolved** (a shape match exists; do not use) | See 2.6 |

### 2.1 Behrend

**[VERBATIM-LEAN]** `Formalism/BehrendSets/Statement.lean`:

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

Why this settles it:

- The size bound N·exp(−C·√(log N · log(K+1))) is the signature of Felix Behrend's 1946 construction. **[BG]**
- With (α, β, γ) = (1, 1, −2), which needs K ≥ 2, the condition says "no three-term arithmetic progression". `BehrendFree K` is a strengthening: no nontrivial solution to any three-term linear relation with coefficients summing to zero and of size at most K. So it is a bounded-coefficient generalization, not literally "3-AP-free". Say "Behrend-type sets", or "sets with no three-term progressions, in a strengthened form".
- `Formalism/FrobeniusOrbits/FrobeniusOrbitsProofs/ThickExists.lean` uses `Behrend.sphere`, `Behrend.map` and `Behrend.exists_large_sphere` (grep hits, `pass6_hits.json`). Those names are not defined in the archive: all 142 occurrences of "Behrend" sit in 17 files, the only namespaces opened are `Formalism.BehrendSets.*`, and no file declares a root `Behrend` namespace. Since every file is project code plus Mathlib, `Behrend.sphere` and `Behrend.map` must be Mathlib's, which is its formalization of Felix Behrend's construction. (The Mathlib file path, `Mathlib/Combinatorics/Additive/AP/Three/Behrend.lean`, is from memory.)
- Kai Behrend's trace formula for stacks has nothing to do with any of this.

Caveat: `BehrendBound` and `BehrendFree` occur only in `BehrendSets/Statement.lean` (plus `SpaceFree` variants in `StatementE.lean`). I did not find a `theorem ... : BehrendBound`. The construction that is actually carried out is the one in `ThickExists.lean`, under different names (`NoRel`). By my own three-way split: Behrend-type sets are **defined** (`BehrendFree`), a construction with Mathlib's Behrend sphere is **proved** (`ThickExists.lean`), and neither has been traced to **Main's path**. So: "Felix Behrend's construction is present in the archive" is safe. "The proof uses it" is very likely but not traced. "The Lean proves `BehrendBound`" is not established.

[READ] on the note's phrase "precise choice of the Iwasawa tower, specifically using Behrend": the same file defines, right above `BehrendFree`,

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

and Frobenius elements `frob s l` in it. **[BG]** (Z/2^(s+2))ˣ/±1 is the Galois group of the real 2^(s+2)-th cyclotomic field over Q, cyclic of order 2^s. So the Behrend-type "thick" sets are subsets of the Galois group of a layer of the 2-power cyclotomic tower, chosen so that Frobenius orbits meet them rarely (`WindowTwo`: at most 2 hits per window). That fits the note's phrase well. It is still my reading of how the pieces relate.

### 2.2 Weyl

**[VERBATIM-LEAN]** `Formalism/BehrendSets/StatementE.lean`:

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

**[BG]** A Vandermonde product divided by ∏ i! is the Weyl dimension formula for an irreducible representation of U(r). The same file's `CountIdentity` compares `mass (k+m−1) · ∏ dimV(w ρ)` with `mass k · ∏ dimV(u ρ)`, where `mass` obeys a recursion with factors `(r−1)! · (v/π)^r`. That is the shape of a mass formula for unitary groups times Weyl dimensions, with `m` steps between rank k and rank k+m−1. This is the closest thing I found to item 9's "Chowla-Selberg, Weyl, and Siegel mass". The name "Weyl" does not appear, and I didn't check where `CountIdentity` is used. So: the dimension-formula reading (my original guess) is now supported by a formula read verbatim, not confirmed.

### 2.3 GRH and ERH scope

**[VERBATIM-LEAN]** `Statements.lean` (whole file is 16 lines). The four GRH-type statements all quantify over `(N : ℕ) [NeZero N] (χ : DirichletCharacter ℂ N)` and use Mathlib's `DirichletCharacter.LFunction`. For example:

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

So "GRH" here means: all Dirichlet L-functions, every modulus, every character. No Dedekind zeta functions, no Hecke L-functions. **[STATUS-PAGE]** Sutherland's page says the same. **[NOTE]** ERH is described as expected "with more time", so it is not claimed. Convention A of the decode (GRH = Dirichlet, ERH = number fields) is the one in force.

### 2.4 The Vandiver-like step

**[VERBATIM-LEAN]** `Development/AutomorphicArithmetic/CharacterBoxes/ExistsPageN.lean` (quoted in `research-lean-main-statements.lean`, section 12):

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

What is verbatim: `VWin` is a hypothesis of the final assembly (`plugWin (hG) (hV : VWin) ...`), and it is discharged by a theorem (`vwin_of_row`), not assumed. Its content is: for certain number fields E, a quantity `shaLen` indexed by a prime and an integer twist e is finite for 0 < e < t, and Σ_l log l · Σ_e shaLen ≤ B. In use, t is about x^401 and B is √(exp(x^ε)) (`VAt`).

What is name-only: that `shaLen` is the length of the cohomology group in the note's item 17, H¹(o_E[1/ℓ], Q_ℓ/Z_ℓ(−e)). The namespace is `Formalism.GaloisCohomology` and the twist index e matches, but I never read the definition of `shaLen`. And "V" standing for Vandiver is a guess.

So for the script: "the proof needs, and the Lean contains a proof of, a quantitative bound on certain Galois cohomology groups in a tower of cyclotomic fields" is supportable. "The Lean proves a weak form of Vandiver's conjecture" is the note's description [NOTE], not something I confirmed in the Lean. `grep` finds 0 occurrences of "Vandiver".

### 2.5 The tower

**[VERBATIM-LEAN]** same file:

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

Reading the Galois condition: E is the subfield of a cyclotomic field fixed by the automorphisms ζ ↦ ζ^a with a ≡ ±1 mod 2^(e+2), ψ(a) = 1, and a a square modulo two auxiliary primes q and d. **[BG]** So E is the compositum of the real 2^(e+2)-th cyclotomic field, the field cut out by ψ, and two quadratic fields. `PageN` ties the level to x: 2^e is about x^(2+8ε). `WinPair` requires q ≡ 3 mod 8 and d ≡ 7 mod 16.

Resolved: the Lean's tower is the **2-power cyclotomic tower** (the cyclotomic Z₂-extension of Q, in [BG] terms), climbed to a height that grows with x. This is the first concrete answer to "which tower". That it is what items 11 and 19 call "the Iwasawa tower" is [READ], and a natural one: the cyclotomic Z_p-extension is the original Iwasawa tower. Note the archive directory named `IwasawaDecomposition` is unrelated (see the archive scan).

### 2.6 Chain length √X: a tempting match to leave alone

**[VERBATIM-LEAN]** `Formalism/SizeWindowBrackets/GrowthBoundGivesRiemannHypothesis.lean`, inside `SizeWindows`:

```text
[verbatim Lean excerpt omitted from the public copy. The archive is the author's work, published via https://alpo.ge/remark.pdf; the prose around this block describes what it says.]
```

So a natural-number parameter `m` of size about √x sits in the size conditions of the RH-only endgame, and `m` indexes `w : H → Fin m → E0 × H → ℝ`. The directory is called `ChainSlopeWindows` and a predicate on Main's path is called `ChainTied`. It is tempting to say "there is the chain of length √X". I can't support that: I don't know what `m` counts, this file is the track not shown to be on Main's path, and "Chain" in a machine-generated name is weak evidence. **Keep off screen.** If the user wants it checked, the place to look is where `SizeWindows` is instantiated (`SChain.lean`, `PChain.lean`, `FixedEpsilonConcreteGrowthBound.lean`).

---

## 3. Corrections to the decode and the draft script

### 3.1 Mathematical corrections

1. **Decode 3.4 and scene 9 ("a positivity test for the hypothesis due to Weil").** The Lean endgame that I can read is a Landau-type one-sided bound, not Weil's positivity criterion. "Guinand" has 0 hits in the archive. Weil positivity and W(·) ≥ 0 are in the note's timeline (items 4 to 6, dated Oct 6 to 8), so they are part of the story of how the idea developed [NOTE]. They should not be presented as how the formal proof works. [READ] The note's phrase "Guinand-Weil had the sign" (item 5) and the Lean's one-sided inequality may be the same observation, that one sign is enough. That is my guess and should stay out of the narration.
   - Suggested replacement for scene 9's first clause: "a classical lemma of Landau that turns a one-sided bound on a prime count into a statement about zeros".

2. **Decode 3.4, "the target is square-root cancellation in this smoothed sum".** Refine: the Lean's target is a one-sided bound of size x^(1/2+ε) on Gz plus a weighted character sum, holding on long windows of x. The two-sided square-root bound is a consequence of the conclusion (GRH), not the thing proved directly.

3. **Decode 1.3 and 3.8, 3.11.** Now sharper, per section 2: GRH is Dirichlet-only; Behrend is Felix; the tower is 2-power cyclotomic. Update those paragraphs' "unknown" markers accordingly.

4. **Decode 3.2 and unblocker 2 (the toy proof qN = M^k + R).** Add: reported **not formalized** in the released Lean [STATUS-PAGE, Zulip, second-hand]. The archive's proof of GRH therefore does not rest on it. It remains an unpublished, unverified claim, and now also one with no formal counterpart. If the video features it (it is a nice animation), it must be framed as the author's account of his starting intuition, with something like "this part isn't in the formal proof".

5. **Structure of the result.** The decode and the script say "a proof of RH" and that the method "extends" to GRH, following the note's order. In the Lean it is the other way round: **GRH for Dirichlet L-functions is the theorem, and RH is a short corollary** (trivial character mod 1, then the functional equation; `CritLine.lean` and `RhOfRight.lean`, about 60 lines of proof, fully readable). The note's timeline is consistent with this: GRH is the last entry (item 20, Nov 16). An RH-only assembly also exists in `SizeWindowBrackets` (1.2(b)), which fits "RH first on Nov 15, then GRH on Nov 16", but that sequencing is [READ].

6. **"Twenty steps" (scene 9).** Unchanged caution, with a new data point: the Lean's own structure does not follow the 20 items. The top of the chain speaks of theta lifts, Galois representations, a local-global compatibility "row", about 180 internal "literature" propositions, and the `VWin` cohomology bound.

### 3.2 Status corrections (all time-stamped; re-check before render)

As of the snapshot's content times (Sutherland's page updated 2026-11-20 19:45 UTC = 11:45am PST; Zulip read about noon PST; the snapshot file's "1pm" title is later than either):

7. **Scene 1, "It's a claim, not yet a confirmed result", and scene 11's final frame "Claimed. Not yet verified."** These are stale as written. The formal side now has substantial independent support [STATUS-PAGE]:
   - all 175,187 modules compile (Lean v4.33.1, Mathlib v4.33.1), zero errors;
   - `#print axioms` on the five `Main.lean` theorems shows only `propext`, `Classical.choice`, `Quot.sound`;
   - `leanchecker` kernel replay passes for 175,187 of 175,187 modules;
   - `nanoda`, an independent kernel written in Rust, accepts the full 61.57 GB export.

   Still open at snapshot time: the `comparator` run end to end (its statement comparison and axiom check had passed in one run), and Lean's default and paranoid kernels on the export. Two other checkers declined the input as unsupported, which is not a rejection.

   Since the framing decision is pending, three wordings the user can choose from:
   - *Conservative:* "As of [time], independent checks of the computer proof have all passed so far, and a few are still running. No human has yet read and understood the argument."
   - *Middle:* "Within hours, others had compiled the proof and re-checked it with an independent program. The machine side is holding up. What's missing is human understanding."
   - *Bold (only if comparator has finished and passed by render time):* "The computer proof has now been independently verified. What nobody has yet is an explanation a mathematician can follow."

   In every version the narrator should still avoid "the Riemann Hypothesis is proved" as a flat statement. A formal proof accepted by the kernels is very strong evidence, with the stated residual trust: the kernels, Mathlib's definitions, and the three standard axioms.

8. **Scene 11's checklist ("compile independently", "confirm the statement is RH", "no extra assumptions", "human-readable proof").** Three of the four boxes can now be ticked or half-ticked, with sources:
   - Compiles independently: yes [STATUS-PAGE].
   - Statement is really RH: `Main.lean` proves Mathlib's own `RiemannHypothesis` [VERBATIM-LEAN]; the page agrees [STATUS-PAGE]; comparator's statement check passed in one run, end-to-end run pending.
   - No extra assumptions: only the three standard axioms [STATUS-PAGE]; our scan found zero `sorry` and zero `axiom` tokens [our scan, `verify-result.json`].
   - Human understanding: no. No human-readable proof exists publicly; the archive has zero comments.

   The data-driven "as of" approach in the snapshot's last paragraph is the right design.

9. **"Formalized without assumptions" (decode section 5, scene 1's "checked line by line").** Was: the author's unverified claim. Now: independently supported as in item 7, comparator pending. It can move out of "he says" into "independent checks so far confirm", with the timestamp.

10. **Caveats that must travel with any status line** [STATUS-PAGE]: Sutherland's checks were run with Claude Code; the build was an unsandboxed cloud build using direct `lean` calls (a 77-module sample was byte-identical to a `lake build`); a pass relies on the kernels and on Mathlib's definitions meaning what they should. The video doesn't need all of that on screen, but "independently verified" without qualification would overstate it. Also worth one clause: the checks were themselves run with the help of the same AI system. That doesn't weaken a kernel verdict (the kernel is not Claude), but viewers will ask.

11. **Decode section 6, "acceptance would require" list.** Items 1 to 3 are now largely met. Item 4 (human understanding) and item 5 (time, publication) stand. The Clay-rules sentence is still from memory and still needs checking before use.

12. **Scene 10, "A written-out version runs past 250,000 pages".** Still [NOTE], from a half-joking footnote. We now have a measured number to put next to it or instead of it: 17,374,215 lines of Lean in 175,187 files. Prefer the measured one.

13. **Reaction context** [STATUS-PAGE, Zulip]: some formal-methods researchers urged caution about announcement timing and mentioned market context; moderators kept the thread technical. If the video touches the timing, the decode's instruction stands: the note says the timing is "horrible" and denies a cynical reading, and doesn't say what it coincides with. Don't fill that in from Zulip asides.

### 3.3 Things in the decode that the new evidence leaves intact

- All of section 1 (background), 2 (function fields, Stepanov), and scenes 2 to 7. Nothing in the Lean evidence touches them.
- The caution in scene 8 that "each lift mimics one order of multiplicity" is the note's analogy. The Lean confirms that theta lifts are heavily present (the key link is `galoisRepresentations_of_thetaLift`, read verbatim in the earlier scan), but nothing I read confirms or refutes the "lift = derivative" analogy or the √X count.
- Collaboration story (section 5): unchanged. The archive can't show who wrote what.

### 3.4 A correction to the earlier Lean scan itself

`research-lean-archive.md`, row "Guinand-Weil explicit formula", says `Statement.lean` defines G(χ, x) "plus Landau-type steps (one-sided power bound implies zero-free half-plane)" and rates it "high for the analytic endgame". Keep the first half. Amend the second: those particular steps (`LandauStep`, `RHofG`) are defined and never proved under those names; the proved and used Landau steps are `zetaLandau` and `zero_free_of_Chebyshev_growth`, on `Gz` and `Gm`. The practical conclusion (the endgame is a Landau-type argument on this smoothed sum) is unchanged and is now better supported.

---

## 4. What is safe to put on screen about the formal proof

### 4.1 Safe, with source

| Fact | Exact value | Source |
|---|---|---|
| Lean files in the archive | 175,187 | Our scan (`verify-result.json`); same number on [STATUS-PAGE] |
| Lines of Lean | 17,374,215 (say "17.4 million") | Our scan |
| Source size | 1.03 GB uncompressed; 239,275,554 bytes compressed, in 14 parts | Our scan; compressed size also on [STATUS-PAGE] |
| Toolchain | Lean v4.33.1; Mathlib at release tag v4.33.1 | [VERBATIM-LEAN] `lean-toolchain`, `lakefile.toml`; [STATUS-PAGE] |
| Top-level theorems | 5, in a 12-line `Main.lean` | [VERBATIM-LEAN] |
| The headline line | `theorem riemannHypothesis : RiemannHypothesis := rhOfAll` | [VERBATIM-LEAN] `Main.lean` line 4 |
| The statement is Mathlib's own definition of RH | yes | Earlier scan (no redefinition anywhere in the archive); [STATUS-PAGE] |
| GRH scope | all Dirichlet L-functions; not number-field (Dedekind, Hecke) L-functions | [VERBATIM-LEAN] `Statements.lean`; [STATUS-PAGE] |
| `sorry`, `axiom`, `native_decide` tokens | 0, 0, 0 | Our scan |
| Comments or docstrings | 0 | Earlier scan (pass 4) |
| Compiles | all 175,187 modules, zero errors | [STATUS-PAGE], as of 19:45 UTC |
| Axioms used by the 5 main theorems | `propext`, `Classical.choice`, `Quot.sound` (Lean's three standard axioms) | [STATUS-PAGE] |
| Kernel replay | `leanchecker`, 175,187 of 175,187 modules, zero rejections | [STATUS-PAGE] |
| Independent kernel | `nanoda` (Rust) accepts the full export: 61.57 GB, 27 min 42 s on 80 threads | [STATUS-PAGE] |
| Still running at snapshot | `comparator` end to end; Lean default and paranoid kernels on the export | [STATUS-PAGE] |
| The smoothed prime sum | Gz(x) = Σ_{n≤x} Λ(n)(x/n − 1) − x log x + (1 + γ)x | [VERBATIM-LEAN] `StatementOC.lean`; matches [NOTE] item 5 |
| The last step, in a line of Lean | `Gz x ≤ x ^ (1 / 2 + C * ε)` ... `→ RiemannHypothesis` | [VERBATIM-LEAN] `PowerBoundGivesRiemannHypothesis.lean`. If shown, caption it "one of the archive's closing steps (the zeta-only version)", since Main's path uses the multi-character version. |
| RH is a corollary of GRH in the Lean | yes | [VERBATIM-LEAN] `rh_of_every` |
| Behrend-type sets appear in the archive | yes, Felix Behrend's construction via Mathlib. Say "appears in", not "is used by the main theorem": not traced to Main | [VERBATIM-LEAN] `BehrendSets/Statement.lean`, `ThickExists.lean` hits |
| Fields in a 2-power cyclotomic tower | yes (in `VWin`, a hypothesis of the final assembly) | [VERBATIM-LEAN] `IsChiField`, `OrdGrp` |

Approximate figures that are fine in narration but should be rounded and hedged: "roughly a million declarations", "about 780,000 theorems" (regex counts from the earlier scan, not Lean's own count); "several times the size of Mathlib" (Mathlib's size was not measured by us).

Every [STATUS-PAGE] row needs the "as of" time and a re-check before render.

### 4.2 Keep off screen

- **The ingredient-to-directory map** in section 4 of `research-lean-archive.md`. Its confidence column is name-match only. In particular do not show "Chowla-Selberg: found", "Siegel mass: found", "relative trace formula: found", "Rallis: found" as confirmations of the note. A neutral "directory names echo the note's vocabulary" is the most that is supportable.
- **Any claim that Hironaka, local Langlands, Bhatt-Scholze, and so on "were formalized".** The roughly 180 "literature" items are internal propositions with those names; one is literally `UnusedSlot72 : Prop := True`. Soundness of the final theorem doesn't depend on the names being faithful. A narrative about them does, and nobody has checked.
- **m ≈ √x as the theta-lift chain length** (2.6).
- **`VWin` as "a proof of a weak Vandiver conjecture"** (2.4). Use the note's own words with attribution if at all.
- **`LandauStep` or `RHofG` shown as a proved theorem** (1.2(a)). `G(χ, x)` as a definition is fine.
- **The trace in 1.3 presented as "the" dependency chain.** Fine as a schematic if labelled "simplified". Step 5 is import-level evidence.
- **The toy proof as part of the formal proof.**
- **Who wrote which part of the Lean.** Not determinable.
- **`la := 3/2` or `Ct = 401` or `eps < 1/52`** as meaningful constants. They are real (verbatim) but I can't explain them, and unexplained magic numbers invite wrong stories.
- **"No human-checkable proof exists"** as an absolute. Say none has been released; the note mentions a 250,000-page document that was not published.

---

## 5. Pronunciation list

Respellings use capitals for the stressed syllable. IPA is given where I'm reasonably sure of it. Confidence: **high** (standard, well attested), **medium** (the common English-language usage, but variants exist), **low** (confirm from a recording).

### 5.1 Must confirm before recording

| Term | Respelling for TTS | IPA | Confidence and note |
|---|---|---|---|
| **Alpöge** | al-pur-GEH (non-rhotic "ur", lips rounded), or al-peu-GEH | Turkish: [alpœˈɟe] | **low.** Turkish surname. ö is the vowel of German "schön" or French "peur". The g is hard, as in "get". The final e is sounded: "geh", not silent and not "jee". Turkish default stress falls on the last syllable. He works in the US and may use an anglicized form himself ("AL-poh-gay" or similar). **Confirm from a talk or interview recording.** Most TTS engines will mangle the ö; test the respelling and consider an SSML phoneme tag. |
| **Levent** | leh-VENT | [leˈvent] | medium. Turkish given name, stress on the second syllable. |
| **Guinand** | GWIN-and (first choice), or gee-NAHN | not sure | **low.** A. P. Guinand was Australian-born and worked in Britain and Canada. I don't know how he said it. Easiest fix: don't say the name. "The explicit formula" or "Weil's explicit formula" carries the meaning. |
| **Behrend** | BAY-rent (German), or BEH-rend (anglicized) | German: [ˈbeːʁɛnt] | medium to low. Felix Behrend was German-born and worked in Australia. English-speaking combinatorialists commonly say "BEAR-end" or "BEH-rend". Either is defensible; pick one and be consistent. |
| **Deligne** | duh-LEEN (close enough in English), more exactly duh-LEEN-yuh with a very light final syllable | French: [dəliɲ] | medium. Belgian, French-speaking. Not "deh-LIG-nee", not "duh-LINE". |
| **Vandiver** | van-DYE-ver | not sure | medium to low. American (Harry Vandiver). I believe the stress is on the second syllable with a long i; "VAN-dih-ver" is also heard. Confirm if the name is used. |
| **Stepanov** | steh-PAH-nof | Russian: [sʲtʲɪˈpanəf] | medium. Stress on the second syllable; final v sounds like f. Given name Sergei: sehr-GAY. |

### 5.2 People

| Term | Respelling | IPA | Confidence |
|---|---|---|---|
| Riemann | REE-mahn | [ˈʁiːman] | high |
| Bernhard (Riemann) | BAIRN-hart | | high |
| Weil (André) | VAY | French: [vɛj] | high. Not "while", not "vile". |
| André | ahn-DRAY | | high |
| Weyl (Hermann) | VILE | [vaɪl] | high. A different person from Weil; the two names sound different. |
| Pierre Deligne | pyair duh-LEEN | | see above |
| Bombieri (Enrico) | bom-BYEH-ree; en-REE-koh | [bomˈbjɛːri] | high |
| Schmidt (Wolfgang) | SHMIT; VOLF-gahng | | high |
| Dirichlet | DEE-rih-klay | German: [diʁiˈkleː] | high for English usage. Some say "DIR-ih-klay" or "dee-ree-SHLAY"; avoid the last. |
| von Mangoldt | fon MAHN-golt | [fɔn ˈmaŋɡɔlt] | high |
| Landau (Edmund) | LAHN-dow (rhymes with "now") | [ˈlandaʊ] | high |
| Gauss | GOWSS | | high |
| Euler | OY-ler | | high. Not "YOO-ler". |
| Hadamard | ah-dah-MAR | | high |
| de la Vallée Poussin | duh lah vah-LAY poo-SAN (nasal final) | | medium |
| Hasse | HAH-suh | | high |
| Iwasawa | ee-wah-SAH-wah | | high (even stress in Japanese; English speakers stress the third syllable) |
| Chebyshev | CHEB-ih-shev (common English), or cheh-bih-SHOFF (closer to Russian) | | medium |
| Siegel | ZEE-gul | [ˈziːɡl̩] | high (English speakers also say SEE-gul) |
| Chowla | CHOW-lah | | medium |
| Selberg | SEL-berg | | high for English usage |
| Rallis | RAL-iss | | medium |
| Bost | BOST (short o) | | medium |
| Borger | BOR-ger | | low: hard or soft g not known to me |
| Gan, Gross, Prasad | GAHN; GROHSS; pruh-SAHD | | medium |
| Bessel | BESS-ul | | high |
| Hecke | HEK-uh | | high |
| Poincaré | pwan-kah-RAY | | high |
| Parseval | PAR-suh-val | | high |
| Bertini | bair-TEE-nee | | high |
| Lichtenbaum | LIK-ten-bowm | | medium |
| Kurihara | koo-ree-HAH-rah | | medium |
| Langlands | LANG-lundz | | high |
| Galois | gal-WAH | | high |
| Frobenius | froh-BEE-nee-us | | high |
| Mellin | MEL-in (English usage), meh-LEEN (closer to Finnish-Swedish) | | medium |
| Sutherland (Andrew) | SUTH-er-lund | | high |
| Buzzard (Kevin) | BUZ-erd | | high |
| Dario Amodei | DAH-ree-oh ah-moh-DAY | | medium (only if the note's "messaged Dario" line is used) |

### 5.3 Terms and tools

| Term | Respelling | Confidence and note |
|---|---|---|
| Lean | LEEN | high |
| Mathlib | MATH-lib (short i, as in "library") | high. Some say "math-LIBE"; "lib" is the community norm. |
| zeta | ZAY-tuh (US), ZEE-tuh (UK) | high. Pick by narrator accent. |
| theta | THAY-tuh (US), THEE-tuh (UK) | high |
| chi (χ) | KYE (rhymes with "sky") | high |
| psi (ψ) | SYE | high |
| Lambda (Λ) | LAM-duh | high |
| epsilon | EP-sih-lon | high |
| gamma (γ) | GAM-uh | high. "Euler's constant" or "the Euler-Mascheroni constant" (mas-keh-ROH-nee). |
| L-function | EL function | high |
| GRH, RH, ERH | spell out the letters | high. Better: say "the Generalized Riemann Hypothesis" in full the first time. |
| automorphic | aw-toh-MOR-fik | high |
| cyclotomic | sye-kloh-TOM-ik | high |
| unitary | YOO-nih-tair-ee | high |
| p-adic, 2-adic | pee-AD-ik, too-AD-ik | high |
| adele, adelic | uh-DELL, uh-DELL-ik | medium |
| Arakelov | ah-rah-KEH-lof | medium |
| kernel | KER-nul | high |
| nanoda | nuh-NOH-duh | low. Project name; I don't know the author's pronunciation. On screen it is fine as text; in narration "an independent kernel written in Rust" avoids the word. |
| comparator | kum-PAIR-uh-ter | medium. As a tool name; avoidable with "a statement-comparison tool". |
| leanchecker | LEEN checker | high |
| propext | PROP-ext ("propositional extensionality") | medium. Better on screen than spoken. |
| Classical.choice | "classical choice" | high |
| Quot.sound | "quote sound", or "quotient soundness" | medium. Better on screen than spoken. |
| Zulip | ZOO-lip | high |
| Stepanov's method | see 5.1 | |
| Guinand-Weil | see 5.1 | |
| Mathlib's `RiemannHypothesis` | "Mathlib's definition of the Riemann Hypothesis" | n/a |
| li(x), Li(x) | "the logarithmic integral" | high. Don't read as "lie of x". |
| √x, x^(1/2+ε) | "the square root of x", "x to the one half plus epsilon" | n/a |
| Oct 6, Nov 15, Nov 20 dates | "October sixth", etc. | n/a |

General TTS advice: for Alpöge, Deligne, Weil and Dirichlet, test the engine's default first. Many engines get Weil wrong ("while") and Dirichlet half right. Use phoneme tags or the respelling in the script text, and listen to every name in context before the final render.

---

## 6. What I did not do

- I did not read the proof of `Comparison₂.formB`, the body of `zero_free_of_Chebyshev_growth` beyond its first lines, the bridge file's proof term, the definition of `shaLen`, or anything upstream of the Landau step. The 17 million lines above the endgame remain unread by anyone on this task.
- I did not verify the Zulip report that the toy proof is absent, beyond the grep facts stated.
- I did not re-check the status page. Everything marked [STATUS-PAGE] is as of the snapshot.
- I did not write the script.
