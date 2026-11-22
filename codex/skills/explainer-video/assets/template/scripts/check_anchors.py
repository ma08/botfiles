#!/usr/bin/env python3
"""Check that every literal word anchor in the scenes exists in the current narration.

Finds wordFrame(S, 'word'), wordFrame(S, 'word', n) and wordFrame(S, 'word', {line: L, nth: n}) calls in
src/scenes/**/*.tsx (plus W('word', n) / wf(s, 'word', n) wrappers, if your scenes define them), maps each
file to its scene via sceneById('...'), and reports anchors whose word is not spoken. Run after every script
edit or re-voice. wordFrame also throws at render time; this just finds them all in one pass.
"""
import json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
tl = json.loads((ROOT / "src/data/timeline.json").read_text())
scenes = {s["id"]: s for s in tl["scenes"]}


def norm(x):
    x = unicodedata.normalize("NFD", x)
    return re.sub(r"[^\w]", "", "".join(c for c in x if unicodedata.category(c) != "Mn").lower()).replace("_", "")


CALL = re.compile(r"(?:wordFrame\(\s*\w+\s*,|\bwf\(\s*\w+\s*,|\bW\()\s*'([^']+)'\s*(?:,\s*(\d+|\{[^}]*\}))?")
bad = total = 0
for f in sorted((ROOT / "src/scenes").rglob("*.tsx")):
    src = f.read_text()
    m = re.search(r"sceneById\('([A-Za-z0-9_]+)'\)", src)
    if not m:
        continue
    sc = scenes.get(m.group(1))
    if not sc:
        print(f"MISSING SCENE {f.relative_to(ROOT)}: '{m.group(1)}' not in timeline.json"); bad += 1; continue
    for nm in CALL.finditer(src):
        total += 1
        word, pick = nm.group(1), nm.group(2) or "0"
        nth, line = 0, None
        if pick.startswith("{"):
            mn = re.search(r"nth\s*:\s*(\d+)", pick); ml = re.search(r"line\s*:\s*(\d+)", pick)
            nth = int(mn.group(1)) if mn else 0
            line = int(ml.group(1)) if ml else None
        else:
            nth = int(pick)
        pool = sc["words"]
        if line is not None:
            if line >= len(sc["lines"]):
                bad += 1; print(f"MISSING {f.relative_to(ROOT)}: line {line} does not exist in {sc['id']}"); continue
            l = sc["lines"][line]
            pool = [w for w in sc["words"] if l["start"] - 0.01 <= w["start"] <= l["end"] + 0.01]
        if [norm(w["text"]) for w in pool].count(norm(word)) <= nth:
            bad += 1
            where = f" in line {line}" if line is not None else ""
            print(f"MISSING {f.relative_to(ROOT)}: '{word}' (occurrence {nth}{where}) not spoken in {sc['id']}")
print(f"{total} anchors checked, {bad} problems")
sys.exit(1 if bad else 0)
