# QA checklist

Run these before calling the video done. Each one caught something real last time.

## Script and timing
- [ ] `npx tsc --noEmit` passes.
- [ ] `python3 scripts/check_anchors.py` reports 0 problems (re-run after every script edit or re-voice).
- [ ] `tts.py` printed no "spoken words != caption words" warnings (respellings are single tokens).
- [ ] Pace per scene: characters per second within about 10% of the median. Words per second misleads (spoken numbers like "175,000" are one word, many syllables).
- [ ] Total length within the agreed window. If long, cut words, don't speed up past about 1.05x.

## Audio
- [ ] `python3 scripts/check_audio.py` per scene: only digit formatting and name spellings differ.
- [ ] Every proper name, cut into one clip from the final takes, approved by ear by the user.
- [ ] Voice clips within about 1 LU of each other (`ffmpeg -i x.mp3 -af ebur128 -f null -`).
- [ ] Music (if any) ends under the end card, not before it. Check for silence baked into the end of the generated track.
- [ ] Final mix normalized (`scripts/loudnorm.py`, -14 LUFS) and its transcription matches the script.

## Picture
- [ ] `node scripts/stills.mjs`: every per-line still matches its caption; the end card doesn't cover a line still being spoken (the last scene has its own tail).
- [ ] Nothing important under the caption band (y > 900); no clipped labels; tags readable at phone size.
- [ ] Frame 0 isn't black (scene 1 uses `instant`), so platforms that use it as the poster show something.
- [ ] `python3 scripts/check_final.py <final.mp4>`: frames just before and after every scene boundary look intentional, frame 0 isn't blank, no unexpected silences, loudness on target.
- [ ] Old-style numerals are off (lining figures are on in SceneFrame); "1/2" instead of "½" in mono fonts.

## Truth
- [ ] Script review applied; on-screen review applied (accuracy-review.md).
- [ ] Live status re-read from first-hand sources right before the final render; `status.json` and the "as of" stamp updated.
- [ ] No narrator-voice assertion of unverified results; every analogy is attributed.
- [ ] Credits on the end card: AI voice disclosed, sources named.

## Files
- [ ] Final MP4s: duration, audio stream, 1920x1080, 30 fps (`ffprobe`).
- [ ] SRT regenerated after the final voicing.
- [ ] A smaller preview (720p, about 10 MB) if a chat or upload limit applies.
- [ ] Thumbnail checked at feed size (about 560 px wide).
