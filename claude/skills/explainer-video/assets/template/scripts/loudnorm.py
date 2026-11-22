#!/usr/bin/env python3
"""Two-pass EBU R128 loudness normalization; the video stream is copied untouched.

Usage: python3 scripts/loudnorm.py out/explainer-raw.mp4 out/explainer.mp4 [--target -14]
-14 LUFS integrated / -1.5 dBTP suits most social platforms.
"""
import json, re, subprocess, sys

src, dst = sys.argv[1], sys.argv[2]
target = sys.argv[sys.argv.index("--target") + 1] if "--target" in sys.argv else "-14"
T = f"I={target}:TP=-1.5:LRA=11"
has_audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", src],
                           capture_output=True, text=True).stdout.strip()
if not has_audio:
    sys.exit(f"{src} has no audio stream (a draft render?); nothing to normalize. Voice it with scripts/tts.py and re-render.")
err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af", f"loudnorm={T}:print_format=json", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S).group(0))
af = (f"loudnorm={T}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
      f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-c:v", "copy", "-af", af, "-ar", "48000",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst], check=True)
print(f"{dst}: input {m['input_i']} LUFS (TP {m['input_tp']}) -> target {target} LUFS")
