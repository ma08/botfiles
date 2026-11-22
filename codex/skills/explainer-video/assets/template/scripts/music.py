#!/usr/bin/env python3
"""Optional: generate an instrumental music bed with ElevenLabs Music and fit it under the narration.

Generates a track of about the video's length, trims any trailing silence the model leaves, time-stretches it
(pitch-preserving) so its natural ending lands at the end of the video, normalizes it to about -30 LUFS (roughly
10 dB under narration), and enables it in script.json ("music": {"file": "music/bed.mp3", "volume": 0.8}).
Re-run with --fit-only after the narration changes length, to refit the existing raw track without regenerating.

Needs ELEVENLABS_API_KEY and a voiced timeline (run scripts/tts.py first). Usage:
  python3 scripts/music.py --prompt "minimal ambient pads, soft felt piano, no drums, no vocals, 60 BPM"
  python3 scripts/music.py --fit-only
"""
import json, os, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
args = sys.argv[1:]
MUSIC = ROOT / "public/music"
RAW, BED = MUSIC / "bed-raw.mp3", MUSIC / "bed.mp3"
tl = json.loads((ROOT / "src/data/timeline.json").read_text())
total = float(tl["totalSeconds"])

if "--fit-only" not in args:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set.")
    prompt = args[args.index("--prompt") + 1] if "--prompt" in args else (
        "Minimal ambient underscore for a calm, curious documentary, meant to sit quietly under narration. Warm pads, "
        "soft sustained piano, slow evolving textures. No drums, no vocals, no strong melody, no sudden changes. "
        "Low intensity throughout and a soft, resolved ending. 60 BPM.")
    MUSIC.mkdir(parents=True, exist_ok=True)
    body = {"prompt": prompt, "music_length_ms": int(min(total, 300) * 1000), "force_instrumental": True}
    req = urllib.request.Request("https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192", data=json.dumps(body).encode(),
                                 headers={"xi-api-key": key, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=600) as r:
        RAW.write_bytes(r.read())
    print(f"generated {RAW.relative_to(ROOT)}")

if not RAW.exists():
    sys.exit("public/music/bed-raw.mp3 not found; generate it first.")
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(RAW)], capture_output=True, text=True).stdout)
log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(RAW), "-af", "silencedetect=n=-50dB:d=1", "-f", "null", "-"], capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
content_end = dur
if starts and (len(ends) < len(starts) or ends[-1] >= dur - 0.05) and starts[-1] > dur * 0.5:
    content_end = starts[-1] + 0.2  # trailing silence baked into the track
target = max(5.0, total - 0.3)
tempo = content_end / target
if not 0.5 <= tempo <= 2.0:
    sys.exit(f"needed tempo {tempo:.3f} is outside 0.5-2.0; generate a track closer to {total:.0f} s")
af = f"atempo={tempo:.4f},loudnorm=I=-30:TP=-6:LRA=7,afade=t=in:st=0:d=3,afade=t=out:st={max(0, total - 2.3):.2f}:d=2"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", f"{content_end:.2f}", "-i", str(RAW), "-filter:a", af, "-ar", "44100", "-b:a", "160k", str(BED)], check=True)
sp = ROOT / "script/script.json"
s = json.loads(sp.read_text())
s["music"] = s.get("music") or {"file": "music/bed.mp3", "volume": 0.8}
sp.write_text(json.dumps(s, ensure_ascii=False, indent=2))
print(f"fitted bed: raw content {content_end:.1f}s -> {target:.1f}s (tempo {tempo:.3f}); re-run scripts/tts.py to pick it up")
