# Scene builder brief (template)

Copy this into the project as `BRIEF.md`, fill in the brackets, and give each scene builder: the brief, its scene ids, and a visual direction per scene (what's on screen at each spoken beat). Builders work in parallel, so file ownership matters.

---

You build animated scenes for a <length>, 1920x1080, 30 fps Remotion video explaining <topic> to <audience>. Narration is already recorded (or drafted); visuals must sync to it.

## Project
- Root: `<project-dir>`. Don't run `npm install` or change `package.json`.
- Read first: `src/theme.ts`, `src/lib/anim.ts`, `src/lib/timeline.ts`, `src/components/SceneFrame.tsx`, `src/components/Math.tsx`, `src/components/StatusStamp.tsx`, `src/Root.tsx`, and one finished scene as a pattern (an existing scene in this project, or the template's example: https://github.com/ma08/botfiles/blob/main/claude/skills/explainer-video/assets/template/src/scenes/S01Hook.tsx).
- Timings: `src/data/timeline.json`. Use `sceneById(id)`, `wordFrame(scene, 'word')` or `wordFrame(scene, 'word', {line: L})` for repeated words, `lineStartFrame(scene, i)`, `sceneFrames(scene)`. `python3 scripts/words.py <scene>` lists words with line and occurrence numbers. Key every beat to a spoken word; never hard-code narration frames.
- Data: `src/data/*.json` (generated from real sources). Import JSON directly.
- Style reference: <path to the approved style still, or describe it>.

## File ownership
- Edit only your assigned `src/scenes/SNN*.tsx` files (keep the exported names). Helpers go under `src/scenes/sNN/`.
- Don't edit shared files (`theme.ts`, `lib/*`, `components/*`, `Root.tsx`, `scenes/index.ts`, data, script). If you need a shared change, say so in your report.

## Rules
- Deterministic: all motion from `useCurrentFrame()`. No CSS transitions or animations, no `Math.random` (use `random(seed)` from remotion), no `Date.now`, no network.
- Wrap each scene in `<SceneFrame index={N} kicker="...">`. Use `Title`, `Body`, `Em`, `Tag` where they fit; build custom SVG for data visuals.
- Nothing important below y = 900 (burned-in captions sit there).
- One idea on screen at a time, revealed in sync. Progressive reveals, drawn paths, counters, gentle camera moves. No static slides, no clutter.
- On-screen text is labels, numbers and honesty tags, not a copy of the narration.
- Real data only. Thousands separators. Minimal axis labels.
- No em dashes in on-screen text. Use "1/2" rather than "½" in mono fonts, and the `Math.tsx` components for radicals and fractions.
- To combine an entrance with your own opacity, pass it as the base: `enter(frame, start, 18, 18, 0.6)`, not `opacity` next to the spread.
- Tags and footnotes at 21 px or larger so they read on a phone.

## Honesty labels (must be on screen in the named scene)
- <scene>: <label, e.g. "schematic", "from the note", "our reading of the code, simplified", "as of <time>">
- Never on screen: <claims that are name-match only, unverified mappings, who wrote which part, etc.>

## Check your work (required)
- `npx tsc --noEmit` (report errors in files you don't own, don't fix them).
- `python3 scripts/check_anchors.py`.
- `node scripts/stills.mjs <scene ids>` renders a still per narration line plus a contact sheet; `--frames 120,300 --scale 1` renders chosen frames at full size. Open each image and look: legibility, overlap with captions, alignment, empty or cluttered frames, sync with what's said at that frame. Iterate. At least 6 stills per scene.
- Report in under 250 words: what each scene shows beat by beat, shared-file changes you need, open issues, and 2 representative still paths per scene.
