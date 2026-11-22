#!/usr/bin/env bash
# Scene 1 shows page 1 of Levent Alpöge's note. The page is the author's work, so it isn't committed here.
# This downloads the public PDF and renders page 1 the same way the video did (link boxes hidden).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p public/img
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/remark.pdf" https://alpo.ge/remark.pdf
pdftoppm -r 110 -png -hide-annotations -f 1 -l 1 "$tmp/remark.pdf" public/img/remark
ls -la public/img/remark-1.png
