"""Two-pass EBU R128 loudness normalization (video stream copied). Usage: loudnorm.py in.mp4 out.mp4"""
import json, re, subprocess, sys
src, dst = sys.argv[1], sys.argv[2]
T = "I=-14:TP=-1.5:LRA=11"
err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af", f"loudnorm={T}:print_format=json", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S).group(0))
af = (f"loudnorm={T}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
      f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-c:v", "copy", "-af", af, "-ar", "48000",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst], check=True)
print(f"{dst}: measured {m['input_i']} LUFS, TP {m['input_tp']}")
