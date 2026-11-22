# Explaining a fresh or contested claim

Status changes by the hour after a big announcement. In the worked example the verification picture moved from "claimed" to "six independent checkers accept it" within a day, and a morning snapshot was stale by the afternoon.

## Gather status first-hand
- Read the verifiers' own pages and the expert forum thread directly; news articles relay late and sometimes wrong. Note the page's "last updated" time and the time you read it.
- If a page needs a login you don't have, say so instead of relying on summaries.
- Hash the primary source (PDF, archive) and re-check it before rendering in case it was revised.
- Save a dated snapshot file: what passed, what's pending, who checked, caveats the checkers themselves state.

## Make status data, not prose
- Put every time-sensitive phrase in `script/status.json` (`asof_spoken`, `asof_onscreen`, `pending_spoken`, a `checks` list) and reference it from lines as `{asof_spoken}`.
- Show an "as of" stamp (`<StatusStamp />`) for the whole status beat, plus the checkers' own caveats as a footnote.
- Refresh = re-read sources, edit `status.json`, `python3 scripts/tts.py` (re-voices only changed lines), re-render.

## Wording ladder (pick the rung the evidence supports)
1. "X says/claims ..." (announcement only)
2. "Others have compiled it; checks so far report ..." (partial independent checks)
3. "Independent checks report every file compiles, it uses only the standard axioms, and N independent checkers accept it; one official run is pending" (machine side nearly complete)
4. "The formal proof has been independently verified" (all checks done). Even here, the narrator doesn't say "X is proved" flatly; "if it holds up" stays on big conclusions until people understand the argument.

Keep separate what machines have checked and what humans understand. "No human-readable proof has been released" is not the same as "none exists".
