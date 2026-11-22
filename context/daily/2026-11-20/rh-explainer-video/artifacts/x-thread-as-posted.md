# The X thread, as posted

Posted by Sourya Kakarla (@curious_queue) on 2026-11-21 at about 4:56am PST. The authoritative copy is the live thread:
https://x.com/curious_queue/status/2124124652192862458

Transcribed from the signed-in web view shortly after posting. X collapses long posts behind "Show more", and the web view only exposed the collapsed text for posts 2 to 4. Where the visible text stops, this file says so and quotes the draft in italics; the posted text may differ in small edits, so check the live thread.

## 1/ (with the captioned video attached)

> i got curious and built this 5 min explainer (using opus 5.5) for myself to understand
>
> - what exactly the Riemann Hypothesis is
> - how the proof by @__alpoge__ worked
> - the major insights etc.
>
> wild times... let em tokens compound into understanding of all that is and beyond!!

## 2/

> the proof (alpo.ge/remark.pdf) is 17.4M lines of lean with zero comments
>
> (nobody has a human-readable proof yet apparently)
>
> RH in one line: the primes are about as regular as they could possibly be
>
> "regular" here means: estimate how many primes there are below x with a ...

*(collapsed by X here; the draft continued: "smooth formula (li(x)), and you're never off by much more than √x (precisely: off by at most ~√x·log x, for every x, forever. and it's known the error can't be much smaller than √x, so that's the best case) e.g. below a trillion: ~37.6 billion primes, and the formula misses by only ~38k")*

## 3/

> the idea, per the note:
> - in the finite-field version of RH, stepanov's trick works: build a polynomial that vanishes with high multiplicity
> - multiplicity needs derivatives
> - you can't differentiate integers (d/dx of 7 is just 0)
> - workaround: chain "theta lifts", each one ...

*(collapsed by X here; the draft continued: "mimicking one more order of multiplicity" and "~√X of them. per the note that number was claude's suggestion")*

## 4/

> what's been checked (as of ~7pm PT nov 20, per andrew sutherland's page + lean zulip):
> - all 175,187 files compile, in several independent builds
> - the 5 main theorems use only lean's 3 standard axioms
> - full kernel replay: zero rejections
> - 6+ independent proof checkers accept ...

*(collapsed by X here; the draft continued: "the official comparator run finishes over the weekend" and "the lean folks went from \"is this real\" to \"ok how do we read it\" in about 7 hours")*

## 5/

> note: alpo.ge/remark.pdf
> checks: math.mit.edu/~drew/grh/
> lean zulip thread: #general > "Discussion: Alpöge Proves the Riemann Hypothesis": (link to the thread)
>
> (video: script + animations built with claude code using opus 5.5+fable 5.2, voice is elevenlabs)

## 6/

> apologies from me and claude if any issues with name pronunciation :/
>
> it did its best to verify

## What changed from the draft

The draft had a separate "why it matters" post ("if it holds up, this may be one of the first major proofs a machine checked before anyone could fully explain it"). Sourya cut it, wrote his own opener, folded the proof facts into post 2, credited both models in the sources post, and added the pronunciation note.
