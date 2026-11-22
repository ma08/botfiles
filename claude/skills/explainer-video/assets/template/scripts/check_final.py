#!/usr/bin/env python3
"""QA a rendered MP4: streams, duration vs timeline, loudness, frame 0, and every scene boundary.

Usage: python3 scripts/check_final.py out/explainer-captioned.mp4
Prints a summary and writes out/final-qa/<name>-boundaries.jpg: frame 0 plus frames 0.25 s before and 0.2 s after
each scene boundary, tiled. Look at it: frame 0 shouldn't be blank (it's often the poster), and transitions
should look intentional.
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if len(sys.argv) < 2:
    sys.exit("usage: check_final.py <video.mp4>")
src = Path(sys.argv[1])
tl = json.loads((ROOT / "src/data/timeline.json").read_text())
fps = tl["fps"]
probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration",
                                   "-of", "json", str(src)], capture_output=True, text=True, check=True).stdout)
streams = probe["streams"]
dur = float(probe["format"]["duration"])
v = next((s for s in streams if s["codec_type"] == "video"), None)
a = next((s for s in streams if s["codec_type"] == "audio"), None)
expected = sum(round(s["duration"] * fps) for s in tl["scenes"]) / fps
print(f"video: {v['codec_name']} {v['width']}x{v['height']} @ {v['r_frame_rate']}" if v else "video: MISSING")
print(f"audio: {a['codec_name']}" if a else "audio: none (draft render?)")
print(f"duration: {dur:.2f}s (timeline {expected:.2f}s)" + ("" if abs(dur - expected) < 0.2 else "  <-- MISMATCH"))
if a:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", err); pk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    print(f"loudness: {i[-1] if i else '?'} LUFS integrated, true peak {pk[-1] if pk else '?'} dBFS")
    sil = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af", "silencedetect=n=-45dB:d=1.5", "-f", "null", "-"], capture_output=True, text=True).stderr
    gaps = re.findall(r"silence_start: ([\d.]+)", sil)
    print(f"silences >1.5s at: {', '.join(f'{float(g):.1f}s' for g in gaps) or 'none'}")

out = ROOT / "out/final-qa"
out.mkdir(parents=True, exist_ok=True)
times, t = [0.0], 0.0
for k, s in enumerate(tl["scenes"]):
    if k:
        times += [max(0, t - 0.25), t + 0.2]
    t += round(s["duration"] * fps) / fps
files = []
for n, ts in enumerate(times):
    f = out / f"b{n:02d}.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{ts:.3f}", "-i", str(src), "-frames:v", "1", "-vf", "scale=480:270", str(f)], check=True)
    files.append(f)
cols = 4
layout = "|".join(f"{(k % cols) * 480}_{(k // cols) * 270}" for k in range(len(files)))
inputs = sum([["-i", str(f)] for f in files], [])
sheet = out / f"{src.stem}-boundaries.jpg"
filt = "".join(f"[{k}:v]" for k in range(len(files))) + f"xstack=inputs={len(files)}:layout={layout}:fill=black" if len(files) > 1 else "null"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", filt, str(sheet)], check=True)
for f in files:
    f.unlink()
print(f"boundary sheet: {sheet.relative_to(ROOT)} (frame 0, then before/after each scene boundary)")
