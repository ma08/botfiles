# Options

Settle the ones that change the plan with a few one-at-a-time questions; default the rest and say so.

## Content

| Option | Default | Notes |
|---|---|---|
| Audience depth | Smart generalist with one deep beat | Lay: all metaphor, no formulas. Technical: show the key formula and the formal statement. One "deep beat" (about 30 to 40 s) names the actual idea. |
| Length | About 5 min | Narration at about 150 wpm (with a 4% tempo-up, about 155). 5 min is about 650 to 750 words across 10 to 14 scenes. |
| Framing of unverified claims | Attribute, never assert | See live-claims.md for a wording ladder from "claimed" to "independently verified". |
| Status freshness | Data-driven status lines with an "as of" stamp | Put time-sensitive facts in `script/status.json` and reference them as `{key}` in lines, so a refresh is one file edit plus re-voicing the changed lines. |
| Companion deliverables | None | Written deep dive, X thread, LinkedIn post, thumbnail. |

## Look

| Option | Default | Notes |
|---|---|---|
| Theme | `ink` | `ink`: cool near-black, blue accent, Instrument Serif + Inter + JetBrains Mono. `zone-night`: warm black, orange, Cormorant Garamond italic + DM Sans + DM Mono (the worked example). `paper`: light editorial, Newsreader + IBM Plex. `observatory`: navy and gold. |
| Project design system | Use it if the repo has one | Map its tokens onto the names in `src/theme.ts` (bg, fg, muted, line, accent, ...). |
| Format | 1920x1080, 30 fps | Tested. Vertical or square output needs scenes re-laid (absolute pixel layouts); untested. |
| Captions | Both a burned-in cut and a clean cut with SRT | Burned-in suits X and LinkedIn autoplay (muted). |
| Transitions | Each scene fades through the background color | Set `instant` on scene 1 so frame 0 (often the poster) isn't black. |

## Voice and sound

| Option | Default | Notes |
|---|---|---|
| Provider | ElevenLabs `text-to-speech/{voice}/with-timestamps` | The only tested path. Other providers need per-word timings in the same `timeline.json` shape. |
| Voice | A premade ElevenLabs voice | Make a lineup clip of 4 to 8 voices reading the same opening, with timestamps, and let the user pick by ear. |
| Model | `eleven_multilingual_v2` | `eleven_v3` is more expressive, but tone and name pronunciation drift between separately generated clips; check seams. |
| Seed | Fixed (4242) | Per-scene `seed` overrides re-roll one take. The seed is part of the audio cache key. |
| Tempo | 1.0 | 1.04 tightens pacing without audible pitch change (ffmpeg atempo). Word timings are divided by the tempo automatically. |
| Draft mode | Available | `tts.py --draft` estimates timings from word counts. Silent render, no key. |
| Music | Off | `scripts/music.py` generates an ElevenLabs Music bed, trims trailing silence, fits it to the narration, normalizes to about -30 LUFS. |
| Final loudness | -14 LUFS integrated, -1.5 dBTP | `scripts/loudnorm.py`, two-pass, video copied. |

## Process

| Option | Default | Notes |
|---|---|---|
| Decode pass | On for hard topics | A strong model labels every claim as source, background or reading. |
| Accuracy reviews | Script review before voicing; on-screen review after building | A second strong model; see accuracy-review.md. |
| Scene building | Parallel subagents for 6+ scenes, each owning its files | Fall back to sequential if your agent can't spawn subagents. |
| Delivery cadence | Final cut only | Or a rough cut first, then polish after notes. |
