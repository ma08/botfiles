---
name: explainer-video
description: Make a narrated, animated explainer video (about 1 to 8 minutes, 1080p MP4 with captions) about a technical, scientific or mathematical topic, paper, announcement or claim, from sources through research, script, accuracy review, AI voiceover with word-synced animation in Remotion, QA, render, thumbnail and social copy. Use when someone asks for an explainer video, an animated walkthrough of a paper or proof, a narrated visual summary for X/LinkedIn/YouTube, or to reuse the worked Riemann Hypothesis example. Not for editing existing footage.
---

# Explainer Video

Turn sources into a narrated, animated explainer: real data in every visual, narration synced word by word, an honest framing of anything unverified, and a render that's ready to post.

Example output: a 5-minute explainer of a claimed Riemann Hypothesis proof, posted at https://x.com/curious_queue/status/2124124652192862458. Its full source, generated audio, review history and a "how it was made" writeup are at https://github.com/ma08/botfiles/tree/main/context/daily/2026-11-20/rh-explainer-video (in the botfiles repo this skill comes from). Read that writeup once before your first project; its `project/` folder shows 12 finished scenes and a data generator (`scripts/gen_data.py`).

## What you need

- Node 18+ with npm, Python 3.10+, `ffmpeg`/`ffprobe`. Remotion downloads its own headless Chrome on first render.
- Optional `ELEVENLABS_API_KEY` for the voiceover and music bed. Without it, draft mode renders a silent, captioned video with estimated timings.
- Optional `OPENAI_API_KEY`, only for the transcription QA script.
- Remotion has its own licence terms for companies: read https://www.remotion.dev/license before using it commercially.

## Options (settle these with the user before building)

Ask only what changes the plan; use defaults otherwise. Full table: [references/options.md](references/options.md).

| Option | Default | Choices |
|---|---|---|
| Audience depth | smart generalist + one deep beat | lay, generalist, technical |
| Length | about 5 min (650 to 750 narration words at about 150 wpm) | 1 to 8 min |
| Look | `ink` preset, or the project's own design system if it has one | `ink`, `zone-night`, `paper`, `observatory`, custom tokens |
| Voice | ElevenLabs premade voice, `eleven_multilingual_v2` | any ElevenLabs voice/model; `eleven_v3` is more expressive but drifts between clips; draft (no voice) |
| Music bed | off | ElevenLabs Music ambient bed, about 10 dB under the voice |
| Captions | burned-in cut plus clean cut plus SRT | either |
| Framing of unverified claims | "claims", "says", "according to"; never "proved" in the narrator's voice | live status block with an "as of" stamp |
| Review loop | a second strong model reviews the script and on-screen text | skip for low-stakes topics |
| Delivery | final cut only | rough cut first, then polish |

Format: 1920x1080 at 30 fps is the tested path. Vertical or square output needs re-laid scenes (layouts use absolute pixels); treat it as an untested extension. Other TTS providers also work only if you produce per-word timings in the same `timeline.json` shape; that is an untested extension point.

## Workflow

Keep a short task record (sources, decisions, status, timestamps) if the repo has a convention for one. Put large renders outside git.

### 1. Sources and status
- Read the primary source completely (paper, note, announcement, code). Save a local copy and its hash if it might change.
- Find what independent people say. Prefer first-hand pages (the verifier's own page, the forum thread) over news relays, and record the time you read each.
- If the topic is a fresh or contested claim, write a status snapshot: what is verified, by whom, what is pending, as of when. See [references/live-claims.md](references/live-claims.md).

### 2. Decode (for hard topics)
Ask a strong model (or a subagent) for a decode with every claim labelled: the source says it, standard background, or the decoder's own reading. Then a ranked list of the key ideas, the accuracy risks, and a first scene outline. Never present the decoder's reconstruction as the source's claim.

### 3. Plan and decisions
Draft the scene list (about 10 to 14 scenes for 5 minutes, one idea each) and put the open options to the user in a few one-at-a-time questions. Show style choices as rendered stills, and voice choices as short audio samples, rather than describing them.

### 4. Scaffold
```bash
python3 <skill>/scripts/new_project.py <project-dir> --theme ink   # copies template, npm install, draft timeline
```
The template is a working 2-scene example (Euclid's proof). Read `src/scenes/S01Hook.tsx` and `S02Proof.tsx` for the patterns before replacing them.

### 5. Script and voice
- Replace `script/script.json`: `meta` (title, subtitle, kicker, attribution for the thumbnail), `voice`, `timing`, `pronunciations`, and scenes of short spoken lines. Plain spoken English, about 150 wpm, contractions fine, no hype.
- Respellings in `pronunciations` must be one token ("Duh-leen", not "Duh leen") so spoken and caption words stay one-to-one.
- Run the accuracy review in [references/accuracy-review.md](references/accuracy-review.md) and apply its must-fix lines before voicing.
- After any edit to `script.json`, rebuild the timeline (`tts.py --draft` or `tts.py`); scenes and the thumbnail read `src/data/timeline.json`, not the script.
```bash
python3 scripts/tts.py --draft      # silent timings from word counts; no key needed; renders carry a DRAFT badge
python3 scripts/tts.py              # ElevenLabs voice + word timestamps (changed scenes only)
python3 scripts/music.py            # optional music bed, fitted to the narration
```
Send the user a clip of every proper name as spoken before voicing the rest, and ask them to approve it. A transcriber can't judge pronunciation.

### 6. Build scenes
- One component per scene in `src/scenes/`, registered in `src/scenes/index.ts`. Key every beat to a spoken word with `wordFrame(scene, 'word')`; never hard-code frames. When a word repeats, scope it to a line: `wordFrame(S, 'squared', {line: 2})`. `python3 scripts/words.py <scene>` lists every spoken word with its line and occurrence number.
- For math, use `src/components/Math.tsx` (`Radical`, `Frac`, `Sup`, `Sub`); display serifs often lack glyphs like √, and font fallback looks wrong.
- Draw from real data generated by a script (`scripts/gen_data.py` in the worked example), not typed numbers.
- For 6+ scenes, split them across parallel subagents if your agent supports that, each owning its own scene files, using [references/scene-builder-brief.md](references/scene-builder-brief.md). Each builder renders and looks at its own stills before reporting.
- Every scene needs its honesty labels on screen (for example "schematic", "from the note", "our reading of the code").

### 7. QA gates (see [references/qa-checklist.md](references/qa-checklist.md))
- `npx tsc --noEmit` and `python3 scripts/check_anchors.py`: types pass and every word anchor exists in the narration.
- `node scripts/stills.mjs`: one still per narration line plus contact sheets. Look at every sheet: picture matches caption, nothing clipped or under the captions, no empty frames. To read small text, render chosen frames at full size: `node scripts/stills.mjs <scene> --frames 120,300 --scale 1`.
- A second model reviews all on-screen text against the stills and the evidence.
- `python3 scripts/check_audio.py`: transcription diff per scene (optional, needs `OPENAI_API_KEY`).
- Re-check any live status right before the final render and update `script/status.json`.

### 8. Render and finish
```bash
npx remotion render src/index.ts ExplainerCaptioned out/explainer-captioned-raw.mp4
npx remotion render src/index.ts Explainer out/explainer-raw.mp4
python3 scripts/loudnorm.py out/explainer-captioned-raw.mp4 out/explainer-captioned.mp4   # -14 LUFS
python3 scripts/make_srt.py
npx remotion still src/index.ts Thumbnail out/thumbnail.png --frame=0
```
Check the final file itself with `python3 scripts/check_final.py out/explainer-captioned.mp4` (streams, duration vs timeline, loudness, long silences, and a sheet of frame 0 plus both sides of every scene boundary), and transcribe the final mix (`scripts/check_audio.py --file ...`). Make a smaller preview (720p) if a chat or upload limit applies.

### 9. Social copy
Draft posts in the user's own voice if you have samples, with the honest status line and sources. Tagging people notifies them; ask first. Flag any line that speaks for the user (a reaction, how long it took). Post nothing yourself.

## Honesty rules

- The narrator never asserts an unverified result. Attribute it ("he says", "according to the note"), and keep "may" and "if it holds up" on bold conclusions.
- Distinguish what the source says, what is standard background, and what is your reading, both in narration and on screen.
- Credit people by name in text. Don't use company or product logos in a way that suggests endorsement.
- Disclose the AI voice in the credits or end card. Cite sources on the end card or in the post.
- Don't commit copyrighted source images or full texts into a public repo; fetch them at build time instead.

## Files

- `scripts/new_project.py`: scaffold a project from `assets/template/`.
- `assets/template/`: the Remotion project (theme presets, timing and animation libraries, scene frame, captions, status stamp, math components, thumbnail, a 2-scene example) and its scripts: `tts.py`, `music.py`, `words.py`, `check_anchors.py`, `check_audio.py`, `stills.mjs`, `check_final.py`, `make_srt.py`, `loudnorm.py`.
- `references/`: options, accuracy review prompts, scene-builder brief, QA checklist, live claims, pitfalls.

Read [references/pitfalls.md](references/pitfalls.md) before the first render: it lists the failures that cost the most time last run.
