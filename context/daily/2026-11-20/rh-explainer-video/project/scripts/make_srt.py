"""Write out/rh-explainer.srt from src/data/timeline.json using the same chunking as Captions.tsx."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
t = json.loads((ROOT / "src/data/timeline.json").read_text())
FPS = t["fps"]
WEAK = set("the a an of and to in on that his its for with by at is from into than but or as he it".split())


def text_of(ws):
    return " ".join(w["text"] for w in ws)


def chunk(words, max_chars=52):
    chunks, cur = [], []
    def emit(ws):
        if ws:
            chunks.append({"text": text_of(ws), "start": ws[0]["start"], "end": ws[-1]["end"]})
    for w in words:
        if cur and len(text_of(cur + [w])) > max_chars:
            cut = -1
            for i in range(len(cur) - 1, 0, -1):
                if re.search(r"[,;]$", cur[i]["text"]) and len(text_of(cur[:i + 1])) >= 20:
                    cut = i; break
            if cut == -1:
                cut = len(cur) - 1
                while cut > 1 and cur[cut]["text"].lower() in WEAK:
                    cut -= 1
            emit(cur[:cut + 1]); cur = cur[cut + 1:]
        cur.append(w)
        if re.search(r"[.?!:]$", w["text"]) and len(text_of(cur)) > 14:
            emit(cur); cur = []
    emit(cur)
    i = len(chunks) - 1
    while i > 0:
        c, pr = chunks[i], chunks[i - 1]
        if len(c["text"]) <= 8 and not re.search(r"[.?!:]$", pr["text"]) and len(pr["text"] + " " + c["text"]) <= 64:
            chunks[i - 1:i + 1] = [{"text": pr["text"] + " " + c["text"], "start": pr["start"], "end": c["end"]}]
        i -= 1
    for i, c in enumerate(chunks):
        nxt = chunks[i + 1] if i + 1 < len(chunks) else None
        c["end"] = min(nxt["start"], c["end"] + 0.6) if nxt else c["end"] + 0.6
    return chunks


def ts(sec):
    ms = int(round(sec * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


out, n, offset = [], 1, 0.0
for s in t["scenes"]:
    frames = round(s["duration"] * FPS)
    base = offset + s["leadIn"]
    for c in chunk(s["words"]):
        out.append(f"{n}\n{ts(base + c['start'])} --> {ts(base + c['end'])}\n{c['text']}\n")
        n += 1
    offset += frames / FPS
(ROOT / "out").mkdir(exist_ok=True)
(ROOT / "out/rh-explainer.srt").write_text("\n".join(out))
print(f"wrote {n - 1} cues, ends at {ts(offset)}")
