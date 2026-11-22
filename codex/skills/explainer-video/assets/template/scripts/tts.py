#!/usr/bin/env python3
"""Build src/data/timeline.json from script/script.json.

Two modes:
  --draft   No audio, no API key. Word timings are estimated from word counts (script.timing.draft_wpm),
            so scenes can be built, previewed and rendered (silently) before any voice exists.
  default   Voice each scene with ElevenLabs (text-to-speech/{voice}/with-timestamps), apply an optional
            pitch-preserving tempo, and write per-word timings from the returned character alignment.
            Needs ELEVENLABS_API_KEY in the environment. Audio is cached per scene by a hash of the text,
            voice, model, seed and tempo, so only changed scenes are re-voiced.

Usage:
  python3 scripts/tts.py --draft
  python3 scripts/tts.py                 # voice changed scenes
  python3 scripts/tts.py --only s03_x    # force re-voice of listed scenes
  python3 scripts/tts.py --force         # re-voice everything

Line text may reference keys from script/status.json as {key}. Pronunciation respellings must be a single
token (use hyphens: "Duh-leen", not "Duh leen") so spoken words line up one-to-one with caption words.
"""
import base64, hashlib, json, os, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
args = sys.argv[1:]
DRAFT = "--draft" in args
FORCE = "--force" in args
ONLY = set(args[args.index("--only") + 1].split(",")) if "--only" in args else set()

script = json.loads((ROOT / "script/script.json").read_text())
status_path = ROOT / "script/status.json"
status = json.loads(status_path.read_text()) if status_path.exists() else {}
voice = script.get("voice", {})
timing = script.get("timing", {})
pron = script.get("pronunciations", {})
FPS = 30
LEAD_IN = float(timing.get("lead_in", 0.5))
TAIL = float(timing.get("tail", 0.7))
LAST_TAIL = float(timing.get("last_tail", 3.0))
WPM = float(timing.get("draft_wpm", 150))
TEMPO = float(voice.get("tempo", 1.0))
AUDIO_DIR = ROOT / "public/audio"
CACHE = ROOT / "script/.tts_cache.json"
cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}


class SafeDict(dict):
    def __missing__(self, k):
        return "{" + k + "}"


def fill(t):
    return t.format_map(SafeDict(status)) if "{" in t else t


def to_tts(text):
    for k in sorted(pron, key=len, reverse=True):
        text = re.sub(rf"(?<![\w-]){re.escape(k)}(?![\w-])", pron[k], text)
    return text


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def draft_words(text):
    """Estimate word timings: 60/WPM s per word plus pauses after commas and sentence ends."""
    t, out = 0.0, []
    per = 60.0 / WPM
    for w in text.split():
        d = per * (0.75 + 0.05 * min(len(w), 12))
        out.append({"text": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d + (0.45 if re.search(r"[.?!]$", w) else 0.22 if re.search(r"[,;:]$", w) else 0.04)
    return out


def elevenlabs(text, seed):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set. Export it, or run with --draft for a silent timing pass.")
    body = {"text": text, "model_id": voice.get("model", "eleven_multilingual_v2"), "seed": seed,
            "voice_settings": {"stability": voice.get("stability", 0.5), "similarity_boost": voice.get("similarity_boost", 0.75)}}
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice['voice_id']}/with-timestamps?output_format=mp3_44100_192"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"xi-api-key": key, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs error {e.code}: {e.read()[:300]!r}")


def words_from_alignment(al):
    words, cur, cs, ce = [], "", None, None
    for c, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
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


scenes_out = []
for idx, sc in enumerate(script["scenes"]):
    sid = sc["id"]
    lines = [fill(l["caption"]) for l in sc["lines"]]
    caption_text = " ".join(lines)
    cw = caption_text.split()
    last = idx == len(script["scenes"]) - 1
    if DRAFT:
        words = draft_words(caption_text)
        ad = words[-1]["end"] if words else 1.0
        audio_rel = None
    else:
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        tts_text = to_tts(caption_text)
        seed = int(sc.get("seed", voice.get("seed", 4242)))
        h = hashlib.sha256(json.dumps([voice.get("voice_id"), voice.get("model"), tts_text, seed]).encode()).hexdigest()[:16]
        raw = AUDIO_DIR / f"{sid}.raw.mp3"
        mp3 = AUDIO_DIR / f"{sid}.mp3"
        meta = AUDIO_DIR / f"{sid}.align.json"
        if FORCE or sid in ONLY or cache.get(sid) != h or not raw.exists() or not meta.exists():
            print(f"voicing {sid} ({len(tts_text)} chars)")
            res = elevenlabs(tts_text, seed)
            raw.write_bytes(base64.b64decode(res["audio_base64"]))
            meta.write_text(json.dumps(res.get("alignment") or res.get("normalized_alignment")))
            cache[sid] = h
        if not mp3.exists() or mp3.stat().st_mtime < raw.stat().st_mtime or cache.get(sid + ":tempo") != TEMPO:
            af = ["-filter:a", f"atempo={TEMPO}"] if abs(TEMPO - 1.0) > 1e-6 else []
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), *af, "-ar", "44100", "-b:a", "192k", str(mp3)], check=True)
            cache[sid + ":tempo"] = TEMPO
        tw = words_from_alignment(json.loads(meta.read_text()))
        if len(tw) != len(cw):
            print(f"WARN {sid}: spoken words {len(tw)} != caption words {len(cw)} (respellings must be one token); mapping by index")
        words = []
        for i, w in enumerate(cw):
            j = min(i, len(tw) - 1)
            words.append({"text": w, "start": round(tw[j][1] / TEMPO, 3), "end": round(tw[j][2] / TEMPO, 3)})
        ad = duration(mp3)
        audio_rel = f"audio/{sid}.mp3"
    out_lines, k = [], 0
    for l, text in zip(sc["lines"], lines):
        n = len(text.split())
        seg = words[k:k + n]; k += n
        out_lines.append({"caption": text, "start": seg[0]["start"] if seg else 0, "end": seg[-1]["end"] if seg else 0,
                          **({"status": True} if l.get("status") else {})})
    tail = LAST_TAIL if last else TAIL
    scenes_out.append({"id": sid, "title": sc["title"], "audio": audio_rel, "audioDuration": round(ad, 3), "leadIn": LEAD_IN,
                       "duration": round(LEAD_IN + ad + tail, 3), "lines": out_lines, "words": words})
    print(f"{sid:20s} {'draft' if DRAFT else 'audio'} {ad:6.2f}s  scene {LEAD_IN + ad + tail:6.2f}s")

music = script.get("music")
if music and not (ROOT / "public" / music.get("file", "")).exists():
    print(f"WARN music file public/{music.get('file')} not found; music disabled")
    music = None
if not DRAFT:
    CACHE.write_text(json.dumps(cache, indent=1))
total = sum(s["duration"] for s in scenes_out)
(ROOT / "src/data").mkdir(parents=True, exist_ok=True)
(ROOT / "src/data/timeline.json").write_text(json.dumps(
    {"fps": FPS, "mode": "draft" if DRAFT else "voiced", "meta": script.get("meta", {}), "music": music,
     "scenes": scenes_out, "totalSeconds": round(total, 2)}, ensure_ascii=False, indent=1))
(ROOT / "src/data/status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1))
print(f"TOTAL {total:.1f}s = {int(total // 60)}:{total % 60:04.1f}  ({'draft' if DRAFT else 'voiced'})")
