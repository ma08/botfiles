#!/usr/bin/env python3
"""Optional QA: transcribe each voiced scene (or a final MP4) and diff against the script.

Catches words a TTS take dropped, added or garbled. Expected noise: numbers written as digits, and how a
transcriber spells unusual names. Listen to names yourself; a transcriber can't judge pronunciation.

Needs OPENAI_API_KEY (uses the transcription endpoint). Usage:
  python3 scripts/check_audio.py                 # every voiced scene
  python3 scripts/check_audio.py s02_proof       # some scenes
  python3 scripts/check_audio.py --file out/explainer.mp4   # a final mix against the whole script
"""
import difflib, json, os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = os.environ.get("OPENAI_API_KEY")
if not KEY:
    sys.exit("OPENAI_API_KEY is not set (only needed for this optional check).")
MODEL = os.environ.get("TRANSCRIBE_MODEL", "gpt-4o-transcribe")
tl = json.loads((ROOT / "src/data/timeline.json").read_text())
norm = lambda s: re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()


def transcribe(path):
    with tempfile.TemporaryDirectory() as d:
        small = Path(d) / "a.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k", str(small)], check=True)
        out = subprocess.run(["curl", "-s", "https://api.openai.com/v1/audio/transcriptions", "-H", f"Authorization: Bearer {KEY}",
                              "-F", f"model={MODEL}", "-F", f"file=@{small}"], capture_output=True, text=True).stdout
    return json.loads(out).get("text", "")


def diff(expected, heard, label):
    a, b = norm(expected), norm(heard)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    d = [(" ".join(a[i1:i2]), " ".join(b[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
    print(f"{label:20s} match {sm.ratio():.3f}  differences: {d[:12]}")


args = sys.argv[1:]
if "--file" in args:
    f = args[args.index("--file") + 1]
    diff(" ".join(l["caption"] for s in tl["scenes"] for l in s["lines"]), transcribe(ROOT / f), Path(f).name)
else:
    only = set(args)
    for s in tl["scenes"]:
        if (only and s["id"] not in only) or not s.get("audio"):
            continue
        diff(" ".join(l["caption"] for l in s["lines"]), transcribe(ROOT / "public" / s["audio"]), s["id"])
