#!/usr/bin/env python3
"""Scaffold a new explainer-video project from this skill's Remotion template.

Usage:
  python3 <skill>/scripts/new_project.py <target-dir> [--theme ink|zone-night|paper|observatory] [--name my-video] [--no-install]

Copies assets/template to <target-dir>, sets the theme preset and package name, runs `npm install`
(unless --no-install), and builds a draft timeline (no API key needed) so the project typechecks and renders
immediately. The template ships a 2-scene example (Euclid's proof); replace script/script.json and src/scenes.
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TEMPLATE = HERE / "assets/template"
THEMES = ["ink", "zone-night", "paper", "observatory"]

ap = argparse.ArgumentParser()
ap.add_argument("target")
ap.add_argument("--theme", default="ink", choices=THEMES)
ap.add_argument("--name", default=None)
ap.add_argument("--no-install", action="store_true")
ap.add_argument("--force", action="store_true", help="allow a non-empty target directory")
a = ap.parse_args()

dst = Path(a.target).expanduser().resolve()
if dst.exists() and any(dst.iterdir()) and not a.force:
    sys.exit(f"{dst} exists and is not empty (use --force to copy into it anyway)")
shutil.copytree(TEMPLATE, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("node_modules", "out", "__pycache__"))
gi = dst / "gitignore"
if gi.exists():
    gi.rename(dst / ".gitignore")

theme = dst / "src/theme.ts"
theme.write_text(re.sub(r"export const PRESET: PresetName = '[^']+';", f"export const PRESET: PresetName = '{a.theme}';", theme.read_text()))
pkg = dst / "package.json"
p = json.loads(pkg.read_text())
p["name"] = re.sub(r"[^a-z0-9-]+", "-", (a.name or dst.name).lower()).strip("-") or "explainer-video-project"
pkg.write_text(json.dumps(p, indent=2) + "\n")

if not a.no_install:
    subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=dst, check=True)
subprocess.run([sys.executable, "scripts/tts.py", "--draft"], cwd=dst, check=True)

print(f"""
Project ready at {dst} (theme: {a.theme}).
Next:
  cd {dst}
  npx remotion studio src/index.ts        # live preview (optional)
  node scripts/stills.mjs                 # one still per narration line + contact sheets
  python3 scripts/tts.py                  # real voice (needs ELEVENLABS_API_KEY), or keep --draft
  npx remotion render src/index.ts ExplainerCaptioned out/explainer-captioned-raw.mp4
  python3 scripts/loudnorm.py out/explainer-captioned-raw.mp4 out/explainer-captioned.mp4
""")
