# Scene builder brief (RH explainer)

This is the brief that was handed to the four scene-builder subagents, kept as written apart from removing private paths.

You build animated scenes for a ~5:06, 1920x1080, 30 fps Remotion video explaining the Riemann Hypothesis and Levent Alpöge's Nov 20, 2026 announcement (with Claude) of a Lean-formalized proof of RH and GRH (Dirichlet L-functions). Audience: smart generalists on X. Narration is already recorded; your visuals must sync to it.

## Project
- Root: this `project/` folder (Remotion 4.0.545, React 18, TS). Do NOT run `npm install` or change package.json.
- Read first: `src/theme.ts`, `src/lib/anim.ts`, `src/lib/timeline.ts`, `src/components/SceneFrame.tsx`, `src/components/StatusStamp.tsx`, `src/scenes/Placeholder.tsx`, `src/Root.tsx`.
- Narration + word timings: `src/data/timeline.json` (per scene: `lines` with start/end seconds, `words` with start/end seconds; times are relative to narration start, and `lib/timeline.ts` adds the scene `leadIn`). Use `sceneById(id)`, `wordFrame(scene, 'word', nth)`, `lineStartFrame(scene, i)`, `sceneFrames(scene)` to place beats. Never hard-code frame numbers for narration beats; key them to words so re-voicing keeps sync.
- Script text: `script/script.json`. Data (real, precomputed): `src/data/primes.json`, `zeros.json`, `explicit.json`, `lastdigit.json`, `curve.json`, `lean.json`, `notetimeline.json`, `status.json`. Import JSON directly (`import zeros from '../data/zeros.json'`).
- Image: `public/img/remark-1.png` (page 1 of the note), use `staticFile('img/remark-1.png')` with `<Img>`.
- Style reference still: a rendered frame of scene 3 in the approved "Zone night" look (not included). The look: warm black bg, cream text, Cormorant Garamond italic display, DM Sans body, DM Mono labels, orange accent used sparingly, soft glow on key data marks.

## File ownership (important: several builders work in parallel)
- Edit ONLY your assigned scene files `src/scenes/SXX*.tsx` (keep the exported component name). You may add helper files under `src/scenes/<your-scene-prefix>/` (e.g. `src/scenes/s04/Waves.tsx`).
- Do not edit shared files (`theme.ts`, `lib/*`, `components/*`, `Root.tsx`, `scenes/index.ts`, data, script). If you need a shared change, describe it in your final report instead.

## Rules
- Deterministic rendering: all motion from `useCurrentFrame()`. No CSS transitions/animations, no `Math.random` (use `random(seed)` from remotion), no Date.now, no network.
- Wrap each scene in `<SceneFrame index={N} kicker="...">`. Use `Title`, `Body`, `Em`, `Label` where they fit; build custom SVG/canvas for data visuals.
- Keep everything above the caption zone: nothing important below y = 900 (captions sit at the bottom ~150 px when enabled).
- The scene is on screen for its whole duration (`sceneFrames`); the frame fades in/out at edges. Fill the time with purposeful motion; avoid static slides and avoid clutter. One idea on screen at a time, revealed in sync with the narration. Prefer progressive reveals, drawing paths, counters, gentle camera moves (scale/translate of an SVG group).
- Text on screen must not just duplicate the narration; use short labels, numbers, and the honesty tags listed below.
- Use the real data. Label axes minimally. Numbers formatted with thin separators (e.g. 37,607,912,018).
- No em dashes in on-screen text. Plain wording.

## Honesty labels (must appear on screen in the named scene)
- s01: when "a broader version" is spoken: "Generalized Riemann Hypothesis, for Dirichlet L-functions". Name card: "Levent Alpöge · number theorist · Anthropic".
- s02: the smooth curve is li(x) (logarithmic integral), label it "li(x)". Show "π(10¹²) = 37,607,912,018" and "li − π = 38,263" when spoken.
- s03: "Checked numerically: more than 10 trillion zeros".
- s04: waves summing to a staircase must be labelled "ψ(x): primes and prime powers, weighted by log p". Under the GRH line: "primes ending in 7 = primes ≡ 7 mod 10".
- s05: "Weil: curves over finite fields · Deligne: all dimensions · Stepanov: certain curves (Bombieri 1973: all curves)".
- s06: multiplicity picture tagged "schematic".
- s08: ladder and √X counter tagged "from the note"; theta-lift picture tagged "schematic"; X labelled "length of the prime sum (von Mangoldt sum)". Do NOT say lifts go to a "larger" group.
- s09: toy tagged "Author's account · unpublished · reported absent from the released Lean (Lean Zulip, Nov 20)". Landau ending tagged "Our reading of the released code, simplified" + "smoothed, weighted prime sum" + "applied to zeta and to families of Dirichlet L-functions". If you show a formula: Gz(x) = Σ_{n≤x} Λ(n)(x/n − 1) − x log x + (1 + γ)x captioned "zeta-only version". Do not say "never overshoots".
- s10: "17,374,215 lines · 175,187 files (our count)"; "Mathlib" shown next to "Lean's shared math library"; "Text search: 0 sorry · 0 axiom · 0 native_decide (our scan; not a substitute for the kernel checks)". The `main_lean` lines in lean.json are verbatim; show them in DM Mono. Any dependency arrow "simplified".
- s11: `StatusStamp` (as-of timestamp) visible for the whole status beat; footnotes from status.json (`onscreen_footnote`, `onscreen_footnote_2`) on screen during the status line; list pending items by name; credit split tagged "per Alpöge's note". Read all status text from `src/data/status.json` (it will be refreshed before final render), never hard-code it.
- s12: "No human-readable proof released" (not "exists"). End card must include small credits: "Narration: AI voice (ElevenLabs). Sources: alpo.ge/remark.pdf · math.mit.edu/~drew/grh · Lean Zulip".
- Never on screen: claims that specific named literature results "were formalized", the m ≈ √x parameter in the code as "the chain", "weak Vandiver proved", who wrote which part of the code.

## Checking your work (required)
- Typecheck: `npx tsc --noEmit` from the project root (ignore errors in files you don't own, but report them).
- Render stills of your scenes at several frames, including each key beat and the last second: `npx remotion still src/index.ts Scene-s04-music out/stills/s04-f0450.png --frame=450` (composition ids are `Scene-` + scene id with `_` replaced by `-`; captions are ON in these per-scene comps). Open each PNG and actually look: legibility, overlap with captions, alignment, empty or cluttered frames, sync with what's being said at that frame (check `src/data/timeline.json`). Iterate until it looks crafted. Aim for at least 6 stills per scene.
- Optional quick motion check: `npx remotion render src/index.ts Scene-s04-music out/preview-s04.mp4 --scale=0.5` then sample frames with ffmpeg.
- Final report (under 250 words): what each scene shows beat by beat, any shared-file changes you need, open issues, and the paths of 2 representative stills per scene.
