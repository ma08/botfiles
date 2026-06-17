#!/usr/bin/env bash
# Read-only verification summary for a Finder-browsable raw iPhone media archive.
# Usage: verify-raw-archive.sh <archive-root> [out-dir]

set -u

ARCHIVE_ROOT="${1:-}"
OUT_DIR="${2:-./iphone-media-archive-artifacts}"

if [[ -z "$ARCHIVE_ROOT" ]]; then
  printf 'Usage: %s <archive-root> [out-dir]\n' "$0" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"
STAMP="$(TZ=America/Los_Angeles date '+%Y%m%d-%H%M%S')"
LOG="$OUT_DIR/verify-raw-archive-$STAMP.log"

section() {
  printf '\n===== %s =====\n' "$1"
}

run() {
  printf '\n$ %s\n' "$*"
  "$@" 2>&1 || printf '[exit %s]\n' "$?"
}

{
  section "timestamp"
  TZ=America/Los_Angeles date '+%Y-%m-%d ~%I:%M%p PST'
  printf 'archive_root: %s\n' "$ARCHIVE_ROOT"

  section "space and existence"
  run df -h "$ARCHIVE_ROOT"
  run test -d "$ARCHIVE_ROOT"
  if [[ ! -d "$ARCHIVE_ROOT" ]]; then
    printf 'ERROR: archive root not found: %s\n' "$ARCHIVE_ROOT"
    exit 2
  fi

  section "size and count"
  run du -sh "$ARCHIVE_ROOT"
  printf 'non-AppleDouble files: '
  find "$ARCHIVE_ROOT" -type f ! -name '._*' -print | wc -l | tr -d ' '
  printf '\n'

  section "extension counts"
  find "$ARCHIVE_ROOT" -type f ! -name '._*' -print \
    | awk '
      {
        n=split($0, parts, "/")
        name=parts[n]
        ext=name
        if (ext !~ /\./) ext="[no extension]"
        else {
          sub(/^.*\./, "", ext)
          ext=toupper(ext)
        }
        counts[ext]++
      }
      END {
        for (ext in counts) print ext, counts[ext]
      }
    ' | sort

  section "sample file checks"
  for ext in HEIC JPG JPEG PNG MOV MP4 DNG AAE; do
    sample="$(find "$ARCHIVE_ROOT" -type f ! -name '._*' -iname "*.${ext}" -print | head -1)"
    if [[ -n "$sample" ]]; then
      printf '\n-- %s sample --\n%s\n' "$ext" "$sample"
      run file "$sample"
      run stat -f '%N | %z bytes | mtime %Sm' -t '%Y-%m-%d %H:%M:%S' "$sample"
      case "$ext" in
        HEIC|JPG|JPEG|PNG|DNG)
          if command -v sips >/dev/null 2>&1; then
            run sips -g pixelWidth -g pixelHeight "$sample"
          fi
          ;;
        MOV|MP4)
          if command -v ffprobe >/dev/null 2>&1; then
            run ffprobe -v error -show_entries format=duration,size -show_streams -of compact=p=0:nk=1 "$sample"
          fi
          ;;
      esac
    fi
  done
} >"$LOG"

printf '%s\n' "$LOG"
