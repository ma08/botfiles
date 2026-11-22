# explainer-video

An agent skill (Claude Code and Codex) for making narrated, animated explainer videos about technical, scientific or mathematical topics: sources, research and accuracy review, script, AI voiceover with word-synced animation in [Remotion](https://www.remotion.dev/), QA, render, thumbnail and social copy.

## Example

[A 5-minute explainer of Levent Alpöge's claimed proof of the Riemann Hypothesis](https://x.com/curious_queue/status/2124124652192862458) (thread on X, Nov 21, 2026). The script, scene animation code, research and QA were done by Claude (Opus 5.5 orchestrating in Claude Code, Fable 5.2 for the math decode and accuracy reviews, four parallel subagents for the scenes) under human direction. The voice and music are ElevenLabs.

- Full-quality video, captions and thumbnail: [release `rh-explainer-2026-11-20`](https://github.com/ma08/botfiles/releases/tag/rh-explainer-2026-11-20)
- Everything behind it (source, generated audio, script and review history, and a "how it was made" writeup): [`context/daily/2026-11-20/rh-explainer-video/`](https://github.com/ma08/botfiles/tree/main/context/daily/2026-11-20/rh-explainer-video)

## What's in this folder

| Path | What |
|---|---|
| `SKILL.md` | The workflow the agent follows, the options, and the honesty rules |
| `scripts/new_project.py` | Scaffolds a new video project from the template |
| `assets/template/` | A Remotion project: four theme presets, word-synced timing helpers, captions, an "as of" status stamp, math components, a thumbnail, a 2-scene example (Euclid's proof), and the pipeline scripts (voice, music, anchor checks, stills, final-file QA, SRT, loudness) |
| `references/` | Options, accuracy-review prompts, a brief for parallel scene builders, a QA checklist, handling live claims, and pitfalls |

## Try it

```bash
python3 claude/skills/explainer-video/scripts/new_project.py ~/my-explainer --theme ink
cd ~/my-explainer
node scripts/stills.mjs                                   # stills + contact sheets (silent draft timings)
npx remotion render src/index.ts ExplainerCaptioned out/draft.mp4
export ELEVENLABS_API_KEY=...                             # optional: real voice + word timestamps
python3 scripts/tts.py && npx remotion render src/index.ts ExplainerCaptioned out/explainer-raw.mp4
python3 scripts/loudnorm.py out/explainer-raw.mp4 out/explainer.mp4
python3 scripts/check_final.py out/explainer.mp4             # streams, loudness, poster frame, scene boundaries
```

To use it as a skill, copy this folder to `~/.claude/skills/explainer-video` (Claude Code) or `~/.codex/skills/explainer-video` (Codex), then ask for an explainer video.

Needs Node 18+, Python 3.10+ and ffmpeg. Draft mode needs no API keys. Voice and music use ElevenLabs (`ELEVENLABS_API_KEY`). The optional transcription check uses OpenAI (`OPENAI_API_KEY`).

## Notes

- Remotion is source-available with its own licence terms for companies: see https://www.remotion.dev/license.
- Narration made with ElevenLabs is AI-generated; say so in the video or post.
- The tested path is 16:9 at 1080p with ElevenLabs voices. Other aspect ratios and TTS providers are extension points that haven't been tested.
