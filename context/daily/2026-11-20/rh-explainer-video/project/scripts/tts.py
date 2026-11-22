"""Voice each scene with ElevenLabs (George, eleven_v3), capture word timings, write src/data/timeline.json.

Usage: python3 scripts/tts.py [--force] [--only s03_zeros,s11_checks]
Reads script/script.json + script/status.json. Caches per-scene audio by text hash.
"""
import base64, hashlib, json, os, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = os.environ.get("ELEVENLABS_API_KEY", "")


def require_key():
    if not KEY:
        sys.exit("ELEVENLABS_API_KEY is not set. Export it in your shell to re-voice scenes. "
                 "The committed audio in public/audio/ is reused as long as the script text is unchanged.")

args = sys.argv[1:]
FORCE = "--force" in args
ONLY = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None

script = json.loads((ROOT / "script/script.json").read_text())
status = json.loads((ROOT / "script/status.json").read_text())
voice = script["voice"]
pron = script.get("pronunciations", {})
FPS = 30
LEAD_IN, TAIL = 0.5, 0.7
LAST_TAIL = 4.0  # end card time after the final line
TEMPO = 1.04  # pitch-preserving speed-up applied after TTS
AUDIO_DIR = ROOT / "public/audio"; AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CACHE = ROOT / "script/.tts_cache.json"
cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}


def fill(t):
    return t.format(**status) if "{" in t else t


def to_tts(text):
    # replace whole words, longest keys first; keys may include apostrophes
    for k in sorted(pron, key=len, reverse=True):
        text = re.sub(rf"(?<![\w-]){re.escape(k)}(?![\w-])", pron[k], text)
    return text


def tts_with_timestamps(text, seed=4242):
    body = {"text": text, "model_id": voice["model"], "seed": seed,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice['voice_id']}/with-timestamps?output_format=mp3_44100_192"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def words_from_alignment(al):
    chars = al["characters"]; st = al["character_start_times_seconds"]; en = al["character_end_times_seconds"]
    words, cur, cs, ce = [], "", None, None
    for c, s, e in zip(chars, st, en):
        if c.isspace():
            if cur:
                words.append((cur, cs, ce)); cur = ""
            continue
        if not cur:
            cs = s
        cur += c; ce = e
    if cur:
        words.append((cur, cs, ce))
    return words


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


scenes_out = []
for sc in script["scenes"]:
    sid = sc["id"]
    lines = [fill(l["caption"]) for l in sc["lines"]]
    caption_text = " ".join(lines)
    tts_text = to_tts(caption_text)
    seed = sc.get("seed", 4242)
    h = hashlib.sha256((voice["model"] + voice["voice_id"] + tts_text + str(seed)).encode()).hexdigest()[:16]
    mp3 = AUDIO_DIR / f"{sid}.mp3"
    meta_path = AUDIO_DIR / f"{sid}.align.json"
    if FORCE or (ONLY and sid in ONLY) or cache.get(sid) != h or not mp3.exists() or not meta_path.exists():
        if ONLY and sid not in ONLY and mp3.exists() and meta_path.exists():
            pass
        else:
            require_key()
            print("voicing", sid, f"({len(tts_text)} chars)")
            res = tts_with_timestamps(tts_text, seed)
            raw = AUDIO_DIR / f"{sid}.raw.mp3"
            raw.write_bytes(base64.b64decode(res["audio_base64"]))
            meta_path.write_text(json.dumps(res.get("alignment") or res.get("normalized_alignment")))
            cache[sid] = h
    raw = AUDIO_DIR / f"{sid}.raw.mp3"
    if raw.exists() and (FORCE or not mp3.exists() or mp3.stat().st_mtime < raw.stat().st_mtime or cache.get(sid + ":tempo") != TEMPO):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-filter:a", f"atempo={TEMPO}",
                        "-ar", "44100", "-b:a", "192k", str(mp3)], check=True)
        cache[sid + ":tempo"] = TEMPO
    al = json.loads(meta_path.read_text())
    tw = words_from_alignment(al)
    cw = caption_text.split()
    if len(tw) != len(cw):
        print(f"WARN {sid}: tts words {len(tw)} != caption words {len(cw)}; mapping by index with clamp")
    words = []
    for i, w in enumerate(cw):
        j = min(i, len(tw) - 1)
        words.append({"text": w, "start": round(tw[j][1] / TEMPO, 3), "end": round(tw[j][2] / TEMPO, 3)})
    # line boundaries by word counts
    out_lines, k = [], 0
    for l, text in zip(sc["lines"], lines):
        n = len(text.split())
        seg = words[k:k + n]; k += n
        out_lines.append({"caption": text, "start": seg[0]["start"] if seg else 0, "end": seg[-1]["end"] if seg else 0,
                          **({"status": True} if l.get("status") else {})})
    ad = duration(mp3)
    tail = LAST_TAIL if sc is script["scenes"][-1] else TAIL
    scenes_out.append({"id": sid, "title": sc["title"], "audio": f"audio/{sid}.mp3", "audioDuration": round(ad, 3),
                       "leadIn": LEAD_IN, "duration": round(LEAD_IN + ad + tail, 3), "lines": out_lines, "words": words})
    print(f"{sid:18s} audio {ad:6.2f}s  scene {LEAD_IN + ad + tail:6.2f}s")

CACHE.write_text(json.dumps(cache, indent=1))
total = sum(s["duration"] for s in scenes_out)
(ROOT / "src/data").mkdir(parents=True, exist_ok=True)
(ROOT / "src/data/timeline.json").write_text(json.dumps({"fps": FPS, "scenes": scenes_out, "totalSeconds": round(total, 2)}, ensure_ascii=False, indent=1))
(ROOT / "src/data/status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1))
print(f"TOTAL {total:.1f}s = {int(total // 60)}:{total % 60:04.1f}")
