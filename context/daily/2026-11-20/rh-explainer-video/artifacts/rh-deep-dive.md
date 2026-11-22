# The Riemann Hypothesis claim of Nov 20, 2026: a deep dive

Written for Sourya. Status lines were refreshed to about 6:55pm PST, Nov 20, 2026, and will go stale fast.

Four labels run through this piece. "The note says" means Alpöge's four-page note. "Standard background" is textbook mathematics. "Read in the Lean" means text we read in files from the archive (nothing was compiled by us). "My reading" is reconstruction, and you should discount it accordingly.

## 1. The one-paragraph version

On Nov 20, Levent Alpöge, a number theorist at Anthropic, posted a short note saying that he and Claude found a proof of the Riemann Hypothesis (RH), and released 17.4 million lines of Lean code as the proof. No human-readable proof came with it. The Lean file's headline theorem is Mathlib's own statement of RH, plus the generalization to all Dirichlet L-functions (GRH). As of about 6:55pm PST, Nov 20, several independent builds had compiled all of it, it rests only on Lean's three standard axioms, every module had been replayed through the kernel, at least six independent proof checkers had accepted the full proof, and an independent comparison tool had confirmed the five statements match. Only the official `lake comparator --paranoid` run was still going, expected over the weekend. So the machine side is effectively settled by the Lean community's account, and the human side is close to empty: nobody, including by his own account the author, yet understands the whole argument. The note's central idea is that a chain of "theta lifts", about √X of them, can play the role that derivatives play in a 1969 proof of the analogous theorem over finite fields.

## 2. What RH says, built up from primes

All of this section is standard background.

Let π(x) be the number of primes up to x. Primes thin out: near a large number t, roughly one in log t numbers is prime. Adding up that density gives the logarithmic integral,

> li(x) = ∫ dt / log t (from 0 to x, or from 2 if you prefer Li)

and the Prime Number Theorem (1896) says π(x)/li(x) tends to 1. The fit is very good. Up to 10^12 there are 37,607,912,018 primes and li overshoots by just 38,263.

RH is a statement about how good the fit stays forever. It's equivalent to

> |π(x) − li(x)| ≤ C · √x · log x.

What's proved without RH is far weaker: the known error terms don't even reach x^0.999.

Where do zeros come in? Riemann (1859) studied

> ζ(s) = Σ 1/n^s = Π over primes p of 1/(1 − p^(−s)), for Re s > 1.

The sum is over all integers and the product is over primes, which is why ζ knows about primes. The formula only converges for Re s > 1, but ζ extends uniquely to the whole complex plane (apart from a pole at s = 1), and the extension has zeros. Some are boring (−2, −4, −6, ...). The rest lie in the strip 0 < Re s < 1. RH says every one of them has real part exactly 1/2. More than 10^13 have been checked numerically and all sit on the line.

The link between zeros and primes is the explicit formula. Use a weighted prime count, ψ(x) = Σ_{n≤x} Λ(n), where Λ(n) is log p when n is a power of a prime p and 0 otherwise. Then

> ψ(x) = x − Σ_ρ x^ρ/ρ − (small explicit terms),

summed over the nontrivial zeros ρ. This is a Fourier-style decomposition, and it's the "music of the primes". Write ρ = β + iγ. Then x^ρ = x^β · e^(iγ log x): a wave in log x with frequency γ and amplitude x^β. The main term x is the smooth trend, and each zero adds an oscillation. Zeros come in mirrored pairs around the line Re s = 1/2, so if any zero is off the line, one of the pair has β > 1/2 and its wave grows faster than √x. If all zeros are on the line, every wave has amplitude √x and the total error is about √x times logs. That's why √x: it's the quietest the waves can be.

## 3. GRH and why people care

Standard background. A Dirichlet character χ mod q is a periodic, multiplicative function on the integers, a kind of discrete Fourier mode on the residues mod q. Twisting the zeta sum by it gives a Dirichlet L-function, L(s, χ) = Σ χ(n)/n^s. These govern primes in arithmetic progressions (primes that are 3 mod 4, say). GRH says all their zeros in the strip are on the line too. RH is the special case of the trivial character.

Concrete consequences of GRH:

- Primes are evenly spread across residue classes with square-root error, uniformly in the modulus. Unconditionally we only know this for tiny moduli or on average.
- The Miller primality test becomes deterministic and fast: the smallest witness is at most 2(log n)^2.
- The least quadratic non-residue mod p is O(log^2 p), where the unconditional bound is a small power of p.
- Class group and class number computations get provable running times.
- Hundreds of published theorems begin "assuming GRH". Those would become unconditional (the ones that need only the Dirichlet case, see the scope note below).

On cryptography, to be precise: GRH doesn't break encryption. It says nothing about factoring being easy. It makes some algorithms provably correct or provably fast that were already used in practice, and deterministic primality testing was already unconditional since AKS (2002).

Scope note, read in the Lean: "GRH" in this archive means all Dirichlet L-functions, every modulus and character. It doesn't cover zeta functions of number fields or Hecke L-functions. The note calls that further case the Extended Riemann Hypothesis and says only that he expects it "with more time". It isn't claimed.

## 4. The finite-field template

Standard background, except where marked.

There's a parallel world where RH is a theorem. Replace integers with polynomials over a finite field F_q. Primes become irreducible polynomials, and the question turns into counting points on a curve over F_q. André Weil proved that RH in the 1940s: the point count differs from q + 1 by at most 2g√q, where g is the genus. Pierre Deligne proved the higher-dimensional version in 1974.

In 1969 Sergei Stepanov found an elementary proof for certain curves, later generalized by Bombieri and Schmidt. The trick, for a curve like y² = f(x) over F_p:

1. Build a nonzero auxiliary polynomial that vanishes to order at least m at every point you want to count.
2. Keep its degree D under control.
3. A degree-D polynomial has at most D zeros counted with multiplicity. So (points) × m ≤ D.

With m = 1 this gives nothing. The saving comes entirely from multiplicity: each point is charged m times against a fixed degree budget. With m around √p you get the square-root bound. And multiplicity comes from derivatives, which in characteristic p are cheap, because x^p differentiates to zero.

Here's the wall. Polynomials have d/dt. Integers don't: any derivation d on Z satisfies d(1) = 0 and therefore d(n) = 0. There's no variable to differentiate "7" with respect to. People have worked on substitutes for decades (the "field with one element", Borger's λ-rings, Fermat quotients), and none had produced Stepanov-style multiplicity for ζ. The note says the same thing in its own words: multiplicity is hard to find over the integers, corresponding to something like differentiating whole numbers.

## 5. The new idea, per the note

A caution first. The note is an announcement plus a dated list of 20 fragments. It contains no proof sketch. Alpöge writes that parts of the list paraphrase a Claude-written summary and might make no sense. So this section separates carefully.

**The chain of theta lifts (the note says).** The argument is described as a descendant of Stepanov's. In place of derivatives it chains theta lifts, each one "mimicking multiplicity". A theta lift (standard background) is an operation that transfers an automorphic form from one group to a partner group, using a theta function as the integral kernel. The note's timeline has lifts running U(X₀) → U(X₁) → ... → U(X_m) between "totally definite unitary groups", winning multiplicity m. Those groups are compact, so forms on them are functions on finite sets (standard background), which makes sizes and divisibility computable.

**The √X ladder (the note says).** For a von Mangoldt sum of length X, Claude suggested a chain of length √X. Alpöge presents this as the line that will make mathematicians fall out of their chairs, and adds "what else could it be?" That fits the template: Stepanov takes m near √q to count about q points. We found nothing in the Lean that confirms or refutes the √X count. There's a parameter of size about √x in one file, but we can't say what it counts, so don't lean on it.

**The sign-only toy (the note says, and it's unverified).** Alpöge says he had a new proof of Weil's and Deligne's theorems in the finite-field setting that uses only signs, summarized as qN = M^k + R. My reading of the footnote: take a sum M you want to bound, and form a k-fold sum over a "path" quadric x₁x₂ + ... + x_{k−1}x_k. One way of evaluating gives q·N, a weighted point count whose sign is known from geometry. The other gives M^k plus a remainder R that is small by applying Parseval k times. If N and M^k have opposite signs they can't cancel, so |M|^k ≤ |R|, and large k gives the square-root bound. The appeal is that it needs only a sign and repeated Fourier duality, both of which have number-field analogues. Three caveats: this toy proof is unpublished; nobody outside has checked it; and two Lean Zulip participants reported it doesn't appear in the released Lean (second-hand, we didn't verify it beyond finding zero hits for "Stepanov"). The formal proof doesn't rest on it.

**Automorphy as the source of the sign (the note says; mechanism is my reading).** In the finite-field world a sign comes from cohomology. The note says he searched for a "natively automorphic" determinant to play that role, and that the turning point was seeing "multiplicity 2 on O(2,n)" with it. After that, more lifts meant more multiplicity and "we were going to win". My reading: multiplicity one only reproduces known results, so getting two showed the barrier could be broken, and iteration followed.

**Divisibility as multiplicity (my reading).** Several timeline items concern divisibility of period values by powers of primes, norms of lifts, and mass formulas. The most coherent interpretation is that "vanishing to order m" becomes "divisible by a high prime power", and the degree count becomes: an integer that is highly divisible yet small must be zero. The note never states this.

**Towers (the note says; identification is my reading).** The note uses an "Iwasawa tower" by analogy with Weil's use of all extension fields F_{q^n} at once, chosen "using Behrend", a step he expects to be unnecessary. Read in the Lean: number fields in the 2-power cyclotomic tower appear in a hypothesis of the final assembly, and Felix Behrend's construction of sets without three-term progressions (in a strengthened form) appears in the archive via Mathlib. That these are what the note means is a natural reading, and neither was traced to the main theorem. The note also mentions fighting for "a significant weakening of Vandiver", a statement about class groups. That's the note's description; the name doesn't occur in the Lean.

**How it ends (read in the Lean).** This is the one part with solid footing. For each character family the Lean forms a smoothed prime sum. Its zeta part is

> Gz(x) = Σ_{n≤x} Λ(n)(x/n − 1) − x log x + (1 + γ)x,

which matches the expression in the note's item 5 term for term. Standard background: Gz(x) equals minus a sum over zeros of x^ρ/(ρ(ρ−1)), so bounding it by about √x is RH-strength. The Lean adds positively weighted character twists to get Gm(x), proves Gm(x) ≤ x^(1/2+cε) on long windows of x arbitrarily far out, and then applies a classical lemma of Landau: a one-sided bound like this forces every L-function in the family to be nonzero for Re s > 1/2. Extending to all characters gives GRH, and RH drops out as a corollary via the trivial character and the functional equation. Two points worth noticing. The Lean proves GRH first and RH from it, the reverse of the note's telling. And the note's timeline talks about Weil positivity, but the formal ending we read is Landau's one-sided bound. Everything upstream of that inequality, which is where the theta lifts live, we didn't read. Nobody on this task did.

## 6. What's in the Lean and what's been checked

**The archive (our static scan).** 175,187 Lean files, 17,374,215 lines, 1.03 GB of source. `Main.lean` is 12 lines with five theorems. The headline is `theorem riemannHypothesis : RiemannHypothesis := rhOfAll`, where `RiemannHypothesis` is Mathlib's own definition and isn't redefined anywhere. Zero `sorry`, zero `axiom`, zero `native_decide`. Also zero comments or docstrings: the code is readable only through names.

**Independent checks, as of about 6:55pm PST, Nov 20** (Andrew Sutherland's page at MIT, updated 2:05pm PST, plus the Lean Zulip thread, both read first-hand):

| Check | Result |
|---|---|
| All 175,187 modules compile (Lean v4.33.1, Mathlib v4.33.1) | pass, zero errors |
| Axioms behind the five main theorems | only `propext`, `Classical.choice`, `Quot.sound` |
| Mathlib binaries identical to the official cache | pass |
| `leanchecker` kernel replay | 175,187 of 175,187, zero rejections |
| `nanoda` (independent Rust kernel) on the 61.57 GB export | accepts |
| `lean4lean` module by module | 175,187 of 175,187 pass |
| `con-leche` (verified checker) on the export | accepts |
| `con-leche --compare` (independent statement comparison) | all five theorems confirmed against the challenge |
| Other independent checkers (Lean Zulip, Szymon Teżewski and others) | con-agua, Pestka, nanoclo, tenet accept; a second from-scratch build plus nanoda also passes |
| Several more independent builds | compiled-file hashes match Sutherland's |
| `lake comparator --paranoid` (Lean's own kernels on the export) | running; Sutherland expects it to finish over the weekend and says he has "no doubts about the outcome" |

Caveats from the page itself: Sutherland's checks were run with Claude Code, on an unsandboxed cloud build. That doesn't weaken a kernel verdict, because the kernel isn't Claude, and other people's independent builds match his. On the forum, Lean developer Joachim Breitner wrote that the independent checking "passed without a hitch", and Sutherland said he sees no realistic scenario in which the proof doesn't imply Mathlib's statement of RH.

**The trust story.** A Lean proof is a giant term in a small formal language. The kernel is a small program that checks the term really has the type of the theorem. Elaborate tactics and AI-written code upstream don't need to be trusted, because only the final term is checked. So what you trust is:

1. The kernels. Six or more independent implementations agreeing, at least one of them formally verified, makes a shared bug extremely unlikely.
2. Mathlib's definitions. The theorem is about Mathlib's `riemannZeta`. If that definition were subtly wrong, the proof would be about the wrong object. It's widely used and reviewed, which is why the statement being Mathlib's own matters so much.
3. Three axioms that nearly all of Lean mathematics uses: propositional extensionality, the axiom of choice, and quotient soundness.

What a kernel check tells you: the stated theorem follows from the axioms. What it doesn't tell you: why it's true, whether the argument is anything like the note's description, or whether any of the intermediate ideas are reusable. The archive contains about 180 internal propositions named after results from the literature, and soundness doesn't depend on those names being faithful. Nobody has checked that they are.

## 7. The major unblockers, ranked

Ranked by the emphasis the note gives them. This is the note's weighting, with no verified weight in the Lean.

1. **Chained theta lifts as multiplicity, with length √X.** You can't differentiate an integer, but you can repeat a symmetry transfer, and each repetition does one derivative's job. (The note credits the length to Claude.)
2. **The sign-only toy proof.** Two quantities forced to opposite signs can't hide each other, so each is as small as the leftover. (Unpublished, reportedly absent from the Lean.)
3. **Sign from automorphy, and multiplicity 2.** Symmetry supplies the positivity that geometry supplies over finite fields; getting past order one showed the route was open.
4. **The right test quantity.** A smoothed prime sum whose zero-sum converges absolutely, so that a one-sided bound is enough. (This one is confirmed in the Lean's ending.)
5. **Divisibility versus size.** A whole number divisible by a huge prime power but small must be zero. (My reading of several items.)
6. **A tower of number fields.** Climb fields the way Weil climbed F_q, F_{q²}, ... to squeeze out constants. (The note; plus an averaging or "division" step it says was needed to get from 2/3 to 1/2, which we couldn't decode.)

## 8. Open questions and what to watch next

- **The last comparator run.** `lake comparator --paranoid` is expected over the weekend. Nobody on the forum expects a surprise; the formal claim is already about as settled as formal claims get.
- **A human-readable write-up.** Alpöge says he'll write it properly. He mentions an auto-generated document of 250,000+ pages that he chose not to post.
- **Simplifications.** He expects the argument to shrink "massively" and soon, and names the Behrend step as one he thinks is unnecessary. A short proof would change everything about how this is absorbed.
- **The toy proof.** A sign-only proof of Weil's theorem is small enough for humans to check in days. If it's written up and holds, the story gains a lot of credibility as mathematics. If it doesn't appear, the note's account of the intuition stays unanchored.
- **Does the Lean match the note?** Someone needs to extract the real dependency cone of the main theorem and see whether theta lift chains of length √X are in it.
- **Masullo's human proof of GRH.** The same day, Ravi Vakil posted a "hurried announcement" of a separate, entirely human proof of GRH by Alessandro Masullo (a draft of roughly 940 pages that Brian Conrad has been reviewing for months). On the Lean forum, people running LLMs over the draft reported apparent errors in its main theorem; the draft itself says the author and Conrad know of "several glitches". Status unclear; we didn't investigate further. It doesn't bear on the Lean proof's correctness, but it does mean "first" claims about this week should be made carefully.
- **The Vandiver-type step.** If the proof contains a new theorem about class groups as a lemma, that's independently important and independently checkable.
- **Community digestion.** On the Lean forum the mood shifted during the day from "is this real?" to "how do we understand it?": people started informalization projects and dependency maps, and several called the code very hard to read. No specific flaw has been identified. Some formal-methods researchers criticized the timing of the announcement; the note itself calls the timing "horrible" and denies a cynical reading.

## 9. Why this matters beyond math

Stated soberly, and conditional on the remaining checks passing.

First, the order of events is new. Normally a proof is understood by its author, then by referees, and formalized years later if at all. Here the machine-checked artifact exists before any human understands it, including the author, who says so directly. Mathematics has always treated proof as both certification and explanation. This splits them. We may have the certificate without the explanation, and the community has no settled norms for that.

Second, the account of the collaboration, which is only the author's account. He describes supplying the long-held plan, the finite-field analogy and the direction, and says Claude outpaced him on the technical side in an area he hasn't mastered. If accurate, that's a model doing original research-level work, with a human setting direction. The archive can't show who contributed what.

Third, for a builder: formal verification is what made this claim checkable in hours by strangers. The same pattern (untrusted generator, small trusted checker) is the practical lesson for AI-written artifacts generally.

What it isn't: evidence about cryptography, or a finished piece of mathematics. Until people can explain why it works, most mathematicians won't treat it as done.

## 10. Glossary

- **Λ (von Mangoldt):** log p on powers of a prime p, zero elsewhere. The natural weight for counting primes.
- **ζ (zeta):** Riemann's function, Σ 1/n^s extended to the complex plane.
- **Dirichlet character:** a periodic multiplicative function mod q; a Fourier mode on residues.
- **L-function:** a zeta-like series twisted by a character or built from another arithmetic object.
- **GRH / ERH:** RH for Dirichlet L-functions / for number-field zeta functions (usage varies; this is the note's).
- **Explicit formula:** the identity writing a prime count as a main term minus one wave per zero.
- **Automorphic form:** a function with a very large symmetry group; a generalization of modular forms.
- **Theta lift:** a transfer of automorphic forms between two partner groups, using a theta function as kernel.
- **Landau's lemma:** a classical result on transforms of functions of one sign; it turns one-sided bounds into zero-free regions.
- **Iwasawa tower:** an infinite stack of number fields, the analogue of F_q, F_{q²}, ...
- **Lean:** a programming language and proof assistant.
- **Kernel:** the small program that checks a finished proof term.
- **Mathlib:** the community library of formalized mathematics for Lean.
- **Axiom:** a statement accepted without proof. Lean's standard three are `propext`, `Classical.choice`, `Quot.sound`.
- **nanoda:** an independent Lean kernel written in Rust.
- **comparator:** a tool that checks the statement proved is the one claimed, with allowed axioms, across kernels.

## Sources

Files in this folder:

- `research-math-decode.md`
- `research-reconcile-lean-decode.md` (takes precedence over the decode where they differ)
- `research-lean-archive.md` and `research-lean-main-statements.lean`
- `verification-status-snapshot-2026-11-20-630pm.md` (evening status, read ~6:55pm PST)
- `verification-status-snapshot-2026-11-20-1pm.md` (morning status, page content as of 11:45am PST)

Public:

- The note: https://alpo.ge/remark.pdf (Lean archive: https://alpo.ge/lean.tar.gz.part01 to part14)
- Andrew Sutherland's verification page: https://math.mit.edu/~drew/grh/
- Lean Zulip, #general, topic "Discussion: Alpöge Proves the Riemann Hypothesis" (read first-hand; no URL recorded in our snapshot)
- Scientific American: https://www.scientificamerican.com/article/anthropic-mathematician-claims-to-prove-riemann-hypothesis-most-famous-problem-in-all-of-math/
