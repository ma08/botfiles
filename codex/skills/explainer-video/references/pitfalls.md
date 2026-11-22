# Pitfalls (from the worked example)

Each of these cost real time once.

## Timing and sync
- **Hard-coded frames drift** the moment a line is re-voiced. Anchor beats with `wordFrame(scene, 'word')`; it throws on a missing word, and `check_anchors.py` finds them all in one pass. Never write a helper that silently returns frame 0 on a miss.
- **Respellings with spaces** ("Duh leen") break the one-to-one word mapping between audio and captions. Use one hyphenated token.
- **Changing the cache key re-voices everything.** Adding the seed to the hash invalidated every scene and produced 12 new takes (and new timings). Decide the cache key early, and re-run the transcription check after any mass re-voice.
- **The end card covered the last spoken line** because it started at a fixed offset from the scene end. The last scene needs its own tail (`timing.last_tail`) and the card should start after the final line ends.
- **A data file named like the timeline** (`timeline.json` for the note's dates) collided with the generated timing file. Keep generated files' names unique.

## Audio
- **eleven_v3 drifts between clips**: the same name came out differently in separately voiced scenes. Cut every name occurrence from the final takes into one clip and have a human approve it.
- **Generated music can end in silence.** The track resolved 7 s before its file ended, so the video's last seconds were silent. `music.py` trims trailing silence before fitting.
- **Loudness**: TTS clips sat around -20 LUFS; normalize the final mix to -14 LUFS for social, in two passes, copying the video stream.
- **Words per second misleads** when lines contain numbers; use characters per second to compare pace across scenes.

## Picture
- **Frame 0 was black** because scene 1 faded in from zero; X used it as the poster. Use `instant` on scene 1.
- **"½" in mono fonts** renders as a smudge at video sizes; write "1/2".
- **Math glyphs fall back** when the display font lacks them (√ came out with no bar over the radicand). Use `Radical`, `Frac`, `Sup`, `Sub` from `src/components/Math.tsx`.
- **Repeated words** ("squared" said seven times) make `nth` counting error-prone; scope anchors to a line with `{line: L}` and use `scripts/words.py` to see occurrences.
- **Spreading `enter()` after your own `opacity`** silently overwrites it; pass the base opacity as `enter()`'s fifth argument.
- **Old-style figures** in serif display faces make "3" and "5" drop below the line in equations; lining figures are on by default in the template.
- **SVG masks use luminance**: a mask built from black gradient stops hides everything. Use white stops.
- **Orphan captions** ("one." alone, or "new." leading the next caption) look broken. The template's chunker merges short tails into the caption they finish; keep Captions.tsx and make_srt.py in sync.
- **Honesty tags at 15 to 18 px** are invisible on a phone. 21 px minimum.

## Process
- **Stopped subagents leave orphaned headless Chrome processes**; kill them before re-rendering.
- **Status goes stale within hours** for live claims; re-check right before rendering (live-claims.md).
- **A transcription QA can't judge pronunciation**, and a reviewer model can't watch video: give reviewers stills plus source files, and give humans the names clip.
- **Superlatives age badly** ("the first ..."). Re-check them against everything read since the script was written.
- **Public repos**: never commit API keys, private paths, generated audio from private voices, or copyrighted source images; fetch those at build time.
