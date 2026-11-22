# Verification status snapshot (first-hand), 2026-11-20 ~6:55pm PST

Supersedes `verification-status-snapshot-2026-11-20-1pm.md` (whose content was as of 11:45am PST). Read directly in Chrome, logged out. Zulip timestamps are as displayed (PST).

The note is unchanged: live `alpo.ge/remark.pdf` sha256 is still 3fc97784…eb8d.

## Andrew Sutherland's page (https://math.mit.edu/~drew/grh/), "last updated 2026-11-20 22:05 UTC" (2:05pm PST)

New since the morning snapshot:
- con-leche master (independent, verified checker) accepts the full export: 1,468,418 declarations, exit 0 at 21:19 UTC.
- con-leche --compare (an independent implementation of Comparator's statement matching) confirms all five Main theorems against the challenge ("justified by the solution").
- lean4lean passes on all 175,187 compiled modules (five needed a raised step limit and passed on rerun).
- The morning's "con-leche declined" was an old bundled binary; the current version accepts.

Unchanged: all 175,187 modules compile; the five Main theorems use only propext, Classical.choice, Quot.sound; full leanchecker replay passes; nanoda accepts.
Still running: lake comparator (Lean v4.36.0) end to end, and Lean's default and paranoid kernels on the export.
Caveats on page unchanged (unsandboxed build; trust rests on the kernels and Mathlib's definitions).

## Lean Zulip, #general > "Discussion: Alpöge Proves the Riemann Hypothesis" (read to the 6:24pm PST message)

- Szymon Teżewski, 2:06pm: table of accepted runs on the export (sha256 5ea74b91…244e): con-leche --compare (all 5 theorems justified), con-leche, con-agua, Pestka, nanoclo, tenet. Earlier he also reported Pestka; two other checkers failed to finish (parse or performance), "neither is a rejection".
- Another participant, 2:06pm: independent from-scratch build plus nanoda, 175,187/175,187 modules, standard 3 axioms only.
- Another participant, 4:31pm: two more independent builds; olean hashes match Sutherland's exactly.
- Joachim Breitner (Lean developer), 1:10pm: multiple people have built and checked it with multiple checkers; "the independent checking has been done and it passed without a hitch." 12:50pm: "this proof is now very very thoroughly checked."
- Andrew Sutherland, 3:25pm: he doesn't see any realistic scenario in which the proof does not imply Mathlib's statement of RH; people should satisfy themselves that the formal statement is right.
- Sutherland, 3:41pm: running `lake comparator --paranoid`; expected to finish over the weekend; "no doubts about the outcome."
- Understanding: no human-readable proof released. Several community efforts to informalize (Principia Math, a 126-page AI-drafted preprint, a "riemann-review" repo, Tau Ceti roadmaps). Several participants describe the code as very hard to read ("obfuscated" in style). Toy proof (qN = M^k + R) still reported absent from the released Lean; no update.
- Side context, not for the video: a separate 940-page human GRH proof by Alessandro Masullo was announced the same day (Ravi Vakil's blog); a Zulip participant says it was shown to be wrong. Not investigated.

## Implication for the video
Machine verification: effectively complete by community consensus; only the official `lake comparator --paranoid` run is pending (weekend). Human understanding: not yet. New on-screen/narrated status: "six separately written proof checkers accept it"; pending: "the last official comparison run is expected over the weekend".
