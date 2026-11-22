# Verification status snapshot (first-hand), 2026-11-20 ~1:00pm PST

Read directly in a browser (logged out of Zulip; X not used).

## Andrew Sutherland's verification page (primary source)
URL: https://math.mit.edu/~drew/grh/ ("Page last updated 2026-11-20 19:45 UTC", i.e. 11:45am PST). Checks run with Claude Code.

| Check | Result |
|---|---|
| All 175,187 modules compile (Lean v4.33.1, Mathlib v4.33.1) | pass, zero errors, finished 16:43 UTC |
| `#print axioms` on the five Main.lean theorems | pass: propext, Classical.choice, Quot.sound only |
| No axioms declared outside Lean core | pass |
| Mathlib .olean files identical to official cache | pass |
| leanchecker kernel replay of every module | pass, 175,187 of 175,187, zero rejections, ~18:17 UTC |
| Challenge export matches Deicyde/riemann-hypothesis CI | match |
| nanoda (independent Rust kernel) on full 61.57 GB export | accepts, exit 0 at 19:05:45 UTC, 27 min 42 s on 80 threads |
| Lean default + paranoid kernel on the export | running, no verdict yet |
| lake comparator (Lean v4.36.0) end to end | running; statement comparison and axiom check already passed in one run |
| con-leche, con-ron | declined (unsupported reflexive inductive type), not a rejection |
| lean4lean | not applicable (version mismatch) |

Page states RiemannHypothesis is Mathlib's own definition and "GRH" here means Dirichlet L-functions only.
Caveats on the page: unsandboxed cloud build (compiled with direct lean calls, 77-module sample byte-identical to lake build); a pass relies on the kernels used and on Mathlib's definitions meaning what they should.
Source archive sha256 (14 parts joined, 239,275,554 bytes): 9631b4f0...7fc. We recorded each part's sha256 locally.

## Lean Zulip, #general > "Discussion: Alpöge Proves the Riemann Hypothesis" (read ~12:00pm PST)
- A participant (10:41am PST): code compiles on their machine; kernel replays pending.
- Kevin Buzzard (10:44am): several people report it compiles; awaiting a successful comparator run (paranoid mode: checks the statement isn't redefined, and checks with several independent kernels).
- Andrew Sutherland (11:09am): first independent-kernel verdict, nanoda accepts.
- Two participants (10:17 to 10:26am): the remark's sign-only toy proof (qN = M^k + R) does not appear to be in the released Lean; one is attempting a replication.
- A formal-proofs researcher (11:37am): suggests experts quarantine such announcements for weeks, citing market and finance context. Another participant alludes to the IPO.
- A participant asks when there will be reasonable certainty (two independent kernels); estimates in thread range from hours to ~3 days for full runs.
- Moderators keep the thread Lean-only; AI-generated comments disallowed.
- Separate thread exists: "Formalising Masullo's proof of GRH" (not investigated).
- Quanta "updates" page referenced: https://www.quantamagazine.org/updates/transformation/#169564 (not read).

## Implication for the video
Machine verification is largely passing: compile, standard axioms only, full kernel replay, and an independent kernel accept. Still pending at snapshot time: comparator end to end and the Lean kernels on the export. Human understanding: essentially none yet; no human-readable proof; the toy proof isn't formalized. Status-dependent lines must be data-driven with an "as of" timestamp and re-checked before final render.
