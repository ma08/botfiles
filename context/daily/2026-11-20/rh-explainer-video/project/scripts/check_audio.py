"""Transcribe each scene's audio and diff against the caption text (catches TTS drops/additions)."""
import difflib, json, os, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if not os.environ.get("OPENAI_API_KEY"):
    sys.exit("OPENAI_API_KEY is not set. This optional QA step transcribes each scene with gpt-4o-transcribe.")
t = json.loads((ROOT / "src/data/timeline.json").read_text())
only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
norm = lambda s: re.sub(r"[^a-z0-9 ]", " ", s.lower().replace("ö", "o")).split()
for s in t["scenes"]:
    if only and s["id"] not in only: continue
    out = subprocess.run(["curl", "-s", "https://api.openai.com/v1/audio/transcriptions",
                          "-H", f"Authorization: Bearer {os.environ['OPENAI_API_KEY']}",
                          "-F", "model=gpt-4o-transcribe", "-F", f"file=@{ROOT / 'public' / s['audio']}"],
                         capture_output=True, text=True).stdout
    heard = json.loads(out).get("text", "")
    a, b = norm(" ".join(l["caption"] for l in s["lines"])), norm(heard)
    sm = difflib.SequenceMatcher(None, a, b)
    diffs = [(op, " ".join(a[i1:i2]), " ".join(b[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
    print(f"{s['id']:16s} ratio {sm.ratio():.3f}  diffs: {diffs[:8]}")
