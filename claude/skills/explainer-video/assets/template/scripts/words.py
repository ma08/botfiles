#!/usr/bin/env python3
"""Print every spoken word of a scene with its line and occurrence number, to write anchors quickly.

Usage: python3 scripts/words.py s02_proof [word]
Output columns: line, occurrence-in-scene, occurrence-in-line, frame (from scene start), word.
Use them as wordFrame(S, 'word', nth) or wordFrame(S, 'word', {line: L, nth: n}).
"""
import json, re, sys, unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
tl = json.loads((ROOT / "src/data/timeline.json").read_text())
if len(sys.argv) < 2:
    sys.exit("usage: words.py <scene_id> [word]  (scenes: " + ", ".join(s["id"] for s in tl["scenes"]) + ")")
sc = next((s for s in tl["scenes"] if s["id"] == sys.argv[1]), None)
if not sc:
    sys.exit(f"scene {sys.argv[1]} not found")
only = sys.argv[2] if len(sys.argv) > 2 else None


def norm(x):
    x = unicodedata.normalize("NFD", x)
    return re.sub(r"[^\w]", "", "".join(c for c in x if unicodedata.category(c) != "Mn").lower()).replace("_", "")


scene_count, line_count = Counter(), {}
print(f"{'line':>4} {'nth':>3} {'line-nth':>8} {'frame':>6}  word")
for w in sc["words"]:
    li = next((i for i, l in enumerate(sc["lines"]) if l["start"] - 0.01 <= w["start"] <= l["end"] + 0.01), -1)
    k = norm(w["text"])
    lc = line_count.setdefault(li, Counter())
    if not only or k == norm(only):
        print(f"{li:>4} {scene_count[k]:>3} {lc[k]:>8} {round((sc['leadIn'] + w['start']) * tl['fps']):>6}  {w['text']}")
    scene_count[k] += 1
    lc[k] += 1
