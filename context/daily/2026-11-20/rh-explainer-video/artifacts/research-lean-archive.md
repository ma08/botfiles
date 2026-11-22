# Static inspection of `lean.tar.gz` (Alpoge RH/GRH Lean archive)

Prepared 2026-11-20 for the explainer video. Source: `https://alpo.ge/lean.tar.gz.part01` to `part14`, downloaded to a local scratch folder. Nothing from the archive was compiled, built, or executed. All numbers come from streaming the concatenated parts through Python `tarfile` (`r|gz` mode) and scanning file contents in memory. Only 102 small files were extracted for reading: 99 `.lean` files plus the 3 config files, about 0.57 MB.

Companion file with verbatim statements: `research-lean-main-statements.lean` (same folder). Scan scripts, summaries and hit lists: `lean-archive-scan/` (same folder).

## TL;DR

- **Size.** 175,187 `.lean` files, 17,374,215 lines, 1.03 GB of source (239 MB compressed). There are roughly 1.07 million declarations, including about 784k `theorem`s and 213k `def`s. Mathlib is **not** vendored, and every file is project code.
- **Main statement.** `lean/src/Main.lean` proves `theorem riemannHypothesis : RiemannHypothesis`, where `RiemannHypothesis` is **Mathlib's own definition**. It also proves four GRH-type statements about **Dirichlet L-functions** (Mathlib's `DirichletCharacter.LFunction`). Those four are defined in a statement file that imports only Mathlib. I found no weakening. GRH here means Dirichlet L-functions only: no Dedekind zeta and no Hecke L-functions. The note itself says ERH is future work.
- **Trust surface.**
  - Zero `sorry`, `admit`, `axiom`, `native_decide`, `implemented_by`, `extern`, `unsafe`, `opaque`, `debug.skipKernelTC`, `ofReduceBool`, `trustCompiler` or `sorryAx`, in either raw or comment-stripped text.
  - Three small custom elaborators skip the elaborator's type check and leave checking to the kernel. They look benign, because the kernel still checks everything.
  - There is no `#print axioms` for the main theorems anywhere in the archive.
- **No comments at all.** The archive has zero `--` and zero `/-` in 1 GB of Lean, so there are no docstrings, README or blueprint. Architecture can only be read from directory and declaration names plus the import graph.
- **What static inspection settles.** The statement is the real RH and GRH for Dirichlet L-functions, and there are no textual escape hatches. **What it can't settle:** whether the 17-million-line development actually compiles and kernel-checks, and whether `#print axioms` would show only `propext`, `Classical.choice` and `Quot.sound`.

## 1. Size and shape

### Archive facts

| Item | Value |
|---|---|
| Parts | 14 (13 × 18,000,000 B + 5,275,554 B = 239,275,554 B) |
| Tar members | 175,190 regular files. No directory entries, symlinks, hardlinks or devices. No absolute paths or `..` components. |
| `.lean` files | 175,187 |
| Other files | `lean/lakefile.toml`, `lean/lake-manifest.json`, `lean/lean-toolchain` (nothing else: no README, no `.md`, no blueprint, no CI) |
| Lean bytes | 1,030,531,854 |
| Lean lines | 17,374,215 total; 15,531,759 non-blank |
| File size | median 58 lines, p90 233, p99 560, max 17,981 (`Formalism/HermitianCurvature/HermitianCurvatureProofs/IsAdmissibleSplittingCharPairMulTwist.lean`, 914 KB) |
| Declarations (line-start regex) | 784,092 `theorem`, 34,663 `lemma`, 212,819 `def`, 13,202 `abbrev`, 8,286 `structure`, 8,199 `instance`, 4,662 `example`, 121 `inductive`, 43 `class` |
| `*Statement.lean` files | 46,610 (27% of files): a pervasive "statement file + proof file" split |
| Exact duplicate files | 9 hash groups, 14 extra copies (negligible) |
| Comments | **zero** occurrences of `--` or `/-` anywhere. As a positive control, 725,150 lines in 165,061 files start with `theorem`. The archive appears machine-stripped of all comments and docstrings. |

Note: the previously saved `listing.txt` (106,783 entries) was **truncated**. It stops partway through `Development/AutomorphicSpectrum`. The figures above come from the full stream.

### Toolchain and dependencies

- `lean-toolchain`: `leanprover/lean4:v4.33.1`.
- `lakefile.toml`:
  - Package `"tree"`, `srcDir = "src"`, `moreLeanArgs = ["--tstack=400000"]`.
  - `leanOptions`: `autoImplicit = false`, `relaxedAutoImplicit = false`, `maxSynthPendingDepth = 3`, `maxHeartbeats = 4000000`.
  - Single `require`: Mathlib at `0df444a360eaa60ab8c11dca51a86af692955474`. This is exactly the **upstream Mathlib release tag `v4.33.1`** (`refs/tags/v4.33.1`, 2026-08-21, by Kim Morrison, "chore: bump toolchain to v4.33.1").
    - Its only parent is tag `v4.33.0` (`db584cd6…`), and the one commit changes only `lean-toolchain`.
    - Like other Mathlib release tags, it sits off `master`: compare shows `diverged`, ahead 1, behind 2,693 relative to today's master. That is expected and not a fork.
  - Libraries: `BuildAid`, `CompanionTheory`, `Development`, `Formalism`, `GroundTheory` (explicit sub-globs), `GroundTheoryFields` (`synthInstance.maxHeartbeats = 400000`), `Lemmata`, `PositivityTheory`, `ReciprocityTheory`, `Supplements`, and `Main` with `roots = ["Statements", "Main"]`.
- `lake-manifest.json`: Mathlib plus the usual transitive packages at pinned revs: plausible, LeanSearchClient, import-graph, ProofWidgets4, aesop, quote4 (Qq), batteries, lean4-cli. All URLs are the standard `github.com/leanprover-community/*` or `github.com/leanprover/*` repos. All 8 inherited `(url, rev)` pairs **match Mathlib's own `lake-manifest.json` at the `v4.33.1` tag exactly**.
- **Mathlib is not vendored.** There is no `Mathlib/` (or any dependency) directory in the tar, and lake would fetch Mathlib separately. 155,753 files `import Mathlib` (the whole library). Only 269 files import specific Mathlib modules instead. A handful import `Lean` or `Batteries.Tactic.OpenPrivate`. So **all 175,187 files are project code, with no vendored dependency trees**. That's roughly 8x Mathlib's size, if Mathlib is around 2M lines (my approximation, not measured here). Who wrote which part can't be told from the source; see Section 5.

### Top-level structure (lines from the full stream)

| Library dir | Files | Lines |
|---|---:|---:|
| `Development` | 141,928 | 12,232,663 |
| `Formalism` | 18,254 | 3,200,748 |
| `GroundTheory` | 8,507 | 1,119,138 |
| `ReciprocityTheory` | 3,845 | 563,016 |
| `CompanionTheory` | 2,027 | 194,218 |
| `PositivityTheory` | 449 | 55,130 |
| `Lemmata` | 167 | 9,232 |
| `Supplements` | 3 | 22 |
| `BuildAid` | 5 | 20 |
| `Main.lean`, `Statements.lean` (root) | 2 | 28 |

Largest second-level areas:

| Directory | Files | Lines |
|---|---:|---:|
| `Development/AbelianVarietyTheory` | 99,187 | 8,142,960 |
| `Development/AutomorphicArithmetic` | 18,431 | 1,776,375 |
| `Development/AutomorphicSpectrum` | 15,147 | 1,195,844 |
| `Formalism/LocalToGlobal` | 5,501 | 955,843 |
| `Development/WeilBound` | 7,051 | 848,547 |
| `Formalism/SharpRestriction` | 3,093 | 709,436 |
| `GroundTheory/HeightsAndTheta` | 6,410 | 641,322 |
| `Formalism/HermitianCurvature` | 1,922 | 460,802 |
| `Formalism/PeriodIntegrals` | 4,350 | 451,856 |
| `ReciprocityTheory/ReductiveGroups` | 2,799 | 409,976 |

`Development/AbelianVarietyTheory/Proofs` alone has 95,418 files and 7.44M lines, about 43% of the archive.

### Import graph

All internal imports resolve; there are no dangling module names. The import closure of `Main.lean` is the entire archive. The closure of the file that actually proves the theorems (`Supplements/Kernels/MainTheorems.lean`) covers 175,179 of 175,187 files. So the import graph does not isolate a smaller proof core. Import closure is only an upper bound, and the true proof dependencies would need Lean itself (for example, `#print axioms` or a dependency extractor) to determine.

## 2. The main theorems

### Verbatim statements

`lean/src/Main.lean` (whole file):

```lean
import Statements
import Supplements.Kernels.MainTheoremsAll

theorem riemannHypothesis : RiemannHypothesis := rhOfAll

theorem riemannZeta_eq_zero_re : RiemannZetaZerosOnLine := rhOfAll

theorem LFunction_ne_zero_of_half_lt_re : DirichletLNonvanishingRightOfHalf := allChi

theorem LFunction_eq_zero_re : DirichletLZerosOnLine := claimAll.2.1

theorem LFunction_eq_zero_re_of_isPrimitive : PrimitiveDirichletLZerosOnLine := critAll
```

`lean/src/Statements.lean` (whole file, imports only Mathlib):

```lean
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
```

Mathlib at the pinned rev (`Mathlib/NumberTheory/LSeries/RiemannZeta.lean`, lines 121 and 185-186; `DirichletContinuation.lean`, line 61):

```lean
def riemannZeta := hurwitzZetaEven 0

def RiemannHypothesis : Prop :=
  ∀ (s : ℂ) (_ : riemannZeta s = 0) (_ : ¬∃ n : ℕ, s = -2 * (n + 1)) (_ : s ≠ 1), s.re = 1 / 2

noncomputable def LFunction (χ : DirichletCharacter ℂ N) (s : ℂ) : ℂ := ZMod.LFunction χ s
```

### Fidelity judgment

- **RH.** `RiemannHypothesis` in `Main.lean` resolves to Mathlib's root-namespace definition. Three checks back this up:
  - `Main.lean` has no `open`.
  - No declaration named `RiemannHypothesis` (in any namespace) exists anywhere in the archive.
  - No `notation`, `macro` or `syntax` line mentions `RiemannHypothesis`, `riemannZeta` or `LFunction`. All 1,722 notation lines were scanned; the near-misses are `local notation` for things like complex conjugation.

  Mathlib's definition is the standard formal RH. ζ is the meromorphic continuation, built from the Hurwitz zeta function, and only the trivial zeros −2, −4, … and the pole s = 1 are excluded (s = 1 is excluded because Mathlib assigns a junk value there). There is no weakening.
- **`RiemannZetaZerosOnLine`** says the same thing as Mathlib's RH in a custom wrapper.
- **GRH (`DirichletLNonvanishingRightOfHalf`).** For every modulus N ≥ 1 and **every** Dirichlet character χ mod N (primitive, imprimitive and principal), L(χ, s) ≠ 0 whenever Re s > 1/2. The only exception is s = 1 for the trivial character, where the L-function has a pole. This is the zero-free half-plane form of GRH for Dirichlet L-functions. It is equivalent to the critical-line form via the functional equation for primitive χ. Imprimitive L-functions differ only by finite Euler factors, whose zeros lie on Re s = 0.
- **`DirichletLZerosOnLine` and `PrimitiveDirichletLZerosOnLine`** are the critical-strip forms. The open strip 0 < Re s < 1 correctly excludes the Euler-factor zeros on Re s = 0 for imprimitive χ.
- **Scope.** These are Dirichlet L-functions only (Mathlib's `DirichletCharacter.LFunction`). The archive contains no statement about Dedekind zeta functions (`NumberField.dedekindZeta`) or Hecke L-functions. That matches the note, which reserves "Extended RH" for later.
- **Hygiene.** There are no hypotheses or `variable` binders on the five Main theorems, and the lakefile sets `autoImplicit = false` globally. Characters take values in ℂ. Nothing looks vacuous.

### Top of the proof chain

Every step below was read verbatim; see the `.lean` companion file.

1. `Main.riemannHypothesis := rhOfAll`. In `Supplements/Kernels/MainTheorems.lean`, `rhOfAll : RiemannHypothesis := Formalism.VW.rh_of_every allChi` and `allChi : UpperTheory.EveryCharacter := UpperTheory.FinalTheorems.everyCharacter`.
2. `UpperTheory.EveryCharacter` (`Development/AutomorphicArithmetic/CharacterBoxes/EveryCharacter.lean`) is textually identical to `DirichletLNonvanishingRightOfHalf`. So GRH is the real target, and RH is derived from it.
3. GRH implies RH (`Formalism/GammaFactorNonvanishing/CritLine.lean` and `RhOfRight.lean`): apply GRH to the trivial character mod 1 (`LFunction_modOne_eq` gives ζ), then use the zeta functional equation for Re s < 1/2. This is short, standard and fully readable.
4. `everyCharacter := everyCharacter_of_row UpperTheory.Gal.Int.galoisLocalGlobalStrong_recParameter` (`CharacterBoxes/MainConclusion.lean`). It feeds
   `UpperTheory.LiteratureTheorems.every_character_of_literature_of_vWin ⟨h, UpperTheory.Zero.LLC.recTExists, h⟩ (UpperTheory.One.vwin_of_row h)`.
5. `OpenLiteratureStatements` is a `structure ... : Prop` with three fields: `caraianiLocalGlobalDual`, `localLanglandsExists` and `galoisRepOfPolarizedPairLit`. All three are supplied by theorems, not assumed. `galoisLocalGlobalStrong_recParameter` is itself `galoisRepresentations_of_thetaLift UpperTheory.TP.K.tLiftK` ("Galois representations from theta lifts").
6. The bridge file (`.../ThirdPlaceSeries/EveryCharacterOfLiteratureOfVWin.lean`, 814 lines, 208 imports) contains about 180 lemmas named `*_of_literature`. Each discharges a `GlobalTheory.Published.X` Prop with a proved `..._holds` theorem. Examples: Casselman–Wallach, Bernstein–Zelevinsky, Jacquet–Shalika, local Langlands for GL_n, Bhatt–Scholze, Fontaine B_cris, toroidal compactification, Kawamata–Viehweg, Nadel vanishing, arithmetic Hilbert–Samuel, Hironaka-type principalisation, Grothendieck–Messing, Siegel–Weil, Howe duality and Stone–von Neumann. These all flow into `UpperTheory.Lit.every_character_of_theta_integrals_local_matching`.
7. Reduction to primitive characters is `UpperTheory.Top.imprimitive` (Euler-factor argument), from `Formalism.HC.ZeroFreeAll := ∀ ψ : PChar, L(ψ.χ, s) ≠ 0 for Re s > 1/2`, where `PChar` bundles a primitive χ.

Observation for the video: many of these "Published" statements are project-local `abbrev`s of internal Props. One is literally `abbrev GlobalTheory.Published.UnusedSlot72 : Prop := True` (a placeholder slot). Whether each local Prop faithfully captures the named literature theorem is **not** load-bearing for soundness. If the final theorem kernel-checks with standard axioms, RH follows no matter what the intermediate names mean. It does matter for any "they formalized Hironaka and local Langlands" narrative. That narrative needs separate checking. For example, `Development/ResolutionOfSingularities` (499 files, 140,709 lines) proves `strongResolutionOfSingularitiesCharZero : StrongResolutionOfSingularitiesCharZero`, and that definition would need reading against the real theorem.

## 3. Trust surface

All counts are over all 175,187 files. Because the archive has no comments, raw-text and comment-stripped counts coincide.

### Zero hits (raw text, unanchored anywhere on a line, so no comment or docstring mentions either)

- Proof escape hatches: `sorry`, `sorryAx`, `mkSorry`/`mkLabeledSorry`, `admit`, `admitGoal`.
- Axioms: `axiom` as any token (so no top-level axiom declarations), `axiomDecl`/`AxiomVal`/`mkAxiom`.
- Compiler or evaluator trust: `native_decide`, `decide +native`, `bv_decide`, `implemented_by`, `@[extern`, `ofReduceBool`, `trustCompiler`, `lcProof`.
- Unsafe code: `unsafe`, `unsafeCast`, `opaque`.
- Kernel options: `skipKernelTC`, any `debug.*` option.
- Unfinished-proof markers: `proof_wanted`, `#exit`, a bare `stop` tactic.
- Environment hooks: `initialize`/`builtin_initialize`, `run_elab`/`run_meta`, `#eval`, `syntax`/`declare_syntax_cat`/`macro_rules`.
- Attribute-registered extensions: `@[command_elab|term_elab|tactic|macro|init|builtin_*|delab|app_unexpander|env_extension|csimp]`.

The archive does not use the Lean module system (no `module`, `public import` or `meta import` headers). The `Statements.lean` identifiers (and `rhOfAll`, `allChi`, `claimAll`, `critAll`) appear only in `Statements.lean`, `Main.lean` and `Supplements/Kernels/MainTheorems.lean`. Non-ASCII characters in the statement files are all standard Lean math symbols (∀ ℂ → ¬ ∃ ℕ ≠ χ ∨), with no homoglyph tricks.

The only environment-touching calls anywhere are 5 `modifyEnv` (BuildAid, below) and 2 `addDecl` (`CutCptCopy.lean`, below). `elab` appears 4 times in 3 files, all covered below.

### Non-zero items

| Item | Count / location | Assessment |
|---|---|---|
| `run_cmd` | 5, one each in `BuildAid/D1..D5.lean` | Each is `run_cmd Lean.modifyEnv fun env => Lean.LibrarySuggestions.nameDenyListExt.addEntry env "<Namespace>"` for `CompanionTheory`, `CrystallineSemistableComparison`, `GlobalTheory`, `PositivityTheory` and `UpperTheory`. These hide namespaces from library-suggestion tactics (`exact?`-style search). They don't touch the kernel and are harmless. |
| Custom tactic `kexactB` | defined in `Formalism/LocalToGlobal/IndefiniteReal/HeckeNonvanishing/Imports.lean`; 278 uses in 50 files (plus `kc%`/`kq%`/`kd%` macro wrappers) | It elaborates a term **with no expected type** and assigns it to the goal **without an elaborator defeq check**. The kernel still type-checks the final declaration, so this is not a soundness hole. It does push all checking onto the kernel, which can be very expensive, and only a real build shows whether it passes. |
| Custom tactic `kcopy` and command `#kcopy_probe` | `Formalism/LocalToGlobal/NumberFieldFamilies/OwnStruct.lean`; `kcopy` is used in 3 files | It rebuilds a structure value field by field through projections, again with no elaborator type check. The probe only logs messages. Same assessment as `kexactB`. |
| Command `cpt_copy_thms` | defined in `Formalism/HermitianCurvature/HermitianCurvatureProofs/CutCptCopy.lean`; invoked once at `CutMainCpt.lean:945` under `set_option maxHeartbeats 0 in` | It copies a dependency cone of `defnDecl`/`thmDecl` declarations with constants renamed to `...Cpt` versions, using `addDecl`. Standard `addDecl` kernel-checks each copy, and the command throws on any other declaration kind, so it cannot introduce axioms. This is unusual but not a soundness issue. |
| `partial def` | 2, both meta helpers in the files above | Fine. |
| Tactic/term `macro`s | about 90 lines (`local`/`scoped` proof-automation shorthands) | They expand to ordinary tactics. Fine. |
| `set_option allowUnsafeReducibility true` | 37 lines in 33 files (mostly p-adic Hodge theory: `Bcris`, `Acris`, `Fontaine…`) | Elaborator-only (it lets reducibility attributes change). Not a kernel issue. |
| `set_option hygiene false` | 31 lines in 15 files | Macro hygiene only. Fine. |
| Other options | `backward.isDefEq.respectTransparency false` ×1,877; `maxHeartbeats 0` ×4; `maxRecDepth` up to 1,000,000; many `maxHeartbeats` raises (×50,873 at 1,000,000); linter disables | These are performance and elaborator settings. They signal a very heavy build but say nothing about soundness. |
| `open private … from …` | 221 lines in 158 files (for example `open private au_isTeich au_open from Development.AutomorphicArithmetic…`) | Gives access to private lemmas in other project files. Name visibility only; fine. |
| `instance … Fact …` | 234 lines in 178 files (for example `Fact (Nat.Prime 7) := ⟨by norm_num⟩`) | Ordinary proved instances, not assumptions. |
| `Classical.choice` mentions | 306 | A standard axiom. Fine. |
| `#print axioms` | 4 lines in 2 files: `Formalism/PeriodIntegrals/UnitaryGroupMassFormula/UnitaryClassMass/UnitaryClassMass.lean` (3) and `.../LocalUnimodularLattice/Transf.lean` (1) | These check intermediate lemmas only. **None checks the Main theorems**, and no expected output is documented. |
| Name shadowing | the project declares namespaced `Complex`, `Real`, `re` and `ofReal` (for example `Formalism/CoboundaryTransfers/StatementAPI.lean: def Complex`) | None is at root, `Main.lean` opens nothing, and `Statements.lean` imports only Mathlib. No effect on the statements. |

Vendored dependencies: none are vendored, so there is nothing to diff against upstream. The manifest pins standard upstream URLs.

Net: I found no textual escape hatch. If the development builds with this toolchain and Mathlib, the kernel will have checked every proof term. What remains is that standard Lean trust story: the Lean 4.33.1 kernel, Mathlib's definitions, and the three standard axioms.

## 4. Map of the mathematics

Naming is opaque and machine-generated: there are no comments, and names like `CharacterBoxes`, `SizeWindowBrackets`, `PairRows`, `TopMainZj` and `Row0b` don't explain themselves. The table maps the note's ingredients by keyword matches in **paths** (file counts and lines) and in content. The "Confidence" column rates the **name match only**. Apart from the files quoted in Sections 2 and 3, these directories were not opened, so a "high" means the names line up, not that the mathematics was checked. Several of the note's terms never appear literally.

| Note ingredient | Where it shows up | Confidence |
|---|---|---|
| Stepanov method / auxiliary determinant with multiplicity | No identifier or path contains "Stepanov" (0 hits). Related: paths with "determinant" (943 files / 92.6k lines; for example `Development/WeilBound/ThetaLifts/LeviDeterminants`, 116 files / 13k) and "multiplicity" (800 files / 86k; for example `ReciprocityTheory/ReductiveGroups/DiscreteSeries/MultiplicityOne`, 113 files / 16.7k). | low |
| Theta lifts / theta correspondence (chained lifts) | `Development/AutomorphicArithmetic/ThetaCorrespondence` (3,201 files / 179k lines), including `ThetaPairLifts` (2,998 files / 158k) and `WeilRepresentation`, `FockModels`, `RallisInnerProduct`; `Development/WeilBound/ThetaLifts` (788 files / 116k). "theta" appears in 18,663 file paths (1.76M lines). The key link is `galoisLocalGlobalStrong_recParameter := galoisRepresentations_of_thetaLift tLiftK`. | high |
| Seesaw | 452 path files / 41.5k lines, mostly `Development/AbelianVarietyTheory/Proofs/{DivisorProofs,DecoratedLatticeProofs,TwistedOperators}` (for example `SeeSawUnfoldedSupportFixedLevelPlaces.lean`). | medium |
| Rallis inner product | `.../ThetaCorrespondence/RallisInnerProduct` (3 files / 2.5k) plus 91 path files / 9.4k (for example `FunctionModelRallisFromInputs.lean`). | medium |
| GGP / Bessel periods | "GGP" appears in 1 path (6 files match the broader regex). "Bessel" appears in 1,188 path files / 114k: `CompanionTheory/AutomorphicTheory/{BesselWaveGrids,BesselOrbitBounds,LocalBesselUniqueness,PieriRules/ThetaBesselIsometries}`, `Formalism/FormalDegreeBessel`, `Formalism/HermitianCurvature/BesselNonvanishingReduction.lean`. Some hits are Bessel *functions*, not periods. | medium |
| Unitary groups U(X0) → … → U(Xm) | "unitary" appears in 8,942 path files / 961k lines: `Development/AbelianVarietyTheory/Proofs/UnitaryExistence` (767 / 81.7k), `Formalism/PeriodIntegrals/UnitaryGroupMassFormula` (3,615 / 430k), `.../UnitaryDualProof` (300 / 38.6k). | medium |
| O(2, n) | Only 5 path files (for example `.../CapelliIdentities/OrthogonalGroupLemmas.lean`). Not prominent by name. | low |
| Chowla–Selberg | `GroundTheory/HeightsAndTheta/Heights/ChowlaSelberg` (58 files / 5.5k; `Assembly.lean`, `PKroneckerLimit.lean`). | high |
| Siegel mass formula / Siegel–Weil | `Formalism/PeriodIntegrals/UnitaryGroupMassFormula` (3,615 / 430k); `Development/WeilBound/RepresentationTheoryGL/SiegelWeilProof` (635 / 67.5k) and `RegularisedSiegelWeil` (153 / 15.9k); `Formalism/LocalToGlobal/SiegelLatticeTheory` (2,085 / 339k). | high |
| Iwasawa towers | Careful: `Development/AbelianVarietyTheory/Proofs/IwasawaDecomposition` (7,769 files / 600k) is named after the Lie-group decomposition, and in fact holds p-adic Hodge theory (`Acris`, `Bcris`, Fontaine) and theta material. The arithmetic tower shows up in `VWin`, which works in cyclotomic subfields with `2^(e+2) ∣ N` and `PageN: 2^e ≈ x^(2+8ε)`, i.e. a 2-adic cyclotomic tower. There are also a few `CyclotomicTower` files. | medium |
| Vandiver weakening | 0 hits for "Vandiver". The matching object is `UpperTheory.Top.VWin` / `VVle`: bounds on `Formalism.GaloisCohomology.shaLen` (Sha-type Galois cohomology lengths) summed over primes, in those cyclotomic fields. This fits note step 17 (H¹ classes not killed by twisting). It is proved by `vwin_of_row`. | medium |
| Behrend's construction | `Formalism/BehrendSets` (14 files / ~1.1k: `FinalE.lean`, `BehrendVariance/`). | high |
| Bost slope inequality | No "Bost". The slope and Arakelov side: `ReciprocityTheory/ReductiveGroups/ArithmeticGeometry/ArakelovVolumes` (189 / 29k) and `ArakelovGeometry` (79 / 12.6k), `Formalism/LatticeSlopes`, `Formalism/HarderNarasimhan`, `Formalism/SizeWindowBrackets/ChainSlopeWindows` (32 / 19.4k). | low to medium |
| Guinand–Weil explicit formula | No "Guinand". `Formalism/PeriodIntegrals/UnitaryGroupMassFormula/ExplicitFormula` (36 / 5.2k), `Formalism/PeriodIntegrals/ExplicitFormulaCounts`. `Formalism/Statement.lean` defines exactly the note's smoothed sum G(χ, x) = Σ_{n≤x} Λ(n)(1 + Re χ(n))(x/n − 1) − x log x + (1 + γ_χ)x, plus Landau-type steps (one-sided power bound implies zero-free half-plane). | high for the analytic endgame |
| Relative trace formula | 471 path files / 52.8k: `Development/AutomorphicArithmetic/AutomorphicVarieties/ModularityArgument/TraceFormula` (312 / 30.7k), `Development/AbelianVarietyTheory/PublishedTheorems/TwistedTraceFormula` (97 / 13.6k). | medium |
| Poincaré series | 220 path files (this count includes Poincaré *duality* false positives); `Development/AbelianVarietyTheory/BlockTheory/PoincareCuspForms` (18 / 2.6k). | low to medium |
| CM curves / invariant derivation | `GroundTheory/GlobalFields/ComplexMultiplication` (98 / 20.3k); `GlobalTheory.Published.cmCurveGoodOutsidePrime`; "invariant derivation" in 36 path files / 2.5k (for example `ConstantCoeffPIterateInvariantDerivationCoord.lean`, `.../FrobeniusFibreCurves/LogarithmicSubstitution/InvariantDerivationSubstLawThree.lean`). | medium |
| Sixfold cover of GL5 | No "sixfold". The only GL5 directory is `Formalism/LocalToGlobal/GlobalTheory/GL5` (15 files / 3.2k), with names like `PClassDecomp` and `TheoremThreeAllUnitary` that don't obviously match. Metaplectic material: `CompanionTheory/ThickeningEstimates/LieGroupReduction/MetaplecticRepresentation`, `.../ThetaLifts/Reductions/MetaplecticDerivatives` (43 paths). | low |
| qN = M^k + R toy proof of Weil/Deligne | Possibly `Development/WeilBound` (7,051 files / 849k lines; `CoreStatements`, `RepresentationTheoryGL`, `ThetaLifts`), though that is a very large tree for a toy. Also `Formalism/GL3MeanSquares/GenusMeanAsymptotics/JacobiCharacterSums`. No literal "qN". | low |

Other large blocks worth naming in the video:
- `Development/AbelianVarietyTheory`: 8.1M lines, nearly half the archive.
- The "literature" scaffolding:
  - `Development/AbelianVarietyTheory/PublishedTheorems` (493 files / 56k)
  - `Development/WeilBound/CoreStatements/PublishedTheorems` (540 / 48.7k)
  - `PositivityTheory/AutomorphicForms/PublishedInputs` (445 / 55k)
  - `.../AutomorphicVarieties/LiteratureResults`
- `Development/ResolutionOfSingularities` (499 / 140.7k; Hironaka-style statement).
- The analytic endgame: `Formalism/ZetaNonvanishing` (Landau lemma, Mellin transforms), `Formalism/SizeWindowBrackets` (64 / 28k; for example `PowerBoundGivesRiemannHypothesis`, `GrowthBoundGivesRiemannHypothesis`), `Formalism/LandauZeroFreeBounds`, `Formalism/ZeroFreeRegion`.

Naming patterns: 5,571 declarations end in `_holds` and 184 in `_of_literature`. There are about 1,100 `def`/`structure`/`abbrev` names containing "Hyp". Combined with the 46,610 `*Statement.lean` files, this looks like a large agent-driven workflow that states a goal as a Prop and then discharges it later.

**Architecture artifacts:** there is no blueprint, README or docstring. The best architecture views are the five-line `Main.lean`, `Supplements/Kernels/MainTheorems.lean`, `CharacterBoxes/MainConclusion.lean`, the `OpenLiteratureStatements` bridge file, and the `Formalism/Statement*.lean` family (`Statement`, `StatementCM`, `StatementFL`, `StatementOC`, `StatementU`, `DefsOC`). Those top-level `Formalism` files read like checkpoint statements of intermediate claims.

## 5. What static inspection can and cannot establish

**It can establish:**
- The headline theorem uses Mathlib's `RiemannHypothesis`. The GRH statements use Mathlib's Dirichlet L-function and correctly exclude only the pole. Their scope is Dirichlet L-functions, not Dedekind or Hecke.
- The source contains no `sorry`, axiom declarations, `native_decide` or compiler-trust hooks, no `unsafe`/`extern`/`implemented_by` code, no kernel-skipping options, and no environment-mutating initialisers. The only meta code is a library-suggestion deny list plus three type-check-deferring helpers that still route through the kernel.
- Dependencies are standard upstream packages pinned to the official Mathlib release tag `v4.33.1` (August 2026). The transitive pins match Mathlib's own manifest exactly.
- The overall shape: GRH is the real target, RH is a 30-line corollary, and the heavy lifting runs through theta lifts, Galois representations, Sha bounds in a 2-adic cyclotomic tower, about 180 "literature" theorems proved in-repo, and a Landau-type analytic endgame.

**It cannot establish:**
- **That it compiles.** At 17.4M lines (many files with `maxHeartbeats` at 1M to 4M, a few unlimited, and many proofs deferred to kernel defeq through `kexactB`/`kcopy`), a build would take substantial machine time. No build logs or `.olean` artifacts were shipped. Until someone independently builds it, the claim "formalized without assumptions" is unverified.
- **The axiom footprint.** That needs `#print axioms riemannHypothesis` and the same for the other four theorems after a build. Ideally it would also include an independent kernel replay (for example lean4checker or another external checker) to guard against elaborator or environment tricks I can't see statically, or a Lean kernel bug.
- **Whether internal "Published" Props faithfully state the literature theorems they're named after.** This doesn't affect soundness of the endpoint, but it matters for any claim that Hironaka, local Langlands and so on were formalized. Placeholders like `UnusedSlot72 := True` show these labels can't be taken at face value.
- **The mathematics.** The code has no comments, and its names map poorly onto the note's narrative (no "Stepanov", "Vandiver", "Guinand", "Bost" or "sixfold"). Human understanding of the argument isn't something this archive provides.
- **Provenance.** It isn't possible to tell from the source alone how much was written by Claude and how much by Alpoge, though the naming and stripped comments suggest heavy automated generation.

## Method notes

- Pass 1: full stream, comment and string stripping, trust regexes on code lines, declarations, imports, per-directory line counts, keyword maps. About 13.5 min.
- Pass 2: raw-text counts of escape-hatch tokens, module-system-aware imports, and extraction of the main-chain files.
- Pass 3: docstring, "Stepanov", "Vandiver" and TODO counts, plus extraction of more files. Passes 2 and 3 together extracted 99 `.lean` files.
- Pass 4: global count of the comment markers `--` and `/-` with a positive control.
- Pass 5: unanchored meta-programming patterns, `open private`, and the statement identifiers.
- Extracted text: about 0.57 MB in a local scratch folder. Free disk never fell below about 6 GB.
- Mathlib provenance: GitHub API checks of the tag ref, the commit's parent and changed files, a compare against master, and a manifest diff against Mathlib's own `lake-manifest.json` at the tag.
- Regex declaration counts are approximate. They count line-start keywords after attributes and modifiers.
