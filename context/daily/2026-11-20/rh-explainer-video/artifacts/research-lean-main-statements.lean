/-
research-lean-main-statements.lean
Verbatim extracts from https://alpo.ge/lean.tar.gz.part01..part14 (Levent Alpoge, 2026-11-20),
collected by static inspection only (nothing compiled or executed). Archive paths are relative
to lean/src/. Mathlib definitions are quoted from leanprover-community/mathlib4 at the pinned
rev 0df444a360eaa60ab8c11dca51a86af692955474, which is the upstream Mathlib release tag v4.33.1 (2026-08-21).
Toolchain: leanprover/lean4:v4.33.1. This file is a reading aid, not a buildable module:
the Mathlib section is kept inside a comment to avoid redefinition clashes.
-/

/- Trimmed for the public repo: only the top-level statement files (sections 1 to 3, also shown on screen in the video)
   and Mathlib's own definitions (Apache 2.0) are kept. The full archive is the author's work and is published at
   https://alpo.ge (lean.tar.gz.part01..14); research-lean-archive.md describes the rest of the proof chain. -/

/- ===================== 1. lean/src/Main.lean (verbatim, whole file) ===================== -/
import Statements
import Supplements.Kernels.MainTheoremsAll

theorem riemannHypothesis : RiemannHypothesis := rhOfAll

theorem riemannZeta_eq_zero_re : RiemannZetaZerosOnLine := rhOfAll

theorem LFunction_ne_zero_of_half_lt_re : DirichletLNonvanishingRightOfHalf := allChi

theorem LFunction_eq_zero_re : DirichletLZerosOnLine := claimAll.2.1

theorem LFunction_eq_zero_re_of_isPrimitive : PrimitiveDirichletLZerosOnLine := critAll

/- ===================== 2. lean/src/Statements.lean (verbatim, whole file; imports only Mathlib) ===================== -/
import Mathlib

def RiemannZetaZerosOnLine : Prop :=
  ∀ s : ℂ, riemannZeta s = 0 → (¬∃ n : ℕ, s = -2 * ((n : ℂ) + 1)) → s ≠ 1 → s.re = 1 / 2

def DirichletLNonvanishingRightOfHalf : Prop :=
  ∀ (N : ℕ) [NeZero N] (χ : DirichletCharacter ℂ N) (s : ℂ),
    1 / 2 < s.re → (χ ≠ 1 ∨ s ≠ 1) → DirichletCharacter.LFunction χ s ≠ 0

def DirichletLZerosOnLine : Prop :=
  ∀ (N : ℕ) [NeZero N] (χ : DirichletCharacter ℂ N) (s : ℂ),
    0 < s.re → s.re < 1 → DirichletCharacter.LFunction χ s = 0 → s.re = 1 / 2

def PrimitiveDirichletLZerosOnLine : Prop :=
  ∀ (N : ℕ) [NeZero N] (χ : DirichletCharacter ℂ N), χ.IsPrimitive →
    ∀ s : ℂ, 0 < s.re → s.re < 1 → DirichletCharacter.LFunction χ s = 0 → s.re = 1 / 2

/- ===================== 3. lean/src/Supplements/Kernels/MainTheorems.lean (verbatim, whole file) ===================== -/
import Formalism.GammaFactorNonvanishing.CritLine
import Development.AutomorphicArithmetic.CharacterBoxes.ClaimStrip
import Development.AutomorphicArithmetic.CharacterBoxes.MainConclusion

open Complex DirichletCharacter

theorem allChi : UpperTheory.EveryCharacter := UpperTheory.FinalTheorems.everyCharacter

theorem rhOfAll : RiemannHypothesis := Formalism.VW.rh_of_every allChi

theorem critAll (N : ℕ) [NeZero N] (χ : DirichletCharacter ℂ N) (hχ : χ.IsPrimitive) (s : ℂ)
    (h0 : 0 < s.re) (h1 : s.re < 1) (hz : LFunction χ s = 0) : s.re = 1 / 2 :=
  Formalism.VW.critLine allChi N χ hχ s h0 h1 hz

theorem claimAll : Claim.HalfPlane ∧ Claim.Strip ∧ Claim.Zeta :=
  ⟨allChi, Claim.strip allChi, Claim.zeta allChi⟩

/- ===================== 14. Mathlib definitions at the pinned rev (quoted inside a comment) ===================== -/
/-
-- Mathlib/NumberTheory/LSeries/RiemannZeta.lean, lines 119-121 and 182-186:
/-- The Riemann zeta function `ζ(s)`. -/
@[wikidata Q187235]
def riemannZeta := hurwitzZetaEven 0

/-- A formal statement of the **Riemann hypothesis** – constructing a term of this type is worth a
million dollars. -/
@[wikidata Q205966]
def RiemannHypothesis : Prop :=
  ∀ (s : ℂ) (_ : riemannZeta s = 0) (_ : ¬∃ n : ℕ, s = -2 * (n + 1)) (_ : s ≠ 1), s.re = 1 / 2

-- Mathlib/NumberTheory/LSeries/DirichletContinuation.lean, lines 60-61:
@[pp_nodot]
noncomputable def LFunction (χ : DirichletCharacter ℂ N) (s : ℂ) : ℂ := ZMod.LFunction χ s

-- Mathlib/NumberTheory/LSeries/ZMod.lean, lines 83-84:
noncomputable def LFunction (Φ : ZMod N → ℂ) (s : ℂ) : ℂ :=
  N ^ (-s) * ∑ j : ZMod N, Φ j * hurwitzZeta (toAddCircle j) s
-/
