"""Assert every literal word anchor used by the scenes resolves in the current narration timings."""
import json, re, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
t = json.loads((ROOT / "src/data/timeline.json").read_text())
scenes = {s["id"]: s for s in t["scenes"]}
def norm(x):
    x = unicodedata.normalize("NFD", x)
    return re.sub(r"[^\w]", "", "".join(c for c in x if unicodedata.category(c) != "Mn").lower())
bad = 0; total = 0
for f in sorted((ROOT / "src/scenes").rglob("*.tsx")):
    src = f.read_text()
    m = re.search(r"sceneById\('([a-z0-9_]+)'\)", src)
    if not m: continue
    sc = scenes[m.group(1)]
    words = [norm(w["text"]) for w in sc["words"]]
    # wordFrame(S, 'needle', nth?)
    for nm in re.finditer(r"(?:wordFrame\(\s*\w+\s*,|\bwf\(\s*\w+\s*,|\bW\()\s*'([^']+)'\s*(?:,\s*(\d+))?", src):
        total += 1; n = int(nm.group(2) or 0)
        if words.count(norm(nm.group(1))) <= n:
            bad += 1; print(f"MISSING wordFrame {f.name}: '{nm.group(1)}' nth={n}")
    # wordIn(S, line, 'needle', nth?)
    for nm in re.finditer(r"wordIn\(\s*\w+\s*,\s*(\d+)\s*,\s*'([^']+)'\s*(?:,\s*(\d+))?", src):
        total += 1; line = int(nm.group(1)); n = int(nm.group(3) or 0)
        l = sc["lines"][line] if line < len(sc["lines"]) else None
        ws = [norm(w["text"]) for w in sc["words"] if l and l["start"] - 0.05 <= w["start"] <= l["end"] + 0.05]
        if ws.count(norm(nm.group(2))) <= n:
            bad += 1; print(f"MISSING wordIn {f.name}: line {line} '{nm.group(2)}' nth={n}")
print(f"{total} anchors checked, {bad} missing")
